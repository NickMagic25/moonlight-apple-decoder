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
a measured latency improvement survives these tradeoffs. Encoded tile geometry
is currently unverified: AOM can constrain requests according to the picture and
codec limits, so labels always say **requested columns**.

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
