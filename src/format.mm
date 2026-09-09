#include "apple.hpp"
#include <cstring>
namespace mav {
static void color_dictionary(CFMutableDictionaryRef d,const mav_color& c) {
    if(c.valid&MAV_COLOR_DESCRIPTION) {
        if(auto v=CVColorPrimariesGetStringForIntegerCodePoint(c.primaries))CFDictionarySetValue(d,kCMFormatDescriptionExtension_ColorPrimaries,v);
        if(auto v=CVTransferFunctionGetStringForIntegerCodePoint(c.transfer))CFDictionarySetValue(d,kCMFormatDescriptionExtension_TransferFunction,v);
        if(auto v=CVYCbCrMatrixGetStringForIntegerCodePoint(c.matrix))CFDictionarySetValue(d,kCMFormatDescriptionExtension_YCbCrMatrix,v);
    }
    if(c.valid&MAV_COLOR_RANGE)CFDictionarySetValue(d,kCMFormatDescriptionExtension_FullRangeVideo,c.full_range?kCFBooleanTrue:kCFBooleanFalse);
    if(c.valid&MAV_COLOR_CHROMA_LOCATION) {
        const CFStringRef loc[]={kCMFormatDescriptionChromaLocation_Left,kCMFormatDescriptionChromaLocation_Center,kCMFormatDescriptionChromaLocation_TopLeft,kCMFormatDescriptionChromaLocation_Top,kCMFormatDescriptionChromaLocation_BottomLeft,kCMFormatDescriptionChromaLocation_Bottom};
        if(c.chroma_location<6)CFDictionarySetValue(d,kCMFormatDescriptionExtension_ChromaLocationTopField,loc[c.chroma_location]);
    }
    if(c.valid&MAV_COLOR_MASTERING){CFHolder<CFDataRef> v(CFDataCreate(kCFAllocatorDefault,c.mastering,24));CFDictionarySetValue(d,kCMFormatDescriptionExtension_MasteringDisplayColorVolume,v);}
    if(c.valid&MAV_COLOR_CONTENT_LIGHT){CFHolder<CFDataRef> v(CFDataCreate(kCFAllocatorDefault,c.content_light,4));CFDictionarySetValue(d,kCMFormatDescriptionExtension_ContentLightLevelInfo,v);}
}
OSStatus create_format(const Format& f,mav_codec codec,const mav_color& color,CMVideoFormatDescriptionRef* out) {
    CFHolder<CFMutableDictionaryRef> ext(dictionary());if(!ext.value)return kVTAllocationFailedErr;
    color_dictionary(ext,color);number(ext,kCMFormatDescriptionExtension_FieldCount,1);
    if(@available(macOS 12.0,iOS 15.0,tvOS 15.0,*))number(ext,kCMFormatDescriptionExtension_BitsPerComponent,f.bit_depth);
    if(codec==MAV_CODEC_AV1) {
        if(!f.width||!f.height||f.av1c.empty())return kCMFormatDescriptionError_InvalidParameter;
        CFHolder<CFDataRef> av1c(CFDataCreate(kCFAllocatorDefault,f.av1c.data(),f.av1c.size()));
        CFHolder<CFMutableDictionaryRef> atoms(dictionary());CFDictionarySetValue(atoms,CFSTR("av1C"),av1c);
        CFDictionarySetValue(ext,kCMFormatDescriptionExtension_SampleDescriptionExtensionAtoms,atoms);
        return CMVideoFormatDescriptionCreate(kCFAllocatorDefault,kCMVideoCodecType_AV1,f.width,f.height,ext,out);
    }
    if(f.parameter_sets.size()!=3)return kCMFormatDescriptionError_InvalidParameter;
    const uint8_t* ptr[3];size_t sizes[3];for(size_t i=0;i<3;++i){ptr[i]=f.parameter_sets[i].data();sizes[i]=f.parameter_sets[i].size();}
    return CMVideoFormatDescriptionCreateFromHEVCParameterSets(kCFAllocatorDefault,3,ptr,sizes,4,ext,out);
}
// Copy attachment on current systems; retain the borrowed value on macOS 11.
static CFTypeRef copy_attachment(CVPixelBufferRef p,CFStringRef key) {
    if(@available(macOS 12.0,iOS 15.0,tvOS 15.0,*))return CVBufferCopyAttachment(p,key,nullptr);
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
    auto value=CVBufferGetAttachment(p,key,nullptr);return value?CFRetain(value):nullptr;
#pragma clang diagnostic pop
}
static uint16_t code(CVPixelBufferRef p,CFStringRef key,int (*convert)(CFStringRef)) {
    CFHolder<CFTypeRef> v(copy_attachment(p,key));
    return v.value&&CFGetTypeID(v)==CFStringGetTypeID()?convert(static_cast<CFStringRef>(v.value)):2;
}
mav_color image_color(CVPixelBufferRef p) {
    mav_color c{};
    c.primaries=code(p,kCVImageBufferColorPrimariesKey,CVColorPrimariesGetIntegerCodePointForString);
    c.transfer=code(p,kCVImageBufferTransferFunctionKey,CVTransferFunctionGetIntegerCodePointForString);
    c.matrix=code(p,kCVImageBufferYCbCrMatrixKey,CVYCbCrMatrixGetIntegerCodePointForString);
    if(c.primaries!=2||c.transfer!=2||c.matrix!=2)c.valid|=MAV_COLOR_DESCRIPTION;
    auto fmt=CVPixelBufferGetPixelFormatType(p);c.valid|=MAV_COLOR_RANGE;
    c.full_range=fmt==kCVPixelFormatType_420YpCbCr8BiPlanarFullRange||fmt==kCVPixelFormatType_420YpCbCr10BiPlanarFullRange;
    const CFStringRef loc[]={kCVImageBufferChromaLocation_Left,kCVImageBufferChromaLocation_Center,kCVImageBufferChromaLocation_TopLeft,kCVImageBufferChromaLocation_Top,kCVImageBufferChromaLocation_BottomLeft,kCVImageBufferChromaLocation_Bottom};
    CFHolder<CFTypeRef> cl(copy_attachment(p,kCVImageBufferChromaLocationTopFieldKey));
    for(uint8_t i=0;cl.value&&i<6;++i)if(CFEqual(cl,loc[i])){c.valid|=MAV_COLOR_CHROMA_LOCATION;c.chroma_location=i;}
    for(int i=0;i<2;++i){CFHolder<CFTypeRef> v(copy_attachment(p,i?kCVImageBufferContentLightLevelInfoKey:kCVImageBufferMasteringDisplayColorVolumeKey));size_t n=i?4:24;
        if(v.value&&CFGetTypeID(v)==CFDataGetTypeID()&&CFDataGetLength(static_cast<CFDataRef>(v.value))==static_cast<CFIndex>(n)){c.valid|=i?MAV_COLOR_CONTENT_LIGHT:MAV_COLOR_MASTERING;std::memcpy(i?c.content_light:c.mastering,CFDataGetBytePtr(static_cast<CFDataRef>(v.value)),n);}}
    return c;
}
static void attach(CVPixelBufferRef p,CFStringRef key,CFTypeRef value) {
    if(!value)return;CFHolder<CFTypeRef> existing(copy_attachment(p,key));
    if(!existing.value)CVBufferSetAttachment(p,key,value,kCVAttachmentMode_ShouldPropagate);
}
void attach_missing_color(CVPixelBufferRef p,const mav_color& c) {
    if(c.valid&MAV_COLOR_DESCRIPTION){
        attach(p,kCVImageBufferColorPrimariesKey,CVColorPrimariesGetStringForIntegerCodePoint(c.primaries));
        attach(p,kCVImageBufferTransferFunctionKey,CVTransferFunctionGetStringForIntegerCodePoint(c.transfer));
        attach(p,kCVImageBufferYCbCrMatrixKey,CVYCbCrMatrixGetStringForIntegerCodePoint(c.matrix));
    }
    const CFStringRef loc[]={kCVImageBufferChromaLocation_Left,kCVImageBufferChromaLocation_Center,kCVImageBufferChromaLocation_TopLeft,kCVImageBufferChromaLocation_Top,kCVImageBufferChromaLocation_BottomLeft,kCVImageBufferChromaLocation_Bottom};
    if((c.valid&MAV_COLOR_CHROMA_LOCATION)&&c.chroma_location<6)attach(p,kCVImageBufferChromaLocationTopFieldKey,loc[c.chroma_location]);
    for(int i=0;i<2;++i)if(c.valid&(i?MAV_COLOR_CONTENT_LIGHT:MAV_COLOR_MASTERING)){
        auto key=i?kCVImageBufferContentLightLevelInfoKey:kCVImageBufferMasteringDisplayColorVolumeKey;
        CFHolder<CFTypeRef> existing(copy_attachment(p,key));if(!existing.value){CFHolder<CFDataRef> data(CFDataCreate(kCFAllocatorDefault,i?c.content_light:c.mastering,i?4:24));if(data.value)CVBufferSetAttachment(p,key,data,kCVAttachmentMode_ShouldPropagate);}
    }
}
mav_result vt_result(OSStatus s) {
    if(!s)return MAV_OK;
    switch(s){case kVTCouldNotFindVideoDecoderErr:case kVTVideoDecoderUnsupportedDataFormatErr:case kVTVideoDecoderNotAvailableNowErr:return MAV_UNSUPPORTED;
        case kVTVideoDecoderBadDataErr:return MAV_MALFORMED_INPUT;case kVTAllocationFailedErr:return MAV_OUT_OF_MEMORY;default:return MAV_DECODER_FAILED;}
}
}
