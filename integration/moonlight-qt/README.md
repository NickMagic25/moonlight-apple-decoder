# Moonlight Qt consumer integration

The reusable decoder and all adapter source live in `moonlight-apple-decoder`.
The sibling Moonlight checkout supplies the existing client interfaces and the
Metal renderer. `consumer.patch` modifies seven consumer files at revision
`f743c23663bcd01059b620b823629e0afcb3dde8` (common-c
`874ac9548f1bd6f095ef2b435c42cdde460e7821`). It does not move the library into Qt.
The patch is applied to the local checkout for build/renderer validation.

`moonlight-apple-video.pri` is included by the consumer's real qmake build. It
compiles these adapter files from this directory and links the CMake-installed
static library. The static library has no Qt, SDL, FFmpeg or Metal dependency.
The adapter uses FFmpeg's AVFrame/buffer/metadata helpers and the existing Metal
renderer, with no FFmpeg codec decoding on the native route.

## Build and edit loop

Use a local Qt SDK with qmake, Qt Quick/Controls, SVG, and Shader Tools. Qt 6.11.2
is tested. Initialize the Moonlight submodules and its `libs/mac` dependencies
using that checkout's instructions. The helper does not reset the checkout or
install system packages. It refuses to apply conflicting hooks.

```sh
export MOONLIGHT_QT_DIR=/path/to/moonlight-qt
export QMAKE=/path/to/Qt/6.11.2/macos/bin/qmake
# Optional when cmake is not on PATH:
export CMAKE=/path/to/cmake
./scripts/build-moonlight-qt.sh

# Edit the library or this adapter, then run the same build command again.
./scripts/build-moonlight-qt.sh
MOONLIGHT_APPLE_VIDEO_SMOKE=1 \
  ./build-moonlight-qt/app/Moonlight.app/Contents/MacOS/Moonlight

# A separate Debug bundle with symbols and console logging on macOS
MOONLIGHT_QT_BUILD_TYPE=Debug ./scripts/build-moonlight-qt.sh
QT_PLUGINS="$("$QMAKE" -query QT_INSTALL_PLUGINS)"
QT_PLUGIN_PATH="$QT_PLUGINS" QT_QPA_PLATFORM_PLUGIN_PATH="$QT_PLUGINS/platforms" \
MOONLIGHT_APPLE_VIDEO_DECODER=native MOONLIGHT_APPLE_VIDEO_STRICT=1 \
  ./build-moonlight-qt-debug/app/Moonlight.app/Contents/MacOS/Moonlight
```

Overrides: `MOONLIGHT_APPLE_VIDEO_SOURCE_DIR`, `MOONLIGHT_APPLE_VIDEO_BUILD_DIR`,
`MOONLIGHT_APPLE_VIDEO_INSTALL_DIR`, `MOONLIGHT_QT_BUILD_DIR`, and `JOBS`.
Defaults place library build/install and app output in this repository's ignored
`build-qt-library`, `build-qt-install`, and `build-moonlight-qt` directories.
Set `MOONLIGHT_QT_BUILD_TYPE=Debug` to use the separate `*-debug` directories;
this builds both the decoder and Moonlight with debug symbols and makes macOS
Moonlight logging use the console. Debug builds default to SDK-direct mode
(`MOONLIGHT_QT_DEPLOY=0`), so they use the local Qt SDK rather than packaging
it; set `MOONLIGHT_QT_DEPLOY=1` only when testing the deployment path. The
default build type is `Release`, which deploys required plugin groups and ad-hoc signs the generated
bundle, including a bundle-local Qt plugin path configuration. It does not
publish, notarize, or install the app.

The native adapter is enabled for macOS arm64-only builds. Universal/x86 and
other platform builds retain their existing decoder code. The helper builds the
library for macOS 11 by default and leaves the application's qmake deployment
target untouched: Qt 6.11.2 sets macOS 13. Set `MACOSX_DEPLOYMENT_TARGET` only when
intentionally choosing a different library target compatible with your SDK.

## Runtime controls

```sh
# Existing default, including the existing H.264 route:
MOONLIGHT_APPLE_VIDEO_DECODER=ffmpeg \
  ./build-moonlight-qt/app/Moonlight.app/Contents/MacOS/Moonlight

# Native AV1 and HEVC; prominent startup diagnostic if fallback is necessary:
MOONLIGHT_APPLE_VIDEO_DECODER=native \
  ./build-moonlight-qt/app/Moonlight.app/Contents/MacOS/Moonlight

# Require native, including during codec/HDR capability selection:
MOONLIGHT_APPLE_VIDEO_DECODER=native MOONLIGHT_APPLE_VIDEO_STRICT=1 \
  MOONLIGHT_APPLE_VIDEO_INFLIGHT=2 \
  ./build-moonlight-qt/app/Moonlight.app/Contents/MacOS/Moonlight
```

