#include "bitstream.hpp"
#include "test_stream.hpp"
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <random>
#include <string>
#include <vector>
using namespace mav;
using namespace mav_test;
namespace {
unsigned checks=0;
void check(bool ok,const char* message) { ++checks; if (!ok) { std::cerr<<"FAIL "<<message<<"\n"; std::exit(1); } }
Prepared accept(Bitstream& parser,const std::vector<uint8_t>& bytes) {
    Prepared out;std::string error;auto r=parser.prepare(bytes.data(),bytes.size(),out,error);
    if (r!=ParseResult::Ok) {std::cerr<<"Unexpected parse failure: "<<error<<"\n";std::exit(1);} ++checks;return out;
}
void av1_tests() {
    for (unsigned depth:{8u,10u}) {
        Bitstream parser(Codec::AV1);auto key=av1_key_unit(depth);auto first=accept(parser,key);
        check(first.format.width==64&&first.format.height==64,"AV1 dimensions");
        check(first.format.bit_depth==depth&&first.format.profile==0,"AV1 depth/profile");
        check(first.random_access&&first.displayed_frames==1&&first.samples.size()==1,"AV1 random access/display accounting");
        check(first.bytes==key&&first.compressed_copy_count==1,"AV1 payload preservation/copy count");
        check(first.config_changed,"AV1 initial configuration change");
        Format verified;std::string error;check(validate_av1c(first.format.av1c.data(),first.format.av1c.size(),verified,error)==ParseResult::Ok,"AV1 record round trip");
        check(verified==first.format,"AV1 record/sequence consistency");
        check(!accept(parser,key).config_changed,"AV1 repeated sequence does not reconfigure");
        auto inter=accept(parser,av1_frame(false,true));check(!inter.random_access&&!inter.config_changed,"AV1 inter retains sequence");
        auto hidden=accept(parser,av1_frame(false,false));check(hidden.displayed_frames==0&&!hidden.samples[0].display,"AV1 hidden frame accounting");
        auto existing=accept(parser,av1_existing(3));check(existing.displayed_frames==1&&existing.samples[0].show_existing&&existing.samples[0].existing_frame_index==3,"AV1 existing reference event");
        auto multiple=av1_frame(false,false);append(multiple,av1_frame(false,true));auto split=accept(parser,multiple);
        check(split.samples.size()==2&&split.displayed_frames==1&&!split.samples[0].display&&split.samples[1].display,"AV1 hidden+shown child samples");
        check(split.samples[0].offset==0&&split.samples[0].size==split.samples[1].offset&&split.samples[1].offset+split.samples[1].size==multiple.size(),"AV1 child offsets cover owned sample");
        for (size_t boundary=0;boundary<=key.size();++boundary) {
            Bitstream spans_parser(Codec::AV1);Span spans[]={{key.data(),boundary},{key.data()+boundary,key.size()-boundary}};Prepared p;
            check(spans_parser.prepare(spans,2,p,error)==ParseResult::Ok&&p.bytes==key&&p.format==first.format,"AV1 all span boundaries");
            check(p.compressed_copy_count==1&&p.compressed_copy_bytes==key.size(),"AV1 span assembly is final owned sample copy");
        }
        auto changed=accept(parser,av1_key_unit(depth,128,96));check(changed.config_changed&&changed.format.width==128&&changed.format.height==96,"AV1 dimension change");
        Bitstream snapshot=parser;parser.clear();Prepared p;auto noseq=av1_frame();
        check(parser.prepare(noseq.data(),noseq.size(),p,error)==ParseResult::NeedConfiguration,"AV1 reset clears sequence");
        check(accept(snapshot,av1_frame(false)).format.width==128,"AV1 parser snapshot independent of reset");
        auto bad=first.format.av1c;bad[2]^=64;check(validate_av1c(bad.data(),bad.size(),verified,error)==ParseResult::Malformed,"AV1 record rejects depth disagreement");
        bad=first.format.av1c;bad[0]=1;check(validate_av1c(bad.data(),bad.size(),verified,error)==ParseResult::Malformed,"AV1 record marker");
    }
    Bitstream parser(Codec::AV1);auto key=av1_key_unit();accept(parser,key);Prepared p;std::string error;
    std::vector<std::vector<uint8_t>> invalid={{0x0a,0x80},{0x0a,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff},{0x0a,0x7f,0},{0x82,0},{0x13,0},{0x16,0x01,0},{0x12,1,0},{0x22,0}};
    for (const auto& bytes:invalid) check(parser.prepare(bytes.data(),bytes.size(),p,error)==ParseResult::Malformed,"AV1 malformed length/header safely rejected");
    auto unsupported_layer=key;unsupported_layer[0]|=4;unsupported_layer.insert(unsupported_layer.begin()+1,0x20);
    check(parser.prepare(unsupported_layer.data(),unsupported_layer.size(),p,error)==ParseResult::Unsupported,"AV1 unsupported temporal layer");
    auto bad_profile=key;bad_profile[2]|=0x20;
    check(parser.prepare(bad_profile.data(),bad_profile.size(),p,error)==ParseResult::Unsupported,"AV1 unsupported profile");
    auto two=av1_frame();append(two,av1_frame());check(parser.prepare(two.data(),two.size(),p,error)==ParseResult::Unsupported,"AV1 multiple displayed images explicitly rejected");
    auto header=av1_frame();header[0]=0x1a;check(parser.prepare(header.data(),header.size(),p,error)==ParseResult::Malformed,"AV1 missing tile group");
    append(header,obu(4,{0xab,0xcd}));check(accept(parser,header).samples.size()==1,"AV1 frame-header plus tile-group");
    auto failed_change=av1_sequence(10,256,144);append(failed_change,{0x0a,0x80});check(parser.prepare(failed_change.data(),failed_change.size(),p,error)==ParseResult::Malformed,"AV1 failed config update rejected");
    check(accept(parser,av1_frame(false)).format.width==64,"AV1 failed preparation does not mutate cache");
    auto full=av1_sequence(10);append(full,obu(5,{1,3,232,1,144,128}));append(full,av1_frame());
    auto hdr=accept(parser,full);check(hdr.format.color.content_light_valid&&hdr.format.color.content_light[0]==3&&hdr.format.color.content_light[1]==232,"AV1 HDR content light parsed");
    auto new_header=obu(5,{1,3,232,1,144,128});append(new_header,av1_key_unit(10,128,96));
    check(accept(parser,new_header).format.color.content_light_valid,"AV1 metadata preceding new sequence retained");
    check(!accept(parser,av1_key_unit(8)).format.color.content_light_valid,"AV1 new SDR sequence clears inherited HDR metadata");
    auto chroma=av1_sequence(8,64,64,1);append(chroma,av1_frame());auto sitting=accept(parser,chroma);
    check(sitting.format.color.chroma_position_valid&&sitting.format.color.chroma_position==0&&(sitting.format.av1c[2]&3)==1,"AV1 vertical chroma maps to left while av1C retains raw value");
    std::vector<uint8_t> mastering{2,0x19,0x9a,0x19,0x9a,0x4c,0xcd,0x4c,0xcd,0x80,0,0x80,0,0x80,0,0x80,0,0,3,0xe8,0,0,0,0x40,0,128};
    auto master_unit=av1_sequence(10);append(master_unit,obu(5,mastering));append(master_unit,av1_frame());auto master=accept(parser,master_unit).format.color;
    check(master.mastering_valid&&((unsigned(master.mastering[0])<<8)|master.mastering[1])==15000,"AV1 mastering RGB order and chromaticity conversion");
    check(master.mastering[16]==0&&master.mastering[17]==0x98&&master.mastering[18]==0x96&&master.mastering[19]==0x80,"AV1 mastering maximum luminance conversion");
    check(master.mastering[22]==0x27&&master.mastering[23]==0x10,"AV1 mastering minimum luminance conversion");
}

std::vector<uint8_t> hevc_nal(unsigned type,const std::vector<uint8_t>& payload,unsigned start_length=4) {
    std::vector<uint8_t> n(start_length-1,0);n.push_back(1);n.push_back(uint8_t(type<<1));n.push_back(1);
    unsigned zeros=0;
    for (auto b:payload) {
        if (zeros==2 && b<=3) {n.push_back(3);zeros=0;}
        n.push_back(b);zeros=b?0:zeros+1;
    }
    return n;
}
void profile(Writer& w,unsigned depth) {
    w.bits(0,3);w.bits(depth==10?2:1,5);w.bits(0,32);w.bits(0,32);w.bits(0,16);w.bits(120,8);
}
std::vector<uint8_t> vps(unsigned depth=8) {
    Writer w;w.bits(0,4);w.bits(3,2);w.bits(0,6);w.bits(0,3);w.bits(1,1);w.bits(65535,16);profile(w,depth);
    w.bits(1,1);w.ue(3);w.ue(0);w.ue(0);w.bits(0,6);w.ue(0);w.bits(0,1);w.bits(0,1);w.trailing();return hevc_nal(32,w.bytes);
}
std::vector<uint8_t> sps(unsigned depth=8,unsigned width=128,unsigned id=0,unsigned reorder=0) {
    Writer w;w.bits(0,4);w.bits(0,3);w.bits(1,1);profile(w,depth);w.ue(id);w.ue(1);w.ue(width);w.ue(64);w.bits(0,1);
    w.ue(depth-8);w.ue(depth-8);w.ue(0);w.bits(1,1);w.ue(3);w.ue(reorder);w.ue(0);
    w.ue(0);w.ue(3);w.ue(0);w.ue(3);w.ue(0);w.ue(0);w.bits(0,4); // scaling/AMP/SAO/PCM
    w.ue(0);w.bits(0,3);w.bits(1,1); // no ref sets/long-term/MVP/smoothing, VUI present
    w.bits(0,1);w.bits(0,1);w.bits(1,1);w.bits(5,3);w.bits(0,1);w.bits(1,1);
    w.bits(depth==10?9:1,8);w.bits(depth==10?16:1,8);w.bits(depth==10?9:1,8);
    w.bits(1,1);w.ue(0);w.ue(0);w.bits(0,6); // chroma location, neutral/field/info/window/timing/restriction
    w.bits(0,1);w.trailing();return hevc_nal(33,w.bytes,3);
}
std::vector<uint8_t> pps(unsigned id=0,unsigned sps_id=0,bool output_flag=false) {
    Writer w;w.ue(id);w.ue(sps_id);w.bits(0,1);w.bits(output_flag,1);w.bits(0,3);
    w.bits(0,2);w.ue(0);w.ue(0);w.ue(0);w.bits(0,2);w.bits(0,1);w.ue(0);w.ue(0);w.bits(0,4);
    w.bits(0,2);w.bits(0,1);w.bits(0,1);w.bits(0,1);w.bits(0,1);w.ue(0);w.bits(0,1);w.bits(0,1);w.trailing();
    return hevc_nal(34,w.bytes);
}
std::vector<uint8_t> slice(unsigned type=19,bool first=true,unsigned pps_id=0,unsigned slice_type=2,bool output_flag=false,bool display=true) {
    Writer w;w.bits(first,1);if (type>=16&&type<=23)w.bits(0,1);w.ue(pps_id);if (!first)w.bits(1,1);
    w.ue(slice_type);if(output_flag)w.bits(display,1);w.bits(0,32);w.bits(0,16);w.trailing();return hevc_nal(type,w.bytes,3);
}
std::vector<uint8_t> hevc_key(unsigned depth=8) {
    auto b=vps(depth);append(b,sps(depth));append(b,pps());append(b,slice());return b;
}
void hevc_tests() {
    for (unsigned depth:{8u,10u}) {
        Bitstream parser(Codec::HEVC);auto key=hevc_key(depth);auto initial=accept(parser,key);
        check(initial.format.width==128&&initial.format.height==64&&initial.format.bit_depth==depth,"HEVC dimensions/depth");
        check(initial.format.profile==(depth==10?2:1)&&initial.format.parameter_sets.size()==3,"HEVC Main/Main10 and connected parameter sets");
        check(initial.format.color.description_valid&&initial.format.color.primaries==(depth==10?9:1)&&initial.format.color.transfer==(depth==10?16:1),"HEVC VUI color");
        check(initial.random_access&&initial.samples.size()==1&&initial.displayed_frames==1,"HEVC IDR picture");
        auto nal=slice();check(initial.bytes.size()==nal.size()+1&&std::equal(nal.begin()+3,nal.end(),initial.bytes.begin()+4),"HEVC escaped payload preserved with big endian prefix");
        check(initial.bytes[0]==0&&initial.bytes[1]==0&&initial.bytes[2]==0&&initial.bytes[3]==nal.size()-3,"HEVC length prefix excludes start code");
        check(!accept(parser,key).config_changed,"HEVC repeated parameter sets do not reconfigure");
        auto inter=accept(parser,slice(1,true,0,1));check(!inter.random_access&&!inter.config_changed,"HEVC inter caches config");
        auto multi=slice();append(multi,slice(19,false));auto slices=accept(parser,multi);check(slices.samples.size()==1&&slices.displayed_frames==1&&slices.bytes.size()>initial.bytes.size(),"HEVC multiple slices one sample");
        for (size_t boundary=0;boundary<=key.size();++boundary) {
            Bitstream split(Codec::HEVC);Span spans[]={{key.data(),boundary},{key.data()+boundary,key.size()-boundary}};Prepared out;std::string error;
            check(split.prepare(spans,2,out,error)==ParseResult::Ok&&out.bytes==initial.bytes&&out.format==initial.format,"HEVC all span boundaries including split start codes");
        }
        auto unused=sps(depth,256,1);append(unused,pps(1,1));auto unchanged=accept(parser,unused);
        check(!unchanged.config_changed&&unchanged.format.width==128,"HEVC unused parameter sets do not replace active chain");
        auto changed=accept(parser,slice(19,true,1));check(changed.config_changed&&changed.format.width==256,"HEVC picture selects PPS/SPS chain by ID");
        Bitstream separate(Codec::HEVC);check(accept(separate,vps(depth)).samples.empty(),"HEVC isolated VPS accepted without image");
        check(accept(separate,sps(depth)).samples.empty(),"HEVC isolated SPS accepted without image");
        auto config=accept(separate,pps());check(config.samples.empty()&&config.format.width==128,"HEVC configuration before picture");
        check(accept(separate,slice()).random_access,"HEVC picture after parameter-only AUs");
    }
    Bitstream parser(Codec::HEVC);accept(parser,hevc_key());Prepared out;std::string error;
    auto hidden_config=pps(0,0,true);append(hidden_config,slice(19,true,0,2,true,false));auto hidden=accept(parser,hidden_config);
    check(!hidden.samples[0].display&&hidden.displayed_frames==0,"HEVC pic_output_flag hidden picture");
    accept(parser,hevc_key());
    auto check_reject=[&](const std::vector<uint8_t>& bytes,ParseResult expected,const char* message) {check(parser.prepare(bytes.data(),bytes.size(),out,error)==expected,message);};
    check_reject(slice(1,true,33),ParseResult::NeedConfiguration,"HEVC slice unknown PPS");
    auto unknown=pps(2,5);append(unknown,slice(19,true,2));check_reject(unknown,ParseResult::NeedConfiguration,"HEVC PPS unknown SPS");
    check_reject(slice(1,false),ParseResult::Malformed,"HEVC AU cannot begin mid-picture");
    auto two=slice();append(two,slice());check_reject(two,ParseResult::Malformed,"HEVC two pictures rejected");
    check_reject(slice(1,true,0,0),ParseResult::Unsupported,"HEVC B slices explicitly rejected");
    check_reject(slice(8),ParseResult::Unsupported,"HEVC RASL leading picture rejected");
    check(accept(parser,slice(21)).random_access,"HEVC CRA distinguished as random access");
    check(accept(parser,slice(16)).random_access,"HEVC BLA distinguished as random access");
    check_reject(sps(8,128,0,1),ParseResult::Unsupported,"HEVC declared reorder requirement rejected");
    auto late=slice();append(late,pps());check_reject(late,ParseResult::Malformed,"HEVC parameter changes after picture rejected");
    auto bad=slice();bad[4]=0;check_reject(bad,ParseResult::Malformed,"HEVC temporal_id_plus1 zero rejected");
    bad=slice();bad[3]|=128;check_reject(bad,ParseResult::Malformed,"HEVC forbidden bit rejected");
    bad=slice();bad[4]|=8;check_reject(bad,ParseResult::Unsupported,"HEVC extra layer rejected");
    for (const auto& ps:{vps(),sps(),pps()}) for (size_t n=1;n<ps.size();++n) {
        Bitstream fresh(Codec::HEVC);check(fresh.prepare(ps.data(),n,out,error)!=ParseResult::Ok,"HEVC truncated parameter set safely rejected");
    }
    auto metadata=hevc_nal(39,{144,4,3,232,1,144,128});append(metadata,slice());
    auto hdr=accept(parser,metadata);check(hdr.format.color.content_light_valid&&hdr.format.color.content_light[0]==3,"HEVC HDR SEI parsed");
    check(hdr.bytes.size()>accept(parser,slice()).bytes.size(),"HEVC SEI preserved in sample");
    auto changed_sps=sps(8,256);append(changed_sps,slice());check(!accept(parser,changed_sps).format.color.content_light_valid,"HEVC new sequence clears inherited HDR metadata");
    auto new_metadata=hevc_nal(39,{144,4,3,232,1,144,128});append(new_metadata,sps());append(new_metadata,slice());
    check(accept(parser,new_metadata).format.color.content_light_valid,"HEVC metadata preceding new SPS retained");
    check_reject(hevc_nal(39,{144,6,1,2,128}),ParseResult::Malformed,"HEVC truncated SEI rejected");
    std::vector<uint8_t> invalid_epb={0,0,1,66,1,0,0,3,4};check_reject(invalid_epb,ParseResult::Malformed,"HEVC invalid emulation prevention sequence");
}
void malformed_properties() {
    std::mt19937 random(0x4d415631);
    for (unsigned i=0;i<3000;++i) {
        std::vector<uint8_t> bytes(1+random()%256);for (auto& b:bytes)b=uint8_t(random());
        for (auto codec:{Codec::AV1,Codec::HEVC}) {
            Bitstream parser(codec);Prepared out;std::string error;auto r=parser.prepare(bytes.data(),bytes.size(),out,error);
            if (r==ParseResult::Ok) for (const auto& sample:out.samples) check(sample.offset<=out.bytes.size()&&sample.size<=out.bytes.size()-sample.offset,"fuzz accepted sample bounded");
            else check(out.samples.empty()&&out.bytes.empty(),"fuzz rejection has no prepared payload");
        }
    }
}
}
int main() {av1_tests();hevc_tests();malformed_properties();std::cout<<"PASS bitstream "<<checks<<" checks\n";}
