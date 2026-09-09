# moonlight-apple-video

A reusable C ABI around direct asynchronous Apple VideoToolbox decoding of AV1
Main 8/10-bit and HEVC Main/Main10. The implementation lives in this
`moonlight-apple-decoder` repository. Moonlight Qt is an optional consumer and
compatibility reference. The core has no FFmpeg, Moonlight, Qt, SDL or renderer
dependency. Native H.264 is not implemented.

## Build

Prerequisites: Apple SDK with the public AV1 declarations (Xcode 15+), CMake
3.20+, C++17 compiler; Swift 5.9+ for SwiftPM. This work was built with SDK 26.5.
The core supports macOS 11+, iOS/iPadOS 17+, tvOS 17+; AV1 hardware sessions are
runtime gated (macOS 14+/iOS/tvOS 17+ plus actual hardware support). These are
library targets, not a change to a consumer application's deployment target.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0
cmake --build build -j
ctest --test-dir build --output-on-failure
cmake --install build --prefix "$PWD/install"
```

Consumers use `find_package(MoonlightAppleVideo CONFIG REQUIRED)` then
`target_link_libraries(app PRIVATE MoonlightAppleVideo::Decoder)`.
Installed header: `moonlight_apple_video/decoder.h`.

```sh
swift build -c release
swift run -c release mav-swift-smoke
```

The Swift target imports the C Clang module; Swift C++ interoperability is not
required. See [Swift ownership smoke](examples/swift/main.swift) and the full
ownership/concurrency contract in the public header.

Portable parser and mock lifecycle tests also build on Linux. Linux tests and
simulator builds never establish VideoToolbox hardware performance.

## Offline validation and benchmarks

```sh
./scripts/bootstrap-aom.sh # Local AV1 fixture encoder; not a library dependency
./scripts/validate.sh --suite correctness
./scripts/validate.sh --suite offline-hardware --require-hardware --require-codecs av1,hevc --require-variants sdr8,hdr10
./scripts/benchmark.sh --preset 1080p120-av1 --inflight 1,2,3
./scripts/benchmark.sh --preset 1080p120-hevc --inflight 1,2,3
```

See [fixture workflow](docs/fixtures.md), [benchmarks](docs/benchmarks.md), and
[implementation evidence](docs/implementation-report.md) for exact prerequisites,
results, and limits. Encoders run before replay, never during timing. Strict
coverage fails when a required codec/variant is unavailable. Hardware-required
session creation and actual hardware output are checked separately.

[Latency optimization investigation](docs/optimization-investigation.md) compares
paced and saturated decode and ranks the next experiments toward the 1 ms goal.
The [isolated experiment results](docs/experiment-results.md) compare those
branches, including 4K60 SDR/HDR correctness and hardware timing, with commands
and evidence for choosing which changes to prioritize.
Main adopts the HEVC scanner and parser-state optimizations plus optional replay
pacing. See [adopted changes and combined validation](docs/main-adoption.md).
The [4K60 VT interval investigation](docs/vt-interval-investigation.md) separates
API blocking, output-format/cadence controls, and native-to-Qt handoff costs.
The [decoder-service follow-up](docs/vt-wait-dependencies.md) traces the waits
through XPC, CoreMedia semaphores and AppleAVD notifications.

## Architecture and consumer compatibility

[Architecture and lifecycle](docs/architecture.md) describes spans, AV1 temporal
units, hidden/existing-frame accounting, bounded admission, metadata, and clocks.
[Repository investigation](docs/investigation.md) records actual Qt/common-c
source paths and revisions. Qt integration materials are under
`integration/moonlight-qt`; the application keeps its existing Metal renderer.
The reusable implementation is shared by CMake and SwiftPM, not copied into Qt.

```sh
MOONLIGHT_QT_DIR=/path/to/moonlight-qt ./scripts/build-moonlight-qt.sh
```

Live host interoperability and presentation throughput require separate live
client tests; headless decoding alone does not establish either.