Strict mode also forces a native attempt if the backend variable is omitted.
It forbids fallback, including native H.264, 4:4:4, unsupported hardware, and
explicitly incompatible software or renderer selections. Native H.264 is not
implemented. In-flight values 1, 2, and 3 are accepted; default is 2. The existing
codec/HDR controls remain in use. Native initializes only the Metal renderer;
AVSBDL/Vulkan choices remain available through the FFmpeg route.

Native sessions also emit a bounded `Native Metal trace`: the first retained
`CVPixelBuffer`, texture map, and command-buffer completion, followed by a final
count of unavailable drawables, texture-map failures, and Metal command failures.
This is native-adapter-only and does not log every frame at high refresh rates.

Each supported native codec/bit-depth candidate must decode the consumer's
existing 1280x720 compressed test AU in hardware and create actual Metal textures
before the native decoder reports hardware/HDR support. This establishes only
the probed configuration. Real stream dimensions/profile/output format are
validated by the shared decoder and the adapter; unsupported configurations
fail explicitly. No backend switch occurs inside an active native stream.
The AV1 probe accessor trims only validated trailing zero padding at complete
OBU boundaries; live common-c already removes transport padding. Live AV1 bytes
are passed unchanged as low-overhead OBUs; HEVC remains Annex-B spans.

## Threads, ownership, recovery and measurements

The input worker uses common-c's existing pull interface. It owns at most one
current DECODE_UNIT while waiting on the library's event-driven capacity signal.
Common-c's existing queue is bounded to 15 units; its own overflow recovery is
preserved. The adapter measures admission age from complete-AU enqueue until
submit returns; this includes preparation and submission as well as queueing and
capacity waits. It is not a pure queue-wait interval. Sampled common-c queue
depth/peak is reported, but queued compressed bytes and the oldest still-queued
unit's age are unavailable. A genuine format change may drain
old pending samples on this input/control worker. There are no per-frame VT waits
or polling sleeps in the decoder path.

VT completion retains a buffer into a three-slot queue using a try-lock and posts
a semaphore. No drawable, renderer, networking, AVFrame allocation, or blocking
queue lock is reached from that callback. A full handoff queue replaces its oldest decoded image; a contended try-lock
drops the incoming decoded image. Both are counted as already-decoded display drops; they do not discard compressed references.
The handoff worker suppresses obsolete callbacks arriving after a newer frame,
using generation/epoch and wrap-safe common-c frame numbering; those decoded
display drops remain counted. It builds an AVFrame backed by a retained CVPixelBuffer in data[3]
and a release callback in buf[0], then uses the existing Pacer/Metal lifecycle.
Existing Pacer queues, its deferred reference, and Metal's latest-display-link
frame remain separately bounded. The retained image survives reset and decoder
or wrapper destruction independently. No plane mapping or pixel copy occurs.

Unknown VT drops/failures mark recovery and request a keyframe from the handoff
worker, limited to one explicit request per 100 ms. The input worker resets old
decoder state and rejects dependent pictures until a new random-access input,
which the shared parser validates. Queued stale adapter output is discarded.
Common-c handles synchronous DR_NEED_IDR recovery. Reference-frame invalidation
is conservatively not advertised before live validation. Permanent unsupported,
unavailable-API, invalid-configuration and allocation errors latch a terminal
result instead of repeatedly requesting keyframes. A handoff-worker SDL event
wakes the session loop, which displays the error and follows its normal cleanup
on the client thread. The loop also checks the latch after event timeouts. An
incompatible decoded resolution uses the same terminal path. Shutdown closes input,
joins its worker, resolves library callbacks, joins handoff, then tears down the
existing pacer/renderer and every retained output.

The common-c Darwin clock is CLOCK_UPTIME_RAW relative to a private startup epoch.
Eight bracketed samples select a calibrated offset to `mav_monotonic_time_ns`,
with the bracket/1-us quantization uncertainty logged. First-packet/complete-AU
arrival use that mapping. The adapter unwraps the raw 32-bit RTP counter using signed deltas in the
90-kHz media timebase. Contrary to an earlier assumption, this common-c revision
derives presentationTimeUs directly from raw RTP without unwrapping. Its receive-
time fallback is used only while the host supplies no nonzero RTP timestamps.
Repeated/backward source timestamps remain visible; rollover never substitutes
a receive-time value. A portable check covers rollover, repeated/backward PTS and
fallback bounds, and runs again inside the app smoke. The wrapper converts media
time rationally to the renderer's 90-kHz timebase. It is never treated as client wall-clock time.

