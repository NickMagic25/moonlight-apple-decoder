# Implementation and validation report

`moonlight-apple-video` is implemented in this repository as a reusable native AV1/HEVC decoder. The same production C API is exercised by generated server-free fixtures and linked into the actual local Moonlight Qt application. Both required codecs and their real 8-bit and 10-bit/HDR variants have decoded on Apple M3 hardware. Live host interoperability and presentation performance remain untested.

The repository began at `cf9d3afc7f752f164a9216e92055bcefad92c7cb` with only its license. The consumer integration was applied to Moonlight Qt `f743c23663bcd01059b620b823629e0afcb3dde8`, using common-c `874ac9548f1bd6f095ef2b435c42cdde460e7821`. Changes are local workspace changes; this work did not publish a release or install system-wide dependencies. Source/binary hashes and dirty-worktree provenance are captured by `scripts/environment.py` alongside validation and benchmark results.

## Status by codec and variant

| Variant | Implementation | Moonlight Qt integration | Hardware correctness | Timed benchmark |
| --- | --- | --- | --- | --- |
| AV1 Main 8-bit 4:2:0 SDR | Implemented: OBU/configuration parser, av1C/sample construction, asynchronous direct VT, recovery/accounting | PASS: final actual arm64 build, hardware ownership and Metal smoke | PASS: 1080p 240/240 outputs; independent full-plane comparison exact; hidden/existing-frame accounting | PASS at 1080p120; default-two VT median 1.543 ms |
| AV1 Main 10-bit 4:2:0 HDR | Implemented: real 10-bit configuration and output, PQ/BT.2020, normalized HDR metadata | PASS: final 10-bit adapter/renderer smoke and EDR metadata construction; HDR stream metadata independently validated | PASS: 1080p 240/240 outputs with HDR; independent full-plane comparison exact; hidden/existing-frame accounting | PASS at 1080p120; 3440×1440p240 fails default startup bound, passes bounded queue-32 experiment |
| HEVC Main 8-bit 4:2:0 SDR | Implemented: VPS/SPS/PPS relationships, Annex-B conversion, asynchronous direct VT, recovery | PASS: final actual arm64 build, hardware ownership and Metal smoke | PASS: 1080p 240/240 outputs; independent full-plane comparison exact | PASS at 1080p120; default-two VT median 1.542 ms |
| HEVC Main10 10-bit 4:2:0 HDR | Implemented: real Main10 decode and output, PQ/BT.2020 and normalized HDR metadata | PASS: final 10-bit adapter/renderer smoke and EDR metadata construction; HDR stream metadata independently validated | PASS: 1080p 240/240 outputs with HDR; independent full-plane comparison exact | PASS at 1080p120 and 3440×1440p240, including two-minute run |
| Native H.264 | Intentionally omitted optional feature | Existing FFmpeg route preserved; strict native selection rejects it | NOT APPLICABLE to this library | NOT MEASURED |

The app smoke explicitly instantiates the native adapter with the consumer's existing 1280x720 codec probes. Its PASS establishes hardware output, ownership and Metal texture compatibility. Added metadata checks verify mastering/content-light round trips and Apple EDR metadata construction/removal. It does not exercise live Session decoder selection, worker/pacer threads or a long live HDR session. Long reference-dependent sequences, explicit HDR signaling, pixel correctness and loss/reset handling are independently tested through the same production decoder API.

## Architecture and changed file groups

