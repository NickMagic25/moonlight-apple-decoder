# Server-free fixtures and correctness

The production decoder has no encoder or FFmpeg dependency. The macOS `mav-fixture` tool uses `VTCompressionSession` for HEVC and the standalone AOM encoder for AV1. `mav-replay` reads complete access units and uses the installed public C API and the same native decoder linked into Moonlight Qt.

Build with an available CMake 3.20+ and Xcode macOS SDK:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 4
./scripts/bootstrap-aom.sh
./scripts/validate.sh --suite correctness
./scripts/validate.sh --suite offline-hardware --require-hardware --require-codecs av1,hevc --require-variants sdr8,hdr10
```

`CMAKE`, `PYTHON`, `JOBS`, `AOMENC`, and `--build-dir` can select local tools. A broken version-manager shim is not an installed working CMake: set `CMAKE` to the actual executable. The bootstrap fetches AOM v3.13.3 at `92d4c37fbdd08944a0e721bbaeb13318f10aebb0` from the [AOM project](https://aomedia.googlesource.com/aom/), builds `.local/aom-build/aomenc` and `aomdec`, and installs nothing system-wide. Network access is required once for regeneration; saved fixtures require no encoder. Run hardware tools outside an automation sandbox that denies VideoToolbox device service access; on this machine that sandbox returned `-12911`, while the identical binaries succeeded with normal hardware access.

The default hardware suite exercises both codecs and both SDR8/HDR10 variants. Explicit requirements and the `offline-hardware` suite return a nonzero status when any required coverage is missing. The ordinary `correctness` suite also runs CTest; on heterogeneous environments it can report `PARTIAL` for unavailable Apple hardware after portable tests pass. `results/validation/summary.json` always distinguishes each codec and variant. Generated payloads and raw references are local artifacts, not committed media.

Direct generation and replay:

```sh
build/mav-fixture --codec av1 --variant hdr10 --width 1920 --height 1080 --fps 120 --frames 120 --gop 60 --output fixtures/generated/example --aomenc .local/aom-build/aomenc
build/mav-replay --fixture fixtures/generated/example/manifest.json --mode correctness --loops 2 --output results/example
```

Change `av1` to `hevc` and `hdr10` to `sdr8` to cover the other variants. The test pattern has gradients, moving detail, a translating square, and sixteen high-contrast frame-ID cells. AV1 uses a two-column tiled, good-quality CPU6 encode with zero lag, alternate-reference generation disabled, and fixed periodic keys; the parser verifies the result rather than trusting these settings. AOM's realtime CPU8 mode erased some 10-bit frame-ID cells in the compressed stream, confirmed independently with aomdec, so it is not used for baseline generation. HEVC disables encoder frame reordering and uses its actual sample attachments and parameter sets to derive complete Annex-B access units.

Both HDR generators encode actual 10-bit 4:2:0 pixels with Main/Main10 profiles as appropriate and BT.2020/PQ signaling. The fixture tool supplies standards-defined AV1 HDR metadata OBUs or HEVC prefix SEI for a deterministic 1000-nit mastering display and MaxCLL/MaxFALL. These are compressed-stream metadata, not labels attached after decoding. VT accepted compression mastering properties but omitted some SEI on this machine; explicit fixture metadata closes that gap. AV1 MDCV RGB fixed-point units are converted to the public API's HEVC/SMPTE2086 G,B,R representation by the production parser.

## Manifest schema 1

`manifest.json` records codec, profile, framing, width/height, bit depth/chroma, rational frame rate/timebase, color metadata, encoder settings/provenance, `payload_file`, whole-payload SHA-256, and an ordered `access_units` list. Each entry includes contiguous byte offset/length, its own SHA-256, unique frame ID, nullable PTS/DTS, duration, random-access/discontinuity flags, and expected display count. Generated fixtures also record `expected_visible_frame_id`. Metadata byte arrays are base64 in the manifest. The reader checks size limits, path containment, payload hashes, duplicate IDs, bounds, framing, and a valid initial random-access point. File payloads are bounded at 2 GiB and AUs at 64 MiB; generate short clips and loop them for long tests.

The AV1 importer removes the IVF header and each IVF packet's framing; the public decoder receives only codec OBUs. HEVC converts encoder sample length prefixes and extracted VPS/SPS/PPS into Annex-B, retaining non-parameter payloads. No container is submitted to VideoToolbox.

Previously captured complete Moonlight AUs can be packed into this schema and imported using:

```sh
build/mav-fixture --import capture/manifest.json --output fixtures/imported/capture
```

The importer validates compressed syntax and expected display/random-access/format information, copies the exact payload, and preserves original timing, IDs, and expected display sequence. It does not implement transport capture, RTP, pairing, or a server.

## Independent output validation

The correctness sink checks every displayed frame's dimensions, bit depth, hardware selection, HDR metadata, IOSurface, Y and UV Metal textures, known spatial structure, and visible frame ID. A bounded worker owns at most 32 retained frames and never maps pixels in the VT callback. One independent retained pixel buffer is mapped after reset and destruction. `--consumer-delay-ms` delays this worker per output to exercise consumer retention; overflow is an explicit failure. Correctness mode can wait for worker capacity and its timings are not performance evidence.

An optional software reference decoder uses FFmpeg outside the core:

```sh
cmake -S . -B build -DMAV_FFMPEG_ROOT="$MOONLIGHT_QT_DIR/libs/mac"
cmake --build build --target mav-reference-decode mav-replay
DYLD_LIBRARY_PATH="$MOONLIGHT_QT_DIR/libs/mac/lib" build/mav-reference-decode --fixture fixtures/generated/example/manifest.json --output /tmp/reference.yuv
build/mav-replay --fixture fixtures/generated/example/manifest.json --mode correctness --reference-raw /tmp/reference.yuv --output results/example-reference
```

When FFmpeg has no software AV1 decoder, use AOM on the corresponding generated `encoded.ivf`:

```sh
.local/aom-build/aomdec --i420 --rawvideo --output-bit-depth=10 -o /tmp/reference.yuv fixtures/generated/example/encoded.ivf
```

The saved IVF contains exactly the encoded picture bytes before the fixture's static HDR metadata insertion; that metadata cannot alter pixel reconstruction. `--reference-raw` compares every visible Y/U/V sample from the same compressed pictures, without row padding, to planar I420 or low-bit-packed I42010 little-endian. Native P010 is shifted right by six. Tolerances are at most 2 code values for 8-bit and 8 for 10-bit; result JSON reports sample count and observed mean/max error. Reference decoding and full-plane comparison run only in correctness mode.

Fault simulation is deterministic given `--seed`, with optional `--jitter-us`, `--drop-every`, `--corrupt-every`, `--reset-every`, and `--consumer-delay-ms`. It records recovery and terminal accounting; loss triggers reset and waits for a later actual random-access AU. Additional AV1 accounting tests exercise hidden frames and `show_existing_frame` independently of the low-delay baseline.
