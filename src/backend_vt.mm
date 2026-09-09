#include "apple.hpp"
#include <map>
#include <mutex>
#ifdef MAV_EXPERIMENT_VT_DISPATCH
#include "experiment_vt.hpp"
#endif
namespace mav {
#ifdef MAV_EXPERIMENT_VT_DISPATCH
namespace {
thread_local bool experiment_synchronous=false;
thread_local std::vector<ExperimentVTCall> experiment_calls;
thread_local uint64_t experiment_overflow=0;
}
void experiment_vt_begin(bool synchronous,size_t capacity) {
    experiment_synchronous=synchronous;experiment_calls.clear();experiment_calls.reserve(capacity);experiment_overflow=0;
}
const std::vector<ExperimentVTCall>& experiment_vt_calls(){return experiment_calls;}
uint64_t experiment_vt_overflow(){return experiment_overflow;}
#endif
class VideoToolboxBackend final:public Backend {
    VTDecompressionSessionRef session_=nullptr;CMVideoFormatDescriptionRef format_=nullptr;
    BackendInfo info_;mav_color color_{};Format parsed_;
    std::mutex mutex_;std::map<Work*,std::shared_ptr<Work>> pending_;
    static void callback(void* context,void* source,OSStatus status,VTDecodeInfoFlags flags,CVImageBufferRef image,CMTime,CMTime) {
        // First instruction measuring callback ENTRY, before ownership/map work.
        uint64_t entry=mav_monotonic_time_ns();
        static_cast<VideoToolboxBackend*>(context)->finish(static_cast<Work*>(source),status,flags,image,entry);
    }
    void finish(Work* key,OSStatus status,VTDecodeInfoFlags flags,CVImageBufferRef image,uint64_t entry) {
        std::shared_ptr<Work> work;
        {std::lock_guard<std::mutex> l(mutex_);auto it=pending_.find(key);if(it==pending_.end())return;work=std::move(it->second);pending_.erase(it);}
        if(work->completion_claimed.exchange(true))return;
        BackendOutput out;out.result=vt_result(status);out.status=status;out.callback_ns=entry;
        out.dropped=(flags&kVTDecodeInfo_FrameDropped)!=0;
        if(image&&status==noErr) {
            out.width=static_cast<uint32_t>(CVPixelBufferGetWidth(image));out.height=static_cast<uint32_t>(CVPixelBufferGetHeight(image));out.pixel_format=CVPixelBufferGetPixelFormatType(image);
            if(out.pixel_format!=info_.pixel_format||out.width!=parsed_.width||out.height!=parsed_.height) {out.result=MAV_UNSUPPORTED;}
            else {out.image=image;out.color=image_color(image);attach_missing_color(image,color_);}
        } else if(!status&&work->display&&!out.dropped) {
            // Valid hidden frames are successful no-display. A displayed frame
            // without an image is visible as a drop, never a fake output.
            out.dropped=true;
        }
        work->complete(out);
    }
    int32_t property(CFDictionaryRef supported,CFStringRef key,CFTypeRef value,int32_t& effective) {
        effective=-1;
        if(!supported||!CFDictionaryContainsKey(supported,key))return kVTPropertyNotSupportedErr;
        OSStatus s=VTSessionSetProperty(session_,key,value);
        if(s)return s;
        CFHolder<CFTypeRef> read;OSStatus read_status=VTSessionCopyProperty(session_,key,kCFAllocatorDefault,read.out());
        if(!read_status&&read.value){if(CFGetTypeID(read)==CFBooleanGetTypeID())effective=CFBooleanGetValue(static_cast<CFBooleanRef>(read.value));else if(CFGetTypeID(read)==CFNumberGetTypeID())CFNumberGetValue(static_cast<CFNumberRef>(read.value),kCFNumberIntType,&effective);}
        // A write can succeed even if a read-back isn't available; -1 captures that.
        return s;
    }
public:
    ~VideoToolboxBackend()override{invalidate();}
    mav_result configure(const Format& f,const mav_config& c,const mav_color& color)override {
        invalidate();info_=BackendInfo{};color_=color;parsed_=f;
        mav_capability cap{};cap.struct_size=sizeof(cap);cap.version=MAV_ABI_VERSION;
        auto available=backend_capability(c.codec,cap);
        if(available!=MAV_OK)return available;
        if(c.hardware_policy==MAV_HARDWARE_REQUIRED&&!cap.hardware_decode_candidate)return MAV_UNSUPPORTED;
        OSStatus status=create_format(f,c.codec,color,&format_);info_.last_status=status;if(status)return vt_result(status);
        auto dimensions=CMVideoFormatDescriptionGetDimensions(format_);
        if(dimensions.width!=static_cast<int32_t>(f.width)||dimensions.height!=static_cast<int32_t>(f.height)){invalidate();return MAV_MALFORMED_INPUT;}
        uint32_t pixel=f.bit_depth==10?(color.full_range?kCVPixelFormatType_420YpCbCr10BiPlanarFullRange:kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange):(color.full_range?kCVPixelFormatType_420YpCbCr8BiPlanarFullRange:kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange);
        if(c.pixel_format_count){bool found=false;for(uint32_t i=0;i<c.pixel_format_count;++i)found|=c.pixel_formats[i]==pixel;if(!found){invalidate();return MAV_UNSUPPORTED;}}
        CFHolder<CFMutableDictionaryRef> spec(dictionary()),attrs(dictionary()),surface(dictionary());
        if(@available(macOS 10.9,iOS 17.0,tvOS 17.0,*)) {
            CFDictionarySetValue(spec,c.hardware_policy==MAV_HARDWARE_REQUIRED?kVTVideoDecoderSpecification_RequireHardwareAcceleratedVideoDecoder:kVTVideoDecoderSpecification_EnableHardwareAcceleratedVideoDecoder,kCFBooleanTrue);
        } else {invalidate();return MAV_API_UNAVAILABLE;}
        number(attrs,kCVPixelBufferPixelFormatTypeKey,static_cast<int>(pixel));
        CFDictionarySetValue(attrs,kCVPixelBufferIOSurfacePropertiesKey,surface);
        CFDictionarySetValue(attrs,kCVPixelBufferMetalCompatibilityKey,kCFBooleanTrue);
        VTDecompressionOutputCallbackRecord cb{callback,this};
        status=VTDecompressionSessionCreate(kCFAllocatorDefault,format_,spec,attrs,&cb,&session_);info_.last_status=status;
        if(status){invalidate();return vt_result(status);}
        CFHolder<CFTypeRef> hardware;
        if(@available(macOS 10.9,iOS 17.0,tvOS 17.0,*))status=VTSessionCopyProperty(session_,kVTDecompressionPropertyKey_UsingHardwareAcceleratedVideoDecoder,kCFAllocatorDefault,hardware.out());
        if(!status&&hardware.value&&CFGetTypeID(hardware)==CFBooleanGetTypeID())info_.hardware=CFBooleanGetValue(static_cast<CFBooleanRef>(hardware.value));
        if(c.hardware_policy==MAV_HARDWARE_REQUIRED&&(!info_.hardware||status)){info_.last_status=status;invalidate();return MAV_UNSUPPORTED;}
        info_.pixel_format=pixel;
        CFHolder<CFDictionaryRef> properties;status=VTSessionCopySupportedPropertyDictionary(session_,properties.out());
        if(status){info_.realtime_status=status;info_.power_status=status;info_.thread_status=status;}
        else {
            info_.realtime_status=property(properties,kVTDecompressionPropertyKey_RealTime,c.realtime?kCFBooleanTrue:kCFBooleanFalse,info_.realtime_effective);
            if(c.power_efficiency!=-1)info_.power_status=property(properties,kVTDecompressionPropertyKey_MaximizePowerEfficiency,c.power_efficiency?kCFBooleanTrue:kCFBooleanFalse,info_.power_effective);
            else {CFHolder<CFTypeRef> v;auto s=VTSessionCopyProperty(session_,kVTDecompressionPropertyKey_MaximizePowerEfficiency,kCFAllocatorDefault,v.out());info_.power_status=s;if(!s&&v.value&&CFGetTypeID(v)==CFBooleanGetTypeID())info_.power_effective=CFBooleanGetValue(static_cast<CFBooleanRef>(v.value));}
            if(c.thread_count){int n=c.thread_count;CFHolder<CFNumberRef> value(CFNumberCreate(kCFAllocatorDefault,kCFNumberIntType,&n));info_.thread_status=property(properties,kVTDecompressionPropertyKey_ThreadCount,value,info_.thread_effective);}
        }
        return MAV_OK;
    }
    void submit(std::shared_ptr<Work> w)override {
        try {
            CFHolder<CMSampleBufferRef> sample;auto status=create_sample(w,format_,sample.out());
            if(status){BackendOutput o;o.result=vt_result(status);o.status=status;w->complete(o);return;}
            {std::lock_guard<std::mutex> l(mutex_);pending_.emplace(w.get(),w);}
            VTDecodeInfoFlags flags=0;
            w->submit_ns.store(mav_monotonic_time_ns());
            VTDecodeFrameFlags decode_flags=kVTDecodeFrame_EnableAsynchronousDecompression;
#ifdef MAV_EXPERIMENT_VT_DISPATCH
            if(experiment_synchronous)decode_flags=0;
#endif
            status=VTDecompressionSessionDecodeFrame(session_,sample,decode_flags,w.get(),&flags);
            w->return_ns.store(mav_monotonic_time_ns());
#ifdef MAV_EXPERIMENT_VT_DISPATCH
            if(experiment_calls.size()<experiment_calls.capacity())experiment_calls.push_back({w->submit_ns.load(),w->return_ns.load()});
            else ++experiment_overflow;
#endif
            // SDK guarantees no callback for a synchronous error. Map removal
            // is idempotent and ownership also survives an inline success.
            if(status)finish(w.get(),status,flags,nullptr,0);
            else if((flags&kVTDecodeInfo_FrameDropped)&&!w->completion_claimed.exchange(true)){
                // Resolve public capacity now, but KEEP the source context in
                // pending_ until its promised callback or controlled drain.
                // Otherwise a late callback could alias a reused Work address.
                BackendOutput dropped;dropped.dropped=true;w->complete(dropped);
            }
        }catch(const std::bad_alloc&){BackendOutput o;o.result=MAV_OUT_OF_MEMORY;w->complete(o);}
    }
    mav_result drain()override {
        OSStatus status=session_?VTDecompressionSessionWaitForAsynchronousFrames(session_):noErr;
        // The library contract does not depend on callbacks being emitted for
        // every decoder edge case. Controlled drain resolves any missing ones.
        for(;;){Work* w;{std::lock_guard<std::mutex> l(mutex_);if(pending_.empty())break;w=pending_.begin()->first;}finish(w,status?status:kVTVideoDecoderMalfunctionErr,0,nullptr,0);}
        return vt_result(status);
    }
    void invalidate()override {
        if(session_){drain();VTDecompressionSessionInvalidate(session_);CFRelease(session_);session_=nullptr;}
        if(format_){CFRelease(format_);format_=nullptr;}
    }
    BackendInfo info()const override{return info_;}
};
std::unique_ptr<Backend> make_backend(){return std::make_unique<VideoToolboxBackend>();}
mav_result backend_capability(mav_codec codec,mav_capability& c) {
    c.codec=codec;c.api_available=0;c.hardware_decode_candidate=0;
    if(codec==MAV_CODEC_AV1){if(@available(macOS 14.0,iOS 17.0,tvOS 17.0,*))c.api_available=1;}
    else c.api_available=1;
    if(!c.api_available)return MAV_API_UNAVAILABLE;
    c.hardware_decode_candidate=VTIsHardwareDecodeSupported(codec==MAV_CODEC_AV1?kCMVideoCodecType_AV1:kCMVideoCodecType_HEVC);
    return MAV_OK;
}
void retain_pixel(mav_pixel_buffer p){CVPixelBufferRetain(p);}
void release_pixel(mav_pixel_buffer p){CVPixelBufferRelease(p);}
}
