# C++23 and Swift 6.3 upgrade

Validated on 2026-09-09 on an Apple M3 MacBook Pro, macOS 26.6.2, with Xcode
26.6, SDK 26.5, Apple Clang 21, Swift 6.3.3, and CMake 3.31.12.

## Build requirements

CMake requires C++23 for both C++ and Objective-C++, with standard fallback
disabled. The minimum CMake version is now 3.23: that release adds Apple Clang's
[C++23 compiler flag mapping](https://github.com/Kitware/CMake/blob/v3.23.0/Modules/Compiler/AppleClang-CXX.cmake).

SwiftPM requires tools version 6.3 and explicitly selects Swift 6 language mode.
The installed manifest API spells C++23 `.cxx2b`; the emitted `-std=c++2b` flag
selects C++23 in this compiler. Swift 6.3 is the toolchain requirement, while
`6` is the Swift language mode.

The decoder sources, public C header, ABI version, and platform deployment
targets are unchanged: macOS 11, iOS/iPadOS 17, and tvOS 17. The installed CMake
target does not impose the decoder's C++ standard on consumer source files.

## Regression results

| Check | Result |
| --- | --- |
| macOS Release, production configuration | All targets built; 4/4 CTests passed |
| macOS Debug, AddressSanitizer + UndefinedBehaviorSanitizer, VT experiments enabled | All targets built; 6/6 CTests passed; no sanitizer diagnostics |
| SwiftPM Release and Debug | Both built; both C API ownership smoke runs passed |
| iOS 17 and tvOS 17, arm64 device and simulator | All four library builds passed |
| Release hardware replay: AV1/HEVC, SDR8/HDR10, 1080p120/4K60 fixtures | All eight combinations passed, each with 240 accepted/completed/displayed frames across two loops |
| Sanitized hardware replay: AV1/HEVC, SDR8/HDR10, 1080p120 fixtures | All four combinations passed, each with 240 frames and no sanitizer diagnostics |
| AV1 hidden/show-existing and grouped/split accounting, 8/10-bit | Both passed; grouped/split output matched exactly; zero error against the existing libaom reference |
| AV1/HEVC format changes | Both passed: 26 hardware outputs and six implicit format changes per codec; retained pixels stayed stable |
| AV1/HEVC HDR metadata fallback | Both existing stripped-metadata fixtures passed: 120 hardware outputs each at 10-bit |
| Fault recovery and delayed consumer | Seeded AV1 fault test passed; HEVC HDR with a 2 ms consumer delay completed all 240 frames |
| Installed CMake package | External C11 and C++17 consumers passed 2/2 tests; C++17 compile mode was preserved |
| Public symbols | All 12 exported `mav_` symbol names matched the previous installed archive |
| Moonlight Qt 6.11.2 | Release app rebuilt, bundled, and ad-hoc signature verified; native ownership/Metal smoke passed AV1/HEVC at 8/10-bit, 4/4 |

Replay correctness checks cover frame IDs, dimensions, bit depth, HDR metadata,
hardware selection, IOSurface/Metal access, completion accounting, reset, and
retained output after decoder destruction. Compile commands confirmed C++23 for
both `.cpp` and `.mm` files, tools version 6.3 for the Swift manifest, Swift
language mode 6, and C++17 for the Qt adapter and external C++ consumer.

## Reproduction and local evidence

The existing validation entry points remain applicable. With the required
toolchains and generated fixtures available:

```sh
cmake -S . -B build-upgrade-release -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0
cmake --build build-upgrade-release --parallel 4
ctest --test-dir build-upgrade-release --output-on-failure
./scripts/validate.sh --suite correctness --build-dir build-upgrade-release --skip-build --require-hardware --require-codecs av1,hevc --require-variants sdr8,hdr10

cmake -S . -B build-upgrade-sanitize -DCMAKE_BUILD_TYPE=Debug -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 -DMAV_SANITIZE=ON -DMAV_VT_EXPERIMENTS=ON
cmake --build build-upgrade-sanitize --parallel 4
ctest --test-dir build-upgrade-sanitize --output-on-failure
./scripts/check-platforms.sh
python3 scripts/test-reconfiguration.py --build-dir build-upgrade-release --skip-build
```

Detailed run commands and outputs are local under `results/toolchain-upgrade/`.
Platform and Swift logs are in `build-upgrade-platform-*` and
`build-upgrade-swift`; consumer and Qt evidence is under
`build-upgrade-consumer-smoke` and `build-upgrade-consumer-qt`. These generated
directories are ignored by Git. The initial sandboxed replay could not access
Metal; hardware checks passed with normal macOS hardware-service access.

This establishes offline regression coverage on the tested Mac. It does not
establish physical iOS/tvOS decoding, Linux runtime behavior, older macOS runtime
compatibility, live host streaming, or a performance improvement.
