#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
cmake_bin=${CMAKE:-cmake}
version=v3.13.3
revision=92d4c37fbdd08944a0e721bbaeb13318f10aebb0
mkdir -p .local/src
if [ ! -d .local/src/aom/.git ]; then
  git clone --depth 1 --branch "$version" https://aomedia.googlesource.com/aom .local/src/aom
fi
actual=$(git -C .local/src/aom rev-parse HEAD)
[ "$actual" = "$revision" ] || { echo "BLOCKED: .local/src/aom is not the pinned $version revision; preserve it and choose another workspace." >&2; exit 1; }
"$cmake_bin" -S .local/src/aom -B .local/aom-build -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DENABLE_DOCS=OFF -DENABLE_EXAMPLES=ON -DENABLE_TOOLS=ON -DCONFIG_AV1_ENCODER=1 -DCONFIG_AV1_DECODER=1 -DCONFIG_AV1_HIGHBITDEPTH=1
"$cmake_bin" --build .local/aom-build --parallel "${JOBS:-4}" --target aomenc aomdec
printf '%s\n' "AOM $version encoder/decoder ready in .local/aom-build (no system installation)."
