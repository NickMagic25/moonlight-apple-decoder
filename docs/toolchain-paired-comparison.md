# Full paired C++17/C++23 comparison

**No median VT decode-time gate failed across the 24 configurations.** Three
initial latency flags all passed the longer, balanced confirmation. The AV1
ultrawide 240 fps startup failures remain present in both builds at queue 16;
both builds passed the separate queue-32 comparison without frame loss.
This supports no repeatable regression above the configured tolerances in these
measurements, while preserving the initial failures and smaller observed changes.

Measured on 2026-09-09 on the Apple M3 MacBook Pro (Mac15,3), macOS 26.6.2, with Xcode 26.6, Apple Clang 21, and the macOS 26.5 SDK. Both native builds used Release `-O3 -DNDEBUG`, the macOS 11 deployment target, and production settings (no sanitizers or VT experiments).

This extends the [earlier upgraded-build matrix](toolchain-matrix.md) with a full paired baseline. The baseline is `5e482b0392df5d56008be51ca0f6ea6431f4f03a` in C++17 mode. The candidate uses the upgraded C++23 decoder. Full executable/source/build identities, per-run data, and artifact hashes are in the [committed evidence index](evidence/toolchain-paired-comparison.json).

Each of the 24 codec/range/mode combinations had a correctness gate on both builds and three alternating 10-second paired paced trials: **48 correctness gates and 144 timed runs**. The same saved fixture bytes were used on both sides. All 48 correctness gates passed. The two AV1 ultrawide 240 fps configurations also have a separate paired queue-32 comparison (four correctness gates and 12 timed runs).

The three clean latency flags were then tested independently with six 20-second pairs each (six correctness gates and 36 timed runs), balancing which build ran first. Total: **58 correctness gates and 192 timed runs**. Original flags remain preserved.

## Decode latency

The median paired VT decode-time changes ranged from -4.53% to +4.55%. 0 of 24 median VT comparisons exceeded the configured allowance. The allowance is an increase greater than both 5% and 0.1 ms, applied independently to median/p95/p99 VT and public callback latency. These are observed gates, not statistical significance or equivalence tests.

Table values are medians across repetitions. The paired-change column is the median of the three paired percentage changes; it can differ from the percentage change between the two displayed medians. A `REGRESSION` gate can be caused by a tail or public-latency metric even when VT median changes little. `BASELINE_FAILURE` prevents a clean regression conclusion for a workload with existing startup loss.

| Mode | Codec / range | VT median ms, C++17 → C++23 | Paired change | VT p95 ms, C++17 → C++23 | VT p99 ms, C++17 → C++23 | Gate |
|---|---|---:|---:|---:|---:|---|
| 1920×1080@60 | AV1 / sdr | 1.736 → 1.657 | -4.53% | 1.981 → 1.947 | 6.105 → 5.913 | PASS |
| 1920×1080@60 | AV1 / hdr10 | 1.831 → 1.784 | -2.57% | 2.243 → 2.030 | 6.486 → 6.481 | PASS |
| 1920×1080@60 | HEVC / sdr | 1.703 → 1.701 | -0.11% | 2.142 → 2.172 | 3.017 → 2.840 | PASS |
| 1920×1080@60 | HEVC / hdr10 | 1.764 → 1.830 | +4.55% | 2.208 → 2.224 | 2.708 → 2.832 | REGRESSION |
| 1920×1080@120 | AV1 / sdr | 1.676 → 1.632 | +2.45% | 1.952 → 1.940 | 5.998 → 5.976 | REGRESSION |
| 1920×1080@120 | AV1 / hdr10 | 1.731 → 1.713 | +0.91% | 1.987 → 2.036 | 6.311 → 6.426 | PASS |
| 1920×1080@120 | HEVC / sdr | 1.595 → 1.623 | +1.57% | 2.017 → 2.065 | 2.734 → 2.715 | PASS |
| 1920×1080@120 | HEVC / hdr10 | 1.701 → 1.708 | +0.45% | 2.091 → 2.070 | 2.717 → 2.686 | PASS |
| 3440×1440@120 | AV1 / sdr | 2.184 → 2.106 | -3.56% | 2.449 → 2.471 | 11.588 → 11.550 | PASS |
| 3440×1440@120 | AV1 / hdr10 | 2.296 → 2.290 | -0.30% | 2.574 → 2.585 | 12.881 → 12.803 | PASS |
| 3440×1440@120 | HEVC / sdr | 2.096 → 2.087 | -0.56% | 2.704 → 2.631 | 3.856 → 3.857 | PASS |
| 3440×1440@120 | HEVC / hdr10 | 2.200 → 2.218 | +0.38% | 2.877 → 2.916 | 3.965 → 3.946 | PASS |
| 3440×1440@240 | AV1 / sdr | 2.104 → 2.075 | -1.30% | 2.418 → 2.357 | 11.554 → 11.556 | BASELINE_FAILURE |
| 3440×1440@240 | AV1 / hdr10 | 2.165 → 2.141 | -1.61% | 2.458 → 2.448 | 12.806 → 12.647 | BASELINE_FAILURE |
| 3440×1440@240 | HEVC / sdr | 2.032 → 2.000 | -0.83% | 2.547 → 2.528 | 6.198 → 6.168 | PASS |
| 3440×1440@240 | HEVC / hdr10 | 2.101 → 2.104 | +1.20% | 2.661 → 2.728 | 5.855 → 5.892 | PASS |
| 3840×2160@60 | AV1 / sdr | 2.801 → 2.763 | -2.44% | 3.102 → 2.979 | 17.585 → 17.434 | PASS |
| 3840×2160@60 | AV1 / hdr10 | 2.925 → 2.897 | -0.96% | 3.163 → 3.141 | 18.108 → 18.130 | PASS |
| 3840×2160@60 | HEVC / sdr | 2.645 → 2.675 | +1.15% | 3.149 → 3.060 | 5.783 → 5.847 | PASS |
| 3840×2160@60 | HEVC / hdr10 | 2.706 → 2.769 | +2.30% | 3.184 → 3.240 | 6.016 → 6.129 | PASS |
| 3840×2160@120 | AV1 / sdr | 2.662 → 2.629 | -0.01% | 3.061 → 2.903 | 17.298 → 17.319 | PASS |
| 3840×2160@120 | AV1 / hdr10 | 2.774 → 2.771 | +0.81% | 2.985 → 3.195 | 17.948 → 17.984 | REGRESSION |
| 3840×2160@120 | HEVC / sdr | 2.555 → 2.550 | -0.18% | 3.149 → 3.122 | 5.744 → 5.784 | PASS |
| 3840×2160@120 | HEVC / hdr10 | 2.715 → 2.696 | +0.68% | 3.181 → 3.178 | 6.064 → 5.989 | PASS |

