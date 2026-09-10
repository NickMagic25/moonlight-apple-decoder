# Mbps matrix validation

The framework now accepts decimal `bitrate_mbps` and includes all six requested
resolution/frame-rate modes at 50, 100, 250, and 350 Mbps, for AV1/HEVC and
SDR/HDR10: **96 workloads**. Each execution produces human-readable `report.md`,
machine-readable `results.json`, and JUnit XML, alongside native JSON/CSV traces
and provenance. See the [configuration](../benchmarks/bitrate-matrix.yaml) and
[local/CI instructions](testing-framework.md).

The complete comparison finished all **192 correctness checks and 576 timed
trials**. Every correctness check passed an independent software reference with
zero pixel difference. The full run is **not an all-pass performance result**:
50 workloads passed every gate, 24 were inconclusive, 21 had baseline failures,
and one was flagged by an isolated candidate startup failure.

## Focused HEVC rerun — September 9, 2026

The requested repeat covers **3440×1440 at 240 fps and 3840×2160 at 60 fps**,
HEVC SDR/HDR10, and 50/100/250/350 Mbps targets: 16 workloads. It reuses the
same verified compressed fixtures and C++17/C++23 replay binaries as the full
comparison, with three 10-second trials per build and 120 warmup offered
frames. The candidate source revision is `381f897`; the intervening reporting
and Qt overlay edits did not change the native replay binary.

All **32 correctness checks passed with zero pixel difference**. All **96 timed
trials completed**, each recording nominal thermal state at completion. The separate
[Markdown report](evidence/hevc-focused-rerun-20260909/report.md),
[machine-readable results](evidence/hevc-focused-rerun-20260909/results.json),
and [Moonlight timing means](evidence/hevc-focused-rerun-20260909/moonlight-decode-times.json)
preserve this rerun independently of the original full and confirmation runs.

| Mode | PASS | INCONCLUSIVE | BASELINE_FAILURE | Timed delivery failures, C++17 / C++23 |
|---|---:|---:|---:|---:|
| 3440×1440 at 240 fps | 0 | 0 | 8 | 21/24 / 24/24 |
| 3840×2160 at 60 fps | 6 | 2 | 0 | 0/24 / 0/24 |

At **4K 60 fps**, all 48 trials delivered every frame. The six SDR/HDR10
workloads at 100, 250, and 350 Mbps passed all configured gates. The two 50 Mbps
fixtures remain inconclusive because their measured rates are 60.820 Mbps
(SDR) and 83.905 Mbps (HDR10), outside the ±20% tolerance. The SDR 50 Mbps
case also exceeded the queue-inclusive public p95 latency threshold: median
paired increase **1.005 ms / 10.23%**, against a 0.491 ms allowance. Its
INCONCLUSIVE status takes precedence over that latency flag. No 4K workload
exceeded the VT median/p95/p99 thresholds.

At **ultrawide 240 fps**, delivery failed in both builds across all eight
workloads. These measurements cannot establish a clean no-regression result.
The HDR10 350 Mbps case additionally exceeded the VT p95 latency threshold:
median paired increase **0.222 ms / 5.19%**, against a 0.207 ms allowance.
That flag remains descriptive because delivery failed. The previous full run's
same 16 workloads had 9 PASS, 2 INCONCLUSIVE, 4 BASELINE_FAILURE, and 1 REGRESSION;
this repeat does not clear those results or identify the cause of the changed
failure frequency.

The [loss audit](evidence/hevc-focused-rerun-20260909/loss-audit.md) locates all
2,659 missing outputs in frame IDs 0–59: 2,583 scheduler drops and 76
failed/cancelled completions. Every one of the 45 failing trials delivered
frame 60 and every post-warmup frame (IDs 120–2399). Startup losses still count
as delivery failures; this localization does not identify their cause.

An [independent metric audit](evidence/hevc-focused-rerun-20260909/metric-audit.md)
recomputed all 96 timed traces and matched the reported means, sample counts,
weighted case means, and six latency distributions and comparisons. There
are 141,341 frame-ready samples and 141,108 submission samples; the 233
missing API-return timestamps are excluded only from submission timing.

