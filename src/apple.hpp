#pragma once
#include "backend.hpp"
#include <CoreMedia/CoreMedia.h>
#include <VideoToolbox/VideoToolbox.h>
namespace mav {
template<class T> struct CFHolder { T value=nullptr; CFHolder()=default; explicit CFHolder(T v):value(v){} ~CFHolder(){if(value)CFRelease(value);} CFHolder(const CFHolder&)=delete;CFHolder& operator=(const CFHolder&)=delete; operator T()const{return value;} T* out(){return &value;} T detach(){T v=value;value=nullptr;return v;} };
inline CFMutableDictionaryRef dictionary(){return CFDictionaryCreateMutable(kCFAllocatorDefault,0,&kCFTypeDictionaryKeyCallBacks,&kCFTypeDictionaryValueCallBacks);}
inline void number(CFMutableDictionaryRef d,CFStringRef k,int v){CFHolder<CFNumberRef> n(CFNumberCreate(kCFAllocatorDefault,kCFNumberIntType,&v));if(n.value)CFDictionarySetValue(d,k,n);}
OSStatus create_format(const Format&,mav_codec,const mav_color&,CMVideoFormatDescriptionRef*);
OSStatus create_sample(const std::shared_ptr<Work>&,CMVideoFormatDescriptionRef,CMSampleBufferRef*);
mav_color image_color(CVPixelBufferRef);
void attach_missing_color(CVPixelBufferRef,const mav_color&);
mav_result vt_result(OSStatus);
}
