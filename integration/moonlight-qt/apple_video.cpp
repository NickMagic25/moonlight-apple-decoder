#include "apple_video.h"
#include "apple_video_frame.h"
#include "ffmpeg.h"
#include "ffmpeg-renderers/vt.h"
#include "streaming/session.h"
#include <CoreVideo/CVPixelBufferIOSurface.h>
#include <algorithm>
#include <cstdio>
#include <limits>
#include <vector>

namespace {
mav_codec codecFor(int format) {
    return (format & VIDEO_FORMAT_MASK_AV1) ? MAV_CODEC_AV1 : MAV_CODEC_HEVC;
}
bool permanentFailure(mav_result result) {
    return result == MAV_UNSUPPORTED || result == MAV_API_UNAVAILABLE ||
        result == MAV_INVALID_ARGUMENT || result == MAV_OUT_OF_MEMORY ||
        result == MAV_CLOSED || result == MAV_REENTRANT_CALL;
}
void put16(uint8_t* p, uint16_t value) { p[0] = value >> 8; p[1] = value; }
void put32(uint8_t* p, uint32_t value) { put16(p, value >> 16); put16(p + 2, value); }
mav_color streamColor(PDECODE_UNIT du, int range) {
    mav_color color{};
    color.valid = MAV_COLOR_DESCRIPTION | MAV_COLOR_RANGE;
    color.full_range = range == COLOR_RANGE_FULL;
    if (du->hdrActive || du->colorspace == COLORSPACE_REC_2020) {
        color.primaries = 9; color.transfer = du->hdrActive ? 16 : 14; color.matrix = 9;
    } else if (du->colorspace == COLORSPACE_REC_709) {
        color.primaries = 1; color.transfer = 1; color.matrix = 1;
    } else {
        color.primaries = 6; color.transfer = 6; color.matrix = 6;
    }
    SS_HDR_METADATA metadata;
    if (du->hdrActive && LiGetHdrMetadata(&metadata)) {
        if (metadata.displayPrimaries[0].x && metadata.maxDisplayLuminance) {
            color.valid |= MAV_COLOR_MASTERING;
            for (int i = 0; i < 3; ++i) {
                int rgb = (i + 1) % 3;
                put16(color.mastering + i * 4, metadata.displayPrimaries[rgb].x);
                put16(color.mastering + i * 4 + 2, metadata.displayPrimaries[rgb].y);
            }
            put16(color.mastering + 12, metadata.whitePoint.x);
            put16(color.mastering + 14, metadata.whitePoint.y);
            put32(color.mastering + 16, uint32_t(metadata.maxDisplayLuminance) * 10000);
            put32(color.mastering + 20, metadata.minDisplayLuminance);
        }
        if (metadata.maxContentLightLevel || metadata.maxFrameAverageLightLevel) {
            color.valid |= MAV_COLOR_CONTENT_LIGHT;
            put16(color.content_light, metadata.maxContentLightLevel);
            put16(color.content_light + 2, metadata.maxFrameAverageLightLevel);
        }
    }
    return color;
}
struct Probe {
    mav_completion output{};
    unsigned completions = 0;
    static void complete(void* context, const mav_completion* completion) {
        auto* p = static_cast<Probe*>(context);
        ++p->completions;
        p->output = *completion;
        if (completion->pixel_buffer) CVPixelBufferRetain(completion->pixel_buffer);
    }
    ~Probe() { if (output.pixel_buffer) CVPixelBufferRelease(output.pixel_buffer); }
};
}

AppleVideoDecoder::AppleVideoDecoder(bool testOnly) : m_TestOnly(testOnly), m_OutputReady(SDL_CreateSemaphore(0)) {}

