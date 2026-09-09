# Bitstream and AV1 accounting validation

The portable parser accepts one complete HEVC Annex B access unit or one AV1 temporal unit composed of low-overhead OBUs with explicit size fields. HEVC start codes may be three or four bytes and cross input spans. AV1 bytes are not passed through NAL conversion. AV1 span assembly becomes the final owned sample allocation; HEVC span input currently needs assembly followed by length-prefix conversion, and its copy counters expose both operations.

All input is bounded to 64 MiB, 4,096 units/spans, 64 AV1 child frames, and 65,535 bytes per sequence/parameter set. Configuration updates are transactional. HEVC caches VPS/SPS/PPS by identifier and chooses the chain referenced by the picture. Repeated or unused parameter sets do not replace the active configuration. VPS/SPS/PPS syntax, including VUI/HRD bounds and trailing bits, is checked; emulation-prevention bytes are removed only in parsing scratch buffers. Slice parsing copies only a bounded prefix. Configuration and scratch copies are distinct from full compressed sample-copy metrics.

The initial supported path requires AV1 Main 8/10-bit 4:2:0, a single operating point and layer, or HEVC Main/Main10 4:2:0. AV1 sequence configuration, timing-related header prefixes, layer extensions, bounded LEB128 lengths, frame/header/tile-group framing and HDR metadata are parsed. Unsupported layers/tile lists/profile arrangements are rejected explicitly. HEVC declared reordering, B slices, leading pictures, field coding and range/multilayer extensions are rejected explicitly. This is a bounded configuration/framing parser, not an entropy decoder; VideoToolbox checks compressed picture semantics. Resolution overrides that do not match the configured output are rejected by output validation.

AV1 can contain hidden reference pictures followed by one displayed picture. Each coded frame becomes a child VideoToolbox sample; exactly one terminal public completion covers the original temporal unit. An independently submitted hidden frame completes with no displayed image. `show_existing_frame` is submitted directly to VideoToolbox and remains a separately marked display event. The tested Apple M3 implementation returns the existing image and resolves hidden callbacks without requiring a per-frame wait. Multiple displayed images in one public access unit are rejected because the public completion contract carries one image.

AV1 `av1C` contains the four-byte codec configuration record followed by the original sequence OBU. AV1 chroma siting is normalized to HEVC-style chroma-location values for the shared metadata API. AV1 RGB-order mastering metadata with fixed-point chromaticity/luminance is converted to the shared HEVC G,B,R-order units; the configuration record retains AV1's original chroma-sample-position value. Metadata OBUs and HEVC SEI payloads remain in compressed samples.

These implementations were written from codec syntax and inspected against current implementations; no FFmpeg parser implementation was copied. Primary references:

- [AOMedia AV1 syntax](https://github.com/AOMediaCodec/av1-spec/blob/master/06.bitstream.syntax.md) and [metadata semantics](https://github.com/AOMediaCodec/av1-spec/blob/master/07.bitstream.semantics.md).
- [AV1 ISO media binding, including av1C and sample layout](https://aomediacodec.github.io/av1-isobmff/).
- [FFmpeg's public-API VideoToolbox AV1 integration](https://github.com/FFmpeg/FFmpeg/blob/master/libavcodec/videotoolbox_av1.c), inspected for av1C/OBU forwarding, and [HEVC parameter-set parsing](https://github.com/FFmpeg/FFmpeg/blob/n8.0/libavcodec/hevc/ps.c), inspected for configuration syntax.

## Reproduce the accounting test

Build the locally pinned encoder and decoder, then run the dedicated correctness test:

```sh
./scripts/bootstrap-aom.sh
./scripts/test-av1-accounting.py
```

Use `CMAKE=/path/to/cmake`, `AOMENC=/path/to/aomenc`, and `AOMDEC=/path/to/aomdec` when these tools are outside PATH. `--skip-build` reuses an existing build; `--depths 8` or `--depths 10` selects one depth. No streaming server or downloaded media is used. Generated inputs and encoder/reference logs are under `fixtures/generated/av1-accounting-{8,10}/`; hashes, codec-tool arguments and machine information are retained in `provenance.json`. Machine-readable results are under `results/av1-accounting/`.

The recipe generates 48 moving 256x144 frames and deliberately enables libaom alternate-reference frames and lookahead. These are accounting fixtures, not the low-delay benchmark baseline. The test runs the same production C API twice: whole temporal units at three in flight, then individually split coded frames at one in flight. It requires hidden, existing-frame and multi-frame cases to actually occur, checks every terminal completion and ID, verifies hardware selection and IOSurface-backed output, compares whole versus split output exactly, and compares all visible Y/U/V samples against libaom's software decoding of the same compressed stream. NV12 and 10-bit bi-planar output are unpacked without row padding. Reference tolerance is maximum error 2 and mean error 0.10 in native 8-bit or 10-bit sample units. Pixel mapping belongs only to this correctness sink; this test makes no performance claim.

On Apple M3 with SDK 26.5, both 8-bit and 10-bit runs passed: each contained 48 temporal units, 12 multi-frame units, 71 child decode samples, 23 hidden frames and 20 existing-frame display events. Grouped input completed 48 submissions with 48 images; split input completed 71 submissions with 48 images and 23 successful no-display completions. Both ended with zero outstanding work. All 2,654,208 visible samples per variant matched the software reference exactly (maximum and mean error 0), and whole versus split output matched exactly. Hardware tests must run with access to the VideoToolbox service; this environment's restricted sandbox returned decoder malfunction (-12911), while the same binaries succeeded outside that sandbox.

The portable `mav-bitstream-tests` also covers malformed lengths/headers, all span boundaries, configuration-record inconsistency, parameter-set chain changes, truncated parameter sets, multi-slice input, metadata, no-display/existing accounting, and seeded malformed input. It passed separately with AddressSanitizer and UndefinedBehaviorSanitizer. `tests/test_stream.hpp` deliberately provides syntax-only mock input; it is never used as proof of actual decoding.
