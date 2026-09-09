# Workspace investigation — 2026-09-08

Library starts from `cf9d3afc7f752f164a9216e92055bcefad92c7cb` (LICENSE only).
Sibling Moonlight Qt starts from `f743c23663bcd01059b620b823629e0afcb3dde8`,
with common-c `874ac9548f1bd6f095ef2b435c42cdde460e7821`. Both worktrees were clean.
No applicable AGENTS.md was found. MOONLIGHT_QT_DIR was unset.

Host: physical Apple M3 arm64, macOS 26.6.2 (25G83); Xcode provides macOS,
iOS/device+simulator and tvOS/device+simulator SDK 26.5. CMake, Ninja, clang,
and Swift are available; no ffmpeg/aomenc executable is initially on PATH.
Qt ships local FFmpeg libraries. Hardware capabilities remain unverified until
real decode, regardless of the CPU model. Build/dependency details are recorded
by scripts and final validation evidence.

## Actual consumer paths

* `moonlight-qt.pro` and `app/app.pro`: qmake subprojects and platform links.
  Integration must preserve the checkout's deployment target and non-Apple path.
* `app/streaming/session.cpp:278`: `Session::chooseDecoder`; :360 decoder submit;
  :393 capability probes; :734 codec/HDR advertisement.
* `moonlight-common-c/moonlight-common-c/src/VideoDepacketizer.c:974` parses NAL
  data only for H.264/HEVC. :1028 trims transport padding for AV1, which remains
  low-overhead OBUs, not HEVC Annex-B. `src/Limelight.h:145` defines complete
  DECODE_UNIT, receive/enqueue times and presentationTimeUs.
* `app/streaming/video/ffmpeg.cpp:1761`: SPS compatibility rewriting is H.264
  only. :1851 runs the decoder worker, :2096 accepts units, :2186 sends packets.
  :1923 accommodates AV1 encoder excess dimensions by cropping within 64 pixels.
* `app/streaming/video/ffmpeg-renderers/vt_metal.mm`: existing Metal presentation
  consumes CVPixelBuffer through AVFrame data[3]; clones/frees frames and owns
  drawable/GPU lifetime. It must remain outside VT callbacks.
* `app/streaming/video/ffmpeg.cpp`, `decoder.h`, `pacer/pacer.cpp`: decode statistics,
  output ownership and pacing. Current Pacer::submitFrame (:405) always queues;
  Metal supports its dedicated render thread. An older comment in ffmpeg.cpp
  claiming synchronous rendering with pacing off does not describe current code.
  A minimal bounded adapter handoff also keeps wrapper allocation and contention
  on Pacer's mutex outside the VT callback.
* `app/streaming/video/ffmpeg-renderers/vt_metal.mm` and renderer interfaces:
  color attachments, HDR mode and presentation. Wrapper color fields and stream
  metadata must accompany retained buffers without plane copies.
* Decoder return values and `LiCompleteVideoFrame` drive common-c recovery;
  asynchronous native failure must also request a codec random-access frame.
  Teardown must join adapter workers before deleting renderer and decoder.

The Darwin common-c clock (`src/Platform.c:458-479`) is CLOCK_UPTIME_RAW minus
a private startup epoch. The adapter brackets LiGetMicroseconds with library
clock reads to map epochs and records the calibration uncertainty; multiplying
the common-c values by 1000 alone is incorrect. Host PTS is a separate media clock. Further audit of RtpVideoQueue.c:158 shows
this revision derives presentationTimeUs from raw uint32 RTP without unwrapping;
VideoDepacketizer.c:839 only adds a receive-time fallback for zero timestamps.
The adapter must unwrap RTP itself and must distinguish a real rollover to zero
from the no-timestamp fallback.

Metal `vt_metal.mm:453` tests texture creation, :572 waits for GPU completion,
:599 moves AVFrame references for CAMetalDisplayLink, and :619 obtains a drawable.
These blocking operations remain in the existing rendering lifecycle. Pacer
`:332` measures queue/render intervals, and its destructor joins rendering work
and releases retained frames. Native callback latency excludes those operations.
Existing `ffmpeg.cpp:1890-2020` gives bitstream metadata precedence over host HDR
fallback and applies encoder padding crops within 64 pixels. `vt_base.mm:118`
updates host mastering/content-light data. Native wrapper fields must preserve
range, primaries, transfer, matrix, chroma location and retained data[3] ownership.

The Qt CI requests 6.11.2. Prebuilt macOS codec/SDL libraries are present under
libs/mac, but qmake was initially absent. An isolated Qt 6.11.2 SDK was fetched
locally without system installation. Its qconfig.pri sets the application's
macOS deployment target to 13; the helper preserves that value and links the
shared library built for macOS 11. All adapter sources remain canonical under
this library repository's integration/moonlight-qt directory. A seven-file
consumer patch supplies minimal qmake, selection, session-error, native-only HDR
metadata and server-free smoke hooks. The existing Metal EDR path originally
read host-only mastering/CLL cache fields, not AVFrame side data. The optional
native factory flag now populates that cache from normalized frame side data on
the render thread; default FFmpeg renderer behavior is preserved. Admission age
is enqueue-to-submit-return (including preparation/submission), not pure queue
wait. Existing render-call counts/times are not presentation measurements;
Pacer enqueue overflow and Metal latest-frame replacements also lack complete
display-drop accounting. See integration/moonlight-qt/README.md for limits.

## AV1 construction and API evidence

Current FFmpeg `libavcodec/videotoolbox_av1.c` constructs a four-byte av1C record
followed by the original Sequence Header OBU, then passes original frame OBUs.
`videotoolbox.c` puts av1C in SampleDescriptionExtensionAtoms and calls generic
CMVideoFormatDescriptionCreate. There is no invented AV1 parameter-set API.
The implementation will independently parse the normative AV1 syntax, with
no production FFmpeg dependency or copied FFmpeg source.

Sources: [AV1 specification](https://aomediacodec.github.io/av1-spec/),
[AV1 media binding](https://aomediacodec.github.io/av1-isobmff/),
[FFmpeg VT AV1](https://github.com/FFmpeg/FFmpeg/blob/master/libavcodec/videotoolbox_av1.c),
[Apple AV1 identifier](https://developer.apple.com/documentation/coremedia/kcmvideocodectype_av1).
Actual SDK VTDecompressionSession.h documents callback on successful DecodeFrame,
no callback on synchronous error, and inline callback possibility. Timing starts
before that call. Temporal processing and 1x real-time playback remain off.

SDK hardware-require/readback keys are available on macOS 10.9 and iOS/tvOS 17.
The library chooses macOS 11 / iOS 17 / tvOS 17 baseline, guarded AV1 availability;
HEVC is independent of AV1 device support. MaximizePowerEfficiency and RealTime
must not both be explicitly enabled per SDK documentation. Optional properties
will report status/readback without making unsupported hints fatal.

## Validation boundaries

No hardware decoding, live hosts, builds, performance improvement or compatibility
is established by this investigation. Next work is implementation, early AV1
and HEVC offline decoding, then consumer integration and repeatable measurement.
