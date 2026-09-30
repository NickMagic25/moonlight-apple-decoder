#include "pyrowave.hpp"
#include <bit>
#include <cassert>
#include <iostream>

using Bytes=std::vector<uint8_t>;
void word(Bytes& bytes,uint32_t value){for(int i=0;i<4;++i)bytes.push_back(uint8_t(value>>(8*i)));}
void set_word(Bytes& bytes,size_t at,uint32_t value){for(int i=0;i<4;++i)bytes[at+i]=uint8_t(value>>(8*i));}
uint32_t random_word(uint32_t& state){state^=state<<13;state^=state>>17;state^=state<<5;return state;}

// Independent byte-at-a-time reference of the original strict coefficient
// grammar. It deliberately retains each group bound and scalar sign count.
bool reference(const Bytes& record){
    if(record.size()<8||record[4]>=200)return false;
    const unsigned count=std::popcount(unsigned(record[0])|unsigned(record[1])<<8);
    if(8+3*count>record.size())return false;
    size_t cursor=8+3*count;unsigned signs=0;
    for(unsigned i=0;i<count;++i){
        const unsigned control=unsigned(record[8+2*i])|unsigned(record[9+2*i])<<8;
        const unsigned base=record[8+2*count+i]&15;
        for(unsigned group=0;group<8;++group){
            const unsigned planes=base+((control>>(2*group))&3);
            if(planes>record.size()-cursor)return false;
            uint8_t nonzero=0;
            for(unsigned p=0;p<planes;++p)nonzero|=record[cursor+p];
            if(control)signs+=std::popcount(nonzero);
            cursor+=planes;
        }
    }
    return (signs+7)/8<=record.size()-cursor;
}
bool production(Bytes record){
    set_word(record,0,(uint32_t(record.size()/4)<<16)|(unsigned(record[0])|unsigned(record[1])<<8));
    Bytes frame;word(frame,0x80000000u|127u|(127u<<14));word(frame,1);
    frame.insert(frame.end(),record.begin(),record.end());
    mav_config config;mav_config_default(&config,MAV_CODEC_PYROWAVE);config.width=config.height=128;config.chroma_format=1;
    mav_access_unit unit;mav_access_unit_default(&unit,MAV_CODEC_PYROWAVE);
    mav::Span span{frame.data(),frame.size()};mav::Prepared prepared;std::string error;
    const auto result=mav::prepare_pyrowave(&span,1,config,unit,prepared,error);
    if(result==mav::ParseResult::Ok)assert(prepared.bytes==frame);
    else assert(result==mav::ParseResult::Malformed);
    return result==mav::ParseResult::Ok;
}
int main(){
    // The closed-form magnitude width must cover every 16-bit control word.
    for(unsigned control=0;control<65536;++control){
        unsigned sum=0;for(int group=0;group<8;++group)sum+=(control>>(2*group))&3;
        assert(sum==std::popcount(control&0x5555u)+2*std::popcount((control>>1)&0x5555u));
    }
    uint32_t random=0x7f4a7c15u;size_t comparisons=0;
    auto compare=[&](const Bytes& record){assert(reference(record)==production(record));++comparisons;};
    for(unsigned trial=0;trial<1200;++trial){
        const unsigned count=trial%17;Bytes record(8);set_word(record,0,count?((1u<<count)-1):0);
        record[4]=uint8_t(trial%5==0?199:random_word(random)%200);
        std::vector<unsigned> controls(count),bases(count);
        for(unsigned i=0;i<count;++i){controls[i]=trial%4==0?0:random_word(random)&65535;
            record.push_back(uint8_t(controls[i]));record.push_back(uint8_t(controls[i]>>8));}
        for(unsigned i=0;i<count;++i){bases[i]=trial%4==0?15:random_word(random)&15;
            record.push_back(uint8_t(bases[i]|((random_word(random)&15)<<4)));}
        unsigned signs=0;
        for(unsigned i=0;i<count;++i)for(unsigned group=0;group<8;++group){
            uint8_t nonzero=0;
            const unsigned planes=bases[i]+((controls[i]>>(2*group))&3);
            for(unsigned p=0;p<planes;++p){const auto value=uint8_t(trial%3==0?0:random_word(random));
                record.push_back(value);nonzero|=value;}
            if(controls[i])signs+=std::popcount(nonzero);
        }
        for(unsigned i=0;i<(signs+7)/8;++i)record.push_back(uint8_t(random_word(random)));
        while(record.size()%4)record.push_back(0);
        compare(record);
        for(unsigned quantizer:{199u,200u,255u}){auto altered=record;altered[4]=uint8_t(quantizer);compare(altered);}
        // Exhaustive word-aligned truncations include control, magnitude and
        // sign boundaries. Later records use deterministic sampled cuts.
        if(trial<120)for(size_t size=8;size<record.size();size+=4)compare(Bytes(record.begin(),record.begin()+size));
        else for(int cut=0;cut<12;++cut){const size_t size=8+4*(random_word(random)%((record.size()-8)/4+1));
            compare(Bytes(record.begin(),record.begin()+size));}
    }
    std::cout<<"Strict coefficient scalar-oracle comparisons passed: "<<comparisons<<'\n';
}
