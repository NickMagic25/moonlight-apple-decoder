#include "pyrowave.hpp"
#include "pyrowave_bitstream.hpp"
#include <algorithm>
#include <bit>
#include <cstring>
#include <limits>

namespace mav {
namespace {
uint32_t le32(const uint8_t* p) { return uint32_t(p[0])|uint32_t(p[1])<<8|uint32_t(p[2])<<16|uint32_t(p[3])<<24; }
struct Invalid { const char* message; };
void require(bool value,const char* error) { if(!value)throw Invalid{error}; }

// Validate variable coefficient arrays before they can reach a GPU buffer. The
// shader speculatively reads the following word; its upload tail is padded.
void coefficients(const uint8_t* p,size_t n) {
    uint32_t w0=le32(p),w1=le32(p+4);
    require((w1&255)<200,"unsupported quantizer exponent");
    unsigned count=std::popcount(w0&65535);
    require(8+3*count<=n,"truncated coefficient controls");
    size_t cursor=8+3*count;unsigned signs=0;
    for(unsigned i=0;i<count;++i) {
        unsigned word=unsigned(p[8+2*i])|unsigned(p[9+2*i])<<8;
        unsigned base=p[8+2*count+i]&15;
        // Sum the eight independent 2-bit widths before touching their
        // magnitude bytes. Every prefix is nonnegative and bounded by this
        // total, so this retains the scalar per-group truncation contract.
        const unsigned plane_bytes=8*base+std::popcount(word&0x5555u)+2*std::popcount((word>>1)&0x5555u);
        require(plane_bytes<=n-cursor,"truncated magnitude planes");
        // The reference Metal kernel treats code_word == 0 as empty, including
        // when the base width is nonzero. Its encoded bytes still must fit.
        if(!word){cursor+=plane_bytes;continue;}
        uint64_t significant=0;
        for(unsigned group=0;group<8;++group) {
            unsigned planes=base+((word>>(2*group))&3);
            uint8_t nonzero=0;
            for(unsigned j=0;j<planes;++j)nonzero|=p[cursor+j];
            // Keep each group's eight coefficient bits in its own byte.
            significant|=uint64_t(nonzero)<<(group*8);
            cursor+=planes;
        }
        signs+=std::popcount(significant);
    }
    require((signs+7)/8<=n-cursor,"truncated coefficient signs");
}

struct Packets {
    const mav_pyrowave_fragment* p=nullptr;size_t count=0;bool has_loss=false;
    size_t index(size_t offset) const {
        size_t a=0,b=count;
        while(a<b){size_t m=a+(b-a)/2;if(p[m].offset<=offset)a=m+1;else b=m;}
        return a?a-1:count;
    }
    bool lost(size_t a,size_t b) const {
        if(!has_loss)return false;
        for(size_t i=index(a);i<count&&p[i].offset<b;++i)if(p[i].kind&MAV_PYROWAVE_FRAGMENT_LOST)return true;
        return false;
    }
    bool one(size_t a,size_t b) const {size_t i=index(a);return i<count&&b<=size_t(p[i].offset)+p[i].size;}
    size_t next(size_t offset,bool flagged,size_t end) const {
        for(size_t i=index(offset)+1;i<count;++i)
            if(!(p[i].kind&MAV_PYROWAVE_FRAGMENT_LOST)&&(!flagged||(p[i].kind&MAV_PYROWAVE_FRAGMENT_RECORD_START)))return p[i].offset;
        return end;
    }
};
}
ParseResult prepare_pyrowave(const Span* spans,size_t span_count,const mav_config& config,
                             const mav_access_unit& input,Prepared& out,std::string& error) {
    out=Prepared{};
    try {
        size_t total=0;
        for(size_t i=0;i<span_count;++i){require(spans[i].size<=MAV_MAX_ACCESS_UNIT_BYTES-total,"frame too large");total+=spans[i].size;}
        require(total>=8&&total%4==0,"frame is not word aligned");
        std::vector<uint8_t> bytes;bytes.reserve(total);
        for(size_t i=0;i<span_count;++i)if(spans[i].size)bytes.insert(bytes.end(),spans[i].data,spans[i].data+spans[i].size);
        Packets packets{input.pyrowave_fragments,input.pyrowave_fragment_count};
        require(packets.count<=MAV_MAX_SPANS&&(!packets.count||packets.p),"invalid fragment map");
        size_t extent=0;
        for(size_t i=0;i<packets.count;++i){const auto& f=packets.p[i];
            require(f.offset==extent&&f.size&&f.size<=total-extent&&f.kind<=MAV_PYROWAVE_FRAGMENT_RECORD_START,"fragment map does not tile frame");
            packets.has_loss|=(f.kind&MAV_PYROWAVE_FRAGMENT_LOST)!=0;extent+=f.size;}
        require(!packets.count||extent==total,"incomplete fragment map");
        require(input.pyrowave_critical_packets<=packets.count,"critical packet count exceeds frame");
        require(!packets.lost(0,8),"sequence header was lost");
        bool records=(le32(bytes.data())&0x80000000u)!=0;
        size_t sequence_at=records?0:8;
        require(sequence_at+8<=total,"missing sequence header");
        uint32_t header0=le32(bytes.data()+sequence_at),header1=le32(bytes.data()+sequence_at+4);
        require(header0!=UINT32_MAX&&(header0&0x80000000u)&&((header1>>24)&3)==0,"invalid sequence header");
        Format format;format.width=(header0&0x3fff)+1;format.height=((header0>>14)&0x3fff)+1;
        format.chroma=(header1&(1u<<26))?3:1;format.bit_depth=config.bit_depth?config.bit_depth:8;
        require(format.chroma==3||!(format.width%2||format.height%2),"420 dimensions must be even");
        require((!config.width||config.width==format.width)&&(!config.height||config.height==format.height)&&
                (!config.chroma_format||config.chroma_format==format.chroma),"sequence geometry differs from negotiated stream");
        // Vibepollo's pinned encoder leaves the sequence-header VUI bits zero
        // even when the negotiated stream is limited-range or BT.2020/PQ.
        // Their zero values therefore cannot override authenticated transport
        // color/HDR metadata. AU.color and config.fallback_color own that data.
        PyroWave::BlockLayout layout;
        require(layout.init(int(format.width),int(format.height),format.chroma==3?PyroWave::ChromaSubsampling::Chroma444:PyroWave::ChromaSubsampling::Chroma420),"invalid dimensions");
        uint32_t announced=header1&0xffffff,sequence=(header0>>28)&7;
        require(announced<=uint32_t(layout.block_count_32x32),"too many announced blocks");
        std::vector<uint8_t> seen(size_t(layout.block_count_32x32),0);
        size_t coarse=0;
        for(int c=0;c<3;++c)for(int band=0;band<4;++band)coarse+=layout.block_meta[c][4][band].block_count_32x32;
        bool sequence_seen=false,partial=false,coarse_intact=true,past_coarse=false,aligned=false;
        bool known_coarse=input.pyrowave_critical_packets!=0;
        if(known_coarse)for(size_t i=0;i<input.pyrowave_critical_packets;++i)if(packets.p[i].kind&MAV_PYROWAVE_FRAGMENT_LOST)coarse_intact=false;
        bool flagged=packets.count&&(packets.p[0].kind&MAV_PYROWAVE_FRAGMENT_RECORD_START);
        size_t payload_size=packets.count>=2?size_t(packets.p[0].size)+8:std::numeric_limits<size_t>::max();
        uint32_t block_count=0;
        out.bytes.reserve(total);
        auto note_loss=[&]{partial=true;if(!known_coarse&&!past_coarse)coarse_intact=false;};
        auto walk=[&](size_t start,size_t end,bool allow_padding,bool allow_loss){
            size_t cursor=start;
            while(cursor<end){
                if(allow_loss&&packets.lost(cursor,std::min(cursor+8,end))){
                    note_loss();cursor=flagged||aligned?packets.next(cursor,flagged,end):end;continue;}
                require(end-cursor>=8,"truncated record header");
                const uint8_t* p=bytes.data()+cursor;uint32_t a=le32(p),b=le32(p+4);
                if(a==UINT32_MAX){
                    require(allow_padding&&sequence_seen,"unexpected padding record");
                    uint64_t length=8+uint64_t(b)*4;require(length<=end-cursor,"padding exceeds frame");
                    if(!packets.lost(cursor,cursor+size_t(length)))
                        for(size_t i=8;i<size_t(length);++i)require(!p[i],"nonzero padding");
                    cursor+=size_t(length);continue;
                }
                size_t length=8;
                if(a&0x80000000u){
                    require(!sequence_seen&&cursor==sequence_at&&a==header0&&b==header1,"second or misplaced sequence header");sequence_seen=true;
                }else{
                    require(sequence_seen,"block precedes sequence header");
                    require(((a>>28)&7)==sequence,"block sequence differs from frame");
                    size_t words=(a>>16)&4095;require(words>=2,"block is smaller than header");length=words*4;
                    require(length<=end-cursor,"block exceeds frame");
                    size_t index=b>>8;require(index<seen.size(),"block index out of range");
                    if(index>=coarse)past_coarse=true;
                    if(allow_loss&&packets.lost(cursor,cursor+length)){note_loss();aligned=false;cursor+=length;continue;}
                    require(!seen[index],"duplicate block index");seen[index]=1;
                    coefficients(p,length);++block_count;
                    // Fragment boundary searches only decide how to recover
                    // after loss. An intact map still receives all structural
                    // and coefficient validation without those per-record queries.
                    aligned=packets.has_loss&&index>=coarse&&length+8<=payload_size&&packets.one(cursor,cursor+length);
                }
                out.bytes.insert(out.bytes.end(),p,p+length);cursor+=length;
            }
        };
        if(records)walk(0,total,true,true);
        else {
            require(!packets.lost(0,total),"loss in length-prefixed frame");
            uint32_t count=le32(bytes.data());require(count&&count<=(total-4)/12,"invalid packet count");
            size_t cursor=4;
            for(uint32_t i=0;i<count;++i){require(total-cursor>=4,"missing packet length");size_t size=le32(bytes.data()+cursor);cursor+=4;
                require(size>=8&&size%4==0&&size<=total-cursor,"invalid packet length");walk(cursor,cursor+size,false,false);cursor+=size;}
            require(cursor==total,"data after last packet");
        }
        require(sequence_seen,"frame has no sequence header");
        require(block_count<=announced,"more blocks than announced");
        require(partial?(coarse_intact&&uint64_t(block_count)*10>uint64_t(announced)*9):block_count==announced,"insufficient intact frame records");
        out.format=std::move(format);out.random_access=true;out.displayed_frames=1;
        out.samples.push_back({0,out.bytes.size(),true,false,true});
        out.compressed_copy_count=out.bytes.size()>8?4:2;
        out.compressed_copy_bytes=total+out.bytes.size()+2*(out.bytes.size()-8);
        return ParseResult::Ok;
    } catch(const Invalid& e){error=e.message;out=Prepared{};return ParseResult::Malformed;}
}
}
