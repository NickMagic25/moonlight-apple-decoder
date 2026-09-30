// swift-tools-version: 6.3
import PackageDescription
import Foundation
// This repository also hosts ignored CMake/Qt acceptance builds. SwiftPM scans
// resources even with an explicit source list, so keep every generated build
// directory outside the root-path target instead of packaging their resources.
let repositoryPath = URL(fileURLWithPath: #filePath).deletingLastPathComponent().path
let generatedDirectories = ((try? FileManager.default.contentsOfDirectory(atPath: repositoryPath)) ?? [])
    .filter { $0 == "build" || $0.hasPrefix("build-") || $0.hasPrefix(".build-") }
// Keep the fork's Vulkan/encoder/build inputs outside the production target.
// Git dependencies initialize submodules automatically; local path dependencies
// must run `git submodule update --init --recursive` before building.
let pyrowaveRoot = URL(fileURLWithPath: repositoryPath).appendingPathComponent("Dependencies/pyrowave")
let pyrowaveExcluded = ((try? FileManager.default.contentsOfDirectory(atPath: pyrowaveRoot.path)) ?? [])
    .filter { $0 != "metal" }
    .map { "Dependencies/pyrowave/" + $0 }
let package = Package(
    name: "MoonlightAppleVideo",
    platforms: [.macOS(.v11), .iOS(.v17), .tvOS(.v17)],
    products: [.library(name: "MoonlightAppleVideo", type: .static, targets: ["MoonlightAppleVideo"]),
               .executable(name: "mav-swift-smoke", targets: ["OwnershipSmoke"])],
    targets: [
        .target(name: "MoonlightAppleVideo", path: ".",
                exclude: ["tests", "tools", "docs", "scripts", "examples", "cmake", "integration", "CMakeLists.txt", "LICENSE", "README.md", "Dependencies/pyrowave/metal/CMakeLists.txt", "Dependencies/pyrowave/metal/README.md", "Dependencies/pyrowave/metal/pyrowave.exports", "Dependencies/pyrowave/metal/shaders"] + generatedDirectories + pyrowaveExcluded,
                sources: ["src/decoder.cpp", "src/clock.cpp", "src/bitstream.cpp", "src/backend_vt.mm", "src/format.mm", "src/sample.mm", "src/pyrowave.cpp", "src/backend_pyrowave.mm", "Dependencies/pyrowave/metal/pyrowave_common.mm", "Dependencies/pyrowave/metal/pyrowave_decoder.mm", "Dependencies/pyrowave/metal/pyrowave_bitstream.cpp"],
                publicHeadersPath: "include",
                // PyroWave's coefficient validation is part of the realtime
                // decode path. At -O0 it exceeds a 165 Hz frame budget even on
                // an M3; keep debug symbols/assertions but optimize this native
                // library in Debug, while the consuming Swift app stays Debug.
                cxxSettings: [.headerSearchPath("src"), .headerSearchPath("Dependencies/pyrowave/metal"), .unsafeFlags(["-fobjc-arc"]),
                              .unsafeFlags(["-O2"], .when(configuration: .debug)) ],
                linkerSettings: [.linkedFramework("VideoToolbox"), .linkedFramework("CoreMedia"), .linkedFramework("CoreVideo"), .linkedFramework("CoreFoundation"), .linkedFramework("IOSurface"), .linkedFramework("Metal"), .linkedFramework("Foundation"), .linkedFramework("QuartzCore")]),
        .executableTarget(name: "OwnershipSmoke", dependencies: ["MoonlightAppleVideo"], path: "examples/swift")
    ],
    swiftLanguageModes: [.v6],
    // SwiftPM names the C++23 standard using its draft spelling.
    cxxLanguageStandard: .cxx2b)
