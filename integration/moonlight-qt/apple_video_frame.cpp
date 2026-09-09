#include "apple_video_frame.h"
extern "C" {
#include <libavutil/mastering_display_metadata.h>
#include <libavutil/mathematics.h>
}

namespace {
void releasePixelBuffer(void*, uint8_t* data) {
    CVPixelBufferRelease(reinterpret_cast<CVPixelBufferRef>(data));
}
uint16_t be16(const uint8_t* p) { return (uint16_t(p[0]) << 8) | p[1]; }
uint32_t be32(const uint8_t* p) { return (uint32_t(be16(p)) << 16) | be16(p + 2); }
void put16(uint8_t* p, uint16_t v) { p[0] = v >> 8; p[1] = v; }
void put32(uint8_t* p, uint32_t v) { put16(p, v >> 16); put16(p + 2, v); }
bool metadataValue(AVRational q, int scale, uint32_t limit, uint32_t& value) {
    if (q.den <= 0 || q.num < 0) return false;
    const int64_t scaled = av_rescale_q(q.num, AVRational{1, q.den}, AVRational{1, scale});
    if (scaled < 0 || uint64_t(scaled) > limit) return false;
    value = uint32_t(scaled);
    return true;
}
}

AppleVideoHdrMetadata appleVideoFrameHdrMetadata(const AVFrame* frame) {
    AppleVideoHdrMetadata result;
    if (!frame) return result;
    const AVFrameSideData* side = av_frame_get_side_data(frame, AV_FRAME_DATA_MASTERING_DISPLAY_METADATA);
    if (side && side->size >= sizeof(AVMasteringDisplayMetadata)) {
        const auto* md = reinterpret_cast<const AVMasteringDisplayMetadata*>(side->data);
        bool valid = md->has_primaries && md->has_luminance;
        uint32_t value = 0;
        for (int gbr = 0; gbr < 3 && valid; ++gbr) {
            const int rgb = (gbr + 1) % 3;
            for (int xy = 0; xy < 2 && valid; ++xy) {
                valid = metadataValue(md->display_primaries[rgb][xy], 50000, 50000, value);
                if (valid) put16(result.mastering.data() + gbr * 4 + xy * 2, uint16_t(value));
            }
        }
        for (int xy = 0; xy < 2 && valid; ++xy) {
            valid = metadataValue(md->white_point[xy], 50000, 50000, value);
            if (valid) put16(result.mastering.data() + 12 + xy * 2, uint16_t(value));
        }
        if (valid) valid = metadataValue(md->max_luminance, 10000, UINT32_MAX, value);
        if (valid) put32(result.mastering.data() + 16, value);
        if (valid) valid = metadataValue(md->min_luminance, 10000, UINT32_MAX, value);
        if (valid) put32(result.mastering.data() + 20, value);
        result.hasMastering = valid;
    }
    side = av_frame_get_side_data(frame, AV_FRAME_DATA_CONTENT_LIGHT_LEVEL);
    if (side && side->size >= sizeof(AVContentLightMetadata)) {
        const auto* cl = reinterpret_cast<const AVContentLightMetadata*>(side->data);
        if (cl->MaxCLL <= UINT16_MAX && cl->MaxFALL <= UINT16_MAX) {
            put16(result.contentLight.data(), uint16_t(cl->MaxCLL));
            put16(result.contentLight.data() + 2, uint16_t(cl->MaxFALL));
            result.hasContentLight = true;
        }
    }
    return result;
}

AVFrame* appleVideoWrapFrame(const mav_completion& c, int width, int height) {
    if (!c.pixel_buffer || c.status != MAV_COMPLETION_OUTPUT) return nullptr;
    AVFrame* frame = av_frame_alloc();
    if (!frame) return nullptr;
    CVPixelBufferRetain(c.pixel_buffer);
    frame->buf[0] = av_buffer_create(reinterpret_cast<uint8_t*>(c.pixel_buffer), 0,
                                   releasePixelBuffer, nullptr, AV_BUFFER_FLAG_READONLY);
    if (!frame->buf[0]) {
        CVPixelBufferRelease(c.pixel_buffer);
        av_frame_free(&frame);
        return nullptr;
    }
    frame->format = AV_PIX_FMT_VIDEOTOOLBOX;
    frame->data[3] = reinterpret_cast<uint8_t*>(c.pixel_buffer);
    frame->width = int(c.width);
    frame->height = int(c.height);
    // Match the existing AV1 right/bottom padding policy, without CPU mapping.
    if (width > 0 && height > 0 && frame->width >= width && frame->height >= height &&
        frame->width - width < 64 && frame->height - height < 64) {
        frame->crop_right = frame->width - width;
        frame->crop_bottom = frame->height - height;
        av_frame_apply_cropping(frame, 0);
    }
    frame->pts = c.pts.valid && c.pts.timescale > 0 ?
        av_rescale_q(c.pts.value, AVRational{1, c.pts.timescale}, AVRational{1, 90000}) : AV_NOPTS_VALUE;
    frame->time_base = AVRational{1, 90000};
    if (c.color.valid & MAV_COLOR_DESCRIPTION) {
        frame->color_primaries = static_cast<AVColorPrimaries>(c.color.primaries);
        frame->color_trc = static_cast<AVColorTransferCharacteristic>(c.color.transfer);
        frame->colorspace = static_cast<AVColorSpace>(c.color.matrix);
    }
    if (c.color.valid & MAV_COLOR_RANGE)
        frame->color_range = c.color.full_range ? AVCOL_RANGE_JPEG : AVCOL_RANGE_MPEG;
    if ((c.color.valid & MAV_COLOR_CHROMA_LOCATION) && c.color.chroma_location < 6) {
        static const AVChromaLocation locations[] = {AVCHROMA_LOC_LEFT, AVCHROMA_LOC_CENTER,
            AVCHROMA_LOC_TOPLEFT, AVCHROMA_LOC_TOP, AVCHROMA_LOC_BOTTOMLEFT, AVCHROMA_LOC_BOTTOM};
        frame->chroma_location = locations[c.color.chroma_location];
    }
    if (c.color.valid & MAV_COLOR_MASTERING) {
        auto md = av_mastering_display_metadata_create_side_data(frame);
        if (!md) { av_frame_free(&frame); return nullptr; }
        // Library/SEI is G,B,R; AVFrame mastering data is R,G,B.
        for (int rgb = 0; rgb < 3; ++rgb) {
            int gbr = (rgb + 2) % 3;
            for (int xy = 0; xy < 2; ++xy)
                md->display_primaries[rgb][xy] = av_make_q(be16(c.color.mastering + gbr * 4 + xy * 2), 50000);
        }
        md->white_point[0] = av_make_q(be16(c.color.mastering + 12), 50000);
        md->white_point[1] = av_make_q(be16(c.color.mastering + 14), 50000);
        md->max_luminance = av_d2q(double(be32(c.color.mastering + 16)) / 10000, INT32_MAX);
        md->min_luminance = av_d2q(double(be32(c.color.mastering + 20)) / 10000, INT32_MAX);
        md->has_primaries = md->has_luminance = 1;
    }
    if (c.color.valid & MAV_COLOR_CONTENT_LIGHT) {
        auto cl = av_content_light_metadata_create_side_data(frame);
        if (!cl) { av_frame_free(&frame); return nullptr; }
        cl->MaxCLL = be16(c.color.content_light);
        cl->MaxFALL = be16(c.color.content_light + 2);
    }
    return frame;
}
