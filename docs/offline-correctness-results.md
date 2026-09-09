# Observed offline correctness evidence

The following tests ran on this workspace's Apple M3 MacBook Pro (Mac15,3), macOS 26.6.2, with a physical VideoToolbox hardware session and Xcode's macOS SDK. They require no streaming server. Hardware service access was unavailable inside the command sandbox (`-12911`), and the same executables passed with normal hardware access.

| Native variant | Generated stream | Strict replay | Independent same-stream software comparison |
| --- | --- | --- | --- |
| AV1 Main 8-bit SDR | 1920x1080, 120 AUs, inter frames, periodic keys, tiled | PASS: 240 outputs / 240 accepted across 2 loops | PASS: 373,248,000 visible Y/U/V samples; mean/max error 0 / 0 versus AOM |
| AV1 Main 10-bit HDR | 1920x1080, 120 AUs, BT.2020/PQ and static HDR metadata | PASS: 240 outputs / 240 accepted across 2 loops | PASS: 373,248,000 visible Y/U/V samples; mean/max error 0 / 0 versus AOM |
| HEVC Main 8-bit SDR | 1920x1080, 120 AUs, inter frames, periodic keys | PASS: 240 outputs / 240 accepted across 2 loops | PASS: 373,248,000 visible Y/U/V samples; mean/max error 0 / 0 versus FFmpeg software HEVC |
| HEVC Main10 HDR | 1920x1080, 120 AUs, BT.2020/PQ and static HDR metadata | PASS: 240 outputs / 240 accepted across 2 loops | PASS: 373,248,000 visible Y/U/V samples; mean/max error 0 / 0 versus FFmpeg software HEVC |

All four strict runs checked visible frame IDs and image structure, output dimensions and bit depth, real hardware selection, IOSurface backing, creation of Y/UV Metal textures, one terminal completion per accepted submission, and retained output validity after decoder reset/destruction. Required HDR runs checked normalized primaries/transfer/matrix and mastering/content-light metadata. The independent comparison checks every visible plane sample, not row padding or a hash of lossy pre-encode pixels.

The seeded AV1 fault run offered 120 AUs and accepted/completed/displayed 39, with 80 deliberate/dependency-safe discarded arrivals, one synchronous rejection, and six resets. It recovered at later random-access points and reported no trace overflow or unresolved submissions. This is loss/recovery evidence, not a latency or throughput result. A two-loop HEVC HDR correctness run with a 2 ms delay on each validation-consumer output completed all 240 accepted submissions, retained at most 18 buffers in its bounded worker, and had no trace overflow.

Machine-readable local results are `results/validation/summary.json`, `results/validation/{codec}-{variant}.json`, `results/reference-{codec}-{variant}.json`, `results/fault-av1.json`, and `results/slow-consumer-hevc-hdr10.json`. Fixtures are local under `fixtures/generated/{codec}-{variant}-1920x1080p120-120/`, with payload SHA-256 and encoder settings in each manifest. The independent AV1 decoder was AOM 3.13.3; the HEVC decoder was the software decoder in the local Moonlight Qt FFmpeg distribution.

These correctness runs use image inspection/CPU mapping and are not performance measurements. See the separate benchmark report for timed Release runs. They do not establish live Sunshine/Apollo compatibility, network transport behavior, presentation refresh rate, another Apple device's capabilities, or 4:4:4 support. Native H.264 is outside the implemented baseline.
