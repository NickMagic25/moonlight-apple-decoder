# C++23 / Swift 6.3 resolution and frame-rate matrix

Measured on 2026-09-09, Apple M3 / macOS 26.6.2, Xcode 26.6, Apple Clang 21,
Swift 6.3.3 and SDK 26.5. The production Release decoder uses C++23; Swift is
only involved in the separately validated package/ownership smoke.

**All 24 hardware correctness gates passed. At the default queue depth of 16,
66 of 72 paced runs passed.** The only failures were AV1 SDR8/HDR10 at
3440×1440/240 fps, where the replay's startup arrival-age limit caused loss.
The original C++17 build reproduced the same failure in 6/6 controlled runs.
With queue depth 32, the upgraded build passed all six follow-up runs without
loss or resets. These separate results do not turn the original failures into
passes. No new toolchain regression was observed in this coverage.

## Protocol and interpretation

- Six modes: 1920×1080 at 60/120 fps, 3440×1440 at 120/240 fps, and 3840×2160
  at 60/120 fps. Each uses AV1/HEVC and SDR8/HDR10, all 4:2:0.
- Hardware correctness first; then three serial 10-second paced runs per case.
  All encoding and builds finished before timed runs. No simultaneous decoder
  tests, software reference decoding, or sanitizer workloads ran during timing.
- Two frames in flight, queue depth 16, continuous fixture loops, first 120
  offered IDs excluded from steady latency statistics, default power preference,
  zero busy-wait polling. Counts include startup, warmup, and loss.
- Full output accounting, hardware validation and no errors/drops are required
  for harness PASS. Every passing run also achieved at least 99% of its requested
  rate, with no resets. The 99% rate check is a stated reporting threshold, not
  a new harness or presentation guarantee.
- Reported FPS includes the final drain. Slightly greater-than-requested rates
  reflect the finite run ending shortly after its last scheduled frame.
- Latency is measured from scheduled complete-AU arrival to the public decoder
  callback, with cold-generation and warmup outputs excluded. Lost frames are
  not in those latency distributions. Their accounting remains explicit.
- AC power; thermal state remained nominal (0) in all default and follow-up
  paced runs. No display, network, audio, or physical iOS/tvOS measurements.

The default matrix offered **86,400 frames** and displayed **86,040**. All 360
missing outputs belong to the six AV1 startup failures: 348 scheduler drops
plus 12 cancelled accepted submissions. Every other run had exact
accepted/completed/displayed accounting.

## Default queue-16 results

Ranges span the three repetitions; public p99 is the worst repetition, not a
pooled percentile. VT p50 measures VT call-to-callback, while public p99 also
includes arrival queueing and library work. Milliseconds throughout.

| Mode | Codec / variant | Paced pass | Decoded FPS range | VT p50 range (ms) | Worst public p99 (ms) |
| --- | --- | ---: | ---: | ---: | ---: |
| 1920×1080 / 60 | AV1 SDR8 | 3/3 | 60.089–60.093 | 1.607–1.668 | 6.362 |
| 1920×1080 / 60 | AV1 HDR10 | 3/3 | 60.086–60.089 | 1.684–1.891 | 6.840 |
| 1920×1080 / 60 | HEVC SDR8 | 3/3 | 60.088–60.088 | 1.594–1.640 | 3.999 |
| 1920×1080 / 60 | HEVC HDR10 | 3/3 | 60.088–60.089 | 1.660–1.769 | 3.181 |
| 1920×1080 / 120 | AV1 SDR8 | 3/3 | 120.077–120.081 | 1.527–1.554 | 6.081 |
| 1920×1080 / 120 | AV1 HDR10 | 3/3 | 120.074–120.077 | 1.677–1.698 | 6.772 |
| 1920×1080 / 120 | HEVC SDR8 | 3/3 | 120.080–120.088 | 1.487–1.505 | 3.060 |
| 1920×1080 / 120 | HEVC HDR10 | 3/3 | 120.073–120.079 | 1.627–1.697 | 3.196 |
| 3440×1440 / 120 | AV1 SDR8 | 3/3 | 120.072–120.077 | 1.995–2.076 | 11.810 |
| 3440×1440 / 120 | AV1 HDR10 | 3/3 | 120.067–120.072 | 2.142–2.185 | 13.123 |
| 3440×1440 / 120 | HEVC SDR8 | 3/3 | 120.071–120.076 | 1.959–1.990 | 4.177 |
| 3440×1440 / 120 | HEVC HDR10 | 3/3 | 120.064–120.075 | 2.060–2.156 | 4.559 |
| 3440×1440 / 240 | AV1 SDR8 | 0/3 | 234.042–234.046 | 1.934–1.955 | 11.659 |
| 3440×1440 / 240 | AV1 HDR10 | 0/3 | 234.037–234.052 | 2.044–2.084 | 12.958 |
| 3440×1440 / 240 | HEVC SDR8 | 3/3 | 240.034–240.052 | 1.907–1.982 | 6.707 |
| 3440×1440 / 240 | HEVC HDR10 | 3/3 | 240.039–240.051 | 1.987–2.126 | 6.418 |
| 3840×2160 / 60 | AV1 SDR8 | 3/3 | 60.081–60.083 | 2.669–2.714 | 17.863 |
| 3840×2160 / 60 | AV1 HDR10 | 3/3 | 60.078–60.082 | 2.834–2.849 | 18.288 |
| 3840×2160 / 60 | HEVC SDR8 | 3/3 | 60.082–60.083 | 2.574–2.629 | 6.441 |
| 3840×2160 / 60 | HEVC HDR10 | 3/3 | 60.081–60.082 | 2.690–2.808 | 6.708 |
| 3840×2160 / 120 | AV1 SDR8 | 3/3 | 120.061–120.067 | 2.624–2.633 | 17.576 |
| 3840×2160 / 120 | AV1 HDR10 | 3/3 | 120.060–120.072 | 2.755–2.796 | 18.474 |
| 3840×2160 / 120 | HEVC SDR8 | 3/3 | 120.063–120.068 | 2.526–2.552 | 6.252 |
| 3840×2160 / 120 | HEVC HDR10 | 3/3 | 120.060–120.066 | 2.618–2.759 | 6.666 |

