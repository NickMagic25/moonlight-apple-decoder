# Encoder-layout experiment

This branch adds fixture controls and reporting. No fixtures, encodes, or timed
decode measurements were run as part of the implementation. The root experiment
coordinator owns generation and every timed run.

Start with AV1 column log2 values **0, 1, 2** (requested 1, 2, 4 columns), keeping
row log2=0. Value 1 is the existing default. This is a bounded experiment, not a
claim that extra tiles improve VideoToolbox latency. Keep the moving-gradient
pattern, source frame IDs, GOP 60, 120 frames, CPU6, six encoder threads,
zero lag, no alternate references, and CQ 12 identical within each case:

| Case | Resolution | Rate | Depth/signal | Column log2 |
| --- | --- | --- | --- | --- |
| 1080p120-sdr8 | 1920x1080 | 120 fps | 8-bit BT.709 | 0, 1, 2 |
| 4k60-sdr8 | 3840x2160 | 60 fps | 8-bit BT.709 | 0, 1, 2 |
| 4k60-hdr10 | 3840x2160 | 60 fps | 10-bit BT.2020/PQ | 0, 1, 2 |

Produce the nine commands without executing them:

```sh
python3 scripts/encoder-layout.py plan --fixture-tool build/mav-fixture --aomenc /Users/nmajkic/git/moonlight-dev/moonlight-apple-decoder/.local/aom-build/aomenc --output-root fixtures/generated/encoder-layout
```

The returned command arrays all request `--aom-psnr 1`. To validate one command
without encoding, append `--plan-only 1`. After the coordinator generates all
nine fixtures, summarize saved size and quality evidence:

```sh
python3 scripts/encoder-layout.py summarize --output-root fixtures/generated/encoder-layout
```

The summary rejects cases with changed pattern, frame count, GOP, depth, AOM
version, or non-layout command arguments. Every generated manifest retains exact
payload SHA-256, launched arguments, requested layout, fixed CQ, and quality data.
Bitrate is total codec AU bytes times 8 divided by duration, including inserted
static HDR metadata and excluding IVF or transport overhead. The summary reports
bitrate percentage and luma PSNR differences from the column-log2=1 baseline;
decode latency remains null until centrally scheduled replay results supply it.

Fixed CQ does not imply equal bitrate or equal reconstruction quality. Report
both size and PSNR changes alongside the same VT submit-to-callback distribution,
cadence, in-flight limit, warmup, and completion/drop accounting. Do not compare
different layout payloads as an identical-compressed-byte backend comparison.
PSNR is AOM's encoder-reconstructed output versus the original source, in encoded
sample values; it is not independent decoder correctness or perceptual HDR
quality. AOM prints summary PSNR to three decimal places. Keep the default unless
a measured latency improvement survives these tradeoffs. Fixture generation alone
does not verify emitted geometry: AOM can constrain requests according to picture
and codec limits. Use the optional probe below before interpreting layout effects.

## Optional verification of actual tiles

The separate `mav-tile-geometry` tool links the public libaom decoder API only;
the production decoder does not acquire an AOM dependency. Configure explicitly:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 -DMAV_AOM_SOURCE=/Users/nmajkic/git/moonlight-dev/moonlight-apple-decoder/.local/src/aom -DMAV_AOM_LIBRARY=/Users/nmajkic/git/moonlight-dev/moonlight-apple-decoder/.local/aom-build/libaom.a
cmake --build build --target mav-tile-geometry --parallel 4
build/mav-tile-geometry --ivf fixtures/generated/encoder-layout/1080p120-sdr8/columns2-rows0/encoded.ivf --expect-columns 4 --expect-rows 1 --output fixtures/generated/encoder-layout/1080p120-sdr8/columns2-rows0/tile-geometry.json
python3 scripts/encoder-layout.py summarize --output-root fixtures/generated/encoder-layout --require-geometry
```

The supplied local libaom archive was built with a macOS 26 minimum, so linking
the optional tool with target 11 emits minimum-version warnings. This binary is
for the current validation machine; target 11 alone does not establish old-macOS
compatibility for that archive. The production decoder remains unaffected.

Run the probe centrally for all nine saved IVF files, mapping column log2 0/1/2
to `--expect-columns 1/2/4`. It performs software decoding, never encoding, and
records no timing. The pinned AOM API names the control `AOMD_GET_TILE_INFO`.
It reports each decoded frame's actual column/row counts, widths and heights in
superblocks, and tile-group count. Every packet must produce one newly decoded
displayed frame; hidden/show-existing outputs are rejected to avoid attributing
the previous frame's geometry. Requested counts, full geometry consistency,
frame count, control statuses, AOM version, and original IVF SHA-256 are recorded.
Unavailable controls, mismatches, or inconsistent geometry return nonzero.

The summary accepts geometry evidence only when its saved IVF hash, frame count,
dimensions, expected counts, and PASS status match the fixture. `--require-geometry`
fails on missing reports. This inspection concerns the exact generated IVF
picture bytes used by fixture generation before deterministic HDR metadata is
inserted; it does not test native decoder performance. Root runs the nine real
probes after the tool's build; implementation validation does not claim geometry
results before those probes finish.

## HEVC slice availability

The public macOS 26.5 SDK `VTCompressionProperties.h` has one slice-size control,
`kVTCompressionPropertyKey_MaxH264SliceBytes` (lines 579–588), explicitly for H.264.
It declares no HEVC slice/tile setter. This experiment therefore adds **no HEVC
layout setter**, does not send H.264 controls to HEVC, and does not set private
keys or replace the hardware encoder with a software encoder. Existing HEVC
generation retains its average-bitrate policy; it is not a fixed-CQ peer of AV1.

The coordinator can collect runtime evidence without encoding frames:

```sh
build/mav-fixture --codec hevc --variant sdr8 --width 1920 --height 1080 --query-hevc-layout 1 --output results/encoder-layout/hevc-query-1080
build/mav-fixture --codec hevc --variant hdr10 --width 3840 --height 2160 --fps 60 --query-hevc-layout 1 --output results/encoder-layout/hevc-query-4k-hdr
```

The tool requires a hardware compression session, selects Main/Main10, calls
`VTSessionCopySupportedPropertyDictionary`, and records its status, supported
keys, and readback/status for advertised keys containing “slice” or “tile”. Those
advertisements alone do not establish a public supported HEVC setter. The report
also records session creation status, hardware readback, encoder ID, and
`UNAVAILABLE_PUBLIC_CONTROL`; no control is set. This query mode does not prepare
or submit frames. Ordinary HEVC generation collects the same report and refreshes
hardware readback after encoding. Failed hardware creation remains a nonzero
blocked result with its OSStatus retained in `encoder-settings.json`.

## Validation without encoding

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 -DCMAKE_OSX_ARCHITECTURES=arm64
cmake --build build --target mav-fixture --parallel 4
python3 tests/fixture_options.py build/mav-fixture
python3 scripts/encoder-layout.py plan --output-root fixtures/generated/encoder-layout
```

The argument tests check unchanged defaults, explicit column/row requests, PSNR
planning, and invalid/cross-codec/import rejection. An intentionally nonexistent
encoder path ensures that planning never launches AOM. No hardware availability,
encoding success, PSNR parsing on new encodes, or decode timing is established by
these checks; those remain the coordinator's next validation steps.