| Files | Responsibility |
| --- | --- |
| `include/moonlight_apple_video/decoder.h`, `include/module.modulemap` | Installed versioned/size-tagged C ABI, opaque decoder, capability/metrics queries, borrowed frame ownership and control-thread contract; Clang module for Swift |
| `src/bitstream.cpp`, `src/bitstream.hpp` | Bounded codec-specific AV1 OBU/sequence/frame-prefix/metadata parsing and HEVC parameter-set/NAL parsing; transactional configuration changes and codec-correct random access |
| `src/format.mm`, `src/sample.mm`, `src/color.hpp` | Public CoreMedia descriptions, AV1 av1C, HEVC parameter-set API, owned sample data, bit-depth-preserving color/HDR normalization |
| `src/backend_vt.mm`, `src/backend.hpp` | Direct asynchronous VTDecompressionSession ownership, hardware-required configuration/readback, sample association, optional-property status/readback |
| `src/decoder.cpp`, `src/clock.cpp`, `src/backend_unavailable.cpp` | Bounded admission, generation isolation, exact terminal completion accounting, drain/reset/destroy, copy/latency metrics, explicit non-Apple backend result |
| `CMakeLists.txt`, `cmake/`, `Package.swift`, `examples/swift/main.swift` | Independent static-library build, installed `MoonlightAppleVideo::Decoder` target, same-source Swift package and Swift import/ownership smoke |
| `tools/fixture.mm`, `tools/fixture_support.hpp`, `tools/replay.mm` | Native fixture generation/import, versioned hashed manifests, absolute-deadline replay, correctness/benchmark/fault sinks, independent image validation |
| `tools/ffmpeg_baseline.mm`, `tools/reference_decode.mm` | Optional, separate FFmpeg VideoToolbox comparison and software reference decoder; never linked into the production decoder |
| `tests/` | Portable parser, C ABI, lifecycle/fake-backend and adapter-clock tests; Apple hardware/AV1 accounting tests; malformed-manifest checks |
| `integration/moonlight-qt/` | Canonical thin adapter, retained AVFrame wrapper, clock/RTP mapping, qmake include and narrowly scoped consumer patch |
| `scripts/` | Local AOM bootstrap, strict correctness/hardware entry points, staged benchmark presets/provenance, Apple SDK/Swift checks, Qt build and server-free smoke helpers |
| `docs/` | Investigation, lifecycle/codec decisions, fixture and benchmark recipes, measured correctness evidence, consumer integration evidence and this report |

The core links only Apple decoding/buffer frameworks and the standard C/C++ runtime. It does not include Qt, SDL, Moonlight/common-c, FFmpeg, Metal presentation objects, or a software video decoder. FFmpeg remains a consumer/tooling dependency where explicitly allowed. The future Apple-native client and a replacement renderer were not built.

The default admits two unresolved public access units, requires hardware, enables asynchronous VT decompression and the real-time hint, and leaves temporal processing and `1xRealTimePlayback` off. In-flight limits 1/2/3 and optional power/thread hints are configurable. Only suitable 8/10-bit bi-planar YUV output is requested; the implementation never silently narrows HDR to 8-bit or maps decoded planes in production.

Accepted copy submissions own their compressed bytes before returning and owe exactly one terminal completion. Rejections, including `WOULD_BLOCK`, consume nothing and owe no callback. Per-submission state exists before the VT call and survives inline callbacks and synchronous failures. Hidden AV1 child samples and existing-frame events remain separately accounted while resolving one public completion. Buffers are borrowed during callbacks; retained CVPixelBuffers remain valid after reset/destruction. User callbacks execute without the internal state lock. Reentrant control calls are rejected; the documented control worker handles drain/reset/destruction.

The consumer patch modifies seven Qt files, including two small Metal interface/metadata hooks; canonical integration sources stay in this repository. The native Qt callback performs only a bounded decoded-buffer handoff. AVFrame allocation, common-c recovery requests, pacing and the existing Metal renderer run outside that callback. Native AV1/HEVC bypass FFmpeg codec decoding. The original FFmpeg default and H.264 route remain available. Host-independent bitstream handling, existing HDR controls and small encoder-padding crop behavior are preserved. The common-c clock is calibrated into Apple `CLOCK_UPTIME_RAW`; raw 32-bit RTP timing is independently unwrapped in its 90-kHz media domain.

## Recorded correctness and build results

