#!/usr/bin/env bash
set -euo pipefail
SOURCE_DIR=$(cd "$(dirname "$0")/.." && pwd)
QT_DIR=${MOONLIGHT_QT_DIR:-$(dirname "$SOURCE_DIR")/moonlight-qt}
LIB_SOURCE=${MOONLIGHT_APPLE_VIDEO_SOURCE_DIR:-$SOURCE_DIR}
LIB_BUILD=${MOONLIGHT_APPLE_VIDEO_BUILD_DIR:-$SOURCE_DIR/build-qt-library}
LIB_INSTALL=${MOONLIGHT_APPLE_VIDEO_INSTALL_DIR:-$SOURCE_DIR/build-qt-install}
QT_BUILD=${MOONLIGHT_QT_BUILD_DIR:-$SOURCE_DIR/build-moonlight-qt}
CMAKE=${CMAKE:-cmake}
JOBS=${JOBS:-$(sysctl -n hw.logicalcpu 2>/dev/null || getconf _NPROCESSORS_ONLN)}
if [[ $(uname -s) != Darwin ]]; then echo 'BLOCKED: the Moonlight Qt native adapter requires macOS.' >&2; exit 1; fi
if [[ ! -f "$QT_DIR/moonlight-qt.pro" ]]; then echo "Missing Moonlight qmake checkout: $QT_DIR" >&2; exit 1; fi
if [[ -z ${QMAKE:-} ]]; then QMAKE=$(command -v qmake6 || command -v qmake || true); fi
if [[ -z $QMAKE ]]; then echo 'BLOCKED: set QMAKE to a local Qt 6 SDK bin/qmake (Qt 6.11.2 tested).' >&2; exit 1; fi
QT_DIR=$(cd "$QT_DIR" && pwd)
LIB_SOURCE=$(cd "$LIB_SOURCE" && pwd)
mkdir -p "$LIB_BUILD" "$LIB_INSTALL" "$QT_BUILD"
LIB_BUILD=$(cd "$LIB_BUILD" && pwd)
LIB_INSTALL=$(cd "$LIB_INSTALL" && pwd)
QT_BUILD=$(cd "$QT_BUILD" && pwd)
PATCH="$LIB_SOURCE/integration/moonlight-qt/consumer.patch"
if git -C "$QT_DIR" apply --reverse --check "$PATCH" 2>/dev/null; then
    echo 'Moonlight native integration hooks already applied.'
elif git -C "$QT_DIR" apply --check "$PATCH"; then
    git -C "$QT_DIR" apply "$PATCH"
else
    echo 'Integration hooks conflict with this checkout; review consumer.patch without discarding local edits.' >&2
    exit 1
fi
"$CMAKE" -S "$LIB_SOURCE" -B "$LIB_BUILD" -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-11.0}" \
    -DCMAKE_INSTALL_PREFIX="$LIB_INSTALL" -DBUILD_TESTING=OFF -DMAV_BUILD_TOOLS=OFF
"$CMAKE" --build "$LIB_BUILD" --parallel "$JOBS"
"$CMAKE" --install "$LIB_BUILD"
export MOONLIGHT_APPLE_VIDEO_SOURCE_DIR="$LIB_SOURCE"
export MOONLIGHT_APPLE_VIDEO_INSTALL_DIR="$LIB_INSTALL"
mkdir -p "$QT_BUILD"
(
    cd "$QT_BUILD"
    "$QMAKE" "$QT_DIR/moonlight-qt.pro" QMAKE_APPLE_DEVICE_ARCHS=arm64
    make -j"$JOBS" release
)
APP="$QT_BUILD/app/Moonlight.app"
if [[ ${MOONLIGHT_QT_DEPLOY:-1} == 1 ]]; then
    # Deploy only app-relevant plugin groups. Qt's generic deployment includes
    # optional database drivers requiring unrelated system libraries.
    QT_PLUGINS=$("$QMAKE" -query QT_INSTALL_PLUGINS)
    mkdir -p "$APP/Contents/PlugIns"
    for group in platforms imageformats iconengines networkinformation tls; do
        if [[ -d "$QT_PLUGINS/$group" ]]; then cp -R "$QT_PLUGINS/$group" "$APP/Contents/PlugIns/"; fi
    done
    QT_BIN=$("$QMAKE" -query QT_INSTALL_BINS)
    "$QT_BIN/macdeployqt" "$APP" -qmldir="$QT_DIR/app/gui" -no-plugins -no-codesign -appstore-compliant
    codesign --force --deep --sign - "$APP"
    codesign --verify --deep "$APP"
fi
printf 'Built: %s\n' "$APP"
printf 'Smoke: MOONLIGHT_APPLE_VIDEO_SMOKE=1 "%s/Contents/MacOS/Moonlight"\n' "$APP"
printf 'Native: MOONLIGHT_APPLE_VIDEO_DECODER=native MOONLIGHT_APPLE_VIDEO_STRICT=1 "%s/Contents/MacOS/Moonlight"\n' "$APP"
