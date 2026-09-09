#pragma once

// Correctness-only helpers for experiments with lossless-compressed VT output.
// Never call the transfer/readback helpers from a measured decode callback or a
// paced/throughput run. Core Video's compressed storage is hardware-specific and
// must not be interpreted by CPU code. See CVPixelBuffer.h's compressed formats.
#import <CoreVideo/CoreVideo.h>
#import <CoreVideo/CVMetalTextureCache.h>
#import <Metal/Metal.h>
#import <VideoToolbox/VideoToolbox.h>
#include <stdexcept>
#include <string>
#include <utility>

namespace vt_experiment {

struct OutputFormat {
    OSType linear;
    unsigned depth;
    bool compressed;
    bool full_range;
};

inline OutputFormat outputFormat(OSType format) {
    switch (format) {
    case kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange:
        return {format, 8, false, false};
    case kCVPixelFormatType_420YpCbCr8BiPlanarFullRange:
        return {format, 8, false, true};
    case kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange:
        return {format, 10, false, false};
    case kCVPixelFormatType_420YpCbCr10BiPlanarFullRange:
        return {format, 10, false, true};
    case kCVPixelFormatType_Lossless_420YpCbCr8BiPlanarVideoRange:
        return {kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange, 8, true, false};
    case kCVPixelFormatType_Lossless_420YpCbCr8BiPlanarFullRange:
        return {kCVPixelFormatType_420YpCbCr8BiPlanarFullRange, 8, true, true};
    case kCVPixelFormatType_Lossless_420YpCbCr10PackedBiPlanarVideoRange:
        return {kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange, 10, true, false};
    case kCVPixelFormatType_Lossless_420YpCbCr10PackedBiPlanarFullRange:
        return {kCVPixelFormatType_420YpCbCr10BiPlanarFullRange, 10, true, true};
    default:
        throw std::runtime_error("unsupported correctness output pixel format " + std::to_string(format));
    }
}

template <class T> class OwnedCF {
    T value_ = nullptr;
public:
    OwnedCF() = default;
    explicit OwnedCF(T value) : value_(value) {}
    ~OwnedCF() { if (value_) CFRelease(value_); }
    OwnedCF(const OwnedCF&) = delete;
    OwnedCF& operator=(const OwnedCF&) = delete;
    OwnedCF(OwnedCF&& other) noexcept : value_(std::exchange(other.value_, nullptr)) {}
    T get() const { return value_; }
    T* out() { return &value_; }
};
using OwnedPixelBuffer = OwnedCF<CVPixelBufferRef>;

// This checks the ORIGINAL decoder output, before any validation conversion.
// Texture creation is a compatibility test, not proof of sample equivalence or
// successful presentation. A separate reference comparison must establish that.
inline void verifyOriginalMetalOutput(CVPixelBufferRef pixel, CVMetalTextureCacheRef cache) {
    if (!pixel || !cache) throw std::runtime_error("missing output buffer or Metal cache");
    auto format = outputFormat(CVPixelBufferGetPixelFormatType(pixel));
    if (format.compressed) {
        if (@available(macOS 12.0, *)) {
            if (!CVIsCompressedPixelFormatAvailable(CVPixelBufferGetPixelFormatType(pixel)))
                throw std::runtime_error("compressed output format unavailable on this device");
        } else throw std::runtime_error("compressed output format capability API unavailable");
    }
    if (CVPixelBufferGetPlaneCount(pixel) != 2 || !CVPixelBufferGetIOSurface(pixel))
        throw std::runtime_error("original output planes/IOSurface mismatch");
    for (size_t plane = 0; plane < 2; ++plane) {
        const auto metalFormat = plane ? (format.depth == 10 ? MTLPixelFormatRG16Unorm : MTLPixelFormatRG8Unorm)
                                       : (format.depth == 10 ? MTLPixelFormatR16Unorm : MTLPixelFormatR8Unorm);
        const auto width = CVPixelBufferGetWidthOfPlane(pixel, plane);
        const auto height = CVPixelBufferGetHeightOfPlane(pixel, plane);
        OwnedCF<CVMetalTextureRef> texture;
        const auto status = CVMetalTextureCacheCreateTextureFromImage(nullptr, cache, pixel, nullptr,
            metalFormat, width, height, plane, texture.out());
        if (status || !texture.get() || !CVMetalTextureGetTexture(texture.get()))
            throw std::runtime_error("original output Metal texture creation failed: " + std::to_string(status));
        id<MTLTexture> metal = CVMetalTextureGetTexture(texture.get());
        if (metal.width != width || metal.height != height || metal.pixelFormat != metalFormat)
            throw std::runtime_error("original output Metal texture description mismatch");
    }
}

// Return a retained linear buffer with identical dimensions, range and depth.
// Linear source buffers are retained directly. Only lossless-compressed formats
// are converted. No scaling, color matching, range reduction or depth reduction
// is requested. Exact software-reference comparison must still verify the result;
// a successful VTPixelTransferSessionTransferImage alone proves no equivalence.
inline OwnedPixelBuffer linearForReadback(CVPixelBufferRef source) {
    if (!source) throw std::runtime_error("missing output for validation readback");
    const auto format = outputFormat(CVPixelBufferGetPixelFormatType(source));
    if (!format.compressed) return OwnedPixelBuffer(CVPixelBufferRetain(source));

    const size_t width = CVPixelBufferGetWidth(source), height = CVPixelBufferGetHeight(source);
    OwnedCF<CFMutableDictionaryRef> attributes(CFDictionaryCreateMutable(nullptr, 0,
        &kCFTypeDictionaryKeyCallBacks, &kCFTypeDictionaryValueCallBacks));
    OwnedCF<CFDictionaryRef> surface(CFDictionaryCreate(nullptr, nullptr, nullptr, 0,
        &kCFTypeDictionaryKeyCallBacks, &kCFTypeDictionaryValueCallBacks));
    if (!attributes.get() || !surface.get()) throw std::runtime_error("readback attributes allocation failed");
    CFDictionarySetValue(attributes.get(), kCVPixelBufferIOSurfacePropertiesKey, surface.get());
    CFDictionarySetValue(attributes.get(), kCVPixelBufferMetalCompatibilityKey, kCFBooleanTrue);
    OwnedPixelBuffer destination;
    const auto allocation = CVPixelBufferCreate(nullptr, width, height, format.linear, attributes.get(), destination.out());
    if (allocation || !destination.get())
        throw std::runtime_error("linear readback buffer allocation failed: " + std::to_string(allocation));

    struct TransferSession {
        VTPixelTransferSessionRef value = nullptr;
        ~TransferSession() { if (value) { VTPixelTransferSessionInvalidate(value); CFRelease(value); } }
    } transfer;
    auto status = VTPixelTransferSessionCreate(nullptr, &transfer.value);
    if (status || !transfer.value)
        throw std::runtime_error("readback transfer session creation failed: " + std::to_string(status));
    // The default normal scaling mode copies the complete image at equal size.
    // Do not request destination color properties: those can enable conversion.
    status = VTPixelTransferSessionTransferImage(transfer.value, source, destination.get());
    if (status) throw std::runtime_error("lossless output readback transfer failed: " + std::to_string(status));
    if (CVPixelBufferGetWidth(destination.get()) != width || CVPixelBufferGetHeight(destination.get()) != height ||
        CVPixelBufferGetPixelFormatType(destination.get()) != format.linear || CVPixelBufferGetPlaneCount(destination.get()) != 2)
        throw std::runtime_error("linear readback output description mismatch");
    return destination;
}

} // namespace vt_experiment
