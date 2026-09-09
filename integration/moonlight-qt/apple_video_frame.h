#pragma once
#include <moonlight_apple_video/decoder.h>
#include <array>
extern "C" {
#include <libavutil/frame.h>
}

// A refcounted renderer wrapper; retains the CVPixelBuffer, never its planes.
AVFrame* appleVideoWrapFrame(const mav_completion& completion, int width, int height);

struct AppleVideoHdrMetadata {
    bool hasMastering = false, hasContentLight = false;
    std::array<uint8_t, 24> mastering{};
    std::array<uint8_t, 4> contentLight{};
};
AppleVideoHdrMetadata appleVideoFrameHdrMetadata(const AVFrame* frame);
