# Measured headless performance

These are physical Apple M3 (`Mac15,3`) results from macOS 26.6.2, SDK 26.5, Release arm64 builds, on AC power. The observed thermal state was nominal. All fixtures are generated moving images with reference-dependent inter frames and periodic keyframes; each backend used identical saved compressed bytes and equivalent 8/10-bit YUV IOSurface output. Hardware selection was verified. No encoder, build, software reference decoder or sanitizer ran alongside these timed runs.

The final evidence contains **59 timed runs**: 54 in the main matrix, two 120-second runs and three controlled queue-limit runs. The initial pilot exposed a scheduler difference and was excluded from these results; both final backends use the same capped 1-ms waits against original absolute arrival deadlines. Sessions stay alive across keyframe-aligned loops with rebased media timestamps. Each short setting has three 10-second repetitions and 120 warmup submissions. Cold outputs are excluded from steady latency distributions, while every offered/admitted/completed/displayed/lost frame remains counted.

The **1.0-ms median VT latency stretch target was not met** in these paced configurations. Native caller-visible median latency was lower than the optional FFmpeg VT baseline in the tested 1080p120 cases. This is a standalone API result, not a live Moonlight or presentation result.

## Default in-flight limit of two

All latency values are milliseconds. Each displayed percentile is the median of that percentile across the three repetitions, not a pooled percentile. Full per-run count/mean/median/p95/p99/min/max distributions and hashes are retained in [machine-readable evidence](evidence/benchmarks.json). “Public AU→output” ends at the native public callback entry or FFmpeg receive-frame return. Native VT call→callback is a different, internal interval; exact equivalent FFmpeg VT boundaries are unavailable.

| Configuration | Native VT p50 | p95 | p99 | Native public AU→output p50 | FFmpeg public AU→output p50 | Native displayed / offered | Native result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1080p120 AV1 SDR8 | 1.543 | 1.747 | 5.864 | 1.710 | 2.588 | 3,600 / 3,600 | 3/3 PASS |
| 1080p120 AV1 HDR10 | 1.675 | 1.931 | 6.363 | 1.949 | 2.449 | 3,600 / 3,600 | 3/3 PASS |
| 1080p120 HEVC Main | 1.542 | 1.904 | 2.611 | 1.821 | 2.321 | 3,600 / 3,600 | 3/3 PASS |
| 1080p120 HEVC Main10 HDR | 1.690 | 2.116 | 2.668 | 2.138 | 2.615 | 3,600 / 3,600 | 3/3 PASS |
| 3440×1440p240 AV1 HDR10 | 2.093 | 2.381 | 12.641 | 2.288 | 2.831 | 7,020 / 7,200 | 0/3 PASS |
| 3440×1440p240 HEVC Main10 HDR | 2.020 | 2.571 | 5.548 | 2.287 | 2.670 | 7,200 / 7,200 | 3/3 PASS |

FFmpeg displayed every offered AU in these baseline runs. It does **not** implement the native scheduler's age-based drop/reset policy, so the AV1 stress result needs the startup qualification below. Steady latency values from that failed native configuration are not evidence of a successful loss-free full run. Loss-free 1080p runs sustained approximately 120 fps; loss-free ultrawide HEVC runs approximately 240 fps. Count/duration values differ slightly from nominal because the interval after the final scheduled frame is not an additional offered frame.

## In-flight and power experiments

For 1080p120 SDR, all 18 native in-flight experiments completed every offered frame. Median VT latency across three repetitions:

| Codec | In-flight 1 | In-flight 2 | In-flight 3 |
| --- | ---: | ---: | ---: |
| AV1 SDR8 | 1.605 | 1.543 | 1.596 |
| HEVC Main | 1.566 | 1.542 | 1.609 |

Two remains the library default; these results do not justify a general increase. An in-flight count is an unresolved-submission bound, not a fixed number of frame intervals of delay.

| 1080p120 HDR codec | Default power preference: VT p50 | Disabled preference: VT p50 | Setter / read-back |
| --- | ---: | ---: | --- |
| AV1 HDR10 | 1.675 | 1.624 | Write accepted (`0`); effective value unavailable (`-1`) |
| HEVC Main10 HDR | 1.690 | 1.624 | Write accepted (`0`); effective value unavailable (`-1`) |

All six disabled-preference runs were loss-free. Their small median shifts overlap normal repetition variation, so no reliable power-related benefit is established. The real-time hint was enabled; temporal processing and 1× real-time playback were off. Only canonical range/depth-preserving bi-planar formats were tested. Ordered-format sweeps, full-range streams and optional thread/synchronous controls were not benchmarked.

## AV1 ultrawide startup and bounded-queue experiment

With the default 16-frame age bound (about 66.67 ms at 240 fps), all three native short runs lost exactly display IDs **0–59**. There were 175 scheduler drops and five cancelled accepted submissions across the three runs. IDs **60–2399** produced every expected image. The complete runs correctly remain **FAIL**.

The original first submissions reached terminal callbacks after 79.1–86.8 ms. The parser-end→VT-submit interval was 62.8–70.7 ms and VT-submit→callback was 15.9–16.1 ms. This trace locates most startup time before VT submission, in a phase containing sample/session configuration and other work; it does not isolate its root cause. The normal cold-output distribution begins at the first *successful* displayed output after recovery, so it must not replace these cancelled first-submission measurements.

