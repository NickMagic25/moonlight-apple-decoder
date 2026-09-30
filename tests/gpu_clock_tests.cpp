#include "gpu_clock.hpp"
#include <cstdlib>
#include <iostream>
#include <limits>
#define CHECK(x) do{if(!(x)){std::cerr<<__LINE__<<": "#x"\n";std::abort();}}while(0)
int main(){
    // The clocks intentionally have unrelated epochs. Preserve integer precision
    // at a decoder uptime larger than Double's exact integer range.
    const uint64_t uptime=(uint64_t(1)<<54)+123;
    auto clock=mav::GPUClockCalibration::from_samples(uptime,50.0,uptime+101);
    CHECK(clock.valid&&clock.decoder_ns==uptime+50&&clock.uncertainty_ns==51);
    uint64_t mapped=0;
    CHECK(clock.map(49.75,mapped)&&mapped==uptime+50-250000000);
    CHECK(clock.map(50.25,mapped)&&mapped==uptime+50+250000000);
    CHECK(clock.map(50.0,mapped)&&mapped==uptime+50);
    CHECK(!mav::GPUClockCalibration::from_samples(0,50.0,101).valid);
    CHECK(!mav::GPUClockCalibration::from_samples(200,50.0,100).valid);
    CHECK(!mav::GPUClockCalibration::from_samples(100,0,101).valid);
    CHECK(!mav::GPUClockCalibration::from_samples(100,NAN,101).valid);
    CHECK(!mav::GPUClockCalibration::from_samples(100,50.0,2000101).valid);
    CHECK(!clock.map(NAN,mapped)&&!clock.map(INFINITY,mapped)&&!clock.map(0,mapped));
    CHECK(!clock.map(1e300,mapped));
    auto low=mav::GPUClockCalibration::from_samples(10,50.0,10);
    CHECK(!low.map(49.0,mapped));
    auto high=mav::GPUClockCalibration::from_samples(UINT64_MAX-10,50.0,UINT64_MAX-10);
    CHECK(!high.map(51.0,mapped));
    std::cout<<"PASS: GPU host-clock calibration, unrelated epochs, long uptime and invalid/overflow rejection\n";
}
