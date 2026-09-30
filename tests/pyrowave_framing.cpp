#include "pyrowave.hpp"
#include <cassert>
#include <iostream>
using Bytes=std::vector<uint8_t>;
void word(Bytes& b,uint32_t v){for(int i=0;i<4;++i)b.push_back(uint8_t(v>>(8*i)));}
void set(Bytes& b,size_t at,uint32_t v){for(int i=0;i<4;++i)b[at+i]=uint8_t(v>>(8*i));}
Bytes sequence(uint32_t count,uint32_t width=128,uint32_t height=128,bool chroma444=false){Bytes b;word(b,0x80000000u|(width-1)|((height-1)<<14));word(b,count|(chroma444?(1u<<26):0));return b;}
void block(Bytes& b,uint32_t index){word(b,2u<<16);word(b,index<<8);}
bool parse(const Bytes& b,std::vector<mav_pyrowave_fragment> fragments={},uint32_t critical=0,Bytes* output=nullptr){
    mav_config c;mav_config_default(&c,MAV_CODEC_PYROWAVE);c.width=128;c.height=128;c.chroma_format=1;
    mav_access_unit u;mav_access_unit_default(&u,MAV_CODEC_PYROWAVE);u.pyrowave_fragments=fragments.data();u.pyrowave_fragment_count=fragments.size();u.pyrowave_critical_packets=critical;
    mav::Span span{b.data(),b.size()};mav::Prepared prepared;std::string error;
    const bool valid=mav::prepare_pyrowave(&span,1,c,u,prepared,error)==mav::ParseResult::Ok;
    if(valid&&output)*output=std::move(prepared.bytes);return valid;
}
int main(){
    Bytes frame=sequence(2);block(frame,0);block(frame,20);assert(parse(frame));
    Bytes plain,mapped;
    assert(parse(frame,{},0,&plain));
    assert(parse(frame,{{0,8,2},{8,8,2},{16,8,2}},1,&mapped));assert(plain==mapped&&mapped==frame);
    assert(parse(frame,{{0,24,0}},0,&mapped)&&mapped==plain);
    Bytes padding=sequence(2);word(padding,UINT32_MAX);word(padding,1);word(padding,0);block(padding,20);block(padding,0);assert(parse(padding));
    Bytes legacy;word(legacy,2);word(legacy,16);legacy.insert(legacy.end(),frame.begin(),frame.begin()+16);word(legacy,8);legacy.insert(legacy.end(),frame.begin()+16,frame.end());assert(parse(legacy));
    auto invalid=frame;set(invalid,8,1u<<16);assert(!parse(invalid));
    invalid=frame;set(invalid,16,(2u<<16)|(1u<<28));assert(!parse(invalid));
    invalid=frame;set(invalid,20,0xffffff00);assert(!parse(invalid));
    invalid=frame;set(invalid,20,0);assert(!parse(invalid));
    invalid=frame;set(invalid,0,0x80000000u|127|(125u<<14));assert(!parse(invalid));
    invalid=frame;set(invalid,4,(1u<<26)|2);assert(!parse(invalid));
    invalid=frame;invalid.insert(invalid.end(),frame.begin(),frame.begin()+8);assert(!parse(invalid));
    invalid=frame;invalid.pop_back();assert(!parse(invalid));
    invalid=padding;invalid[8+8]=1;assert(!parse(invalid));
    invalid=legacy;word(invalid,0);assert(!parse(invalid));
    assert(!parse(frame,{{0,8,0},{9,16,0}}));
    assert(!parse(frame,{{0,24,0}},2));
    assert(!parse(frame,{{0,8,1},{8,16,2}}));
    assert(!parse(legacy,{{0,uint32_t(legacy.size()),1}}));
    // Coefficient controls claim magnitude data outside their bounded record.
    invalid=sequence(1);word(invalid,(3u<<16)|1);word(invalid,0);word(invalid,0x00ffffff);assert(!parse(invalid));
    assert(!parse(invalid,{{0,uint32_t(invalid.size()),2}})); // Intact map never bypasses coefficient bounds.
    assert(!parse(frame,{{0,24,3}})); // Invalid map flags still reject before the intact path.
    // The coarsest records survive; one of 20 finer records is lost and a flagged
    // record boundary permits recovery. Exactly 90% must still reject.
    Bytes partial=sequence(20);for(uint32_t i=0;i<20;++i)block(partial,i);
    std::vector<mav_pyrowave_fragment> fragments{{0,8,2}};
    for(uint32_t i=0;i<20;++i)fragments.push_back({8+i*8,8,i==17?1u:2u});
    assert(parse(partial,fragments,13));
    fragments[19].kind=1;assert(!parse(partial,fragments,13));
    fragments[19].kind=2;fragments[3].kind=1;assert(!parse(partial,fragments,13));
    fragments[3].kind=2;assert(parse(partial,fragments,0));
    // Unflagged packets recover after a known ordinary finer record.
    for(auto& f:fragments)if(f.kind==2)f.kind=0;assert(parse(partial,fragments,13));
    std::cout<<"PyroWave record, legacy, coefficient bounds and partial-frame tests passed\n";
}