Tests ran on a physical Apple M3 MacBook Pro (`Mac15,3`), macOS 26.6.2 (25G83), Xcode SDK 26.5, Apple clang 21 and Qt 6.11.2. AOM 3.13.3 was built inside `.local/` from pinned commit `92d4c37fbdd08944a0e721bbaeb13318f10aebb0`; no software encoder is part of production.

- **PASS: macOS and Linux portable CTest, 4/4 each.** The suites cover bitstream parsing, C ABI, adapter timing and the real decoder state machine with a fake backend. Mock timings are not performance evidence.
- **PASS: strict physical-hardware suite, all four variants.** Each fixture contains 120 generated 1920x1080 access units with gradients, detail, motion, visible frame IDs, inter-frame references and periodic genuine random access. Two replay loops completed 240/240 accepted submissions with actual hardware, correct dimensions/depth/HDR, IOSurface backing, Y/UV Metal texture creation, generation reset and retained-buffer ownership checks. Final Release rerun restored `results/validation/summary.json` to PASS.
- **PASS: same-compressed-stream software comparison, all four variants.** Every visible Y/U/V sample was compared without row padding and with correct P010 unpacking. Each variant compared 373,248,000 samples; observed maximum and mean error were both zero. AV1 used AOM; HEVC used FFmpeg's software decoder. Documented permissible tolerances remain 2 code values for 8-bit and 8 for 10-bit.
- **PASS: out-of-band HDR metadata fallback for both codecs.** The regression recipe removed 240 static mastering/content-light metadata records from each saved HDR stream while preserving actual 10-bit sequence/SPS and picture bytes. The native importer verified the bitstream, and each replay produced 120 hardware images with HDR metadata supplied through the manifest-to-public-configuration fallback. Results are in `results/metadata-fallback/summary.json`.
- **PASS: real AV1 hidden/existing/multi-sample accounting at both depths.** Each run had 48 temporal units, 12 multi-frame units, 71 internal samples, 23 hidden pictures and 20 existing-frame events. Whole-unit replay completed 48/48 with 48 images; split replay completed 71/71 with 48 images and 23 no-display completions. Outstanding work ended at zero. Whole/split images and 2,654,208 software-reference samples per depth matched exactly.
- **PASS: fault recovery and bounded slow-consumer tests.** The seeded AV1 test offered 120 units, accepted/completed/displayed 39, discarded 80 deliberate/dependency-unsafe arrivals, rejected one synchronously and performed six resets without stalled capacity. A 2-ms-per-output HEVC HDR consumer completed 240/240 and retained at most 18 frames in the bounded worker.
- **PASS: valid manifest import plus 21 malformed-manifest cases.** Types, bounds, hashes, duplicate IDs, profiles, paths and odd 4:2:0 dimensions are rejected gracefully.
- **PASS: AddressSanitizer and UndefinedBehaviorSanitizer.** Final CTest passed 4/4; sanitized hardware replay passed all four variants at 240/240, and sanitized AV1 10-bit grouped/split accounting passed. LeakSanitizer is unsupported by this macOS runtime and is not claimed; `detect_leaks=1` was rejected before testing and the supported ASan/UBSan run was repeated separately.
- **PASS: installed CMake package.** A separate C consumer found the installed `MoonlightAppleVideo::Decoder` export, linked, and ran its default-configuration check.
- **PASS: Apple SDK compilation and Swift import.** iOS/iPadOS arm64, iOS arm64 simulator, tvOS arm64 and tvOS arm64 simulator static libraries built. The Release Swift C-ABI ownership smoke ran successfully using a clean native-build scratch directory. These are compile/import results; physical iOS/iPadOS/tvOS decoding remains untested.
- **PASS: final modified Moonlight Qt app and four-variant hardware smoke.** The Release arm64 application preserves Qt's macOS 13 deployment target while the library targets macOS 11. Permanent native format/API failures now latch a terminal error for the Session/client event loop, while transient failures retain keyframe recovery. A narrow Metal hook consumes normalized per-frame mastering/content-light metadata for native EDR, preserving existing FFmpeg behavior. The rebuilt app passed all four codec/depth probes and HDR metadata round-trip, EDR-object construction/removal checks. Evidence, hashes, revisions and limits are in `docs/evidence/qt-build-validation.json` and `docs/evidence/qt-native-smoke.jsonl`.

