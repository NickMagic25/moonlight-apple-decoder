# Decoder architecture and contract

`moonlight-apple-decoder` owns the **moonlight-apple-video** library. Moonlight Qt
is a compatibility reference and optional consumer. The reusable core never
includes Moonlight/common-c, FFmpeg, Qt, SDL, or presentation classes. Metal is
used for the native PyroWave decoder's compute stages; rendering belongs to the
consumer.

`include/moonlight_apple_video/decoder.h` is the installed, size/version-tagged C
ABI. `src/bitstream.cpp` bounds and normalizes access units, parses AV1 sequence
configuration and HEVC parameter-set relationships, and preserves codec payloads.
`src/format.mm` constructs public CoreMedia descriptions. `src/sample.mm` gives
CoreMedia shared ownership of prepared compressed bytes without another payload
copy. `src/backend_vt.mm` owns VT sessions and per-sample sourceFrameRefCon objects.
`src/decoder.cpp` owns admission, generations, public completions and metrics.
`src/clock.cpp` defines the measurement clock. Portable fake-backend tests compile
this same decoder control flow with a different private backend implementation.
`src/pyrowave.cpp` validates Vibepollo framing and partial-frame sideband, and
`src/backend_pyrowave.mm` owns the pinned compute decoder and retained output
texture pool. See [PyroWave](pyrowave.md) for its distinct three-plane contract.

The default is **hardware required**, two unresolved public access units, async
VT decode, real-time hint on, default power preference, no temporal processing,
and no 1x real-time playback flag. Native H.264 is intentionally absent. The Qt
consumer preserves FFmpeg H.264 and existing default backend behavior.

## Input and output

HEVC input is one complete Annex-B access unit with any number of spans. The
parser handles 3/4-byte start codes across spans, caches parameter sets by ID,
and converts only NAL framing to 4-byte lengths. AV1 input is a complete
single-layer low-overhead temporal unit with explicit OBU size fields. IVF,
container and AV1 Annex-B framing belongs to tools. At most one displayed image
is accepted per public unit; hidden frames may precede it and become child VT
samples. A show-existing event remains marked separately from a newly decoded
picture. Configuration-only submissions finish as successful no-display events.

On `MAV_OK`, compressed bytes are owned before submit returns and exactly one
terminal completion is owed. A rejection owes no callback and retains no input.
Each full compressed assembly/preparation copy is counted. Small parser-state
snapshots and configuration parsing allocations are not pixel or full-AU copies.
The current span implementation prioritizes safe ownership; metrics expose its
additional copies instead of claiming compressed zero-copy.

A completion's CVPixelBuffer is borrowed. Retain it to keep it beyond callback;
release it when the consumer finishes. Retained output survives reset/destruction.
The core requests IOSurface and Metal-compatible YUV output, preserving 8/10-bit,
4:2:0 and full/video range. Unsupported consumer formats are rejected explicitly.
For AV1/HEVC, 4:4:4, extra AV1 layers/profiles and reordered HEVC are outside the baseline and
return explicit unsupported results. Valid PTS/DTS with different ordering are
also rejected by this low-delay API path.
PyroWave supports both 4:2:0 and 4:4:4 through a borrowed `mav_gpu_frame` containing
three immutable single-channel Metal textures. Retain/release that frame through
the renderer's GPU completion; it survives decoder reset/destruction. Submission
and presentation never map those decoded planes on the CPU.

## Concurrency and recovery

Serialize submit, drain, reset and destroy on a control/decoder worker. An
operation already in progress returns WOULD_BLOCK to a concurrent operation.
Metrics and event-driven capacity wait may run concurrently. Callbacks can be
inline, run on different threads, and query metrics or retain output; submit,
wait and control operations inside callbacks return REENTRANT_CALL. No user
callback runs holding the state mutex. A short operation guard spans submission,
including an inline callback; supported callbacks never acquire that guard.