FFmpeg's first output took 76.2–84.6 ms and its initial admission backlog reached 72.1–80.5 ms. It kept those late AUs instead of applying the native 66.67-ms reset/drop bound. Its 2400/2400 count therefore does not establish that native sustained decode capacity is lower.

A controlled follow-up changed only `--queue-depth 32`, permitting at most about 133.33 ms of arrival age. In-flight stayed two, offered rate stayed 240 fps, and encoded quality and bytes stayed identical. All three runs decoded **2400/2400**, without resets, drops, rejection, cancellation or trace overflow. Cold caller-visible latency was 67.5–82.2 ms. Median steady VT latency was 2.120 ms and caller-visible median about 2.31 ms. This supports a startup admission-budget explanation for the original failures. It is a bounded-backlog tradeoff, not a reduction in decode latency. The default was deliberately left unchanged; the actual Qt/common-c queue and live session startup still require separate testing.

## Two-minute continuous runs

| 3440×1440p240 HDR codec | Displayed / offered | VT p50 / p95 / p99 (ms) | Decoded rate | Result |
| --- | ---: | ---: | ---: | --- |
| AV1 HDR10 | 28,740 / 28,800 | 2.075 / 2.415 / 12.647 | 239.50 fps | FAIL |
| HEVC Main10 HDR | 28,800 / 28,800 | 2.017 / 2.647 / 5.749 | 240.00 fps | PASS |

Both runs used the default 16-frame age bound and stayed at nominal thermal state. AV1 again lost only the first 60 display IDs (58 scheduler drops and two cancellations), then produced every remaining image. HEVC had no loss. All accepted work completed, outstanding depth never exceeded two and no trace records overflowed. Two minutes on this Mac does not establish another device's long-term thermal behavior.

A separate intentional-overload check offered 2400 AV1 AUs at 4000 fps with a bounded 64-interval queue: 401 accepted/completed, 343 displayed, 1999 scheduler/dependency drops and 58 cancelled/dropped completions. It correctly returned FAIL, recovered repeatedly, kept peak outstanding at two and lost no trace records. Its survivor timings are not treated as a performance success.

## Reproduce and inspect

```sh
./scripts/benchmark.sh --preset 1080p120-av1 --inflight 1,2,3 --ffmpeg-baseline
./scripts/benchmark.sh --preset 1080p120-hevc --inflight 1,2,3 --ffmpeg-baseline
./scripts/benchmark.sh --preset 1080p120-av1-10bit-hdr --ffmpeg-baseline
./scripts/benchmark.sh --preset 1080p120-hevc-main10-hdr --ffmpeg-baseline
./scripts/benchmark.sh --preset 3440x1440p240-av1-10bit-hdr --ffmpeg-baseline
./scripts/benchmark.sh --preset 3440x1440p240-hevc-main10-hdr --ffmpeg-baseline
./scripts/benchmark.sh --preset 1080p120-av1-10bit-hdr --power 0
./scripts/benchmark.sh --preset 1080p120-hevc-main10-hdr --power 0
./scripts/benchmark.sh --preset 3440x1440p240-av1-10bit-hdr --seconds 120 --repetitions 1 --results-dir results/thermal
./scripts/benchmark.sh --preset 3440x1440p240-hevc-main10-hdr --seconds 120 --repetitions 1 --results-dir results/thermal
./scripts/benchmark.sh --preset 3440x1440p240-av1-10bit-hdr --queue-depth 32 --results-dir results/queue32
python3 scripts/summarize-benchmarks.py
python3 scripts/summarize-benchmarks.py --input results/thermal --output docs/evidence/thermal.json
python3 scripts/summarize-benchmarks.py --input results/queue32 --output docs/evidence/queue32.json
```

Use `--skip-build` with an already verified Release build, as in the measured matrix. The optional FFmpeg tool must first be built using `MAV_FFMPEG_ROOT`; see [build and measurement commands](benchmarks.md). Full local CSV/JSON are under `results/benchmarks`, `results/thermal` and `results/queue32`; portable snapshots retain per-run distributions, fixture/binary/source hashes and environment in [main evidence](evidence/benchmarks.json), [thermal evidence](evidence/thermal.json) and [queue experiment](evidence/queue32.json). Independent recomputation reproduced both backends' original percentiles exactly. Supplemental caller-visible distributions are derived from the saved native `sink_entry_ns` and FFmpeg receive timestamps.

Queue wait includes scheduler lateness and admission/capacity delay. Parser preparation excludes later sample/session construction; the supplemental submit-entry→VT-submit interval includes that preparation. All latency phases use the same monotonic clock; media PTS remains separate. Renderer, GPU, presentation and live-client A/B timings are **NOT MEASURED**.

The provided 1440p120/240 and 4K60/120 presets were not part of this measured matrix. A 4:4:4 request explicitly returned BLOCKED because this native library/adapter implements 4:2:0; that is an implementation boundary, not a finding that M3 hardware cannot decode 4:4:4. No image format, resolution, bit depth or input rate was silently substituted.