AppleVideoDecoder::~AppleVideoDecoder() {
    m_Stopping = true;
    if (m_InputThread) {
        LiWakeWaitForVideoFrame();
        SDL_WaitThread(m_InputThread, nullptr);
    }
    // Closing admission and resolving callbacks precede destruction of callback state.
    mav_metrics metrics{}; metrics.struct_size = sizeof(metrics); metrics.version = MAV_ABI_VERSION;
    if (m_Decoder) {
        mav_decoder_drain(m_Decoder);
        mav_decoder_get_metrics(m_Decoder, &metrics);
        mav_decoder_destroy(m_Decoder);
        m_Decoder = nullptr;
    }
    if (m_OutputReady) SDL_SemPost(m_OutputReady);
    if (m_HandoffThread) SDL_WaitThread(m_HandoffThread, nullptr);
    clearOutputQueue();
    if (m_OutputReady) SDL_DestroySemaphore(m_OutputReady);
    delete m_Pacer;
    if (m_OverlayRegistered) Session::get()->getOverlayManager().setOverlayRenderer(nullptr);
    delete m_Renderer;
    if (!m_TestOnly && metrics.accepted) {
        char mean[64] = "unavailable", submissionMean[64] = "unavailable", handoffMean[64] = "unavailable";
        const uint64_t decodeSamples = m_DecodeSamples.load();
        const uint64_t submissionSamples = m_SubmissionSamples.load();
        if (m_HandoffSamples) SDL_snprintf(handoffMean, sizeof(handoffMean), "%.3f", double(m_HandoffNs.load()) / double(m_HandoffSamples.load()) / 1000);
        if (decodeSamples) SDL_snprintf(mean, sizeof(mean), "%.3f", double(m_DecodeNs.load()) / double(decodeSamples) / 1000);
        if (submissionSamples) SDL_snprintf(submissionMean, sizeof(submissionMean), "%.3f", double(m_SubmissionNs.load()) / double(submissionSamples) / 1000);
        SDL_LogInfo(SDL_LOG_CATEGORY_APPLICATION,
            "Native final: submitted=%llu completed=%llu displayed=%llu no-display=%llu failures=%llu "
            "handoff=%llu handoff-dropped=%llu pacer-dropped=%u rendered=%u "
            "pacer-us=%llu render-call-us=%llu VT-submit-to-callback-mean-us=%s callback-to-pacer-mean-us=%s "
            "VT-submit-to-return-mean-us=%s VT-submit-to-return-samples=%llu VT-submit-to-callback-samples=%llu; presentation unavailable",
            (unsigned long long)metrics.accepted, (unsigned long long)metrics.completed,
            (unsigned long long)metrics.displayed, (unsigned long long)metrics.no_display,
            (unsigned long long)metrics.failed, (unsigned long long)m_HandoffFrames.load(),
            (unsigned long long)m_HandoffDrops.load(), m_PacerStats.pacerDroppedFrames,
            m_PacerStats.renderedFrames, (unsigned long long)m_PacerStats.totalPacerTimeUs,
            (unsigned long long)m_PacerStats.totalRenderTimeUs,
            mean, handoffMean, submissionMean, (unsigned long long)submissionSamples,
            (unsigned long long)decodeSamples);
    }
}

