#pragma once
#include <cmath>
#include <cstdint>
#include <limits>

namespace mav {
// Metal host times use the Core Animation clock. Map a bounded paired reading
// into the decoder clock without assuming equal epochs or converting long uptime
// integer timestamps to Double. No allocation or shared mutable calibration.
struct GPUClockCalibration {
    uint64_t decoder_ns=0,uncertainty_ns=0;
    double host_seconds=0;
    bool valid=false;
    static GPUClockCalibration from_samples(uint64_t before,double host,uint64_t after) {
        GPUClockCalibration result;
        if(!before||after<before||!std::isfinite(host)||host<=0)return result;
        const auto width=after-before;
        result.uncertainty_ns=width/2+width%2;
        if(result.uncertainty_ns>1000000)return result;
        result.decoder_ns=before+width/2;result.host_seconds=host;result.valid=true;
        return result;
    }
    bool map(double host,uint64_t& result) const {
        if(!valid||!std::isfinite(host)||host<=0)return false;
        const double delta=(host-host_seconds)*1000000000.0;
        const double magnitude=std::round(std::abs(delta));
        // Strict bound avoids an out-of-range float-to-integer conversion near
        // UINT64_MAX, which Double cannot represent exactly.
        if(!std::isfinite(magnitude)||magnitude>=double(std::numeric_limits<uint64_t>::max()))return false;
        const auto offset=uint64_t(magnitude);
        if(delta>=0){if(offset>UINT64_MAX-decoder_ns)return false;result=decoder_ns+offset;}
        else{if(offset>=decoder_ns)return false;result=decoder_ns-offset;}
        return true;
    }
};
}