Before hardware timing, the framework suite ran 86 tests: 85 passed and the
optional real-encoder process test was skipped because `MAV_FIXTURE_TOOL` was
not set. This native replay rerun does not add runtime validation of the Qt
overlay, presentation, network, or physical iPhone/Apple TV behavior. Generated
reports and provenance are archived byte for byte in a
[separate manifest](evidence/hevc-focused-rerun-20260909/archive.json); raw traces,
native JSON, logs, fixtures, and harness snapshots remain under
`results/hevc-focused-rerun-20260909` locally.

## Full comparison

Read the [generated Markdown report](evidence/bitrate-matrix/full/report.md) or
the [machine-readable results](evidence/bitrate-matrix/full/results.json).
The [original report](evidence/bitrate-matrix/full/report-original.md) is
preserved byte for byte. The enhanced report adds Moonlight decode-time means
from saved traces; its original statuses and failed trials are unchanged.

| Mode | PASS | INCONCLUSIVE | BASELINE_FAILURE | REGRESSION |
|---|---:|---:|---:|---:|
| 1920×1080 at 60 fps | 16 | 0 | 0 | 0 |
| 1920×1080 at 120 fps | 12 | 4 | 0 | 0 |
| 3440×1440 at 120 fps | 7 | 6 | 3 | 0 |
| 3440×1440 at 240 fps | 3 | 0 | 12 | 1 |
| 3840×2160 at 60 fps | 8 | 6 | 2 | 0 |
| 3840×2160 at 120 fps | 4 | 8 | 4 | 0 |

All six timed trials passed native delivery and trace validation in 74
workloads: 50 met bitrate coverage and 24 decoded cleanly at rates outside the
target tolerance. None exceeded a configured latency gate. Twenty other workloads repeatedly failed
frame delivery in both builds across all three repetitions. Their measurements
cannot establish a clean performance result. Several of those fixtures were
encoded above the requested bitrate, so their limits must be interpreted at
the **measured** rate shown in the report.

Across the full run, 454 timed trials passed the native/trace/delivery checks
and 122 failed: 227 passes and 61 failures per build. The run offered 691,200
frames and delivered 627,370, with 61,308 scheduler drops and 2,522
failed/cancelled/dropped completions. No failures were removed as warmup.
All 576 timed trials recorded nominal thermal state.

## Decode time in Moonlight

