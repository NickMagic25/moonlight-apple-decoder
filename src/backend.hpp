#pragma once
#include "moonlight_apple_video/decoder.h"
#include "bitstream.hpp"
#include <atomic>
#include <functional>
#include <memory>
#include <vector>
namespace mav {
struct BackendOutput {
    mav_result result=MAV_OK; int32_t status=0; bool dropped=false;
    mav_pixel_buffer image=nullptr; mav_color color{};
    uint64_t callback_ns=0; uint32_t width=0,height=0,pixel_format=0;
};
struct Work {
    std::shared_ptr<std::vector<uint8_t>> bytes;
    size_t offset=0,size=0; mav_time pts{},dts{},duration{};
    bool random_access=false,display=true,show_existing=false;
    std::function<void(const BackendOutput&)> complete;
    // Written before backend call; inline callback can see submit but not return.
    std::atomic<uint64_t> submit_ns{0}, return_ns{0};
    std::atomic<bool> completion_claimed{false};
};
struct BackendInfo {
    uint32_t hardware=0,pixel_format=0;
    int32_t realtime_status=0,power_status=0,thread_status=0;
    int32_t realtime_effective=-1,power_effective=-1,thread_effective=-1;
    int32_t last_status=0;
};
class Backend {
public:
    virtual ~Backend()=default;
    virtual mav_result configure(const Format&,const mav_config&,const mav_color&)=0;
    // Always resolves Work exactly once, including sample construction failures.
    virtual void submit(std::shared_ptr<Work>)=0;
    virtual mav_result drain()=0;
    virtual void invalidate()=0;
    virtual BackendInfo info() const=0;
};
std::unique_ptr<Backend> make_backend();
mav_result backend_capability(mav_codec,mav_capability&);
void retain_pixel(mav_pixel_buffer);
void release_pixel(mav_pixel_buffer);
}