The library's current deployment baselines are macOS 11, iOS/iPadOS 17 and tvOS 17. AV1 APIs/hardware are checked separately from HEVC, and successful codec-level queries are never presented as proof of the exact stream configuration. Inside this execution environment's restricted command sandbox, VT service access returned `-12911`; identical hardware tests passed with normal device-service access. This is an execution-permission limitation, not evidence that M3 lacks either codec.

## Reproduction commands

From this repository, with working CMake/Python/Xcode tools on PATH (or `CMAKE=/path/to/cmake`, `PYTHON=/path/to/python3`):

```sh
./scripts/bootstrap-aom.sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 -DBUILD_TESTING=ON -DMAV_BUILD_TOOLS=ON
cmake --build build --parallel 4
./scripts/validate.sh --suite correctness
./scripts/validate.sh --suite offline-hardware --require-hardware --require-codecs av1,hevc --require-variants sdr8,hdr10
./scripts/test-av1-accounting.py --skip-build
MOONLIGHT_QT_DIR=/path/to/moonlight-qt python3 scripts/test-reconfiguration.py --skip-build
python3 scripts/test-metadata-fallback.py
python3 tests/manifest_validation.py --fixture fixtures/generated/av1-sdr8-1920x1080p120-120/manifest.json --tool build/mav-fixture
./scripts/check-platforms.sh
cmake --install build --prefix "$PWD/install"
```

The reconfiguration recipe extracts the four real 720p probe arrays from the specified local Qt checkout into ignored `build/probes/`, trims only AV1 padding outside declared OBU payloads, and combines them with validation's canonical `1920x1080p120-120` fixtures. It records input/source hashes and checks both codecs through six implicit format changes each, repeated configurations, HDR-to-SDR metadata clearing, and retained-buffer stability. No probe binaries are bundled.

The Linux portable path is the same CMake build and CTest command; it does not run or substitute for physical Apple hardware tests:

```sh
cmake -S . -B build-linux -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build-linux --parallel 4
ctest --test-dir build-linux --output-on-failure
```

For optional FFmpeg tools, point CMake to an actual local development tree; the reference recipe and exact packing are in `docs/fixtures.md`:

```sh
cmake -S . -B build -DMAV_FFMPEG_ROOT="$MOONLIGHT_QT_DIR/libs/mac"
cmake --build build --parallel 4
DYLD_LIBRARY_PATH="$MOONLIGHT_QT_DIR/libs/mac/lib" build/mav-reference-decode --fixture fixtures/generated/hevc-hdr10-1920x1080p120-120/manifest.json --output /tmp/reference.yuv
build/mav-replay --fixture fixtures/generated/hevc-hdr10-1920x1080p120-120/manifest.json --mode correctness --reference-raw /tmp/reference.yuv --output results/reference-hevc-hdr10
```

The concrete Qt edit/rebuild/launch loop uses its actual qmake build:

```sh
export MOONLIGHT_QT_DIR=/path/to/moonlight-qt
export QMAKE=/path/to/Qt/6.11.2/macos/bin/qmake
./scripts/build-moonlight-qt.sh
./scripts/validate-moonlight-qt.sh
MOONLIGHT_APPLE_VIDEO_DECODER=native MOONLIGHT_APPLE_VIDEO_STRICT=1 ./build-moonlight-qt/app/Moonlight.app/Contents/MacOS/Moonlight
# For the existing backend:
MOONLIGHT_APPLE_VIDEO_DECODER=ffmpeg ./build-moonlight-qt/app/Moonlight.app/Contents/MacOS/Moonlight
```