The native Apple adapter displays **Frame-ready mean (VT submit -> callback)**: the arithmetic
mean of VideoToolbox submission-to-callback durations, including startup and
warmup. The enhanced [full report](evidence/bitrate-matrix/full/report.md#decode-time-shown-by-moonlight)
and [confirmation report](evidence/bitrate-matrix/confirmation/report.md#decode-time-shown-by-moonlight)
now include this metric and **VT submission mean (submit -> return)** for both
builds, per trial and pooled per workload. Frame-ready is the existing
submit-to-callback metric with a clearer label; the JSON key `native_vt` is
unchanged. The new `native_submission` field measures API-call duration.
They also include a separately labeled queue-inclusive proxy for the regular
Qt/FFmpeg overlay's broader **Average decoding time** metric. None is a live
Moonlight session measurement; the native columns apply the adapter's actual
formulas to the recorded replay outputs. Submission and frame-ready means share
a start time and must not be added together; a smaller submission number does
not demonstrate earlier frame availability or presentation.

For example, these are the full-run native means for **HEVC SDR with a 100 Mbps
encoder target**, in milliseconds:

| Mode | Measured Mbps | C++17 submission / frame-ready ms | C++23 submission / frame-ready ms | Original status |
|---|---:|---:|---:|---|
| 1920×1080 at 60 fps | 85.816 | 0.815 / 2.990 | 0.807 / 2.971 | PASS |
| 1920×1080 at 120 fps | 101.643 | 0.695 / 2.205 | 0.698 / 2.212 | PASS |
| 3440×1440 at 120 fps | 98.189 | 0.658 / 2.518 | 0.568 / 2.359 | PASS |
| 3440×1440 at 240 fps | 95.374 | 0.579 / 2.218 | 0.572 / 2.207 | PASS |
| 3840×2160 at 60 fps | 92.471 | 0.740 / 3.650 | 0.756 / 3.675 | PASS |
| 3840×2160 at 120 fps | 122.563 | 0.683 / 3.305 | 0.680 / 3.301 | INCONCLUSIVE |

The last fixture exceeded the allowed bitrate tolerance; its otherwise clean
decoding does not establish coverage at the requested target. All 96 workloads,
including AV1, HDR10, and the other bitrate targets, remain in the full report.

Comparisons between frame rates also change the compressed workload. At a fixed
Mbps target, higher frame rates generally leave fewer encoded bytes per frame.
These short synthetic fixtures additionally repeat their initial encoder
rate-control burst. For the ultrawide HEVC SDR 100 Mbps cases, the first 12
encoded frames occupy 10% of the 120 fps fixture but 5% of the 240 fps fixture.
That expensive block averages 6.671 versus 6.628 ms, while the remaining frames
average 1.879 versus 1.974 ms. The lower overall mean therefore reflects different
frame weighting as well as different encoded bytes. Each C++17/C++23 pair still
receives identical bytes, but the cross-rate rows do not isolate an intrinsic
decoder speedup from increasing frame rate.

The new columns were derived offline from **600 existing timed CSVs** after
verifying their hashes and native JSON against the original results. They cover
627,370 eligible frame-ready samples in the full run and 114,580 in confirmation.
Submission timing has 627,346 and 114,574 samples respectively: 24 full-run and
6 confirmation completions did not capture a valid API-return timestamp. A
callback can arrive before the API call returns. These outputs remain in the
frame-ready population, and their missing submission times are not replaced
with zeros or inferred values. The two sample counts are explicit in each
report and are independent of the existing delivery gates.
Each case mean divides the sum of durations by the number of eligible outputs
across separate trials, including each trial's startup. It does not average
medians or give unequal-sized trials equal weight. Failed/cancelled outputs add
no decode sample, and the original delivery and latency gates remain unchanged.
**No tests, benchmarks, builds, or decoding were rerun for this report update.**
The adapter's two-counter overlay change received a Clang syntax-only check
with the existing Qt consumer's C++17 flags and headers. The application was
not rebuilt or launched, so the updated overlay has no new runtime validation.

Machine-readable supplemental means, counts, integer duration sums, and
provenance are available for the
[full run](evidence/bitrate-matrix/full/moonlight-decode-times.json) and
[confirmation](evidence/bitrate-matrix/confirmation/moonlight-decode-times.json).
The original `results.json`, plans, traces, and audit results remain unchanged;
the [archive manifest](evidence/bitrate-matrix/archive.json) distinguishes
original evidence from enhanced reports. Existing audit hashes for `report.md`
refer to the preserved `report-original.md` copies. See the
[offline refresh command](testing-framework.md#reading-the-evidence) for reuse.

## Startup follow-up

Two HEVC HDR10 workloads at 3440×1440/240 fps each had one failing trial:

| Requested bitrate | Affected trial | Outputs / offered | Startup loss | Recovery |
|---|---|---:|---|---|
| 50 Mbps | Baseline, repetition 1 | 2,341 / 2,400 | Cancelled ID 1; scheduler IDs 2–59 | ID 60 at 261.091 ms |
| 250 Mbps | Candidate, repetition 3 | 2,345 / 2,400 | Cancelled ID 5; scheduler IDs 6–59 | ID 60 at 265.041 ms |

Both affected trials delivered every one of the 2,280 post-warmup frames.
The other five trials for each workload delivered all 2,400 frames. This
localizes the observed losses to startup; it does not identify their cause.
The [startup audit](evidence/bitrate-matrix/startup-audit/report.md) preserves
the trace identities, timing, accounting, and evidence hashes.

The [longer confirmation](evidence/bitrate-matrix/confirmation/report.md)
used six balanced 20-second pairs per workload, identical fixture bytes, and
unchanged decoder settings and binaries. Its
[machine-readable results](evidence/bitrate-matrix/confirmation/results.json)
retain another **4 passing correctness checks and 24 timed trials**.
Thirteen timed trials passed and 11 failed; no latency gate was exceeded.
The 11 failed trials lost frames only before ID 60, recovered around
261–264 ms, and delivered every one of their 4,680 post-warmup frames.

| Target | Baseline failures / trials | Candidate failures / trials | Confirmation status |
|---|---:|---:|---|
| 50 Mbps | 0 / 6 | 1 / 6 | REGRESSION |
| 250 Mbps | 6 / 6 | 4 / 6 | BASELINE_FAILURE |

The follow-up did **not** clear these workloads. Together, the original and
confirmation runs reproduce delivery failures on both builds at each bitrate.
Descriptive failure counts across the nine launches per build are 1/9 on each
build at 50 Mbps, and 6/9 baseline versus 5/9 candidate at 250 Mbps; the original
and follow-up trials have different durations.
They do not isolate a new C++23-specific failure, establish a statistically
equivalent failure rate, or justify an all-pass streaming claim. The observed
decode-time gates did not regress in clean workloads, while startup and
overload failures remain explicit limitations of this result.

## Bitrate coverage and fixture validation

One Mbps means 1,000,000 bits per second. Only **58 of 96 fixtures** achieved a
measured payload rate within the configured ±20% of the requested target.
The remaining 38 misses include 24 otherwise clean workloads, which are marked
INCONCLUSIVE, and 14 workloads that also failed delivery. For example, the
4K/60 fps HEVC HDR10 fixture requested 50 Mbps but measured 83.905 Mbps.
An encoder target is not evidence that the decoder sustained that exact rate.

Simple gradients did not produce the requested high rates. Explicit-bitrate
generation therefore uses deterministic seeded luma noise. Lossy encoding can
damage synthetic source markers even when the decoder is correct, so the
framework now compares every visible Y/U/V sample with an independent FFmpeg
software decode. Both builds use identical compressed bytes and reference
pixels. The original encoder manifest is retained alongside the derived
validation manifest; changing a pattern label without a complete reference
comparison cannot pass the framework.

The 192 checks compared **205,037,568,000 samples across 26,880 outputs**, with
maximum code error zero. All hardware, format, Metal/IOSurface, and lifecycle
checks passed, including 96 HDR10 checks. The independent
[correctness audit](evidence/bitrate-matrix/correctness-audit/report.md) verified
the native evidence hashes, sample counts, and source-manifest provenance.
Temporary raw references were deleted after both builds' correctness checks;
all reference work completed before timing started.

This comparison imported previously generated fixtures: 48 AV1 fixtures used
the realtime AOM encoding policy, 47 HEVC fixtures used realtime VideoToolbox,
and the 4K/60 Hz HEVC HDR10 50 Mbps fixture used offline VideoToolbox after the
realtime encoder dropped frames during preparation. The current generator uses
offline encoding for new explicit-bitrate HEVC requests. These provenance
differences are recorded, and each baseline/candidate pair still receives
identical bytes. A fresh run of the checked-in preset may achieve different
rates and must pass its own coverage gates.

## Reproduction and limits

The full run took place on an Apple M3 Mac15,3 running macOS 26.6.2, on AC power,
from 2026-09-09 20:14:21 to 22:03:51 UTC. Both native builds used Apple Clang
21.0.0, SDK 26.5, Release optimization, macOS 11 deployment target, and disabled
sanitizers/VideoToolbox experiments. The public C ABI and production decoder
settings were unchanged.

- C++17 baseline source: `5e482b0392df5d56008be51ca0f6ea6431f4f03a`.
- Baseline replay SHA-256: `fb2219df1435b4c0a95a6c6e897564eddfec4a405be7fd1d2804e4ac72371242`.
- C++23 replay SHA-256: `d959929f93d79269e1b41e38f4fe4f24ca32def291a90d72621ebd21849146da`.
- Full-run harness snapshot: `17f4daf`; exact script hashes, source/build identity,
  commands, and fixture imports are in the archived plan and results.

Each workload ran three 10-second trials per build with alternating order,
120 offered warmup frames, two in-flight access units, queue depth 16, GOP 60,
and a 180-second timeout. Steady latency excludes warmup and the first output
of each decoder generation; delivery accounting includes all offered frames.
The six latency gates cover VT and public completion median/p95/p99. A
median paired increase must exceed both 5% of the median baseline repetition
value for that statistic and 0.1 ms to flag a
latency regression. These are observational gates, not statistical equivalence
tests or a guarantee of zero performance change.

The checked-in evidence contains both report formats, the exact run plan and
configuration, and audits. The complete local result directories also retain
compressed fixtures, raw frame CSVs, native JSON, logs, and harness snapshots;
the physical CI workflow uploads those artifacts. Raw fixture payloads and
frame traces are not duplicated into Git. Reproducing byte-identical imports
requires the retained fixtures and recorded software toolchain; use the
checked-in preset for a fresh local or CI run.

This is headless decoding on the tested Mac. It does not measure network,
presentation, or physical iPhone/Apple TV performance. Swift 6.3 compatibility
is validated separately from the native C++ replay path. The earlier
[toolchain comparison](toolchain-paired-comparison.md) remains evidence for its
own workloads and must not be generalized to unvalidated bitrate targets.
