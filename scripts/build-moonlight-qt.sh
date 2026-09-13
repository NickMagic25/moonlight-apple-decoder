#!/usr/bin/env bash
set -euo pipefail
SOURCE_DIR=$(cd "$(dirname "$0")/.." && pwd)
QT_DIR=${MOONLIGHT_QT_DIR:-$(dirname "$SOURCE_DIR")/moonlight-qt}
LIB_SOURCE=${MOONLIGHT_APPLE_VIDEO_SOURCE_DIR:-$SOURCE_DIR}
BUILD_TYPE=${MOONLIGHT_QT_BUILD_TYPE:-Release}
case "$BUILD_TYPE" in
    Debug) BUILD_SUFFIX=-debug; QT_MAKE_TARGET=debug; QT_CONFIG=(CONFIG+=debug CONFIG-=release) ;;
    Release) BUILD_SUFFIX=; QT_MAKE_TARGET=release; QT_CONFIG=(CONFIG+=release CONFIG-=debug) ;;
    *) echo 'BLOCKED: MOONLIGHT_QT_BUILD_TYPE must be Debug or Release.' >&2; exit 1 ;;
esac
if [[ -v MOONLIGHT_QT_DEPLOY ]]; then
    DEPLOY=$MOONLIGHT_QT_DEPLOY
elif [[ $BUILD_TYPE == Debug ]]; then
    DEPLOY=0
else
    DEPLOY=1
fi
if [[ $DEPLOY != 0 && $DEPLOY != 1 ]]; then echo 'BLOCKED: MOONLIGHT_QT_DEPLOY must be 0 or 1.' >&2; exit 1; fi
LIB_BUILD=${MOONLIGHT_APPLE_VIDEO_BUILD_DIR:-$SOURCE_DIR/build-qt-library$BUILD_SUFFIX}
LIB_INSTALL=${MOONLIGHT_APPLE_VIDEO_INSTALL_DIR:-$SOURCE_DIR/build-qt-install$BUILD_SUFFIX}
QT_BUILD=${MOONLIGHT_QT_BUILD_DIR:-$SOURCE_DIR/build-moonlight-qt$BUILD_SUFFIX}
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
for PATCH in "$LIB_SOURCE/integration/moonlight-qt/consumer.patch" \
             "$LIB_SOURCE/integration/moonlight-qt/native-presentation-trace.patch" \
             "$LIB_SOURCE/integration/moonlight-qt/native-presentation-fix.patch"; do
    if git -C "$QT_DIR" apply --recount --reverse --check "$PATCH" 2>/dev/null; then
        echo "Moonlight integration patch already applied: $(basename "$PATCH")"
    elif git -C "$QT_DIR" apply --recount --check "$PATCH"; then
        git -C "$QT_DIR" apply --recount "$PATCH"
    elif [[ $PATCH == *native-presentation-trace.patch ]] && \
         rg -q 'Native Metal trace: first command buffer completed' "$QT_DIR/app/streaming/video/ffmpeg-renderers/vt_metal.mm"; then
        # A later native-presentation fix extends this same file, so the
        # standalone trace patch no longer reverses cleanly. Its marker proves
        # the trace is already present without masking unrelated conflicts.
        echo 'Moonlight integration patch already applied: native-presentation-trace.patch (extended)'
    elif [[ $PATCH == *native-presentation-fix.patch ]] && \
         rg -q 'getNativePixelBufferFormat' "$QT_DIR/app/streaming/video/ffmpeg-renderers/vt_metal.mm"; then
        echo 'Moonlight integration patch already applied: native-presentation-fix.patch'
    else
        echo "Integration patch conflicts with this checkout: $(basename "$PATCH"). Review it without discarding local edits." >&2
        exit 1
    fi
done
"$CMAKE" -S "$LIB_SOURCE" -B "$LIB_BUILD" -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET="${MACOSX_DEPLOYMENT_TARGET:-11.0}" \
    -DCMAKE_INSTALL_PREFIX="$LIB_INSTALL" -DBUILD_TESTING=OFF -DMAV_BUILD_TOOLS=OFF
"$CMAKE" --build "$LIB_BUILD" --parallel "$JOBS"
"$CMAKE" --install "$LIB_BUILD"
export MOONLIGHT_APPLE_VIDEO_SOURCE_DIR="$LIB_SOURCE"
export MOONLIGHT_APPLE_VIDEO_INSTALL_DIR="$LIB_INSTALL"
mkdir -p "$QT_BUILD"
APP="$QT_BUILD/app/Moonlight.app"
# macdeployqt cannot safely redeploy an existing bundle because its rewritten
# framework paths hide the original Qt SDK paths. Recreate only this generated
# output; all build objects and source checkouts remain intact.
if [[ $DEPLOY == 1 && -d "$APP" ]]; then rm -rf "$APP"; fi
(
    cd "$QT_BUILD"
    "$QMAKE" "$QT_DIR/moonlight-qt.pro" QMAKE_APPLE_DEVICE_ARCHS=arm64 "${QT_CONFIG[@]}"
    make -j"$JOBS" "$QT_MAKE_TARGET"
)
if [[ $DEPLOY == 1 ]]; then
    QT_BIN=$("$QMAKE" -query QT_INSTALL_BINS)
    "$QT_BIN/macdeployqt" "$APP" -qmldir="$QT_DIR/app/gui" -no-plugins -no-codesign -appstore-compliant
    # Deploy only app-relevant plugin groups. Run this after macdeployqt: the
    # latter clears PlugIns even with -no-plugins.
    QT_PLUGINS=$("$QMAKE" -query QT_INSTALL_PLUGINS)
    mkdir -p "$APP/Contents/PlugIns"
    for group in platforms imageformats iconengines networkinformation tls; do
        if [[ -d "$QT_PLUGINS/$group" ]]; then cp -RL "$QT_PLUGINS/$group" "$APP/Contents/PlugIns/"; fi
    done
    cp "$LIB_SOURCE/integration/moonlight-qt/qt.conf" "$APP/Contents/Resources/qt.conf"
    codesign --force --deep --sign - "$APP"
    codesign --verify --deep "$APP"
fi
printf 'Built: %s\n' "$APP"
printf 'Smoke: MOONLIGHT_APPLE_VIDEO_SMOKE=1 "%s/Contents/MacOS/Moonlight"\n' "$APP"
printf 'Native: MOONLIGHT_APPLE_VIDEO_DECODER=native MOONLIGHT_APPLE_VIDEO_STRICT=1 "%s/Contents/MacOS/Moonlight"\n' "$APP"