bool AppleVideoDecoder::probe(PDECODER_PARAMETERS params) {
    const uint8_t* bytes;
    size_t size;
    if (!FFmpegVideoDecoder::getNativeProbeSample(params->videoFormat, &bytes, &size)) return false;
    Probe probe;
    mav_config config;
    mav_config_default(&config, codecFor(params->videoFormat));
    config.width = 1280; config.height = 720;
    config.bit_depth = params->videoFormat & VIDEO_FORMAT_MASK_10BIT ? 10 : 8;
    config.hardware_policy = MAV_HARDWARE_REQUIRED;
    config.completion = Probe::complete; config.context = &probe;
    mav_decoder* decoder = nullptr;
    mav_result result = mav_decoder_create(&config, &decoder);
    if (result == MAV_OK) {
        mav_span span{bytes, size};
        mav_access_unit unit;
        mav_access_unit_default(&unit, config.codec);
        unit.spans = &span; unit.span_count = 1; unit.flags = MAV_INPUT_RANDOM_ACCESS;
        unit.pts = mav_time{0, 90000, 1};
        result = mav_decoder_submit_copy(decoder, &unit);
        if (result == MAV_OK) result = mav_decoder_drain(decoder);
    }
    mav_metrics metrics{}; metrics.struct_size = sizeof(metrics); metrics.version = MAV_ABI_VERSION;
    if (decoder) mav_decoder_get_metrics(decoder, &metrics);
    // Verify output ownership independently of the decoder, including a cloned AVFrame.
    if (decoder) mav_decoder_destroy(decoder);
    bool passed = result == MAV_OK && probe.completions == 1 &&
        probe.output.status == MAV_COMPLETION_OUTPUT && metrics.hardware_validated &&
        probe.output.width == 1280 && probe.output.height == 720 &&
        probe.output.bit_depth == config.bit_depth && probe.output.pixel_buffer &&
        CVPixelBufferGetIOSurface(probe.output.pixel_buffer);
    AVFrame* frame = passed ? appleVideoWrapFrame(probe.output, 1280, 720) : nullptr;
    passed = passed && frame && frame->data[3] == reinterpret_cast<uint8_t*>(probe.output.pixel_buffer);
    AVFrame* clone = frame ? av_frame_clone(frame) : nullptr;
    av_frame_free(&frame);
    passed = passed && clone && m_Renderer->testRenderFrame(clone);
    av_frame_free(&clone);
    // Exercise the native HDR side-data path independently of the source
    // probe's SDR/HDR signaling. This validates metadata conversion and the
    // renderer's CAEDRMetadata construction, not visible HDR presentation.
    mav_completion hdr = probe.output;
    hdr.color.valid |= MAV_COLOR_MASTERING | MAV_COLOR_CONTENT_LIGHT;
    const uint16_t coordinates[] = {8500, 39850, 6550, 2300, 35400, 14600, 15635, 16450};
    for (size_t i = 0; i < 8; ++i) put16(hdr.color.mastering + i * 2, coordinates[i]);
    put32(hdr.color.mastering + 16, 10000000); put32(hdr.color.mastering + 20, 50);
    put16(hdr.color.content_light, 1000); put16(hdr.color.content_light + 2, 400);
    frame = passed ? appleVideoWrapFrame(hdr, 1280, 720) : nullptr;
    const auto roundtrip = appleVideoFrameHdrMetadata(frame);
    passed = passed && frame && roundtrip.hasMastering && roundtrip.hasContentLight &&
        std::equal(roundtrip.mastering.begin(), roundtrip.mastering.end(), hdr.color.mastering) &&
        std::equal(roundtrip.contentLight.begin(), roundtrip.contentLight.end(), hdr.color.content_light) &&
        m_Renderer->testRenderFrame(frame);
    av_frame_free(&frame);
    // An absent following frame must clear the previous metadata.
    hdr.color.valid &= ~(MAV_COLOR_MASTERING | MAV_COLOR_CONTENT_LIGHT);
    frame = passed ? appleVideoWrapFrame(hdr, 1280, 720) : nullptr;
    const auto absent = appleVideoFrameHdrMetadata(frame);
    passed = passed && frame && !absent.hasMastering && !absent.hasContentLight &&
        m_Renderer->testRenderFrame(frame);
    av_frame_free(&frame);
    SDL_LogInfo(SDL_LOG_CATEGORY_APPLICATION,
        "Native probe codec=%s depth=%u 1280x720 hardware=%u ownership+Metal+HDR-metadata=%s result=%s backend=%d; "
        "negotiated dimensions will be validated by the real stream",
        config.codec == MAV_CODEC_AV1 ? "AV1" : "HEVC", config.bit_depth,
        metrics.hardware_validated, passed ? "PASS" : "FAIL", mav_result_string(result),
        probe.output.backend_status);
    return passed;
}

