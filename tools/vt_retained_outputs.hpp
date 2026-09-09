#pragma once
#if !defined(MAV_VT_EXPERIMENTS) || !MAV_VT_EXPERIMENTS
#error "Retained output experiments require MAV_VT_EXPERIMENTS"
#endif

#import <CoreVideo/CoreVideo.h>
#include <array>
#include <cstdlib>
#include <stdexcept>

namespace vt_experiment {

// An ownership diagnostic for replay's timed sink. Keep a bounded number of
// recent decoded buffers alive as a renderer would, without copying or mapping
// pixels, waiting, or allocating storage in the callback. This does not model
// presentation or GPU use, and is not equivalent to a pixel-pool minimum count.
// The caller must serialize retain()/clear() and resolve callbacks before
// destruction. Replay's existing Sink lock provides that serialization.
class RetainedOutputs {
    static constexpr unsigned capacity_ = 8;
    std::array<CVPixelBufferRef, capacity_> buffers_{};
    unsigned limit_ = 0;
    unsigned next_ = 0;
    unsigned size_ = 0;

public:
    // Inert construction lets the owner parse the environment inside its normal
    // error-handling scope, before beginning any decode work.
    RetainedOutputs() = default;
    ~RetainedOutputs() { clear(); }
    RetainedOutputs(const RetainedOutputs&) = delete;
    RetainedOutputs& operator=(const RetainedOutputs&) = delete;

    static unsigned parseLimit(const char* value) {
        if (!value) return 0;
        if (!*value) throw std::invalid_argument("MAV_VT_RETAIN_OUTPUTS must be an integer in [0,8]");
        unsigned parsed = 0;
        for (const unsigned char* p = reinterpret_cast<const unsigned char*>(value); *p; ++p) {
            if (*p < '0' || *p > '9' || parsed > capacity_ / 10 ||
                (parsed == capacity_ / 10 && unsigned(*p - '0') > capacity_ % 10))
                throw std::invalid_argument("MAV_VT_RETAIN_OUTPUTS must be an integer in [0,8]");
            parsed = parsed * 10 + unsigned(*p - '0');
        }
        return parsed;
    }

    void configureFromEnvironment() {
        if (size_) throw std::logic_error("cannot change output retention while buffers are retained");
        limit_ = parseLimit(std::getenv("MAV_VT_RETAIN_OUTPUTS"));
        next_ = 0;
    }

    void retain(CVPixelBufferRef pixel) noexcept {
        if (!limit_ || !pixel) return;
        // Retain first so replacing a slot with the same CVPixelBuffer is safe.
        CVPixelBufferRetain(pixel);
        CVPixelBufferRef displaced = buffers_[next_];
        buffers_[next_] = pixel;
        next_ = (next_ + 1) % limit_;
        if (size_ < limit_) ++size_;
        if (displaced) CVPixelBufferRelease(displaced);
    }

    void clear() noexcept {
        for (auto& pixel : buffers_) {
            if (pixel) CVPixelBufferRelease(pixel);
            pixel = nullptr;
        }
        next_ = 0;
        size_ = 0;
    }

    unsigned limit() const noexcept { return limit_; }
    unsigned size() const noexcept { return size_; }
};

} // namespace vt_experiment
