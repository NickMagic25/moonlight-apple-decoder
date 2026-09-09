#!/usr/bin/env bash
set -euo pipefail
SOURCE_DIR=$(cd "$(dirname "$0")/.." && pwd)
QT_BUILD=${MOONLIGHT_QT_BUILD_DIR:-$SOURCE_DIR/build-moonlight-qt}
OUTPUT=${MAV_QT_RESULTS_DIR:-$SOURCE_DIR/results/qt-native-smoke}
mkdir -p "$OUTPUT"
MOONLIGHT_APPLE_VIDEO_SMOKE=1 MOONLIGHT_APPLE_VIDEO_DECODER=native MOONLIGHT_APPLE_VIDEO_STRICT=1 \
  "$QT_BUILD/app/Moonlight.app/Contents/MacOS/Moonlight" > "$OUTPUT/results.jsonl" 2> "$OUTPUT/launcher.log"
cat "$OUTPUT/results.jsonl"
printf 'Results: %s\n' "$OUTPUT"