bool AppleVideoDecoder::initialize(PDECODER_PARAMETERS params) {
    if (!m_OutputReady) return false;
    m_Params = *params;
    // Preserve explicit software/renderer choices; native selection can fall back unless strict.
    if (params->vds == StreamingPreferences::VDS_FORCE_SOFTWARE ||
        (params->renderer != StreamingPreferences::RS_AUTO &&
         params->renderer != StreamingPreferences::RS_PROBE_ONLY &&
         params->renderer != StreamingPreferences::RS_METAL) ||
        (params->videoFormat & (VIDEO_FORMAT_MASK_H264 | VIDEO_FORMAT_MASK_YUV444))) return false;
    if (!(params->videoFormat & (VIDEO_FORMAT_MASK_AV1 | VIDEO_FORMAT_MASK_H265))) return false;
    mav_capability capability{}; capability.struct_size = sizeof(capability); capability.version = MAV_ABI_VERSION;
    if (mav_query_capability(codecFor(params->videoFormat), &capability) != MAV_OK ||
        !capability.hardware_decode_candidate) return false;
    m_Renderer = VTMetalRendererFactory::createRenderer(true, true);
    if (!m_Renderer || !m_Renderer->initialize(params) || !probe(params)) return false;
    m_HardwareValidated = true;
    if (m_TestOnly) return true;

    // common-c uses CLOCK_UPTIME_RAW with a private epoch. Calibrate using the
    // narrowest bracket, never infer a shared epoch from timestamp units.
    m_ClockUncertaintyNs = UINT64_MAX;
    for (int i = 0; i < 8; ++i) {
        uint64_t before = mav_monotonic_time_ns();
        uint64_t commonUs = LiGetMicroseconds();
        uint64_t after = mav_monotonic_time_ns();
        if (after - before < m_ClockUncertaintyNs) {
            m_ClockUncertaintyNs = after - before + 1000;
            m_ClockOffsetNs = int64_t(before + (after - before) / 2) - int64_t(commonUs * 1000);
        }
    }
    mav_config config;
    mav_config_default(&config, codecFor(params->videoFormat));
    // Some AV1 encoders pad the coded image. The worker validates against the
    // negotiated dimensions and preserves the existing <=63-pixel crop policy.
    config.width = 0; config.height = 0;
    config.bit_depth = params->videoFormat & VIDEO_FORMAT_MASK_10BIT ? 10 : 8;
    bool ok = false;
    int requested = qgetenv("MOONLIGHT_APPLE_VIDEO_INFLIGHT").toInt(&ok);
    if (ok && requested >= 1 && requested <= 3) m_MaxInFlight = requested;
    config.max_frames_in_flight = m_MaxInFlight;
    config.hardware_policy = MAV_HARDWARE_REQUIRED;
    config.completion = completed; config.context = this;
    if (mav_decoder_create(&config, &m_Decoder) != MAV_OK) return false;
    m_Pacer = new Pacer(m_Renderer, &m_PacerStats);
    if (!m_Pacer->initialize(params->window, params->frameRate, params->enableFramePacing)) return false;
    Session::get()->getOverlayManager().setOverlayRenderer(m_Renderer);
    m_OverlayRegistered = true;
    m_Renderer->prepareToRender();
    m_HandoffThread = SDL_CreateThread(handoffThread, "NativeHandoff", this);
    if (!m_HandoffThread) return false;
    m_InputThread = SDL_CreateThread(inputThread, "NativeInput", this);
    if (!m_InputThread) return false;
    SDL_LogInfo(SDL_LOG_CATEGORY_APPLICATION,
        "Native direct VideoToolbox selected codec=%s depth=%u inflight=%u handoff-slots=3 "
        "common-clock-offset-ns=%lld uncertainty-ns=%llu (no FFmpeg codec decode)",
        config.codec == MAV_CODEC_AV1 ? "AV1" : "HEVC", config.bit_depth, m_MaxInFlight,
        (long long)m_ClockOffsetNs, (unsigned long long)m_ClockUncertaintyNs);
    return true;
}

bool AppleVideoDecoder::isHdrSupported() { return m_Renderer && (m_Renderer->getRendererAttributes() & RENDERER_ATTRIBUTE_HDR_SUPPORT); }
int AppleVideoDecoder::getDecoderCapabilities() {
    // Conservative loss recovery: common-c requests a random-access frame. Do
    // not advertise reference invalidation until independently validated live.
    return CAPABILITY_PULL_RENDERER | CAPABILITY_SLICES_PER_FRAME(MAX_SLICES);
}
int AppleVideoDecoder::getDecoderColorspace() { return m_Renderer ? m_Renderer->getDecoderColorspace() : COLORSPACE_REC_601; }
int AppleVideoDecoder::getDecoderColorRange() { return m_Renderer ? m_Renderer->getDecoderColorRange() : COLOR_RANGE_FULL; }
void AppleVideoDecoder::renderFrameOnMainThread() { if (m_Pacer) m_Pacer->renderOnMainThread(); }
void AppleVideoDecoder::setHdrMode(bool enabled) { if (m_Renderer) m_Renderer->setHdrMode(enabled); }
bool AppleVideoDecoder::notifyWindowChanged(PWINDOW_STATE_CHANGE_INFO info) { return m_Renderer && m_Renderer->notifyWindowChanged(info); }

