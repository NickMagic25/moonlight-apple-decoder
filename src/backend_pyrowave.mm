#include "pyrowave.hpp"
#include "pyrowave_metal.h"
#include "gpu_clock.hpp"
#import <Metal/Metal.h>
#import <QuartzCore/CAMediaTiming.h>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <memory>
#include <mutex>
#if __has_feature(thread_sanitizer)
#include <sanitizer/tsan_interface.h>
#endif

namespace { struct OutputPool; }
struct mav_gpu_frame_opaque {
    std::atomic<uint32_t> references{0};
    std::shared_ptr<OutputPool> owner;
    id<MTLTexture> planes[3];
    uint32_t width=0,height=0,chroma=0,depth=0;
};
namespace {
struct OutputPool:std::enable_shared_from_this<OutputPool> {
    std::mutex mutex;std::condition_variable changed;
    std::vector<std::unique_ptr<mav_gpu_frame_opaque>> slots;
    size_t maximum=6;bool closed=false;
    bool available_locked() const {
        if(closed)return true;
        for(const auto& f:slots)if(!f->references.load())return true;
        return slots.size()<maximum;
    }
    bool available() {std::lock_guard<std::mutex> lock(mutex);return available_locked();}
    mav_result wait(uint64_t timeout) {
        std::unique_lock<std::mutex> lock(mutex);
        if(timeout==UINT64_MAX)changed.wait(lock,[&]{return available_locked();});
        else if(!changed.wait_for(lock,std::chrono::nanoseconds(std::min<uint64_t>(timeout,INT64_MAX)),[&]{return available_locked();}))return MAV_TIMEOUT;
        return closed?MAV_CLOSED:MAV_OK;
    }
    mav_gpu_frame acquire(id<MTLDevice> device,const mav::Format& format) {
        std::lock_guard<std::mutex> lock(mutex);
        mav_gpu_frame frame=nullptr;
        for(const auto& f:slots)if(!f->references.load()){frame=f.get();break;}
        if(!frame){if(slots.size()>=maximum)return nullptr;slots.push_back(std::make_unique<mav_gpu_frame_opaque>());frame=slots.back().get();}
        if(frame->width!=format.width||frame->height!=format.height||frame->chroma!=format.chroma||frame->depth!=format.bit_depth){
            for(uint32_t i=0;i<3;++i){
                NSUInteger divisor=i&&format.chroma==1?2:1;
                MTLTextureDescriptor* descriptor=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:format.bit_depth==10?MTLPixelFormatR16Unorm:MTLPixelFormatR8Unorm
                    width:format.width/divisor height:format.height/divisor mipmapped:NO];
                descriptor.usage=MTLTextureUsageShaderRead|MTLTextureUsageShaderWrite;
                descriptor.storageMode=MTLStorageModePrivate;
                frame->planes[i]=[device newTextureWithDescriptor:descriptor];
                if(!frame->planes[i])return nullptr;
                frame->planes[i].label=i==0?@"PyroWave Y":i==1?@"PyroWave Cb":@"PyroWave Cr";
            }
            frame->width=format.width;frame->height=format.height;frame->chroma=format.chroma;frame->depth=format.bit_depth;
        }
        frame->owner=shared_from_this();frame->references.store(1);
        return frame;
    }
};
mav_result translate(pyrowave_result r) {
    switch(r){case PYROWAVE_SUCCESS:return MAV_OK;case PYROWAVE_ERROR_INVALID_ARGUMENT:return MAV_INVALID_ARGUMENT;
    case PYROWAVE_ERROR_OUT_OF_HOST_MEMORY:case PYROWAVE_ERROR_OUT_OF_DEVICE_MEMORY:return MAV_OUT_OF_MEMORY;
    case PYROWAVE_ERROR_UNSUPPORTED_DEVICE:return MAV_UNSUPPORTED;case PYROWAVE_ERROR_BUSY:return MAV_WOULD_BLOCK;case PYROWAVE_ERROR_CORRUPT_BITSTREAM:return MAV_MALFORMED_INPUT;
    default:return MAV_DECODER_FAILED;}
}
}
extern "C" {
void mav_gpu_frame_retain(mav_gpu_frame frame){if(frame)frame->references.fetch_add(1);}
void mav_gpu_frame_release(mav_gpu_frame frame){
    if(!frame)return;
    // Copy the owner while the caller's reference keeps the slot alive. This
    // permits the final retained output to destroy its pool after decoder teardown.
    auto pool=frame->owner;
    bool available=false;
    {std::lock_guard<std::mutex> lock(pool->mutex);
        if(frame->references.fetch_sub(1)==1){frame->owner.reset();available=true;}}
    if(available)pool->changed.notify_all();
}
void* mav_gpu_frame_plane(mav_gpu_frame frame,uint32_t plane){return frame&&plane<3?(__bridge void*)frame->planes[plane]:nullptr;}
uint32_t mav_gpu_frame_chroma(mav_gpu_frame frame){return frame?frame->chroma:0;}
}
namespace mav {
class PyroWaveBackend final:public Backend {
    id<MTLDevice> device_;id<MTLCommandQueue> queue_;
    pyrowave_device pyro_device_=nullptr;pyrowave_decoder decoder_=nullptr;
    Format format_;mav_color color_{};BackendInfo info_;
    std::shared_ptr<OutputPool> pool_=std::make_shared<OutputPool>();
    mutable std::mutex pending_mutex_;std::condition_variable finished_;size_t pending_=0;
public:
    ~PyroWaveBackend() override {
        invalidate();if(pyro_device_)pyrowave_device_destroy(pyro_device_);
        {std::lock_guard<std::mutex> lock(pool_->mutex);pool_->closed=true;}
        pool_->changed.notify_all();
    }
    mav_result configure(const Format& f,const mav_config& c,const mav_color& color) override {
        invalidate();format_=f;color_=color;info_=BackendInfo{};
        if(c.pixel_format_count)return MAV_UNSUPPORTED; // GPU planes have no CV FourCC.
        if(!device_){device_=MTLCreateSystemDefaultDevice();queue_=[device_ newCommandQueue];}
        if(!device_||!queue_||!pyrowave_device_is_supported((__bridge void*)device_))return MAV_UNSUPPORTED;
        if(!pyro_device_){pyrowave_device_create_info create{};create.mtl_device=(__bridge void*)device_;
            auto result=pyrowave_device_create(&create,&pyro_device_);if(result!=PYROWAVE_SUCCESS)return translate(result);}
        pyrowave_decoder_create_info create{pyro_device_,int(f.width),int(f.height),f.chroma==3?PYROWAVE_CHROMA_SUBSAMPLING_444:PYROWAVE_CHROMA_SUBSAMPLING_420};
        auto result=pyrowave_decoder_create(&create,&decoder_);if(result!=PYROWAVE_SUCCESS)return translate(result);
        {std::lock_guard<std::mutex> lock(pool_->mutex);pool_->maximum=size_t(c.max_frames_in_flight)+4;}
        info_.hardware=1;info_.realtime_effective=c.realtime;
        return MAV_OK;
    }
    void submit(std::shared_ptr<Work> work) override {
        @autoreleasepool {
            BackendOutput failed;
            pyrowave_decoder_clear(decoder_);
            auto result=pyrowave_decoder_push_packet(decoder_,work->bytes->data()+work->offset,work->size);
            if(result!=PYROWAVE_SUCCESS||!pyrowave_decoder_decode_is_ready_with_sideband(decoder_,true,0,0.9f,nullptr,0)){
                failed.result=result==PYROWAVE_SUCCESS?MAV_MALFORMED_INPUT:translate(result);failed.status=result;work->complete(failed);return;}
            auto frame=pool_->acquire(device_,format_);
            if(!frame){failed.result=MAV_OUT_OF_MEMORY;work->complete(failed);return;}
            id<MTLCommandBuffer> command=[queue_ commandBuffer];
            if(!command){mav_gpu_frame_release(frame);failed.result=MAV_OUT_OF_MEMORY;work->complete(failed);return;}
            pyrowave_gpu_buffers output{};
            for(uint32_t i=0;i<3;++i)output.planes[i]=mav_gpu_frame_plane(frame,i);
            work->submit_ns.store(mav_monotonic_time_ns());
            result=pyrowave_decoder_decode_gpu_buffer(decoder_,(__bridge void*)command,&output);
            work->return_ns.store(mav_monotonic_time_ns());
            if(result!=PYROWAVE_SUCCESS){mav_gpu_frame_release(frame);failed.result=translate(result);failed.status=result;work->complete(failed);return;}
            command.label=@"MoonlightAppleVideo PyroWave decode";
            const auto color=color_;const auto format=format_;
            {std::lock_guard<std::mutex> lock(pending_mutex_);++pending_;}
            [command addCompletedHandler:^(id<MTLCommandBuffer> done){
#if __has_feature(thread_sanitizer)
                // Metal publishes copied block captures across its uninstrumented
                // driver dispatch. Describe that real command-publication edge.
                __tsan_acquire((__bridge void*)done);
#endif
                BackendOutput out;out.callback_ns=mav_monotonic_time_ns();
                if(done.status==MTLCommandBufferStatusCompleted){
                    const auto before=mav_monotonic_time_ns();const auto host=CACurrentMediaTime();const auto after=mav_monotonic_time_ns();
                    const auto calibration=GPUClockCalibration::from_samples(before,host,after);
                    const auto start=done.GPUStartTime,end=done.GPUEndTime;
                    uint64_t start_ns=0,end_ns=0;
                    if(end>=start&&calibration.map(start,start_ns)&&calibration.map(end,end_ns)&&
                       start_ns>=work->gpu_commit_ns.load()&&end_ns>=start_ns&&end_ns<=out.callback_ns){
                        out.decode_trace.valid=MAV_DECODE_TRACE_GPU_EXECUTION;
                        out.decode_trace.gpu_start_ns=start_ns;out.decode_trace.gpu_end_ns=end_ns;
                        out.decode_trace.gpu_clock_uncertainty_ns=calibration.uncertainty_ns;
                    }
                }
                if(done.status==MTLCommandBufferStatusCompleted){out.gpu_frame=frame;out.color=color;out.width=format.width;out.height=format.height;}
                else{out.result=MAV_DECODER_FAILED;out.status=int32_t(done.error.code);}
                if(!work->completion_claimed.exchange(true))work->complete(out);
                mav_gpu_frame_release(frame);
                // Notify before releasing the final pending lock: drain may
                // immediately destroy this backend after observing zero.
                {std::lock_guard<std::mutex> lock(pending_mutex_);--pending_;finished_.notify_all();}
            }];
#if __has_feature(thread_sanitizer)
            __tsan_release((__bridge void*)command);
#endif
            work->gpu_commit_ns.store(mav_monotonic_time_ns());
            [command commit];
        }
    }
    mav_result drain() override {std::unique_lock<std::mutex> lock(pending_mutex_);finished_.wait(lock,[&]{return pending_==0;});return MAV_OK;}
    void invalidate() override {drain();if(decoder_){pyrowave_decoder_destroy(decoder_);decoder_=nullptr;}}
    BackendInfo info() const override{return info_;}
    bool has_capacity() const override{
        {std::lock_guard<std::mutex> lock(pending_mutex_);if(pending_>=4)return false;}
        return pool_->available();
    }
    mav_result wait_for_capacity(uint64_t timeout) override{
        auto start=std::chrono::steady_clock::now();
        {std::unique_lock<std::mutex> lock(pending_mutex_);
            if(timeout==UINT64_MAX)finished_.wait(lock,[&]{return pending_<4;});
            else if(!finished_.wait_for(lock,std::chrono::nanoseconds(std::min<uint64_t>(timeout,INT64_MAX)),[&]{return pending_<4;}))return MAV_TIMEOUT;}
        if(timeout!=UINT64_MAX){auto elapsed=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-start).count();timeout=uint64_t(elapsed)<timeout?timeout-uint64_t(elapsed):0;}
        return pool_->wait(timeout);
    }
};
std::unique_ptr<Backend> make_pyrowave_backend(){return std::make_unique<PyroWaveBackend>();}
mav_result pyrowave_capability(mav_capability& capability){
    capability.codec=MAV_CODEC_PYROWAVE;capability.api_available=1;
    capability.hardware_decode_candidate=pyrowave_device_is_supported((__bridge void*)MTLCreateSystemDefaultDevice());return MAV_OK;
}
}
