#pragma once
#include "backend.hpp"
#include <cstring>
namespace mav {
inline mav_color parsed_color(const Color& c) {
    mav_color r{}; r.primaries=c.primaries; r.transfer=c.transfer; r.matrix=c.matrix;
    if(c.description_valid) r.valid|=MAV_COLOR_DESCRIPTION;
    if(c.range_valid) r.valid|=MAV_COLOR_RANGE;
    r.full_range=c.full_range; r.chroma_location=c.chroma_position;
    if(c.chroma_position_valid) r.valid|=MAV_COLOR_CHROMA_LOCATION;
    if(c.mastering_valid) r.valid|=MAV_COLOR_MASTERING;
    if(c.content_light_valid) r.valid|=MAV_COLOR_CONTENT_LIGHT;
    std::memcpy(r.mastering,c.mastering.data(),24);std::memcpy(r.content_light,c.content_light.data(),4);
    return r;
}
inline bool valid_color(const mav_color& c) {
    if((c.valid&~31u)||((c.valid&MAV_COLOR_RANGE)&&c.full_range>1)||
       ((c.valid&MAV_COLOR_CHROMA_LOCATION)&&c.chroma_location>5))return false;
    auto u16=[](const uint8_t* p){return uint32_t(p[0])<<8|p[1];};
    auto u32=[](const uint8_t* p){return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];};
    if(c.valid&MAV_COLOR_MASTERING){
        for(unsigned i=0;i<16;i+=2)if(u16(c.mastering+i)>50000)return false;
        if(u32(c.mastering+20)>u32(c.mastering+16))return false;
    }
    if((c.valid&MAV_COLOR_CONTENT_LIGHT)&&u16(c.content_light)&&u16(c.content_light+2)>u16(c.content_light))return false;
    return true;
}
// Higher-priority valid fields win. Unknown ISO value 2 is filled per component.
inline mav_color merge_color(mav_color high,const mav_color& low) {
    if(!(high.valid&MAV_COLOR_DESCRIPTION)) {
        high.primaries=low.primaries;high.transfer=low.transfer;high.matrix=low.matrix;
    } else if(low.valid&MAV_COLOR_DESCRIPTION) {
        if(high.primaries==2) high.primaries=low.primaries;
        if(high.transfer==2) high.transfer=low.transfer;
        if(high.matrix==2) high.matrix=low.matrix;
    }
    if(!(high.valid&MAV_COLOR_RANGE)) high.full_range=low.full_range;
    if(!(high.valid&MAV_COLOR_CHROMA_LOCATION)) high.chroma_location=low.chroma_location;
    if(!(high.valid&MAV_COLOR_MASTERING)) std::memcpy(high.mastering,low.mastering,24);
    if(!(high.valid&MAV_COLOR_CONTENT_LIGHT)) std::memcpy(high.content_light,low.content_light,4);
    high.valid|=low.valid;return high;
}
}