void AppleVideoDecoder::completed(void* context, const mav_completion* completion) {
    static_cast<AppleVideoDecoder*>(context)->receive(*completion);
}
void AppleVideoDecoder::receive(const mav_completion& completion) {
    // No rendering, allocation, networking, waits or user control operations here.
    if (completion.status == MAV_COMPLETION_FAILED || completion.status == MAV_COMPLETION_DROPPED) {
        if (permanentFailure(completion.result)) { reportFatal(completion.result); return; }
        m_NeedKey = true; m_ResetNeeded = true; m_RequestIdr = true;
        SDL_SemPost(m_OutputReady);
        return;
    }
    if (completion.status != MAV_COMPLETION_OUTPUT || !completion.pixel_buffer) return;
    if (m_Stopping) { ++m_HandoffDrops; return; }
    if (!completion.show_existing_frame && completion.internal_samples == 1) {
        if ((completion.trace.valid & (MAV_TRACE_CALLBACK | MAV_TRACE_VT_SUBMIT)) ==
            (MAV_TRACE_CALLBACK | MAV_TRACE_VT_SUBMIT) && completion.trace.callback_ns >= completion.trace.vt_submit_ns) {
            m_DecodeNs += completion.trace.callback_ns - completion.trace.vt_submit_ns;
            ++m_DecodeSamples;
        }
        // A completion may precede the submission call's return. Only use an
        // observed return timestamp, independently of callback timing samples.
        if ((completion.trace.valid & (MAV_TRACE_VT_SUBMIT | MAV_TRACE_VT_RETURN)) ==
            (MAV_TRACE_VT_SUBMIT | MAV_TRACE_VT_RETURN) && completion.trace.vt_return_ns >= completion.trace.vt_submit_ns) {
            m_SubmissionNs += completion.trace.vt_return_ns - completion.trace.vt_submit_ns;
            ++m_SubmissionSamples;
        }
    }
    std::unique_lock<std::mutex> lock(m_OutputMutex, std::try_to_lock);
    if (!lock.owns_lock()) {
        ++m_HandoffDrops; // Decoded-display drop; reference decode already completed.
        return;
    }
    CVPixelBufferRef obsolete = nullptr;
    if (m_OutputCount == m_Outputs.size()) {
        // Keep the newest decoded image when the consumer falls behind. The
        // queued image being replaced already owns a semaphore permit.
        obsolete = m_Outputs[m_OutputHead].completion.pixel_buffer;
        m_OutputHead = (m_OutputHead + 1) % m_Outputs.size();
        --m_OutputCount;
        ++m_HandoffDrops;
    }
    Output& out = m_Outputs[(m_OutputHead + m_OutputCount) % m_Outputs.size()];
    out.completion = completion;
    out.completion.trace.handoff_ns = mav_monotonic_time_ns();
    out.epoch = m_Epoch;
    CVPixelBufferRetain(completion.pixel_buffer);
    ++m_OutputCount;
    lock.unlock();
    if (obsolete) CVPixelBufferRelease(obsolete);
    else SDL_SemPost(m_OutputReady);
}
void AppleVideoDecoder::clearOutputQueue() {
    std::lock_guard<std::mutex> lock(m_OutputMutex);
    while (m_OutputCount) {
        auto& out = m_Outputs[m_OutputHead];
        CVPixelBufferRelease(out.completion.pixel_buffer);
        m_OutputHead = (m_OutputHead + 1) % m_Outputs.size();
        --m_OutputCount; ++m_HandoffDrops;
    }
}
void AppleVideoDecoder::requestIdrOnHandoffThread() {
    const uint64_t now = mav_monotonic_time_ns();
    if (!m_LastIdrRequestNs || now - m_LastIdrRequestNs >= 100000000) {
        m_LastIdrRequestNs = now;
        LiRequestIdrFrame();
    }
}
void AppleVideoDecoder::reportFatal(mav_result result) {
    // Safe from completion callbacks: latch the result and wake a client worker.
    mav_result expected = MAV_OK;
    if (m_FatalResult.compare_exchange_strong(expected, result)) SDL_SemPost(m_OutputReady);
}
void AppleVideoDecoder::stopForFatalOnHandoffThread() {
    m_Stopping = true;
    LiWakeWaitForVideoFrame();
    SDL_LogError(SDL_LOG_CATEGORY_APPLICATION,
        "Native video cannot continue: %s. Ending the stream without a midstream backend switch.",
        mav_result_string(m_FatalResult));
    SDL_Event event{};
    event.type = SDL_USEREVENT;
    event.user.code = SDL_CODE_APPLE_VIDEO_FATAL;
    // Session also checks the latched error before every event wait, so even
    // a full SDL event queue cannot lose the terminal error.
    SDL_PushEvent(&event);
}
int AppleVideoDecoder::handoffThread(void* context) {
    auto* self = static_cast<AppleVideoDecoder*>(context);
    AppleVideoOutputOrder order;
    for (;;) {
        Output out;
        {
            SDL_SemWait(self->m_OutputReady);
            std::unique_lock<std::mutex> lock(self->m_OutputMutex);
            if (self->fatalError() != MAV_OK) {
                lock.unlock();
                self->stopForFatalOnHandoffThread();
                break;
            }
            if (self->m_Stopping) break;
            if (self->m_RequestIdr.exchange(false)) {
                lock.unlock();
                self->requestIdrOnHandoffThread();
                continue;
            }
            if (!self->m_OutputCount) continue;
            out = self->m_Outputs[self->m_OutputHead];
            self->m_OutputHead = (self->m_OutputHead + 1) % self->m_Outputs.size();
            --self->m_OutputCount;
        }
        if (out.epoch != self->m_Epoch ||
            !order.accept(out.epoch, out.completion.generation, uint32_t(out.completion.frame_id))) {
            CVPixelBufferRelease(out.completion.pixel_buffer);
            ++self->m_HandoffDrops;
            continue;
        }
        bool compatible = out.completion.width >= unsigned(self->m_Params.width) &&
            out.completion.height >= unsigned(self->m_Params.height) &&
            out.completion.width - self->m_Params.width < 64 &&
            out.completion.height - self->m_Params.height < 64;
        AVFrame* frame = out.epoch == self->m_Epoch && compatible ?
            appleVideoWrapFrame(out.completion, self->m_Params.width, self->m_Params.height) : nullptr;
        CVPixelBufferRelease(out.completion.pixel_buffer);
        if (!frame) {
            ++self->m_HandoffDrops;
            if (!compatible) {
                self->reportFatal(MAV_UNSUPPORTED);
            } else if (out.epoch == self->m_Epoch) {
                self->reportFatal(MAV_OUT_OF_MEMORY);
            }
            continue;
        }
        // Pacer's existing statistics use the common-c clock, not library time.
        frame->pkt_dts = LiGetMicroseconds();
        const uint64_t handoffNs = mav_monotonic_time_ns();
        if ((out.completion.trace.valid & MAV_TRACE_CALLBACK) && out.completion.trace.callback_ns <= handoffNs) {
            self->m_HandoffNs += handoffNs - out.completion.trace.callback_ns;
            ++self->m_HandoffSamples;
        }
        ++self->m_HandoffFrames;
        self->m_Pacer->submitFrame(frame);
    }
    return 0;
}

