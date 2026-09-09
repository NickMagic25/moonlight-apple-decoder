# Decoder comparison

Overall: **FAIL** (paired).

Cases: 2; repetitions per build: 6; requested seconds per trial: 20; warmup offered frames: 120.

Alternating baseline/candidate order by repetition and case; identical fixture bytes; all correctness gates before serial paced timing; paired differences across repetitions, not pooled frames. Configured thresholds are observational gates, not statistical equivalence or significance tests. Steady samples exclude offered warmup IDs and first successful output per decoder generation. Failures and startup losses remain in accounting. Headless decode does not measure rendering or network.

Machine-readable evidence: [results.json](results.json). Bitrates use decimal megabits per second (1 Mbps = 1,000,000 bits/s). Requested bitrate is an encoder target; measured bitrate is the encoded payload rate, excluding transport overhead. A clean decode run outside the configured bitrate tolerance is INCONCLUSIVE for the requested workload.

| Case | Result | Requested Mbps | Measured Mbps | Baseline VT median / p95 / p99 ms | Candidate VT median / p95 / p99 ms | Paired median delta |
|---|---|---:|---:|---:|---:|---:|
| ultrawide-3440x1440p240-hevc-hdr10-50mbps | REGRESSION | 50.000 | 50.947 | 1.982 / 2.910 / 6.238 | 1.985 / 2.878 / 6.291 | 0.133% |
| ultrawide-3440x1440p240-hevc-hdr10-250mbps | BASELINE_FAILURE | 250.000 | 213.563 | 2.534 / 3.427 / 13.552 | 2.532 / 3.486 / 13.549 | 0.377% |

Threshold: the median paired increase must exceed both the absolute allowance (0.1 ms) and relative allowance (5.0% of baseline median) to flag a latency regression. Applied independently to VT and public completion median/p95/p99. All output accounting and delivered-rate gates must also pass.

Explicit bitrate targets require measured payload rate within ±20%. A null target retains the legacy encoder policy and does not impose a bitrate coverage gate.

A PASS means the configured gates passed in this sample. It does not prove absence of a smaller regression. Public latency includes scheduled arrival, queuing and callback delivery; VT latency ends at the internal decoder callback.

## ultrawide-3440x1440p240-hevc-hdr10-50mbps

Status: REGRESSION

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 50.947 Mbps. Encoder target: 50.000 Mbps; measured/target: 101.9%.

- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=59; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 4800 / 4800 | 240.024 | 0 / 0 | 63.642 |
| candidate / 1 | 4800 / 4800 | 240.023 | 0 / 0 | 71.427 |
| candidate / 2 | 4800 / 4800 | 240.024 | 0 / 0 | 69.680 |
| baseline / 2 | 4800 / 4800 | 240.023 | 0 / 0 | 69.635 |
| baseline / 3 | 4800 / 4800 | 240.026 | 0 / 0 | 74.013 |
| candidate / 3 | 4740 / 4800 | 237.023 | 59 / 1 | 264.278 |
| candidate / 4 | 4800 / 4800 | 240.023 | 0 / 0 | 69.443 |
| baseline / 4 | 4800 / 4800 | 240.022 | 0 / 0 | 68.668 |
| baseline / 5 | 4800 / 4800 | 240.023 | 0 / 0 | 70.651 |
| candidate / 5 | 4800 / 4800 | 240.025 | 0 / 0 | 72.860 |
| candidate / 6 | 4800 / 4800 | 240.024 | 0 / 0 | 70.118 |
| baseline / 6 | 4800 / 4800 | 240.024 | 0 / 0 | 72.680 |

## ultrawide-3440x1440p240-hevc-hdr10-250mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 213.563 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.4%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=54; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=54; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 4: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=54; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 5: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 5: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=54; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 6: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 6: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=54; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 4800 / 4800 | 240.006 | 0 / 0 | 65.783 |
| baseline / 1 | 4742 / 4800 | 237.111 | 56 / 2 | 71.941 |
| baseline / 2 | 4745 / 4800 | 237.263 | 54 / 1 | 66.981 |
| candidate / 2 | 4745 / 4800 | 237.259 | 54 / 1 | 67.467 |
| candidate / 3 | 4744 / 4800 | 237.209 | 55 / 1 | 68.414 |
| baseline / 3 | 4744 / 4800 | 237.216 | 55 / 1 | 68.646 |
| baseline / 4 | 4745 / 4800 | 237.265 | 54 / 1 | 67.518 |
| candidate / 4 | 4800 / 4800 | 240.022 | 0 / 0 | 65.758 |
| candidate / 5 | 4744 / 4800 | 237.203 | 55 / 1 | 68.391 |
| baseline / 5 | 4744 / 4800 | 237.218 | 54 / 2 | 68.036 |
| baseline / 6 | 4743 / 4800 | 237.165 | 55 / 2 | 69.117 |
| candidate / 6 | 4744 / 4800 | 237.205 | 54 / 2 | 68.099 |