### Observed latency threshold breaches

| Mode / codec / range | Metric | Median paired increase | Change | Case gate |
|---|---|---:|---:|---|
| 1920×1080@60 / hevc / hdr10 | vt_p99_ms | +0.177 ms | +6.91% | REGRESSION |
| 1920×1080@120 / av1 / sdr | public_median_ms | +0.145 ms | +6.98% | REGRESSION |
| 3440×1440@240 / av1 / sdr | public_p95_ms | +0.412 ms | +10.24% | BASELINE_FAILURE |
| 3440×1440@240 / av1 / hdr10 | public_p95_ms | +0.674 ms | +15.11% | BASELINE_FAILURE |
| 3840×2160@120 / av1 / hdr10 | vt_p95_ms | +0.210 ms | +7.03% | REGRESSION |

Every repetition and its direction/variation are retained in the evidence. A three-pair tail flag needs confirmation before attributing it to the language-mode change. Failed or cancelled startup frames are never removed from accounting to improve a latency result.

## Output accounting and startup

| Build, queue 16 | Timed runs passing functional/rate gates | Displayed / offered | Scheduler drops | Failed/cancelled completions |
|---|---:|---:|---:|---:|
| C++17 | 66/72 | 86041/86400 | 350 | 9 |
| C++23 | 67/72 | 86101/86400 | 290 | 9 |

The AV1 3440×1440 at 240 fps startup issue occurs in both builds. The 16-frame scheduled-arrival age allowance is about 66.7 ms; expensive initial submission can exceed it and force a reset plus a wait for a genuine random-access frame. This is separate from sustained hardware decode latency. The evidence records first successful output and the status/timing of the initial submission, including cancellation. A first successful output after recovery is not the original cold submission.

### Paired queue-32 comparison

Queue 32 permits about 133.3 ms of scheduled-arrival age. It supplies startup headroom; it does not make VideoToolbox decode faster and does not change the decoder or client defaults.

| Mode | Codec / range | VT median ms, C++17 → C++23 | Paired change | VT p95 ms, C++17 → C++23 | VT p99 ms, C++17 → C++23 | Gate |
|---|---|---:|---:|---:|---:|---|
| 3440×1440@240 | AV1 / sdr | 1.964 → 1.960 | -0.86% | 2.291 → 2.236 | 11.462 → 11.440 | PASS |
| 3440×1440@240 | AV1 / hdr10 | 2.114 → 2.105 | -0.64% | 2.486 → 2.364 | 12.698 → 12.734 | PASS |

Baseline: 14400/14400 outputs, 0 scheduler drops, 0 failed/cancelled completions across 6 trials.

Candidate: 14400/14400 outputs, 0 scheduler drops, 0 failed/cancelled completions across 6 trials.

## Balanced confirmation of the three clean latency flags