int AppleVideoDecoder::inputThread(void* context) {
    auto* self = static_cast<AppleVideoDecoder*>(context);
    while (!self->m_Stopping && self->fatalError() == MAV_OK) {
        VIDEO_FRAME_HANDLE handle;
        PDECODE_UNIT du;
        if (!LiWaitForNextVideoFrame(&handle, &du)) continue;
        int result = self->m_Stopping || self->fatalError() != MAV_OK ? DR_OK : self->submitDecodeUnit(du);
        LiCompleteVideoFrame(handle, result);
    }
    return 0;
}
int AppleVideoDecoder::submitDecodeUnit(PDECODE_UNIT du) {
    if (!du || !du->bufferList || du->fullLength <= 0 || unsigned(du->fullLength) > MAV_MAX_ACCESS_UNIT_BYTES)
        return DR_NEED_IDR;
    ++m_Received;
    uint32_t frameNumber = uint32_t(du->frameNumber);
    if (m_LastFrameNumber && frameNumber != m_LastFrameNumber && uint32_t(frameNumber - m_LastFrameNumber) < 0x80000000u)
        m_NetworkDropped += uint32_t(frameNumber - m_LastFrameNumber) - 1;
    m_LastFrameNumber = frameNumber;
    if (m_ResetNeeded.exchange(false)) {
        ++m_Epoch;
        mav_decoder_reset(m_Decoder);
        clearOutputQueue();
    }
    if (m_NeedKey && du->frameType != FRAME_TYPE_IDR) return DR_NEED_IDR;
    std::vector<mav_span> spans;
    size_t size = 0;
    for (PLENTRY entry = du->bufferList; entry; entry = entry->next) {
        if (!entry->data || entry->length <= 0 || spans.size() >= MAV_MAX_SPANS ||
            size_t(entry->length) > MAV_MAX_ACCESS_UNIT_BYTES - size) return DR_NEED_IDR;
        spans.push_back(mav_span{reinterpret_cast<const uint8_t*>(entry->data), size_t(entry->length)});
        size += entry->length;
    }
    if (size != size_t(du->fullLength)) return DR_NEED_IDR;
    mav_access_unit unit;
    mav_access_unit_default(&unit, codecFor(m_Params.videoFormat));
    unit.spans = spans.data(); unit.span_count = spans.size(); unit.frame_id = frameNumber;
    if (du->frameType == FRAME_TYPE_IDR) unit.flags |= MAV_INPUT_RANDOM_ACCESS;
    const auto pts = m_Timestamps.map(du->rtpTimestamp, du->presentationTimeUs);
    if (pts.valid) unit.pts = mav_time{pts.value, pts.timescale, 1};
    unit.color = streamColor(du, getDecoderColorRange());
    auto mapTime = [&](uint64_t us) -> uint64_t {
        if (!us || us > uint64_t(INT64_MAX / 1000)) return 0;
        const int64_t scaled = int64_t(us * 1000);
        if (m_ClockOffsetNs > 0 && scaled > INT64_MAX - m_ClockOffsetNs) return 0;
        const int64_t value = scaled + m_ClockOffsetNs;
        return value > 0 ? uint64_t(value) : 0;
    };
    unit.scheduled_arrival_ns = mapTime(du->enqueueTimeUs);
    unit.first_packet_ns = mapTime(du->receiveTimeUs);
    mav_result result;
    bool capacityObserved = false;
    for (;;) {
        if (m_Stopping || fatalError() != MAV_OK) return DR_OK;
        m_PeakCommonQueue = std::max(m_PeakCommonQueue, unsigned(std::max(0, LiGetPendingVideoFrames())));
        result = mav_decoder_submit_copy(m_Decoder, &unit);
        if (result != MAV_WOULD_BLOCK) break;
        if (capacityObserved) {
            // Only this worker submits or controls the decoder. After a capacity
            // wake, a retry cannot become full without our own acceptance. A
            // second WOULD_BLOCK therefore identifies pending reconfiguration.
            // Checking an outstanding snapshot after the first rejection would
            // race a normal completion and accidentally drain ordinary frames.
            result = mav_decoder_drain(m_Decoder);
            if (result != MAV_OK) break;
            capacityObserved = false;
        } else {
            result = mav_decoder_wait_for_capacity(m_Decoder, 50000000);
            capacityObserved = result == MAV_OK;
            if (result != MAV_OK && result != MAV_TIMEOUT) break;
        }
    }
    if (result != MAV_OK) {
        if (permanentFailure(result)) {
            reportFatal(result);
            return DR_OK; // Release the current DU; the entire session is ending.
        }
        m_NeedKey = true;
        m_ResetNeeded = result != MAV_NEED_RANDOM_ACCESS;
        SDL_LogWarn(SDL_LOG_CATEGORY_APPLICATION, "Native frame %u rejected: %s; requesting random access", frameNumber, mav_result_string(result));
        return DR_NEED_IDR;
    }
    if (du->frameType == FRAME_TYPE_IDR && !m_ResetNeeded) m_NeedKey = false;
    const uint64_t admittedUs = LiGetMicroseconds();
    m_LastAdmissionAgeUs = admittedUs >= du->enqueueTimeUs ? admittedUs - du->enqueueTimeUs : 0;
    m_PeakAdmissionAgeUs = std::max(m_PeakAdmissionAgeUs, m_LastAdmissionAgeUs);
    updateOverlay();
    return DR_OK;
}
void AppleVideoDecoder::updateOverlay() {
    uint64_t now = mav_monotonic_time_ns();
    if (now - m_LastOverlayNs < 1000000000) return;
    m_LastOverlayNs = now;
    auto& overlay = Session::get()->getOverlayManager();
    if (!overlay.isOverlayEnabled(Overlay::OverlayDebug)) return;
    mav_metrics metrics{}; metrics.struct_size = sizeof(metrics); metrics.version = MAV_ABI_VERSION;
    mav_decoder_get_metrics(m_Decoder, &metrics);
    char text[1024];
    char mean[64] = "unavailable", submissionMean[64] = "unavailable";
    const uint64_t decodeSamples = m_DecodeSamples.load();
    const uint64_t submissionSamples = m_SubmissionSamples.load();
    if (decodeSamples) SDL_snprintf(mean, sizeof(mean), "%.3f ms", double(m_DecodeNs.load()) / double(decodeSamples) / 1000000);
    if (submissionSamples) SDL_snprintf(submissionMean, sizeof(submissionMean), "%.3f ms", double(m_SubmissionNs.load()) / double(submissionSamples) / 1000000);
    SDL_snprintf(text, sizeof(text),
        "Native VideoToolbox %s %d-bit / Metal\nReceived: %llu  Decoded: %llu  Network loss: %llu\n"
        "In flight: %llu/%u  Backpressure: %llu  Recovery: %llu\n"
        "Common-c queue: %d (sampled peak %u/15)\nAdmission age: %llu us (peak %llu us)\n"
        "Display handoff drops: %llu  Decode errors: %llu\n"
        "VT submission mean (submit -> return): %s (%llu samples)\n"
        "Frame-ready mean (VT submit -> callback): %s (%llu samples)\nPresentation latency: unavailable",
        codecFor(m_Params.videoFormat) == MAV_CODEC_AV1 ? "AV1" : "HEVC",
        m_Params.videoFormat & VIDEO_FORMAT_MASK_10BIT ? 10 : 8,
        (unsigned long long)m_Received, (unsigned long long)metrics.displayed,
        (unsigned long long)m_NetworkDropped, (unsigned long long)metrics.outstanding, m_MaxInFlight,
        (unsigned long long)metrics.would_block, (unsigned long long)metrics.recoveries,
        LiGetPendingVideoFrames(), m_PeakCommonQueue, (unsigned long long)m_LastAdmissionAgeUs,
        (unsigned long long)m_PeakAdmissionAgeUs, (unsigned long long)m_HandoffDrops.load(),
        (unsigned long long)metrics.failed, submissionMean, (unsigned long long)submissionSamples,
        mean, (unsigned long long)decodeSamples);
    overlay.updateOverlayText(Overlay::OverlayDebug, text);
}

