# PyroWave Metal decode

`MAV_CODEC_PYROWAVE` uses the pinned native Metal implementation of
[Themaister/PyroWave](https://github.com/Themaister/pyrowave) at bitstream identity
`186f0393`, matching [Vibepollo's streaming protocol](https://github.com/Nonary/Vibepollo/blob/master/docs/pyrowave-protocol.md).
Its MIT source and license are in the
[PyroWave fork submodule](../Dependencies/pyrowave); see the development
integration state under [dependency maintenance](#dependency-maintenance). No Vulkan, Granite,
FFmpeg or CPU pixel decoder is linked into this path.

The GPU implementation requires an Apple7 or later Metal GPU (Apple Silicon M1 /
A14 or later). Query `mav_query_capability` before offering this codec. The library
compiles for its existing macOS/iOS/tvOS deployment targets; that does not prove
simulator, physical mobile device or live host acceptance.
The extended GPU-output and fragment layouts use C ABI version `2`; consumers
must rebuild against this header and use `MAV_ABI_VERSION` for tagged structures.

## Input and recovery

Set `mav_config.codec = MAV_CODEC_PYROWAVE`, exact negotiated dimensions,
`bit_depth = 8` or `10`, and `chroma_format = 1` (4:2:0) or `3` (4:4:4). The floating
point bitstream does not encode bit depth, so the negotiated setting chooses
R8 UNORM or R16 UNORM output. Samples are normalized code values, including
10-bit samples; R16 output does not use P010's left-shifted packing.
Vibepollo's pinned encoder does not populate the sequence header's color/range
bits. Supply negotiated range/matrix and current transport HDR metadata through
`mav_access_unit.color` / `mav_config.fallback_color`; zero header bits do not
override those values.

`MAV_FRAMING_PYROWAVE` detects both Vibepollo record framing and compatibility
length-prefixed packets. Submit one complete transport frame, after stripping
the short frame header. The parser bounds sequence geometry, block indexes,
record lengths, sequence values, duplicate headers/indexes, coefficient controls,
magnitude planes, sign bits and padding before any GPU command is encoded.
Configuration-only all-zero images remain valid. Every picture is independently
decodable; malformed input loses that frame and the next valid picture can be
submitted to the same decoder without requesting a host keyframe.

Optional `mav_pyrowave_fragment` entries tile the flattened input in packet order.
Each has its byte `offset`, `size` and `kind`: received ordinary payload `0`, lost
payload `1`, or received payload that starts with a record `2`. Lost payload bytes
are placeholders and are never parsed. `pyrowave_critical_packets` describes the
leading packet count carrying the coarse wavelet data. Record recovery skips every
record intersecting loss and resumes only at a known record boundary, or at the
protocol's validated ordinary-record boundary. Partial output requires intact
critical data and **more than** 90% of the announced block records. Any loss in
length-prefixed framing drops the frame.

## Dependency maintenance

PyroWave is a Git submodule of [NickMagic25/pyrowave](https://github.com/NickMagic25/pyrowave),
not copied decoder source. Production compiles only the fork's Metal decoder,
common device and packet parser into the existing static library. The upstream
encoder is compiled only by tests and benchmarks. Generated MSL stays in the
fork; Vulkan and Granite are not production dependencies.

Initialize a clone or local SwiftPM path dependency with:

```sh
git submodule update --init --recursive
```

The fork's integration revision is `488564aa2b5ffca0377938c27a1b67fce817c5b9`,
based on upstream `89f7e47d4abbf650c91fae766728af866c5e32a0` and preserving the
`186f0393` wire-format identity. The local submodule branch
`codex/apple-decoder-integration` commits these integration changes:
nonblocking upload capacity (`PYROWAVE_ERROR_BUSY`), zeroed upload padding,
output texture/device checks and sideband validation. The parent gitlink pins
that integration commit. It is saved locally and must be published in the fork
before publishing this decoder for remote builds. No commit or push is performed
by build scripts.

Make future Metal changes in the submodule. Commit/publish its reviewed revision
first, then update the decoder gitlink; a Swiftlight decoder revision change also
requires both client lockfiles. Do not change the protocol identity solely because
the fork revision changes.

## GPU ownership and scheduling

The decoder uploads compressed coefficients and their offset table into shared
Metal buffers. Compute dequantization and inverse wavelet stages write three
private, shader-readable textures directly: Y, Cb and Cr. The renderer samples
these same textures. It must use their Metal device and keep the output lease
alive through its command completion. There are no decoded CPU plane copies,
CPU pixel mappings or synchronous GPU waits during submission.

An output completion has `gpu_frame` and no `pixel_buffer`. Call
`mav_gpu_frame_retain` during the borrowed callback, use
`mav_gpu_frame_plane(frame, 0...2)` as borrowed `id<MTLTexture>` pointers, and release
with `mav_gpu_frame_release`. `mav_gpu_frame_chroma` returns `1` or `3`. A retained
lease survives decoder reset/destruction, and its textures are immutable until the
last reference is released.

Submission uses one ordered Metal command queue and completes asynchronously after
its GPU command finishes. The wavelet pyramid and compressed upload slots are
bounded; at most four decode commands are in flight. The output texture pool holds
at most `max_frames_in_flight + 4` leases, allocated lazily and reused after release.
Retaining all outputs causes `MAV_WOULD_BLOCK`; the event-driven capacity wait also
wakes when a retained output is released. Drain/reset/destruction wait on a control
worker for command completion, while retained output planes remain valid.

Compressed-copy metrics include input assembly, record normalization, coefficient
assembly and compressed GPU upload. They do not claim compressed zero-copy.
PyroWave callbacks preserve monotonic arrival/preparation/callback/handoff timing,
but never set the VideoToolbox-specific submit/return trace flags. GPU completion
is not drawable presentation, physical scanout or input-to-photon latency.

The optional `mav_decode_trace` completion tail separates backend entry,
`pyrowave_decoder_decode_gpu_buffer` CPU upload/encoding, Metal commit, and mapped
GPU start/end. Combine it with that completion's preparation and callback timestamps
to locate same-frame costs; do not subtract averages from unrelated windows.
GPU times are read asynchronously after completion and calibrated into the decoder
clock with reported sampling uncertainty. There are no additional GPU waits,
timestamp-counter buffers or per-frame trace allocations. The ABI-2 prefix remains
compatible; use the bounded completion-copy helper and stage getter when consuming
an optional tail.

## Reproducible checks

```sh
cmake -S . -B .build-pyrowave -DMAV_BUILD_TOOLS=OFF -DBUILD_TESTING=ON
cmake --build .build-pyrowave -j
ctest --test-dir .build-pyrowave --output-on-failure
mkdir -p .build-pyrowave/fixtures
.build-pyrowave/mav-pyrowave-metal-tests .build-pyrowave/fixtures
```

The portable framing suite exercises malformed controls, both framings, padding,
sideband maps, critical loss and the strict recovery threshold. The Metal test
builds the **test-only**, exact-pinned upstream encoder and feeds its records through
the production decoder. It verifies three-plane readback, 4:2:0 8-bit and odd-sized
4:4:4 R16 output, rejection followed by a valid frame, retained output across
reset/destruction, pool exhaustion/release, partial GPU output followed by critical loss/recovery,
and nonblocking upload admission.
GPU tests return skip code `77` when the process cannot access an Apple7 Metal GPU;
a skip is not a successful GPU check.

## High-rate decoding and Debug builds

The native library uses `-O2` in SwiftPM Debug and CMake Debug; it also optimizes
an empty CMake build type. Debug configurations retain symbols and assertions;
the consuming Swift application retains its Debug configuration. Coefficient validation is
required before GPU admission, and an unoptimized native build cannot sustain
high frame rates simply because the Metal compute stages are fast.

The optional benchmark target isolates that cost:

```sh
cmake -S . -B .build-pyrowave-debug -DCMAKE_BUILD_TYPE=Debug \
  -DMAV_BUILD_TOOLS=OFF -DBUILD_TESTING=ON
cmake --build .build-pyrowave-debug --target mav-pyrowave-benchmark -j
.build-pyrowave-debug/mav-pyrowave-benchmark 3440 1440 120 444
```

Set `-DMAV_OPTIMIZED_DEBUG=OFF` in a separate CMake build directory to reproduce
unoptimized native Debug behavior for comparison or single-step debugging.

It encodes a synthetic gradient once with the pinned, test-only Metal encoder,
warms ten frames, then measures 120 sequential decodes through the production
API. A separate direct-decoder pass records Metal command GPU start/end times.
The source gradient is 8-bit, decoded to negotiated R16 4:4:4 output; this measures
the same output geometry and compute stages, not PQ/HDR accuracy. It excludes
network transport, the Swiftlight renderer and drawable presentation. Its GPU
waits are benchmark-only. It is not a live 165 Hz cadence or latency acceptance
test, and its compressed payload does not saturate a gigabit link.

On September 30, 2026, this Mac's Apple M3 decoded the 293,160-byte 3440×1440
4:4:4 synthetic access unit as follows (milliseconds, median / 95th percentile):

| Native build | CPU preparation | CPU submit | Admission to GPU callback | Sequential decodes/s |
| --- | --- | --- | --- | --- |
| Original unoptimized Debug | 4.27 / 4.31 | 4.91 / 4.98 | 6.81 / 7.00 | 146 |
| Optimized Debug | 0.315 / 0.355 | 0.350 / 0.393 | 1.84 / 1.92 | 534 |
| Release | 0.228 / 0.253 | 0.261 / 0.284 | 1.81 / 1.88 | 541 |

Direct GPU compute was approximately 1.25–1.34 ms median. A 165 Hz frame period
is 6.06 ms, so the original Debug preparation and decode already exceeded the
period before rendering or network work. These measurements explain a native
Debug bottleneck; they do not establish live host, Ethernet, HDR or display
acceptance.

Intact access units now validate the fragment map once and skip per-record
boundary searches that are only needed for loss recovery. Any lost fragment
retains the original recovery path. Coefficient validation checks each control's
aggregate magnitude width before reading its bytes, skips the shader-defined
zero-control payload, and counts the eight independent coefficient masks with
one packed popcount. Truncated controls, magnitudes and signs still reject.

The benchmark also accepts `coefficients` and `blocks` as its fifth argument.
These construct deterministic legal coefficient records near the 1,000 Mbps /
165 Hz payload budget, with intact 1,024-byte packet maps. They isolate the
validation cost of dense records and many smaller records; they do not represent
captured media or verify HDR appearance. For example:

```sh
.build-pyrowave-debug/mav-pyrowave-benchmark 3440 1440 120 444 blocks
```

An isolated Apple M3 run on September 30, 2026 used the same 757,572-byte access
unit, 6,338 records and 793 packet fragments for each CPU variant. Preparation
times were (milliseconds, median / 95th percentile):

| Validation variant | CPU preparation |
| --- | --- |
| Original scalar validation and fragment searches | 0.965 / 0.992 |
| Intact-fragment fast path | 0.709 / 0.728 |
| Intact-fragment and coefficient fast paths | 0.627 / 0.689 |

On the complementary 757,368-byte dense-record fixture, the separate coefficient
change reduced preparation from 0.630 / 0.708 to 0.513 / 0.589 ms. Accepted access
unit bytes and all three decoded-plane hashes remained identical. The scalar
oracle test covers all 65,536 control-width combinations and 39,464 production
acceptance comparisons, including word-aligned truncations, quantizer limits,
zero controls and missing signs. These isolated CPU measurements exclude live
network, rendering and presentation effects.

On September 30, 2026, the native Metal round trips ran on this Mac with GPU
access: 128×128 4:2:0 R8 distinct two-dimensional gradients had maximum normalized
error `0.00392157` (one 8-bit code value) on all three planes; 127×97 4:4:4 R16
gradients had maximum error `0.00234989` on Y, `0.00367742` on Cb and
`0.00379950` on Cr. These are small synthetic lossy-codec correctness checks. They do not
establish compatibility with Vibepollo's Vulkan encoder, PQ/HDR display accuracy,
high-resolution throughput or live presentation latency. The same portable checks
passed with ASan/UBSan, and the Metal lifecycle/color checks passed with ASan/UBSan
and a separate TSan build. The sanitizer build annotates Metal's uninstrumented
command publication edge; it does not suppress reported races. Live Swiftlight/host
acceptance and controlled cadence measurements remain separate gates.