Normalized bitstream/VT color metadata takes precedence over valid host fallback
passed with the AU. The wrapper preserves ISO primaries, transfer, matrix, range,
chroma location, mastering display and content light metadata. HEVC location 0
means left and 1 means center. Host mastering values are reordered RGB to GBR and
encoded in the public API's documented units. A native-only renderer factory flag
makes Metal consume the wrapper's mastering/content-light side data for its
CAEDRMetadata cache. Per-frame normalized metadata therefore retains precedence
through EDR setup, including updates and removal; asynchronous host HDR callbacks
cannot overwrite that native cache. The existing FFmpeg factory default retains
its original host-metadata behavior. The original small right/bottom crop policy
remains in place.

The native overlay reports input/decode/backpressure/recovery/display-handoff
counts and two timing means, each with its sample count:

- **VT submission mean (submit -> return):** elapsed time inside the
  VideoToolbox decode submission call. Returning from this call does not
  guarantee the output image is ready.
- **Frame-ready mean (VT submit -> callback):** elapsed time from submitting the
  frame to VideoToolbox until its decoded-image callback. This retains the
  previous VT submit-to-callback metric; it does not include rendering or actual
  presentation.

Both are cumulative arithmetic means over the adapter's lifetime, including
startup, warmup and recovery. They count successful, newly decoded single-sample
outputs before display handoff; no-display and show-existing events are excluded.
A callback can occur before the submission call returns, so some completions do
not carry a valid return timestamp. Such outputs still contribute to frame-ready
timing when its timestamps are valid, but are omitted from submission timing;
missing return timestamps are never inferred or counted as zero. Independent
sample counts expose this difference in coverage. A lower submission mean does
not establish faster decoding or earlier presentation.
Both intervals start at VT submission and can overlap; their means must not be
added together or subtracted to infer hardware execution time.

The final log retains `VT-submit-to-callback-mean-us` and adds
`VT-submit-to-return-mean-us`, `VT-submit-to-return-samples` and
`VT-submit-to-callback-samples`. The standalone benchmark is the source for
distributions. Pacer statistics are read only after
its threads join; final logs report its queue and render-call totals and measured
callback-to-pacer handoff mean. Missing intervals are reported as unavailable. The existing
Metal render-call can include drawable acquisition and GPU waiting; with
CAMetalDisplayLink, GPU work occurs later outside that interval. Separate
drawable-wait, GPU-wait, GPU-submission and actual presentation timings are
unavailable. Pacer's rendered count records renderer calls, not presentations.
Inherited Pacer enqueue-overflow and Metal latest-frame replacements do not
increment its drop counter, so these logs are not complete application display
drop instrumentation. No headless smoke result is
presented as a display-rate or live-stream performance result.

## Validation and provenance

Run `./scripts/validate-moonlight-qt.sh` to save JSONL under
`results/qt-native-smoke`. The app's `MOONLIGHT_APPLE_VIDEO_SMOKE=1` entry point needs no server and tests all
four required codec/bit-depth candidates. It validates hardware readback,
1280x720 output, IOSurface backing, zero-copy AVFrame ownership/cloning after
decoder destruction, existing Metal texture creation, and a synthetic mastering/
content-light side-data round trip with CAEDRMetadata construction and subsequent
metadata removal. This does not visually validate HDR output. Every missing candidate
makes this command fail. JSONL goes to stdout; Moonlight reports its detailed log
path on stderr. Run outside a sandbox that denies VideoToolbox hardware service
access; a sandbox error is not a codec capability result.

The actual app built and all four smoke variants passed on Apple M3, macOS
26.6.2, Xcode SDK 26.5, Qt 6.11.2. These short existing probe samples establish
adapter/renderer ownership and codec-bit-depth wiring; required long-sequence and
HDR signal validation belongs to the separate production-API fixture tests.
The smoke uses the probe path, not the production pull/handoff/pacer threads or
the session's strict/fallback and terminal-error UI branches. Live host
negotiation, recovery under real packet loss, presentation pacing,
and live native-versus-FFmpeg performance are **untested**. No Sunshine/Apollo/
VibeApollo/VibeShine compatibility is claimed from these synthetic probes.

The consumer's compressed test arrays, renderer APIs and compatibility behavior
are from Moonlight Qt at the revision above, under its GPLv3 license. The adapter
calls those existing components and does not copy a VideoToolbox or FFmpeg decoder
implementation. This repository's GPLv3 license applies to its new adapter code.
