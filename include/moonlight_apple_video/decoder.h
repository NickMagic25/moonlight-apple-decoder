#ifndef MOONLIGHT_APPLE_VIDEO_DECODER_H
#define MOONLIGHT_APPLE_VIDEO_DECODER_H
#include <stddef.h>
#include <stdint.h>
#ifdef __APPLE__
#include <CoreVideo/CVPixelBuffer.h>
typedef CVPixelBufferRef mav_pixel_buffer;
#else
typedef struct __CVBuffer *mav_pixel_buffer;
#endif
#ifdef __cplusplus
extern "C" {
#endif
#define MAV_ABI_VERSION 1u
#define MAV_MAX_ACCESS_UNIT_BYTES (64u * 1024u * 1024u)
#define MAV_MAX_SPANS 4096u
typedef struct mav_decoder mav_decoder;
typedef enum mav_result {
    MAV_OK=0, MAV_WOULD_BLOCK=1, MAV_INVALID_ARGUMENT=2, MAV_MALFORMED_INPUT=3,
    MAV_UNSUPPORTED=4, MAV_NEED_RANDOM_ACCESS=5, MAV_DECODER_FAILED=6,
    MAV_OUT_OF_MEMORY=7, MAV_REENTRANT_CALL=8, MAV_CLOSED=9, MAV_TIMEOUT=10,
    MAV_API_UNAVAILABLE=11
} mav_result;
typedef enum mav_codec { MAV_CODEC_AV1=1, MAV_CODEC_HEVC=2 } mav_codec;
typedef enum mav_framing { MAV_FRAMING_AV1_LOW_OVERHEAD=1, MAV_FRAMING_HEVC_ANNEX_B=2 } mav_framing;
typedef enum mav_hardware_policy { MAV_HARDWARE_REQUIRED=0, MAV_HARDWARE_PREFERRED=1 } mav_hardware_policy;
typedef enum mav_completion_status {
    MAV_COMPLETION_OUTPUT=0, MAV_COMPLETION_NO_DISPLAY=1, MAV_COMPLETION_FAILED=2,
    MAV_COMPLETION_DROPPED=3, MAV_COMPLETION_CANCELLED=4
} mav_completion_status;
typedef struct mav_time { int64_t value; int32_t timescale; uint32_t valid; } mav_time;
enum { MAV_COLOR_DESCRIPTION=1, MAV_COLOR_RANGE=2, MAV_COLOR_CHROMA_LOCATION=4,
       MAV_COLOR_MASTERING=8, MAV_COLOR_CONTENT_LIGHT=16 };
/* ISO/IEC 23091-2 color values. Mastering bytes use big endian HEVC/SMPTE2086
 * units (G,B,R,white xy /50000, max/min luminance /10000); content light is
 * big endian maxCLL/maxFALL. Chroma locations: 0 left, 1 center, 2 top-left,
 * 3 top, 4 bottom-left, 5 bottom (HEVC chroma_sample_loc_type values).
 * Unknown fields have their validity bit cleared. */
typedef struct mav_color {
    uint32_t valid; uint16_t primaries, transfer, matrix; uint8_t full_range;
    uint8_t chroma_location; uint8_t mastering[24]; uint8_t content_light[4];
} mav_color;
typedef struct mav_span { const uint8_t *data; size_t size; } mav_span;
enum { MAV_INPUT_RANDOM_ACCESS=1, MAV_INPUT_DISCONTINUITY=2 };
typedef struct mav_access_unit {
    uint32_t struct_size, version; mav_codec codec; mav_framing framing;
    const mav_span *spans; size_t span_count; uint64_t frame_id; void *caller_context;
    mav_time pts, dts, duration; uint32_t flags; mav_color color;
    /* Values in mav_monotonic_time_ns domain; zero means unavailable.
     * Do not put host presentation timestamps or unmapped common-c clock here. */
    uint64_t scheduled_arrival_ns, first_packet_ns;
} mav_access_unit;
enum { MAV_TRACE_PREPARATION=1, MAV_TRACE_VT_SUBMIT=2, MAV_TRACE_VT_RETURN=4,
       MAV_TRACE_CALLBACK=8, MAV_TRACE_ARRIVAL=16, MAV_TRACE_FIRST_PACKET=32 };
typedef struct mav_trace {
    uint32_t valid; uint64_t first_packet_ns, scheduled_arrival_ns, admission_ns;
    uint64_t preparation_start_ns, preparation_end_ns, vt_submit_ns, vt_return_ns;
    uint64_t callback_ns, handoff_ns;
    /* With multiple child samples: first submit to last callback, distinguished
     * by internal_samples. Existing-frame events are not newly decoded frames. */
} mav_trace;
typedef struct mav_completion {
    uint32_t struct_size, version; uint64_t frame_id, generation; void *caller_context;
    mav_completion_status status; mav_result result; int32_t backend_status;
    mav_pixel_buffer pixel_buffer; mav_time pts, duration; mav_color color;
    uint32_t width, height, pixel_format, bit_depth, hardware_accelerated;
    uint32_t internal_samples, displayed_outputs, show_existing_frame;
    mav_trace trace;
} mav_completion;
typedef void (*mav_completion_callback)(void *context, const mav_completion *completion);
typedef void (*mav_capacity_callback)(void *context);
typedef struct mav_config {
    uint32_t struct_size, version; mav_codec codec; uint32_t width, height, bit_depth;
    mav_hardware_policy hardware_policy; uint32_t max_frames_in_flight;
    /* CoreVideo FourCC constraints, zero count chooses 420v/f or x420/xf20
     * according to signaled bit depth/range. Never silently narrows to 8-bit. */
    uint32_t pixel_formats[8], pixel_format_count;
    int32_t realtime; /* 0/1 */
    int32_t power_efficiency; /* -1 default, 0 disabled; 1 unsupported with realtime */
    uint32_t thread_count; /* 0 default, optional diagnostic hint */
    mav_color fallback_color;
    mav_completion_callback completion; mav_capacity_callback capacity_available; void *context;
} mav_config;
typedef struct mav_metrics {
    uint32_t struct_size, version; uint64_t generation, accepted, completed, displayed;
    uint64_t no_display, failed, dropped, cancelled, would_block, rejected;
    uint64_t internal_samples, compressed_copy_count, compressed_copy_bytes;
    uint64_t outstanding, peak_outstanding, session_creations, recoveries;
    uint32_t hardware_accelerated, hardware_validated, pixel_format;
    int32_t realtime_status, power_efficiency_status, thread_count_status;
    int32_t realtime_effective, power_efficiency_effective, thread_count_effective;
    int32_t last_backend_status;
} mav_metrics;
typedef struct mav_capability {
    uint32_t struct_size, version; mav_codec codec;
    uint32_t api_available, hardware_decode_candidate;
    /* Candidate is codec-level only. Exact support requires a real successful
     * output and mav_metrics.hardware_validated for that stream configuration. */
} mav_capability;
void mav_config_default(mav_config *config, mav_codec codec);
void mav_access_unit_default(mav_access_unit *unit, mav_codec codec);
uint64_t mav_monotonic_time_ns(void);
const char *mav_result_string(mav_result result);
mav_result mav_query_capability(mav_codec codec, mav_capability *capability);
mav_result mav_decoder_create(const mav_config *config, mav_decoder **decoder);
/* One COMPLETE low-delay access unit. HEVC: Annex-B, any span boundaries.
 * AV1: low-overhead OBUs, each with an explicit LEB128 size field,
 * a single-layer temporal unit with at most one displayed image;
 * hidden coded frames and show_existing_frame are explicitly accounted for.
 * IVF, MP4 and AV1 Annex-B outer framing must be removed by an importer.
 * Accepted (MAV_OK) means bytes owned before return and exactly ONE terminal
 * completion, including configuration-only/no-display inputs. Synchronous
 * rejection (including WOULD_BLOCK) consumes nothing and yields no completion.
 * Random-access flags are hints; the parser validates actual codec syntax.
 * Config changes with pending work return WOULD_BLOCK; drain on a control
 * thread then retry. Input discontinuity requires reset first (flag alone
 * does not silently discard accepted work).
 *
 * Callbacks may be inline and on different threads. Buffers and completion
 * structs are BORROWED during callback; retain CVPixelBuffer to keep output
 * after callback/reset/destruction. No pixel planes are copied by this core.
 * User callbacks are never called holding the state mutex. Submit/control
 * operations must be serialized by the caller; concurrent operations return
 * WOULD_BLOCK. Queries and capacity wait may run concurrently. Callback may
 * query metrics, retain output and signal a worker, but must not submit, wait,
 * drain, reset or destroy (MAV_REENTRANT_CALL). Do not throw across this C ABI.
 * Do not block callbacks on another thread entering control operations.
 */
mav_result mav_decoder_submit_copy(mav_decoder *decoder, const mav_access_unit *unit);
/* Event-driven wait; 0 timeout polls, UINT64_MAX waits indefinitely.
 * A wake grants no reservation; retry submit. Not callable from callbacks. */
mav_result mav_decoder_wait_for_capacity(mav_decoder *decoder, uint64_t timeout_ns);
/* Drain completes accepted work, preserving config/reference state. Reset
 * discards old-generation output, cancels pending submissions, clears codec
 * state, and requires a new random-access point. On return no old callbacks
 * remain in progress. Retained CVPixelBuffers stay valid. Destruction closes
 * admission and synchronously resolves work. Caller must join other API users
 * before destroy. After destroy returns anything except WOULD_BLOCK or
 * REENTRANT_CALL, the handle is invalid even if backend drain reported failure. */
mav_result mav_decoder_drain(mav_decoder *decoder);
mav_result mav_decoder_reset(mav_decoder *decoder);
mav_result mav_decoder_destroy(mav_decoder *decoder);
mav_result mav_decoder_get_metrics(mav_decoder *decoder, mav_metrics *metrics);
#ifdef __cplusplus
}
#endif
#endif
