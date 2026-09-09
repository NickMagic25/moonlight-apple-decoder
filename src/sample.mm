#include "apple.hpp"
namespace mav {
static CMTime time(const mav_time& t){return t.valid?CMTimeMake(t.value,t.timescale):kCMTimeInvalid;}
static void free_block(void* refcon,void*,size_t){delete static_cast<std::shared_ptr<std::vector<uint8_t>>*>(refcon);}
OSStatus create_sample(const std::shared_ptr<Work>& w,CMVideoFormatDescriptionRef format,CMSampleBufferRef* out) {
    if(!w->bytes||w->offset>w->bytes->size()||!w->size||w->size>w->bytes->size()-w->offset)return kCMBlockBufferBadLengthParameterErr;
    auto owner=new std::shared_ptr<std::vector<uint8_t>>(w->bytes);
    CMBlockBufferCustomBlockSource source{kCMBlockBufferCustomBlockSourceVersion,nullptr,free_block,owner};
    CFHolder<CMBlockBufferRef> block;
    auto status=CMBlockBufferCreateWithMemoryBlock(kCFAllocatorDefault,w->bytes->data()+w->offset,w->size,kCFAllocatorNull,&source,0,w->size,0,block.out());
    if(status){delete owner;return status;}
    CMSampleTimingInfo timing{time(w->duration),time(w->pts),time(w->dts)};
    size_t size=w->size;
    status=CMSampleBufferCreateReady(kCFAllocatorDefault,block,format,1,1,&timing,1,&size,out);
    if(!status){auto a=CMSampleBufferGetSampleAttachmentsArray(*out,true);if(a&&CFArrayGetCount(a)){auto d=static_cast<CFMutableDictionaryRef>(const_cast<void*>(CFArrayGetValueAtIndex(a,0)));CFDictionarySetValue(d,kCMSampleAttachmentKey_NotSync,w->random_access?kCFBooleanFalse:kCFBooleanTrue);}}
    return status;
}
}