The confirmation configuration was fixed before these followup runs. Each case has six 20-second pairs; baseline and candidate each run first three times. The same fixtures, decoder settings, warmup, and 5%/0.1 ms allowances are retained. All 36 timed runs passed output and frame-rate checks, and all 18 aggregate latency gates passed. These are separate observations, not replacement measurements.

| Mode | Codec / range | VT median ms, C++17 → C++23 | Paired change | VT p95 ms, C++17 → C++23 | VT p99 ms, C++17 → C++23 | Gate |
|---|---|---:|---:|---:|---:|---|
| 1920×1080@60 | HEVC / hdr10 | 1.704 → 1.696 | +0.09% | 2.140 → 2.131 | 2.697 → 2.681 | PASS |
| 1920×1080@120 | AV1 / sdr | 1.567 → 1.540 | -1.91% | 1.827 → 1.754 | 5.950 → 5.935 | PASS |
| 3840×2160@120 | AV1 / hdr10 | 2.769 → 2.761 | -0.19% | 3.023 → 3.069 | 17.950 → 17.959 | PASS |

| Initial flagged metric | Initial paired increase | Confirmation paired change | Confirmation threshold exceeded |
|---|---:|---:|---|
| 1080p-1920x1080p60-hevc-hdr10-legacy / vt_p99_ms | +0.177 ms | -0.024 ms (-0.83%) | No |
| 1080p-1920x1080p120-av1-sdr-legacy / public_median_ms | +0.145 ms | -0.072 ms (-4.08%) | No |
| 4k-3840x2160p120-av1-hdr10-legacy / vt_p95_ms | +0.210 ms | +0.078 ms (+2.58%) | No |

The initial 1080p120 AV1 SDR public-median deltas were +0.163, −0.235, and +0.145 ms. The later run in each pair was slower, regardless of build. This is consistent with order/drift confounding; it does not identify its cause. The two native tail flags had positive deltas in all three initial pairs, which warranted this independent confirmation. The 4K120 AV1 HDR p95 remained slightly higher in confirmation (+0.078 ms), within the declared allowance; it was not reduced to zero. No statistical equivalence claim follows from either sample.

Individual confirmation pairs still varied: one of six HEVC p99 pairs and two
of six AV1 public-median pairs exceeded their corresponding allowance. The
configured median-paired rule passed; this does not mean every observation was
unchanged or faster.


## Reproduce and extend

Use the [YAML testing framework](testing-framework.md). The exact configurations are [full-matrix.yaml](../benchmarks/full-matrix.yaml) and [full-matrix-q32.yaml](../benchmarks/full-matrix-q32.yaml). These comparisons keep the prior encoder policy (`bitrate_kbps: null`) to preserve existing fixture bytes. Explicit bitrate targets are implemented and independently exercised by the small bitrate smoke tests; requested and measured bitrates are separate.

Raw manifests, payloads, commands, JSON, CSV, environment records, and JUnit reports are preserved locally under `results/toolchain-paired-comparison/` and `results/toolchain-paired-comparison-q32/`. The balanced followup is in `results/toolchain-paired-confirmation/`, configured by [toolchain-confirmation.yaml](../benchmarks/toolchain-confirmation.yaml). The hardware CI workflow archives the same complete directory layout.

## Framework validation

All 47 framework tests passed locally with the native encoder-timeout test
enabled; the native CTest suite passed 5/5. Five small real AV1/HEVC SDR/HDR/GOP
fixtures also passed bitrate generation, verified import, and hardware decoding.
The fixture-tool changes left the measured replay executable unchanged.

[Hosted CI](https://github.com/NickMagic25/moonlight-apple-decoder/actions/runs/34387010444)
passed on Linux and macOS, including native tool compilation, the actual
encoder-child timeout check, and the Swift package smoke. Physical hardware CI
is provided as a manual workflow; no self-hosted runners were registered in
this repository when checked. These performance measurements ran locally.

## Scope and limits

These measurements isolate native C++17 versus C++23 with the same compiler/SDK. Swift 6.3 and Swift 6 language-mode compatibility are covered by builds and the Swift package smoke; this replay path does not execute Swift. All timed runs report nominal thermal state, with AC attached at the start and end. No builds, encoders, software decoders, or sanitizer workloads ran concurrently with timed trials. The initial matrix shared the host with lightweight file checks, Python framework tests, and Git operations; no local tests ran during the balanced confirmation.

This is a headless, short synthetic-pattern comparison on one Mac. It does not measure Sunshine/network behavior, rendering, VSync, display HDR switching, audio, or actual monitor presentation at 240 Hz. Steady timing excludes 120 offered warmup frames and each generation’s first successful output, while all losses remain in functional/rate gates. Passing a tolerance does not exclude smaller regressions; tail flags and existing startup failures must remain visible.