int AppleVideoDecoder::runOfflineSmoke() {
    if (!appleVideoTimestampSmoke()) { std::fprintf(stderr, "RTP timestamp wrap/fallback checks failed\n"); return 1; }
    if (SDL_InitSubSystem(SDL_INIT_VIDEO) != 0) { std::fprintf(stderr, "SDL video init failed: %s\n", SDL_GetError()); return 1; }
    SDL_Window* window = SDL_CreateWindow("Native decoder smoke", SDL_WINDOWPOS_UNDEFINED,
        SDL_WINDOWPOS_UNDEFINED, 1280, 720, SDL_WINDOW_HIDDEN | SDL_WINDOW_METAL);
    if (!window) { std::fprintf(stderr, "Native smoke window failed: %s\n", SDL_GetError()); return 1; }
    int failures = 0;
    const int formats[] = {VIDEO_FORMAT_AV1_MAIN8, VIDEO_FORMAT_AV1_MAIN10, VIDEO_FORMAT_H265, VIDEO_FORMAT_H265_MAIN10};
    for (int format : formats) {
        DECODER_PARAMETERS p{};
        p.window = window; p.videoFormat = format; p.width = 1280; p.height = 720; p.frameRate = 60;
        p.testOnly = true; p.vds = StreamingPreferences::VDS_FORCE_HARDWARE; p.renderer = StreamingPreferences::RS_METAL;
        AppleVideoDecoder decoder(true);
        bool passed = decoder.initialize(&p);
        std::fprintf(stdout, "{\"test\":\"qt-native-ownership-metal\",\"codec\":\"%s\",\"bit_depth\":%d,\"status\":\"%s\"}\n",
            codecFor(format) == MAV_CODEC_AV1 ? "av1" : "hevc", format & VIDEO_FORMAT_MASK_10BIT ? 10 : 8,
            passed ? "PASS" : "FAIL");
        if (!passed) ++failures;
    }
    SDL_DestroyWindow(window);
    return failures ? 1 : 0;
}