Admission and per-sample ownership are established before entering VideoToolbox.
A shared Work survives both submission return and callback, including inline
completion and synchronous failure. Child samples are aggregated into exactly
one public terminal status. Errors enter random-access recovery. The next actual
codec random-access point recreates the session when outstanding work is drained.
Identical configuration does not recreate it. Changes with outstanding work
return WOULD_BLOCK; a worker may drain then retry. No arbitrary compressed
reference frame is discarded as a latest-frame policy.

Drain waits only as a controlled lifecycle operation and finishes accepted work.
Reset increments generation before waiting, cancels old-generation delivery,
invalidates reference state and requires new configuration/random access.
Destruction closes admission and joins VT callbacks before freeing decoder state.
Caller joins its other API users before destruction. Output-buffer lifetime is
independent from submission capacity for VT output. PyroWave additionally bounds
live retained output leases and applies backpressure when that pool is occupied.
Malformed PyroWave frames do not poison following independent frames.

## Metadata and timing

Valid bitstream fields are authoritative. Valid VideoToolbox image attachments
fill unspecified bitstream fields; explicit per-unit metadata then configuration
fallback fills remaining fields. Unknown ISO color value 2 is filled per field.
Mastering and CLL data are normalized to CoreMedia/HEVC units. HDR requires real
10-bit codec signaling and transfer metadata; no 8-bit-to-HDR relabeling occurs.
PyroWave's floating point syntax has no bit-depth flag and Vibepollo leaves its
header's VUI bits unset. Negotiated bit depth plus explicit per-unit/transport and
configuration color metadata determine its output interpretation.

All latency trace timestamps use `CLOCK_UPTIME_RAW` nanoseconds on Apple.
PTS/DTS remain in their supplied media timebase and are never client wall time.
Common-c's Darwin clock subtracts a private start epoch; the Qt adapter must map
that clock with paired readings rather than multiply microseconds alone.

`vt_submit_to_callback_ns` starts immediately before VTDecompressionSessionDecodeFrame
and ends at callback entry. It includes driver queueing and callback scheduling.
An inline callback cannot know the later submission return time, so that field's
validity is clear. Multiple child sample intervals and existing-frame events
must remain distinguishable in reports. Rendering/presentation are unavailable
in headless replay; zero is never substituted. Capability queries are only
codec-level candidates; `hardware_validated` requires an actual hardware output
for the configured stream.

An additive, size-tagged `mav_decode_trace` tail provides codec-neutral backend
start, native decode-call submit/return, and (for PyroWave) Metal commit/start/end.
The existing ABI-2 completion prefix and `mav_trace` layout remain unchanged.
Consumers compiled against the extended header should use `mav_completion_copy`
instead of copying an incoming completion at the new full size: it reads only the
producer's supplied prefix and zeroes an absent tail. This metadata copy does not
retain borrowed output storage. `mav_completion_get_decode_trace` returns
`MAV_API_UNAVAILABLE` for an older completion without reading its absent tail.

Metal GPU host timestamps are converted to decoder nanoseconds with a fresh
bracketed `CACurrentMediaTime` reading at completion. Only finite, ordered GPU
times inside commit-to-callback and calibration uncertainty at most one millisecond
are published. The half bracket measures local sampling uncertainty, not physical
scanout accuracy. All validity bits remain clear when timing is unavailable. These
stages separate CPU preparation, backend packet assembly, upload/encoding, GPU
queueing/execution, and CPU completion notification for the same access unit.

## Provenance

New parser and lifecycle code were independently implemented from public AV1 and
HEVC syntax and Apple SDK declarations. Current FFmpeg VT source was inspected
for av1C/CoreMedia construction, with no FFmpeg runtime dependency in the core.
Initial local 720p probes used existing Moonlight Qt test access units (GPL-3.0
project); those payloads are not bundled here. Generated moving-pattern fixtures
have their own manifests, encoder revisions/settings and hashes. Tested synthetic
inputs establish codec/API behavior, not compatibility with every streaming host.