Generated fixtures and full per-frame CSV/JSON remain under ignored `fixtures/generated/` and `results/`. Manifests include payload/AU SHA-256, encoder settings and provenance. `docs/offline-correctness-results.md` records the correctness evidence; `docs/bitstream-and-accounting.md` gives the additional AV1 accounting recipe. No external video or running Sunshine server is needed.

## Measured performance

The final matrix contains **59 physical-hardware timed runs** using Release builds, saved identical AUs, continuous sessions, matched absolute-deadline schedulers and explicit cold/warmup exclusions. The [performance report](performance-results.md) contains all per-codec tables, exact commands, the queue-policy comparison and limits. Portable snapshots preserve full per-run distributions and provenance in [main benchmark evidence](evidence/benchmarks.json), [two-minute evidence](evidence/thermal.json) and [bounded-queue experiment](evidence/queue32.json); raw CSV/JSON remain under `results/`.

The **1.0-ms median VT submission-to-callback stretch target was not met** in these paced cases. At the default in-flight count of two, 1080p120 median VT latency was 1.543 ms for AV1 SDR8, 1.675 ms for AV1 HDR10, 1.542 ms for HEVC Main and 1.690 ms for HEVC Main10 HDR. All four 1080p120 variants were loss-free. Corresponding caller-visible median AU-to-output latency was lower than the optional FFmpeg VT baseline in these tests; the report compares native public callback entry with FFmpeg receive-frame return, not mismatched internal decoder boundaries.

At 3440×1440p240 HDR, HEVC passed all three short runs and the two-minute run with 28,800/28,800 outputs. AV1's default 16-interval backlog bound caused startup loss of the first 60 display IDs in each run; every later frame decoded. The original AV1 runs remain FAIL, including 28,740/28,800 in the two-minute run. A controlled 32-interval bound retained all 2400/2400 frames in each of three repetitions at unchanged rate, quality and in-flight count. This establishes a startup backlog tradeoff, not universal low-latency success. Actual Qt startup and its common-c queue need live testing.

Disabling the power-efficiency preference was accepted but effective read-back was unavailable; small changes overlapped run variation and did not establish a reliable benefit. No frame formats or offered rates were substituted. Full-application rendering, GPU/presentation latency and live A/B remain **NOT MEASURED**.

## Limits and untested compatibility

The initial native path is 4:2:0 low-delay AV1 Main and HEVC Main/Main10. Extra AV1 operating points/layers/profiles, 4:4:4, HEVC B/leading/field/range-extension cases and declared reordering are explicitly unsupported; they are not silently converted or decoded with a hidden software fallback. Capture import expects complete access units with a valid manifest and is not an RTP/network recorder. Compressed zero-copy is not provided; safe-copy ownership and actual full-payload copy counts are exposed.

The M3 results apply to the tested configurations. Other SoCs, physical iOS/iPadOS/tvOS devices and high-resolution/rate combinations without a recorded result remain untested. The headless harness proves decoding and buffer compatibility, not matching monitor refresh, GPU submission latency or presentation. Unsupported optional properties remain status/readback results rather than initialization failures.

No live Sunshine, Apollo, VibeApollo, VibeShine or other host session was tested. Live codec/HDR negotiation, network loss recovery, end-to-end presentation pacing and full-app A/B performance require live testing. Reference-frame invalidation is not advertised by this decoder. Dedicated drawable/GPU waits and complete inherited presentation-drop counts are not instrumented; the existing render-call statistics are not presentation counts. The adapter exposes common-c queue depth/peak and held-AU admission age, which includes preparation and submit time; it does not provide a separate oldest-still-queued-AU age or queued-byte count. The implementation does not branch on host names. Synthetic fixtures and Qt's probes are not claims of broad host compatibility. Optional native H.264, a new Apple-native client, renderer redesign and XCFramework distribution packaging were not included.
