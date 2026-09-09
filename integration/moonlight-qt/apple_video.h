#pragma once

#include "decoder.h"
#include "apple_video_timing.h"
#include "ffmpeg-renderers/pacer/pacer.h"
#include <moonlight_apple_video/decoder.h>
#include <array>
#include <atomic>
#include <mutex>

#define SDL_CODE_APPLE_VIDEO_FATAL 108

// Client-only adapter. No FFmpeg codec decoding is used by this implementation.
class AppleVideoDecoder final : public IVideoDecoder {
public:
    explicit AppleVideoDecoder(bool testOnly);
    ~AppleVideoDecoder() override;
    bool initialize(PDECODER_PARAMETERS params) override;
    bool isHardwareAccelerated() override { return m_HardwareValidated; }
    bool isAlwaysFullScreen() override { return false; }
    bool isHdrSupported() override;
    int getDecoderCapabilities() override;
    int getDecoderColorspace() override;
    int getDecoderColorRange() override;
    QSize getDecoderMaxResolution() override { return QSize(0, 0); }
    int submitDecodeUnit(PDECODE_UNIT du) override;
    void renderFrameOnMainThread() override;
    void setHdrMode(bool enabled) override;
    bool notifyWindowChanged(PWINDOW_STATE_CHANGE_INFO info) override;
    static int runOfflineSmoke();
    mav_result fatalError() const { return m_FatalResult.load(); }

private:
    struct Output { mav_completion completion{}; uint64_t epoch = 0; };
    static void completed(void* context, const mav_completion* completion);
    static int inputThread(void* context);
    static int handoffThread(void* context);
    void receive(const mav_completion& completion);
    void updateOverlay();
    bool probe(PDECODER_PARAMETERS params);
    void clearOutputQueue();
    void requestIdrOnHandoffThread();
    void reportFatal(mav_result result);
    void stopForFatalOnHandoffThread();

    bool m_TestOnly;
    bool m_HardwareValidated = false;
    bool m_OverlayRegistered = false;
    DECODER_PARAMETERS m_Params{};
    mav_decoder* m_Decoder = nullptr;
    IFFmpegRenderer* m_Renderer = nullptr;
    Pacer* m_Pacer = nullptr;
    VIDEO_STATS m_PacerStats{}; // owned by Pacer; read only after Pacer has joined
    SDL_Thread* m_InputThread = nullptr;
    SDL_Thread* m_HandoffThread = nullptr;
    std::atomic<bool> m_Stopping{false}, m_NeedKey{true}, m_ResetNeeded{false}, m_RequestIdr{false};
    std::atomic<mav_result> m_FatalResult{MAV_OK};
    std::atomic<uint64_t> m_Epoch{0}, m_HandoffDrops{0}, m_HandoffFrames{0}, m_HandoffNs{0};
    std::atomic<uint64_t> m_DecodeNs{0}, m_DecodeSamples{0}, m_HandoffSamples{0};
    std::atomic<uint64_t> m_SubmissionNs{0}, m_SubmissionSamples{0};
    std::mutex m_OutputMutex;
    SDL_sem* m_OutputReady = nullptr;
    std::array<Output, 3> m_Outputs{};
    size_t m_OutputHead = 0, m_OutputCount = 0;
    int64_t m_ClockOffsetNs = 0;
    uint64_t m_ClockUncertaintyNs = 0, m_LastOverlayNs = 0;
    uint64_t m_Received = 0, m_NetworkDropped = 0;
    uint32_t m_LastFrameNumber = 0;
    uint32_t m_MaxInFlight = 2;
    uint64_t m_LastIdrRequestNs = 0; // handoff worker only
    uint64_t m_LastAdmissionAgeUs = 0, m_PeakAdmissionAgeUs = 0;
    unsigned m_PeakCommonQueue = 0;
    AppleVideoTimestampUnwrapper m_Timestamps;
};