A frame interval is 16.667 ms at 60 fps, 8.333 ms at 120 fps, and 4.167 ms at
240 fps. Several high-resolution AV1 cases, and HEVC at ultrawide 240 fps,
exceed that interval at public p99 despite maintaining average throughput.
The committed evidence includes per-run public p50/p95/p99, counts and fractions
above one frame interval, queue/scheduler tails, CPU use, and cold/startup data.
These measurements do not establish presentation latency or a 1 ms decoder.

## Ultrawide AV1 startup failure and controlled follow-up

All six default AV1 240 fps runs cancelled frames 0 and 1, discarded frames
2–59, and displayed **every frame 60–2399**. First successful output occurred
267.8–274.8 ms after the scheduled start. This is startup loss followed by
recovery at the next genuine random-access point, not continuing loss in the
warmed stream.

Initial admission-to-VT-submit was 60.8–68.0 ms; the initial completion/cancellation
arrived 76.3–82.9 ms after the first deadline. Parser preparation was only
0.030–0.052 ms. The remaining setup interval includes format/session/sample work;
these timestamps do not isolate session creation. At 240 fps, 16 frame intervals
permit 66.7 ms of arrival age. With two submissions pending, the next frame's
budget expires around 75 ms after stream start, causing reset and dependency-safe
recovery. Scheduler-lateness samples taken before waiting for capacity do not
include the entire capacity wait.

The ordinary cold-generation latency describes the **first successful frame 60
following recovery**, not the cancelled initial frame. The evidence separately
retains initial submission status/terminal latency and time to first success.

The follow-up used the same saved streams, two in-flight submissions, 240 fps,
2,400 offered AUs, continuous loops, warmup, power preference, and three repeats.
C++17 queue-16 and C++23 queue-32 runs alternated within each repetition. Both
used Apple Clang 21; the baseline source was commit
`5e482b0392df5d56008be51ca0f6ea6431f4f03a`.

| Variant | Build / queue | Pass | Outputs per run | FPS range | First successful output range (ms) |
| --- | --- | ---: | ---: | ---: | ---: |
| HDR10 | C++17 / 16 | 0/3 | 2340 / 2400 | 234.040–234.044 | 274.0–276.9 |
| HDR10 | C++23 / 32 | 3/3 | 2400 / 2400 | 240.043–240.043 | 81.9–83.3 |
| SDR8 | C++17 / 16 | 0/3 | 2340 / 2400 | 234.041–234.054 | 270.3–272.3 |
| SDR8 | C++23 / 32 | 3/3 | 2400 / 2400 | 240.043–240.048 | 78.4–82.7 |

Queue 32 expands permitted arrival age to 133.3 ms. It preserved all input during
startup and removed the reset/recovery delay in these six runs. It is a tested
headless-harness mitigation with more allowable startup backlog, not a faster
hardware decode mode or a universal live-client buffering policy. The decoder
and benchmark defaults were not changed. A future client could investigate a
bounded startup-specific allowance or earlier setup when stream configuration
is available, then retain its tighter steady-state policy.

## Evidence and reproduction

[Machine-readable evidence](evidence/toolchain-matrix.json) retains every default
and follow-up run, correctness results, commands, build/fixture hashes, and
unpooled timing distributions. Raw CSV/JSON/logs and generated fixtures remain
local under `results/toolchain-matrix/` and `fixtures/generated/`; they are ignored
by Git. These are synthetic fixture results, not live Sunshine/Apollo streams.

After building the Release tools and preparing all fixtures, the default matrix
can be reproduced with the existing benchmark entry point:

```sh
for mode in 1080p60 1080p120 3440x1440p120 3440x1440p240 4k60 4k120; do
  for variant in av1 av1-10bit-hdr hevc hevc-main10-hdr; do
    ./scripts/benchmark.sh --preset "$mode-$variant" \
      --build-dir build-upgrade-release --skip-build \
      --results-dir results/toolchain-matrix-repeat \
      --inflight 2 --queue-depth 16 --seconds 10 --repetitions 3 --warmup 120
  done
done
```

Use a separate results directory and `--queue-depth 32` for the two ultrawide AV1
240 fps mitigation cases; preserve the original failures. Generation commands for
the 14 newly created fixtures, hashes for all 24 fixtures, and baseline/follow-up
replay invocations are recorded in the evidence.

The [performance opportunities review](toolchain-performance-opportunities.md)
describes allocation, fragmented-input-copy, bit-reader, and future Swift-client
experiments. The matrix measures the upgraded build's behavior; it is not a
whole-matrix C++17-versus-C++23 speedup comparison. The baseline controls isolate
the observed startup failure only.
