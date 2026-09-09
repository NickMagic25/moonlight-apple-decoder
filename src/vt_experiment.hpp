#pragma once
#ifndef MAV_VT_EXPERIMENTS
#error "VideoToolbox experiment helpers require MAV_VT_EXPERIMENTS"
#endif

#include "apple.hpp"
#include <CoreVideo/CVPixelFormatDescription.h>
#include <os/signpost.h>
#include <algorithm>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sstream>

namespace mav {
// Diagnostic builds only. These controls deliberately stay outside the C ABI.
// Lossless formats must be consumed by compatible GPU APIs, never interpreted
// as linear CPU pixel planes. Unsupported requests fail rather than fall back.
struct VTExperiment {
    uint32_t pixel_format=0;
    uint32_t linear_pixel_format=0,allowed_formats[8]{},allowed_format_count=0;
    bool native_pixel=false;
    int realtime=-1,thread_count=-1,power_efficiency=-1,asynchronous=1,metal=1,iosurface=1,signposts=0;
    std::string error;

    bool integer(const char* key,int& value,int maximum) {
        const char* raw=std::getenv(key);
        if(!raw)return true;
        unsigned parsed=0;
        if(!*raw){error=std::string(key)+" must be a decimal integer";return false;}
        for(const unsigned char* p=reinterpret_cast<const unsigned char*>(raw);*p;++p){
            if(*p<'0'||*p>'9'||parsed>unsigned(maximum)/10||
                (parsed==unsigned(maximum)/10&&unsigned(*p-'0')>unsigned(maximum)%10)){
                error=std::string(key)+" must be an integer in [0,"+std::to_string(maximum)+"]";return false;
            }
            parsed=parsed*10+unsigned(*p-'0');
            if(parsed>unsigned(maximum)){error=std::string(key)+" exceeds its supported range";return false;}
        }
        value=static_cast<int>(parsed);return true;
    }
    bool load() {
        *this=VTExperiment{};
        if(const char* raw=std::getenv("MAV_VT_PIXEL_FORMAT")){
            if(!std::strcmp(raw,"native"))native_pixel=true;
            else {
                if(std::strlen(raw)!=4){error="MAV_VT_PIXEL_FORMAT must be native or exactly four ASCII characters";return false;}
                for(unsigned i=0;i<4;++i){unsigned char c=raw[i];if(c<32||c>126){error="MAV_VT_PIXEL_FORMAT contains a non-printable character";return false;}pixel_format=(pixel_format<<8)|c;}
            }
        }
        return integer("MAV_VT_REALTIME",realtime,1)&&integer("MAV_VT_THREAD_COUNT",thread_count,INT_MAX)&&
            integer("MAV_VT_POWER_EFFICIENCY",power_efficiency,0)&&
            integer("MAV_VT_ASYNC",asynchronous,1)&&integer("MAV_VT_METAL",metal,1)&&
            integer("MAV_VT_IOSURFACE",iosurface,1)&&integer("MAV_VT_SIGNPOST",signposts,1);
    }
    static uint32_t linear_equivalent(uint32_t pixel) {
        switch(pixel){
            case kCVPixelFormatType_Lossless_420YpCbCr8BiPlanarVideoRange:return kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange;
            case kCVPixelFormatType_Lossless_420YpCbCr8BiPlanarFullRange:return kCVPixelFormatType_420YpCbCr8BiPlanarFullRange;
            case kCVPixelFormatType_Lossless_420YpCbCr10PackedBiPlanarVideoRange:return kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange;
            case kCVPixelFormatType_Lossless_420YpCbCr10PackedBiPlanarFullRange:return kCVPixelFormatType_420YpCbCr10BiPlanarFullRange;
            default:return pixel;
        }
    }
    bool select_pixel(uint32_t& selected) {
        linear_pixel_format=selected;
        if(!pixel_format)return true;
        if(linear_equivalent(pixel_format)!=selected){error="pixel-format override must preserve 4:2:0, bit depth and range";return false;}
        if((pixel_format>>24)=='&'){
            if(@available(macOS 12.0,iOS 15.0,tvOS 15.0,*)){
                if(!CVIsCompressedPixelFormatAvailable(pixel_format)){error="requested lossless pixel format is unavailable on this device";return false;}
            }else{error="compressed pixel-format capability API unavailable";return false;}
        }
        selected=pixel_format;return true;
    }
    bool accepts_native_pixel(uint32_t actual) const {
        if(linear_equivalent(actual)!=linear_pixel_format)return false;
        if(allowed_format_count){bool found=false;for(uint32_t i=0;i<allowed_format_count;++i)found|=allowed_formats[i]==actual;if(!found)return false;}
        return true;
    }
    static std::string fourcc(uint32_t pixel) {
        std::string result(4,' ');
        for(unsigned i=0;i<4;++i){unsigned char c=(pixel>>(24-8*i))&255;result[i]=c>=32&&c<=126?char(c):'?';}
        return result;
    }
    static std::string json_string(const std::string& value) {
        std::string result="\"";
        for(unsigned char c:value){if(c=='"'||c=='\\'){result+='\\';result+=char(c);}else if(c<32){char escaped[7];std::snprintf(escaped,sizeof(escaped),"\\u%04x",c);result+=escaped;}else result+=char(c);}
        return result+'"';
    }
    static std::string description(CFTypeRef value) {
        if(!value)return "null";
        CFHolder<CFStringRef> text(CFCopyDescription(value));
        if(!text.value)return "<unavailable>";
        CFIndex size=CFStringGetMaximumSizeForEncoding(CFStringGetLength(text),kCFStringEncodingUTF8)+1;
        std::vector<char> bytes(static_cast<size_t>(size));
        return CFStringGetCString(text,bytes.data(),size,kCFStringEncodingUTF8)?std::string(bytes.data()):"<unavailable>";
    }
    void log_failure(mav_result result) const {
        std::fprintf(stderr,"MAV_VT_EXPERIMENT {\"schema\":1,\"diagnostic\":true,\"result\":%d,\"error\":%s}\n",int(result),json_string(error).c_str());
    }
    static bool supported(CFDictionaryRef properties,CFStringRef key){return properties&&CFDictionaryContainsKey(properties,key);}
    static std::string json_value(CFTypeRef value) {
        if(!value)return "null";
        if(CFGetTypeID(value)==CFBooleanGetTypeID())return CFBooleanGetValue(static_cast<CFBooleanRef>(value))?"true":"false";
        if(CFGetTypeID(value)==CFNumberGetTypeID()){int64_t number=0;if(CFNumberGetValue(static_cast<CFNumberRef>(value),kCFNumberSInt64Type,&number))return std::to_string(number);}
        return json_string(description(value));
    }
    static void log_property(std::ostringstream& out,VTDecompressionSessionRef session,CFDictionaryRef properties,CFStringRef key,int setter_status,bool setter_requested) {
        CFHolder<CFTypeRef> value;OSStatus status=VTSessionCopyProperty(session,key,kCFAllocatorDefault,value.out());
        out<<"{\"supported\":"<<(supported(properties,key)?"true":"false")<<",\"setter_requested\":"<<(setter_requested?"true":"false")
            <<",\"setter_status\":"<<(setter_requested?std::to_string(setter_status):"null")
            <<",\"read_status\":"<<status<<",\"value\":"<<json_value(value)<<'}';
    }
    static void log_formats(std::ostringstream& out,VTDecompressionSessionRef session,CFDictionaryRef properties,CFStringRef key) {
        CFHolder<CFTypeRef> value;OSStatus status=VTSessionCopyProperty(session,key,kCFAllocatorDefault,value.out());
        out<<"{\"supported\":"<<(supported(properties,key)?"true":"false")<<",\"read_status\":"<<status<<",\"formats\":";
        if(value.value&&CFGetTypeID(value)==CFArrayGetTypeID()){
            auto array=static_cast<CFArrayRef>(value.value);out<<'[';
            for(CFIndex i=0;i<CFArrayGetCount(array);++i){if(i)out<<',';auto entry=CFArrayGetValueAtIndex(array,i);int32_t pixel=0;
                if(CFGetTypeID(entry)==CFNumberGetTypeID()&&CFNumberGetValue(static_cast<CFNumberRef>(entry),kCFNumberSInt32Type,&pixel))out<<json_string(fourcc(static_cast<uint32_t>(pixel)));
                else out<<"null";
            }out<<']';
        }else out<<"null";
        out<<'}';
    }
    void log_session(VTDecompressionSessionRef session,const mav_config& requested,const mav_config& applied,const BackendInfo& info,CFDictionaryRef properties,OSStatus properties_status) const {
        std::ostringstream out;
        std::ostringstream identity;identity<<static_cast<const void*>(session);
        out<<"{\"schema\":1,\"diagnostic\":true,\"session\":"<<json_string(identity.str())
            <<",\"requested\":{\"pixel_format\":"<<(native_pixel?"\"native\"":pixel_format?json_string(fourcc(pixel_format)):"null")
            <<",\"realtime_override\":"<<realtime<<",\"thread_count_override\":"<<thread_count
            <<",\"async\":"<<asynchronous<<",\"metal_attribute\":"<<metal<<",\"iosurface_attribute\":"<<iosurface<<",\"signpost\":"<<signposts<<'}'
            <<",\"applied\":{\"pixel_format\":"<<(native_pixel?"null":json_string(fourcc(info.pixel_format)))<<",\"hardware_required\":"<<(requested.hardware_policy==MAV_HARDWARE_REQUIRED?"true":"false")
            <<",\"hardware_accelerated\":"<<info.hardware<<",\"realtime\":"<<applied.realtime<<",\"thread_count\":"<<applied.thread_count<<",\"power_efficiency\":"<<applied.power_efficiency<<'}'
            <<",\"supported_properties_status\":"<<properties_status<<",\"supported_properties\":[";
        if(properties){CFIndex count=CFDictionaryGetCount(properties);std::vector<const void*> keys(static_cast<size_t>(count));CFDictionaryGetKeysAndValues(properties,keys.data(),nullptr);std::vector<std::string> names;for(auto key:keys)names.push_back(description(key));std::sort(names.begin(),names.end());for(size_t i=0;i<names.size();++i){if(i)out<<',';out<<json_string(names[i]);}}
        out<<"],\"realtime\":";log_property(out,session,properties,kVTDecompressionPropertyKey_RealTime,info.realtime_status,true);
        out<<",\"power_efficiency\":";log_property(out,session,properties,kVTDecompressionPropertyKey_MaximizePowerEfficiency,info.power_status,applied.power_efficiency!=-1);
        out<<",\"generate_hdr_metadata\":";
        if(@available(macOS 14.0,iOS 17.0,tvOS 17.0,*))log_property(out,session,properties,kVTDecompressionPropertyKey_GeneratePerFrameHDRDisplayMetadata,0,false);
        else out<<"null";
        out<<",\"thread_count\":";log_property(out,session,properties,kVTDecompressionPropertyKey_ThreadCount,info.thread_status,applied.thread_count!=0);
        out<<",\"pixel_buffer_pool_is_shared\":";log_property(out,session,properties,kVTDecompressionPropertyKey_PixelBufferPoolIsShared,0,false);
        out<<",\"pixel_formats_by_performance\":";log_formats(out,session,properties,kVTDecompressionPropertyKey_SupportedPixelFormatsOrderedByPerformance);
        out<<",\"pixel_formats_by_quality\":";log_formats(out,session,properties,kVTDecompressionPropertyKey_SupportedPixelFormatsOrderedByQuality);
        out<<'}';std::fprintf(stderr,"MAV_VT_EXPERIMENT %s\n",out.str().c_str());
    }
    void log_first_output(VTDecompressionSessionRef session,CVPixelBufferRef image,uint64_t callback_ns) const noexcept {
        try {
        CFHolder<CFTypeRef> shared;OSStatus status=VTSessionCopyProperty(session,kVTDecompressionPropertyKey_PixelBufferPoolIsShared,kCFAllocatorDefault,shared.out());
        std::ostringstream identity;identity<<static_cast<const void*>(session);
        std::ostringstream out;out<<"{\"schema\":1,\"diagnostic\":true,\"event\":\"first_output\",\"session\":"<<json_string(identity.str())
            <<",\"callback_ns\":"<<callback_ns<<",\"actual_pixel_format\":"<<json_string(fourcc(CVPixelBufferGetPixelFormatType(image)))
            <<",\"actual_iosurface\":"<<(CVPixelBufferGetIOSurface(image)?"true":"false")
            <<",\"pixel_buffer_pool_is_shared\":{\"read_status\":"<<status<<",\"value\":"<<json_value(shared)<<"}}";
        std::fprintf(stderr,"MAV_VT_EXPERIMENT %s\n",out.str().c_str());
        } catch(...) {
            // Diagnostic allocation failure must never escape Apple's C callback.
            std::fputs("MAV_VT_EXPERIMENT {\"schema\":1,\"diagnostic\":true,\"event\":\"first_output\",\"error\":\"report allocation failed\"}\n",stderr);
        }
    }
    static os_log_t log(){static os_log_t value=os_log_create("net.edrisil.moonlight-apple-decoder",OS_LOG_CATEGORY_POINTS_OF_INTEREST);return value;}
    void begin(const Work* work,uint64_t submit_ns) const {
        if(!signposts)return;
        auto logger=log();auto id=os_signpost_id_make_with_pointer(logger,work);
        // Payload anchors correlate Instruments events with CLOCK_UPTIME_RAW
        // CSV timestamps; instrumented runs are diagnostics, not timing claims.
        os_signpost_interval_begin(logger,id,"VTFrame","work=%{public}p submit_ns=%{public}llu bytes=%{public}zu",work,static_cast<unsigned long long>(submit_ns),work->size);
        os_signpost_interval_begin(logger,id,"VTDecodeCall","work=%{public}p submit_ns=%{public}llu",work,static_cast<unsigned long long>(submit_ns));
    }
    void returned(const Work* work,uint64_t return_ns,OSStatus status) const {
        if(!signposts)return;
        auto logger=log();auto id=os_signpost_id_make_with_pointer(logger,work);
        os_signpost_interval_end(logger,id,"VTDecodeCall","work=%{public}p return_ns=%{public}llu status=%{public}d",work,static_cast<unsigned long long>(return_ns),int(status));
    }
    void completed(const Work* work,uint64_t callback_ns,OSStatus status,VTDecodeInfoFlags flags) const {
        if(!signposts)return;
        auto logger=log();auto id=os_signpost_id_make_with_pointer(logger,work);
        os_signpost_interval_end(logger,id,"VTFrame","work=%{public}p callback_ns=%{public}llu status=%{public}d flags=%{public}u callback_observed=%{public}d",work,static_cast<unsigned long long>(callback_ns),int(status),unsigned(flags),callback_ns!=0);
    }
};
}
