// swift-tools-version: 6.3
import PackageDescription
let package = Package(
    name: "MoonlightAppleVideo",
    platforms: [.macOS(.v11), .iOS(.v17), .tvOS(.v17)],
    products: [.library(name: "MoonlightAppleVideo", type: .static, targets: ["MoonlightAppleVideo"]),
               .executable(name: "mav-swift-smoke", targets: ["OwnershipSmoke"])],
    targets: [
        .target(name: "MoonlightAppleVideo", path: ".",
                exclude: ["tests", "tools", "docs", "scripts", "examples", "cmake", "integration", "CMakeLists.txt", "LICENSE", "README.md"],
                sources: ["src/decoder.cpp", "src/clock.cpp", "src/bitstream.cpp", "src/backend_vt.mm", "src/format.mm", "src/sample.mm"],
                publicHeadersPath: "include",
                cxxSettings: [.headerSearchPath("src")],
                linkerSettings: [.linkedFramework("VideoToolbox"), .linkedFramework("CoreMedia"), .linkedFramework("CoreVideo"), .linkedFramework("CoreFoundation"), .linkedFramework("IOSurface")]),
        .executableTarget(name: "OwnershipSmoke", dependencies: ["MoonlightAppleVideo"], path: "examples/swift")
    ],
    swiftLanguageModes: [.v6],
    // SwiftPM names the C++23 standard using its draft spelling.
    cxxLanguageStandard: .cxx2b)
