#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
CMAKE_BIN=${CMAKE:-cmake}
if [[ $(uname -s) != Darwin ]]; then
  echo 'BLOCKED: Apple SDK compilation requires macOS/Xcode' >&2
  exit 2
fi
for spec in 'ios:iOS:iphoneos:17.0:arm64' 'ios-simulator:iOS:iphonesimulator:17.0:arm64' 'tvos:tvOS:appletvos:17.0:arm64' 'tvos-simulator:tvOS:appletvsimulator:17.0:arm64'; do
  IFS=: read -r name system sdk minimum arch <<< "$spec"
  xcrun --sdk "$sdk" --show-sdk-path
  "$CMAKE_BIN" -S "$ROOT" -B "$ROOT/build-$name" -DCMAKE_SYSTEM_NAME="$system" -DCMAKE_OSX_SYSROOT="$sdk" -DCMAKE_OSX_ARCHITECTURES="$arch" -DCMAKE_OSX_DEPLOYMENT_TARGET="$minimum" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DMAV_BUILD_TOOLS=OFF
  "$CMAKE_BIN" --build "$ROOT/build-$name" -j "${JOBS:-4}"
done
export CLANG_MODULE_CACHE_PATH="$ROOT/build-swift-native/module-cache"
export SWIFTPM_MODULECACHE_OVERRIDE="$CLANG_MODULE_CACHE_PATH"
cd "$ROOT"
swift build --disable-sandbox --build-system native --scratch-path build-swift-native --cache-path build-swift-native/cache --config-path build-swift-native/config --security-path build-swift-native/security -c release
"$ROOT/build-swift-native/release/mav-swift-smoke"
echo 'PASS: Apple SDK compilation and Swift import; physical iOS/tvOS decode NOT TESTED'
