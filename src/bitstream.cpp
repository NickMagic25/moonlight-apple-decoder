#include "bitstream.hpp"
#include <algorithm>
#include <cstring>
#include <limits>
#include <map>
#include <optional>
#include <stdexcept>
#include <tuple>
#include <utility>

namespace mav {
bool Color::operator==(const Color& b) const {
    return std::tie(primaries,transfer,matrix,description_valid,range_valid,full_range,
                    chroma_position,chroma_position_valid,mastering_valid,content_light_valid,mastering,content_light) ==
           std::tie(b.primaries,b.transfer,b.matrix,b.description_valid,b.range_valid,b.full_range,
                    b.chroma_position,b.chroma_position_valid,b.mastering_valid,b.content_light_valid,b.mastering,b.content_light);
}
bool Format::operator==(const Format& b) const {
    return width == b.width && height == b.height && profile == b.profile && level == b.level &&
           bit_depth == b.bit_depth && chroma == b.chroma && color == b.color && av1c == b.av1c &&
           parameter_sets == b.parameter_sets;
}
namespace {
constexpr size_t MaxBytes = 64u * 1024 * 1024, MaxUnits = 4096;
struct Error { ParseResult result; const char* message; };
[[noreturn]] void malformed(const char* s) { throw Error{ParseResult::Malformed,s}; }
[[noreturn]] void unsupported(const char* s) { throw Error{ParseResult::Unsupported,s}; }
[[noreturn]] void need_config(const char* s) { throw Error{ParseResult::NeedConfiguration,s}; }
class Bits {
    const uint8_t* p_; size_t count_, pos_ = 0;
public:
    Bits(const uint8_t* p, size_t n): p_(p), count_(n*8) {}
    uint32_t get(unsigned n) {
        if (n > 32 || n > count_ - pos_) malformed("truncated bit syntax");
        uint32_t v = 0;
        for (unsigned i = 0; i < n; ++i, ++pos_) v = (v << 1) | ((p_[pos_/8] >> (7-pos_%8)) & 1);
        return v;
    }
    bool bit() { return get(1) != 0; }
    void skip(size_t n) { if (n > count_ - pos_) malformed("truncated bit syntax"); pos_ += n; }
    uint32_t ue(uint32_t max = std::numeric_limits<uint32_t>::max()-1) {
        unsigned zeros = 0;
        while (!bit()) if (++zeros > 31) malformed("Exp-Golomb integer overflow");
        uint32_t value = ((uint32_t(1) << zeros)-1) + get(zeros);
        if (value > max) malformed("Exp-Golomb value out of bounds");
        return value;
    }
    int32_t se() { uint32_t v = ue(0x7ffffffe); return v & 1 ? int32_t((v+1)/2) : -int32_t(v/2); }
    void trailing() { if (!bit()) malformed("missing trailing one bit"); while (pos_ < count_) if (bit()) malformed("nonzero trailing padding"); }
    size_t left() const { return count_-pos_; }
};
uint64_t leb(const uint8_t* p, size_t n, size_t& at) {
    uint64_t value = 0;
    for (unsigned i = 0; i < 8; ++i) {
        if (at >= n) malformed("truncated AV1 LEB128 length");
        uint8_t b = p[at++];
        value |= uint64_t(b & 127) << (7*i);
        if (!(b & 128)) return value;
    }
    malformed("AV1 LEB128 exceeds eight bytes");
}
uint16_t be16(const uint8_t* p) { return uint16_t(p[0]) << 8 | p[1]; }
uint32_t be32(const uint8_t* p) { return uint32_t(p[0]) << 24 | uint32_t(p[1]) << 16 | uint32_t(p[2]) << 8 | p[3]; }
void put16(uint8_t* p, uint32_t v) { p[0] = uint8_t(v >> 8); p[1] = uint8_t(v); }
void put32(uint8_t* p, uint32_t v) { for (int i=3;i>=0;--i) { p[i]=uint8_t(v); v>>=8; } }
void merge_hdr(Color& destination,const Color& source) {
    if (source.mastering_valid) {destination.mastering=source.mastering;destination.mastering_valid=true;}
    if (source.content_light_valid) {destination.content_light=source.content_light;destination.content_light_valid=true;}
}
struct Obu { size_t start, payload, size, end; unsigned type; };
std::vector<Obu> obus(const uint8_t* p, size_t n) {
    std::vector<Obu> out;
    size_t pos=0;
    while (pos<n) {
        if (out.size() == MaxUnits) malformed("too many AV1 OBUs");
        size_t start=pos;
        uint8_t header=p[pos++];
        if (header & 0x81) malformed("AV1 forbidden or reserved header bit set");
        unsigned type=(header>>3)&15;
        if (header & 4) {
            if (pos==n) malformed("truncated AV1 OBU extension");
            uint8_t ext=p[pos++];
            if (ext & 7) malformed("AV1 extension reserved bits set");
            if (ext >> 3) unsupported("AV1 temporal/spatial layers beyond layer zero unsupported");
        }
        if (!(header & 2)) unsupported("AV1 requires low-overhead OBUs with explicit size fields; import Annex B/container framing first");
        uint64_t size=leb(p,n,pos);
        if (size > n-pos) malformed("AV1 OBU payload exceeds access unit");
        if (type==8) unsupported("AV1 tile lists are outside the single-layer low-delay path");
        if (type==2 && size) malformed("AV1 temporal delimiter payload must be empty");
        out.push_back({start,pos,size_t(size),pos+size_t(size),type});
        pos+=size_t(size);
    }
    return out;
}
struct Sequence {
    Format format;
    bool valid=false,reduced=false,decoder_model=false,equal_interval=false,model_op=false;
    unsigned presentation_bits=0,removal_bits=0,order_bits=0,id_bits=0;
    unsigned screen_tools=2,integer_mv=2,width_bits=0,height_bits=0;
    bool initial_delay=false; uint8_t delay=0,tier=0,chroma_sample_position=0;
    bool enable_superres=false;
};
Sequence sequence(const uint8_t* p,size_t n) {
    if (n>65535) malformed("AV1 sequence header exceeds configuration size limit");
    Sequence s; Bits b(p,n); auto& f=s.format;
    f.profile=uint8_t(b.get(3));
    if (f.profile != 0) unsupported("AV1 baseline requires Main profile");
    bool still=b.bit(); s.reduced=b.bit();
    if (s.reduced && !still) malformed("AV1 reduced header without still_picture");
    if (s.reduced) f.level=uint8_t(b.get(5));
    else {
        unsigned buffer_bits=0;
        if (b.bit()) {
            if (!b.get(32) || !b.get(32)) malformed("AV1 timing denominator is zero");
            s.equal_interval=b.bit(); if (s.equal_interval) b.ue();
            s.decoder_model=b.bit();
            if (s.decoder_model) {
                buffer_bits=b.get(5)+1; b.skip(32); s.removal_bits=b.get(5)+1; s.presentation_bits=b.get(5)+1;
            }
        }
        bool delay_present=b.bit();
        if (b.get(5)) unsupported("AV1 multiple operating points unsupported");
        unsigned operating_point=b.get(12);
        if (operating_point != 0 && operating_point != 0x101) unsupported("AV1 operating point contains additional layers");
        f.level=uint8_t(b.get(5));
        if (f.level>7) s.tier=uint8_t(b.get(1));
        if (s.decoder_model) {
            s.model_op=b.bit();
            if (s.model_op) { b.skip(buffer_bits*2); b.skip(1); }
        }
        if (delay_present) { s.initial_delay=b.bit(); if (s.initial_delay) s.delay=uint8_t(b.get(4)); }
    }
    if (f.level>23 && f.level!=31) malformed("reserved AV1 level index");
    s.width_bits=b.get(4)+1; s.height_bits=b.get(4)+1;
    f.width=b.get(s.width_bits)+1; f.height=b.get(s.height_bits)+1;
    if (!s.reduced && b.bit()) { unsigned delta=b.get(4)+2; s.id_bits=delta+b.get(3)+1; }
    b.skip(3);
    if (!s.reduced) {
        b.skip(4); bool order=b.bit(); if (order) b.skip(2);
        if (!b.bit()) s.screen_tools=b.get(1);
        if (s.screen_tools>0 && !b.bit()) s.integer_mv=b.get(1);
        if (order) s.order_bits=b.get(3)+1;
    }
    s.enable_superres=b.bit(); b.skip(2);
    f.bit_depth=b.bit()?10:8;
    if (b.bit()) unsupported("AV1 monochrome is outside the required 4:2:0 baseline");
    auto& c=f.color;
    c.description_valid=b.bit();
    if (c.description_valid) { c.primaries=uint16_t(b.get(8)); c.transfer=uint16_t(b.get(8)); c.matrix=uint16_t(b.get(8)); }
    if (c.primaries==1 && c.transfer==13 && c.matrix==0) unsupported("AV1 RGB identity signaling is not Main 4:2:0");
    c.full_range=b.bit(); c.range_valid=true;
    s.chroma_sample_position=uint8_t(b.get(2));
    if (s.chroma_sample_position==3) malformed("reserved AV1 chroma sample position");
    // Normalize to HEVC chroma_sample_loc_type: 0=left, 2=top-left.
    c.chroma_position=s.chroma_sample_position==2?2:0;
    c.chroma_position_valid=s.chroma_sample_position!=0;
    b.skip(1); b.skip(1); b.trailing();
    s.valid=true; return s;
}
void make_av1c(Sequence& seq,const uint8_t* p,size_t n) {
    auto& f=seq.format;
    f.av1c={0x81,uint8_t((f.profile<<5)|f.level),uint8_t((seq.tier<<7)|((f.bit_depth==10)<<6)|12|seq.chroma_sample_position),
            uint8_t(seq.initial_delay?(0x10|seq.delay):0)};
    f.av1c.insert(f.av1c.end(),p,p+n);
}
Sample av1_frame(const uint8_t* p,size_t n,const Sequence& s) {
    Bits b(p,n); Sample sample; bool resilient=true;
    if (!s.reduced) {
        sample.show_existing=b.bit();
        if (sample.show_existing) {
            sample.existing_frame_index=uint8_t(b.get(3));
            if (s.decoder_model && !s.equal_interval) b.skip(s.presentation_bits);
            b.skip(s.id_bits);
            // Exact reference validity is enforced by the decoder; syntax alone
            // must also support fixtures beginning after an earlier submission.
            return sample;
        }
        sample.frame_type=uint8_t(b.get(2)); sample.display=b.bit();
        if (sample.display && s.decoder_model && !s.equal_interval) b.skip(s.presentation_bits);
        if (!sample.display) b.skip(1);
        if (sample.frame_type!=3 && !(sample.frame_type==0 && sample.display)) resilient=b.bit();
    }
    b.skip(1);
    bool screen=s.screen_tools==2?b.bit():bool(s.screen_tools);
    if (screen && s.integer_mv==2) b.skip(1);
    b.skip(s.id_bits);
    if (!s.reduced && sample.frame_type!=3) b.skip(1); // frame_size_override_flag
    b.skip(s.order_bits);
    bool intra=sample.frame_type==0 || sample.frame_type==2;
    if (!intra && !resilient) b.skip(3);
    if (s.decoder_model && b.bit() && s.model_op) b.skip(s.removal_bits);
    sample.refresh_frame_flags=(sample.frame_type==3 || (sample.frame_type==0 && sample.display))?255:uint8_t(b.get(8));
    sample.random_access=sample.frame_type==0 && sample.display;
    return sample;
}
void av1_metadata(const uint8_t* p,size_t n,Color& c) {
    size_t at=0; uint64_t type=leb(p,n,at);
    if (type==1) {
        if (n-at<5) malformed("truncated AV1 HDR content light metadata");
        std::copy_n(p+at,4,c.content_light.begin()); c.content_light_valid=true;
        Bits trailing(p+at+4,n-at-4); trailing.trailing();
    } else if (type==2) {
        if (n-at<25) malformed("truncated AV1 mastering display metadata");
        // AV1 uses 2^-16 chromaticity, 2^-8 max nit, 2^-14 min nit.
        // AV1 primary order is R,G,B; HEVC/ST2086 payload order is G,B,R.
        constexpr unsigned component[8]={2,3,4,5,0,1,6,7};
        for (unsigned i=0;i<8;++i) put16(c.mastering.data()+i*2,(uint32_t(be16(p+at+component[i]*2))*50000+32768)/65536);
        uint64_t max=(uint64_t(be32(p+at+16))*10000+128)/256;
        uint64_t min=(uint64_t(be32(p+at+20))*10000+8192)/16384;
        if (max>UINT32_MAX || min>UINT32_MAX) malformed("HDR mastering luminance out of bounds");
        put32(c.mastering.data()+16,uint32_t(max)); put32(c.mastering.data()+20,uint32_t(min));
        c.mastering_valid=true; Bits trailing(p+at+24,n-at-24); trailing.trailing();
    } else if (type==3) {
        if (at==n) malformed("truncated AV1 scalability metadata");
        // Every predefined mode has multiple spatial or temporal layers.
        // SCALABILITY_SS can describe the supported single-layer arrangement.
        if (p[at++]!=14) unsupported("AV1 scalability metadata requires unsupported layers");
        Bits b(p+at,n-at);
        if (b.get(2)) unsupported("AV1 scalability metadata contains multiple spatial layers");
        bool dimensions=b.bit(),description=b.bit(),groups=b.bit();
        if (b.get(3)) malformed("AV1 scalability metadata reserved bits nonzero");
        if (dimensions) b.skip(32);
        if (description) b.skip(8);
        if (groups) {
            unsigned count=b.get(8);
            for (unsigned i=0;i<count;++i) {
                if (b.get(3)) unsupported("AV1 scalability metadata contains multiple temporal layers");
                b.skip(2); unsigned refs=b.get(3); b.skip(refs*8);
            }
        }
        b.trailing();
    }
}

struct Nal { size_t start,size; unsigned type; };
std::vector<Nal> nals(const uint8_t* p,size_t n) {
    std::vector<Nal> out;
    auto next=[&](size_t pos,size_t& start,size_t& payload)->bool {
        unsigned zeros=0;
        for (size_t i=pos;i<n;++i) {
            if (!p[i]) { ++zeros; continue; }
            if (p[i]==1 && zeros>=2) { start=i-zeros; payload=i+1; return true; }
            zeros=0;
        }
        return false;
    };
    size_t start=0,payload=0;
    if (!next(0,start,payload)) malformed("HEVC access unit lacks Annex B start code");
    for (size_t i=0;i<start;++i) if (p[i]) malformed("nonzero bytes before HEVC start code");
    for (;;) {
        size_t next_start=n,next_payload=n;
        bool found=next(payload,next_start,next_payload);
        size_t end=next_start;
        while (end>payload && p[end-1]==0) --end;
        if (end-payload<2) malformed("empty or truncated HEVC NAL unit");
        if (p[payload]&128) malformed("HEVC forbidden bit set");
        unsigned layer=((p[payload]&1)<<5)|(p[payload+1]>>3);
        if (layer) unsupported("HEVC multilayer stream unsupported");
        if (!(p[payload+1]&7)) malformed("HEVC temporal_id_plus1 is zero");
        unsigned type=(p[payload]>>1)&63;
        if (out.size()==MaxUnits) malformed("too many HEVC NAL units");
        out.push_back({payload,end-payload,type});
        if (!found) break;
        payload=next_payload;
    }
    return out;
}
std::vector<uint8_t> rbsp(const uint8_t* p,size_t n,size_t limit=MaxBytes) {
    std::vector<uint8_t> out; out.reserve(std::min(n,limit)); unsigned zeros=0;
    for (size_t i=0;i<n && out.size()<limit;++i) {
        uint8_t v=p[i];
        if (zeros>=2 && v==3) {
            if (i+1==n || p[i+1]>3) malformed("invalid HEVC emulation prevention byte");
            zeros=0; continue;
        }
        out.push_back(v); zeros=v==0?zeros+1:0;
    }
    return out;
}
struct Sps { unsigned id=0,vps=0,ctb_log2=0,poc_bits=0; uint32_t coded_width=0,coded_height=0; Format format; std::vector<uint8_t> bytes; };
struct Pps { unsigned id=0,sps=0,extra_bits=0; bool dependent=false,output_flag=false; std::vector<uint8_t> bytes; };
void ptl(Bits& b,unsigned sublayers,Format& f) {
    if (b.get(2)) unsupported("HEVC nonzero profile space unsupported");
    b.skip(1); f.profile=uint8_t(b.get(5)); uint32_t compat=b.get(32);
    b.skip(48); f.level=uint8_t(b.get(8));
    if (f.profile!=1 && f.profile!=2) {
        if (compat & (uint32_t(1)<<30)) f.profile=1;
        else if (compat & (uint32_t(1)<<29)) f.profile=2;
        else unsupported("HEVC baseline requires Main or Main10 profile");
    }
    bool profile[8]{},level[8]{};
    for (unsigned i=0;i<sublayers;++i) { profile[i]=b.bit(); level[i]=b.bit(); }
    if (sublayers) for (unsigned i=sublayers;i<8;++i) if (b.get(2)) malformed("HEVC PTL reserved bits nonzero");
    for (unsigned i=0;i<sublayers;++i) { if (profile[i]) b.skip(88); if (level[i]) b.skip(8); }
}
void scaling_lists(Bits& b) {
    for (unsigned size=0;size<4;++size) for (unsigned matrix=0;matrix<6;matrix+=(size==3?3:1)) {
        if (!b.bit()) b.ue(matrix);
        else { if (size>1) b.se(); for (unsigned i=0;i<std::min(64u,1u<<(4+2*size));++i) b.se(); }
    }
}
void hevc_hrd(Bits& b,unsigned sublayers) {
    bool nal=b.bit(),vcl=b.bit(),subpic=false;
    if (nal || vcl) {
        subpic=b.bit(); if (subpic) b.skip(8+5+1+5);
        b.skip(4+4); if (subpic) b.skip(4);
        b.skip(5+5+5);
    }
    for (unsigned i=0;i<=sublayers;++i) {
        bool fixed=b.bit(),within=fixed || b.bit(),low=false;
        if (within) b.ue(); else low=b.bit();
        unsigned count=low?1:b.ue(31)+1;
        auto sublayer=[&] {
            for (unsigned cpb=0;cpb<count;++cpb) { b.ue(); b.ue(); if (subpic) { b.ue(); b.ue(); } b.skip(1); }
        };
        if (nal) sublayer(); if (vcl) sublayer();
    }
}
void hevc_vui(Bits& b,Color& c,unsigned sublayers) {
    if (b.bit()) { unsigned id=b.get(8); if (id==255) b.skip(32); }
    if (b.bit()) b.skip(1);
    if (b.bit()) {
        b.skip(3); c.full_range=b.bit(); c.range_valid=true;
        c.description_valid=b.bit();
        if (c.description_valid) { c.primaries=uint16_t(b.get(8)); c.transfer=uint16_t(b.get(8)); c.matrix=uint16_t(b.get(8)); }
    }
    if (b.bit()) {
        c.chroma_position=uint8_t(b.ue(5)); unsigned bottom=b.ue(5); c.chroma_position_valid=true;
        if (bottom!=c.chroma_position) unsupported("HEVC differing top/bottom chroma locations unsupported");
    }
    b.skip(1); bool field_seq=b.bit(); b.skip(1);
    if (field_seq) unsupported("HEVC interlaced/field sequence requires temporal processing");
    if (b.bit()) { b.ue(65535); b.ue(65535); b.ue(65535); b.ue(65535); }
    if (b.bit()) {
        if (!b.get(32) || !b.get(32)) malformed("HEVC VUI timing denominator is zero");
        if (b.bit()) b.ue();
        if (b.bit()) hevc_hrd(b,sublayers);
    }
    if (b.bit()) { b.skip(3); b.ue(4095); b.ue(16); b.ue(16); b.ue(16); b.ue(16); }
}
unsigned hevc_vps(const uint8_t* p,size_t n) {
    if (n>65535) malformed("HEVC VPS exceeds configuration size limit");
    auto raw=rbsp(p+2,n-2); Bits b(raw.data(),raw.size()); unsigned id=b.get(4);
    b.skip(2); if (b.get(6)) unsupported("HEVC VPS contains multiple layers");
    unsigned sublayers=b.get(3); if (sublayers>6) malformed("HEVC invalid VPS sublayers");
    b.skip(1); if (b.get(16)!=65535) malformed("HEVC invalid VPS reserved bits");
    Format f; ptl(b,sublayers,f);
    bool all=b.bit();
    for (unsigned i=all?0:sublayers;i<=sublayers;++i) {
        unsigned buffering=b.ue(15),reorder=b.ue(15); b.ue();
        if (reorder>buffering) malformed("HEVC VPS reorder exceeds DPB");
    }
    if (b.get(6)) unsupported("HEVC VPS max layer ID must be zero");
    unsigned layer_sets=b.ue(1023); for (unsigned i=0;i<layer_sets;++i) b.skip(1);
    if (b.bit()) {
        if (!b.get(32) || !b.get(32)) malformed("HEVC VPS timing denominator is zero");
        if (b.bit()) b.ue();
        unsigned count=b.ue(1024);
        if (count>1) unsupported("HEVC multiple VPS HRD parameter sets unsupported");
        if (count) { b.ue(layer_sets); hevc_hrd(b,sublayers); }
    }
    if (b.bit()) unsupported("HEVC VPS extensions unsupported");
    b.trailing(); return id;
}
Sps hevc_sps(const uint8_t* p,size_t n) {
    if (n>65535) malformed("HEVC SPS exceeds configuration size limit");
    auto raw=rbsp(p+2,n-2); Bits b(raw.data(),raw.size()); Sps s;
    s.vps=b.get(4); unsigned sublayers=b.get(3); if (sublayers>6) malformed("HEVC invalid sublayer count");
    b.skip(1); ptl(b,sublayers,s.format); s.id=b.ue(15);
    unsigned chroma=b.ue(3); if (chroma!=1) unsupported("HEVC baseline requires 4:2:0 chroma");
    s.coded_width=b.ue(65535); s.coded_height=b.ue(65535);
    if (!s.coded_width || !s.coded_height) malformed("HEVC zero picture dimension");
    uint32_t left=0,right=0,top=0,bottom=0;
    if (b.bit()) { left=b.ue(32767); right=b.ue(32767); top=b.ue(32767); bottom=b.ue(32767); }
    if (2*(left+right)>=s.coded_width || 2*(top+bottom)>=s.coded_height) malformed("HEVC conformance crop exceeds picture");
    s.format.width=s.coded_width-2*(left+right); s.format.height=s.coded_height-2*(top+bottom);
    unsigned luma=b.ue(8)+8,chroma_depth=b.ue(8)+8;
    if (luma!=chroma_depth) unsupported("HEVC unequal luma/chroma depth unsupported");
    if (luma!=8 && luma!=10) unsupported("HEVC baseline requires 8 or 10 bit samples");
    if (s.format.profile==1 && luma!=8) malformed("HEVC Main profile cannot signal 10-bit samples");
    s.format.bit_depth=uint8_t(luma); s.poc_bits=b.ue(12)+4;
    bool all=b.bit();
    for (unsigned i=all?0:sublayers;i<=sublayers;++i) {
        unsigned max_dpb=b.ue(15),reorder=b.ue(15); b.ue();
        if (reorder>max_dpb) malformed("HEVC reordering exceeds DPB");
        if (reorder) unsupported("HEVC SPS requires display reordering; use a temporal-processing backend");
    }
    unsigned min_cb=b.ue(3)+3,diff_cb=b.ue(3); s.ctb_log2=min_cb+diff_cb;
    if (s.ctb_log2>6) malformed("HEVC coding block size exceeds 64");
    b.ue(3); b.ue(3); b.ue(4); b.ue(4);
    if (b.bit() && b.bit()) scaling_lists(b);
    b.skip(2);
    if (b.bit()) { b.skip(8); b.ue(3); b.ue(3); b.skip(1); }
    unsigned rps_count=b.ue(64); std::vector<unsigned> delta_counts;
    for (unsigned i=0;i<rps_count;++i) {
        unsigned count=0;
        if (i && b.bit()) {
            b.skip(1); b.ue(32767);
            for (unsigned j=0;j<=delta_counts.back();++j) { bool used=b.bit(); bool use=used || b.bit(); count+=use; }
        } else {
            unsigned neg=b.ue(16),pos=b.ue(16); count=neg+pos;
            if (count>16) malformed("HEVC too many short term references");
            for (unsigned j=0;j<count;++j) { b.ue(32767); b.skip(1); }
        }
        if (count>16) malformed("HEVC predicted reference set exceeds DPB");
        delta_counts.push_back(count);
    }
    if (b.bit()) { unsigned count=b.ue(32); for (unsigned i=0;i<count;++i) b.skip(s.poc_bits+1); }
    b.skip(2); if (b.bit()) hevc_vui(b,s.format.color,sublayers);
    if (b.bit() && b.get(8)) unsupported("HEVC SPS range/multilayer extensions unsupported");
    b.trailing();
    s.bytes.assign(p,p+n); return s;
}
Pps hevc_pps(const uint8_t* p,size_t n) {
    if (n>65535) malformed("HEVC PPS exceeds configuration size limit");
    auto raw=rbsp(p+2,n-2); Bits b(raw.data(),raw.size()); Pps pps;
    pps.id=b.ue(63); pps.sps=b.ue(15); pps.dependent=b.bit(); pps.output_flag=b.bit(); pps.extra_bits=b.get(3);
    b.skip(2); b.ue(14); b.ue(14); b.se(); b.skip(2);
    if (b.bit()) b.ue(6);
    b.se(); b.se(); b.skip(4);
    bool tiles=b.bit(); b.skip(1);
    if (tiles) {
        unsigned columns=b.ue(19),rows=b.ue(21);
        if (!b.bit()) { for (unsigned i=0;i<columns;++i) b.ue(65535); for (unsigned i=0;i<rows;++i) b.ue(65535); }
        b.skip(1);
    }
    b.skip(1);
    if (b.bit()) { b.skip(1); if (!b.bit()) { b.se(); b.se(); } }
    if (b.bit()) scaling_lists(b);
    b.skip(1); b.ue(4); b.skip(1);
    if (b.bit() && b.get(8)) unsupported("HEVC PPS range/multilayer extensions unsupported");
    b.trailing(); pps.bytes.assign(p,p+n); return pps;
}
void hevc_sei(const uint8_t* p,size_t n,Color& c) {
    auto raw=rbsp(p+2,n-2); size_t at=0;
    while (at<raw.size()) {
        if (raw[at]==128 && at+1==raw.size()) break;
        size_t type=0,size=0;
        while (at<raw.size() && raw[at]==255) { type+=255; ++at; }
        if (at==raw.size()) malformed("truncated HEVC SEI type"); type+=raw[at++];
        while (at<raw.size() && raw[at]==255) { size+=255; ++at; }
        if (at==raw.size()) malformed("truncated HEVC SEI size"); size+=raw[at++];
        if (size>raw.size()-at) malformed("HEVC SEI exceeds payload");
        if (type==137) { if (size!=24) malformed("HEVC mastering metadata length"); std::copy_n(raw.data()+at,24,c.mastering.begin()); c.mastering_valid=true; }
        if (type==144) { if (size!=4) malformed("HEVC content light metadata length"); std::copy_n(raw.data()+at,4,c.content_light.begin()); c.content_light_valid=true; }
        at+=size;
    }
}
unsigned ceil_log2(uint64_t value) { unsigned b=0; while ((uint64_t(1)<<b)<value) ++b; return b; }
}

struct Bitstream::State {
    Codec codec; Sequence seq;
    Format format;
    std::map<unsigned,std::vector<uint8_t>> vps;
    std::map<unsigned,Sps> sps;
    std::map<unsigned,Pps> pps;
    Color metadata;
    unsigned active_pps=64;
    explicit State(Codec c):codec(c) {}
    ParseResult av1(const uint8_t*,size_t,Prepared&,bool copy=true);
    ParseResult hevc(const uint8_t*,size_t,Prepared&);
};
ParseResult Bitstream::State::av1(const uint8_t* p,size_t n,Prepared& out,bool copy) {
    auto units=obus(p,n); bool active=false,needs_tiles=false,has_tiles=false; size_t group_start=0;
    Color unit_metadata;
    Sample current;
    auto finish=[&](size_t end) {
        if (!active) return;
        if (needs_tiles && !has_tiles) malformed("AV1 frame header has no tile group");
        current.offset=group_start; current.size=end-group_start;
        out.samples.push_back(current); active=false; group_start=end;
    };
    for (const auto& u:units) {
        if (u.type==1) {
            if (active || !out.samples.empty()) unsupported("AV1 sequence changes within a temporal unit unsupported");
            Sequence next=sequence(p+u.payload,u.size); make_av1c(next,p+u.start,u.end-u.start);
            if (seq.valid && next.format.av1c!=seq.format.av1c) metadata=unit_metadata;
            seq=std::move(next);
        } else if (u.type==3 || u.type==6) {
            if (!seq.valid) need_config("AV1 frame precedes sequence header");
            finish(u.start); current=av1_frame(p+u.payload,u.size,seq);
            if (u.type==6 && current.show_existing) malformed("AV1 show_existing must use a frame header OBU");
            active=true; needs_tiles=u.type==3 && !current.show_existing; has_tiles=u.type==6;
            if (out.samples.size()>=64) unsupported("AV1 temporal unit exceeds 64 coded frames");
        } else if (u.type==4) {
            if (!active || !needs_tiles) malformed("AV1 tile group lacks a frame header");
            if (!u.size) malformed("empty AV1 tile group");
            has_tiles=true;
        } else if (u.type==7) {
            if (!active || !needs_tiles) malformed("AV1 redundant frame header without primary header");
        } else if (u.type==2) {
            if (active || !out.samples.empty()) malformed("multiple AV1 temporal units in one access unit");
        } else if (u.type==5) {av1_metadata(p+u.payload,u.size,unit_metadata);merge_hdr(metadata,unit_metadata);}
    }
    finish(n);
    if (!seq.valid) need_config("AV1 access unit has no cached sequence header");
    out.format=seq.format;
    if (metadata.mastering_valid) { out.format.color.mastering=metadata.mastering; out.format.color.mastering_valid=true; }
    if (metadata.content_light_valid) { out.format.color.content_light=metadata.content_light; out.format.color.content_light_valid=true; }
    for (const auto& sample:out.samples) out.displayed_frames+=sample.display;
    if (out.displayed_frames>1) unsupported("one AV1 access unit may contain only one displayed image");
    out.random_access=!out.samples.empty() && out.samples.front().random_access;
    out.config_changed=!(format==out.format); format=out.format;
    if (copy) out.bytes.assign(p,p+n);
    out.compressed_copy_count=1; out.compressed_copy_bytes=n;
    return ParseResult::Ok;
}
ParseResult Bitstream::State::hevc(const uint8_t* p,size_t n,Prepared& out) {
    auto units=nals(p,n); bool picture=false; unsigned selected_pps=64; Sample sample;
    Color unit_metadata;
    // Parameter sets can arrive in any order before slices in the same AU.
    bool saw_vcl=false;
    for (const auto& u:units) {
        const uint8_t* bytes=p+u.start;
        if (u.type<=31) saw_vcl=true;
        if (saw_vcl && u.type>=32 && u.type<=34) malformed("HEVC parameter sets must precede the picture they configure");
        if (u.type==32) {
            unsigned id=hevc_vps(bytes,u.size); vps[id]=std::vector<uint8_t>(bytes,bytes+u.size);
        } else if (u.type==33) { Sps s=hevc_sps(bytes,u.size); sps[s.id]=std::move(s); }
        else if (u.type==34) { Pps pp=hevc_pps(bytes,u.size); pps[pp.id]=std::move(pp); }
        else if (u.type==39 || u.type==40) hevc_sei(bytes,u.size,unit_metadata);
    }
    for (const auto& u:units) {
        const uint8_t* bytes=p+u.start;
        if (u.type<=31) {
            if (u.type>=22 || (u.type>=10 && u.type<=15)) unsupported("HEVC reserved VCL NAL type");
            if (u.type>=6 && u.type<=9) unsupported("HEVC leading pictures require temporal processing");
            // Only the bounded slice prefix is parsed; entropy-coded bytes are
            // preserved in the submitted NAL and do not need an RBSP copy.
            auto raw=rbsp(bytes+2,u.size-2,256); Bits b(raw.data(),raw.size());
            bool first=b.bit(); if (u.type>=16 && u.type<=23) b.skip(1);
            unsigned pps_id=b.ue(63);
            auto pp=pps.find(pps_id); if (pp==pps.end()) need_config("HEVC slice references unknown PPS");
            auto sp=sps.find(pp->second.sps); if (sp==sps.end()) need_config("HEVC PPS references unknown SPS");
            auto vp=vps.find(sp->second.vps); if (vp==vps.end()) need_config("HEVC SPS references unknown VPS");
            const auto& s=sp->second; const auto& ppv=pp->second;
            if (picture && first) malformed("multiple HEVC pictures in one access unit");
            if (!picture && !first) malformed("HEVC access unit begins with a non-first slice");
            if (picture && selected_pps!=pps_id) malformed("HEVC slices use different PPS identifiers");
            bool dependent=false;
            if (!first) {
                if (ppv.dependent) dependent=b.bit();
                uint64_t ctb=uint64_t(1)<<s.ctb_log2;
                uint64_t count=((s.coded_width+ctb-1)/ctb)*((s.coded_height+ctb-1)/ctb);
                unsigned address=b.get(ceil_log2(count)); if (!address || address>=count) malformed("HEVC slice address out of bounds");
            }
            if (!dependent) {
                b.skip(ppv.extra_bits); unsigned slice_type=b.ue(2);
                if (!slice_type) unsupported("HEVC B slices require the temporal-processing path");
                bool display=ppv.output_flag?b.bit():true;
                if (picture && display!=sample.display) malformed("HEVC slice output flags differ");
                sample.display=display;
            }
            if (first) {
                selected_pps=pps_id; active_pps=pps_id; out.format=s.format;
                out.format.parameter_sets={vp->second,s.bytes,ppv.bytes};
                sample.random_access=u.type>=16 && u.type<=21;
                sample.frame_type=uint8_t(u.type); picture=true;
            }
        }
        if (u.type<32 || u.type>34) {
            if (u.size>MaxBytes-4 || out.bytes.size()>MaxBytes-4-u.size) malformed("HEVC normalized sample exceeds size limit");
            size_t offset=out.bytes.size(); out.bytes.resize(offset+4+u.size);
            put32(out.bytes.data()+offset,uint32_t(u.size)); std::memcpy(out.bytes.data()+offset+4,bytes,u.size);
        }
    }
    if (!picture) {
        // Select a fully connected parameter-set chain for configuration-only AUs.
        for (const auto& pp:pps) {
            if (active_pps<64 && pp.first!=active_pps) continue;
            auto s=sps.find(pp.second.sps); if (s==sps.end()) continue;
            auto v=vps.find(s->second.vps); if (v==vps.end()) continue;
            out.format=s->second.format; out.format.parameter_sets={v->second,s->second.bytes,pp.second.bytes}; break;
        }
        out.bytes.clear();
    }
    if (out.format.width) {
        if (format.parameter_sets.size()==3 && out.format.parameter_sets.size()==3 &&
            (format.parameter_sets[0]!=out.format.parameter_sets[0] || format.parameter_sets[1]!=out.format.parameter_sets[1])) metadata=Color{};
        merge_hdr(metadata,unit_metadata);
        auto& c=out.format.color;
        if (metadata.mastering_valid) { c.mastering=metadata.mastering; c.mastering_valid=true; }
        if (metadata.content_light_valid) { c.content_light=metadata.content_light; c.content_light_valid=true; }
        out.config_changed=!(format==out.format); format=out.format;
    } else {
        merge_hdr(metadata,unit_metadata);
        out.format=format;
    }
    if (picture) { sample.size=out.bytes.size(); out.samples.push_back(sample); out.displayed_frames=sample.display; out.random_access=sample.random_access; }
    out.compressed_copy_count=picture?1:0; out.compressed_copy_bytes=out.bytes.size();
    return ParseResult::Ok;
}
Bitstream::Bitstream(Codec c):state_(new State(c)) {}
Bitstream::~Bitstream()=default;
Bitstream::Bitstream(const Bitstream& b):state_(new State(*b.state_)) {}
Bitstream& Bitstream::operator=(const Bitstream& b) { if (this!=&b) state_.reset(new State(*b.state_)); return *this; }
Bitstream::Bitstream(Bitstream&&) noexcept=default;
Bitstream& Bitstream::operator=(Bitstream&&) noexcept=default;
void Bitstream::clear() noexcept { *state_=State(state_->codec); }
ParseResult Bitstream::prepare(const uint8_t* p,size_t n,Prepared& out,std::string& error) {
    Span span{p,n}; return prepare_impl(&span,1,out,error,true);
}
ParseResult Bitstream::prepare(const Span* spans,size_t count,Prepared& out,std::string& error) {
    return prepare_impl(spans,count,out,error,true);
}
ParseResult Bitstream::prepare_isolated(const Span* spans,size_t count,Prepared& out,std::string& error) {
    return prepare_impl(spans,count,out,error,false);
}
ParseResult Bitstream::prepare_impl(const Span* spans,size_t count,Prepared& out,std::string& error,bool transactional) {
    out=Prepared{}; error.clear();
    if (!spans || !count || count>MaxUnits) { error="invalid compressed span count"; return ParseResult::Malformed; }
    size_t total=0;
    for (size_t i=0;i<count;++i) {
        if ((!spans[i].data && spans[i].size) || spans[i].size>MaxBytes-total) { error="null or oversized compressed spans"; return ParseResult::Malformed; }
        total+=spans[i].size;
    }
    if (!total) { error="empty compressed access unit"; return ParseResult::Malformed; }
    std::vector<uint8_t> assembled;
    const uint8_t* data=spans[0].data;
    if (count>1) {
        assembled.reserve(total);
        for (size_t i=0;i<count;++i) if (spans[i].size) assembled.insert(assembled.end(),spans[i].data,spans[i].data+spans[i].size);
        data=assembled.data();
    }
    std::optional<State> candidate;
    if (transactional) candidate.emplace(*state_);
    State& target=transactional?*candidate:*state_;
    try {
        auto result=target.codec==Codec::AV1?target.av1(data,total,out,count==1):target.hevc(data,total,out);
        if (count>1) {
            // AV1 assembly is its final sample allocation. HEVC must convert
            // Annex B afterward, so preserve the existing two-copy metrics.
            if (target.codec==Codec::AV1) out.bytes=std::move(assembled);
            else { ++out.compressed_copy_count; out.compressed_copy_bytes+=total; }
        }
        if (transactional) *state_=std::move(*candidate);
        return result;
    } catch (const Error& e) { out=Prepared{}; error=e.message; return e.result; }
}
ParseResult validate_av1c(const uint8_t* p,size_t n,Format& f,std::string& error) {
    f=Format{}; error.clear();
    try {
        if (!p || n<5 || n>MaxBytes) malformed("truncated AV1 codec configuration record");
        if (p[0]!=0x81 || (p[3]&0xe0) || (!(p[3]&0x10) && (p[3]&15))) malformed("invalid AV1 configuration marker/version/reserved bits");
        auto units=obus(p+4,n-4);
        if (units.empty() || units.front().type!=1) malformed("AV1 codec record must begin with sequence header");
        for (size_t i=1;i<units.size();++i) if (units[i].type==1) malformed("multiple sequence headers in AV1 codec record");
        const auto& u=units.front(); Sequence s=sequence(p+4+u.payload,u.size); make_av1c(s,p+4+u.start,u.end-u.start);
        if (p[1]!=s.format.av1c[1] || p[2]!=s.format.av1c[2]) malformed("AV1 codec record disagrees with sequence header");
        f=s.format; return ParseResult::Ok;
    } catch (const Error& e) { error=e.message; return e.result; }
}
}
