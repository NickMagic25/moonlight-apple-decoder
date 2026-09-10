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

## Decode time shown by Moonlight

The native Apple adapter displays **“Frame-ready mean (VT submit -> callback)”**: the arithmetic mean from VideoToolbox submission to its decoded-image callback, in milliseconds. This is the same measurement previously labeled “VT submit-to-callback mean”; the machine-readable key remains `native_vt`. These values include cold/startup and warmup outputs, matching the adapter’s cumulative counter; they are not the steady-state medians in the table above. Case means below sum durations and divide by eligible output counts across all captured timed trials, so trials with different output counts are weighted correctly. Each trial includes its own startup. Per-trial means and their sample counts appear below each case.

**“VT submission mean (submit -> return)”** separately measures how long the VideoToolbox API call takes to return. It is not completed decoding or presentation latency. Submission and frame-ready intervals share the same start; do not add their means or interpret their difference as hardware execution time. A callback can occur before the call returns, so some saved completions lack a return timestamp. Those outputs remain eligible for frame-ready timing but are omitted from submission timing, with independent sample counts shown explicitly. Missing return timestamps are never replaced with zero or a callback timestamp.

The regular Qt/FFmpeg **“Average decoding time”** includes input-queue and decoder delivery time and uses recent statistics windows. The queue-inclusive proxy below uses recorded complete-frame arrival to the harness output callback. It approximates that broader boundary; it is not an actual live overlay reading and does not include the app’s output wrapping or rendering. The native frame-ready column matches this repository’s native Apple overlay formula. On Intel/other GPU backends, FFmpeg output-surface delivery need not guarantee GPU completion; the proxy does not establish a common hardware-readiness endpoint across platforms.

Dropped/cancelled frames add no decode sample, so a low mean does not imply smooth delivery. Original PASS/FAIL, bitrate coverage and latency gates are unchanged. A dash means the necessary trace-derived values are unavailable. Machine-readable means and sample counts: [moonlight-decode-times.json](moonlight-decode-times.json).

| Case | Result | VT submission mean ms (baseline / candidate) | Frame-ready mean ms (baseline / candidate) | Queue-inclusive proxy ms (baseline / candidate) | Submission samples (baseline / candidate) | Frame-ready samples (baseline / candidate) |
|---|---|---:|---:|---:|---:|---:|
| ultrawide-3440x1440p240-hevc-hdr10-50mbps | REGRESSION | 0.620 / 0.611 | 2.128 / 2.115 | 2.540 / 2.503 | 28799 / 28738 | 28800 / 28740 |
| ultrawide-3440x1440p240-hevc-hdr10-250mbps | BASELINE_FAILURE | 0.661 / 0.678 | 2.738 / 2.764 | 3.502 / 3.590 | 28461 / 28576 | 28463 / 28577 |

## ultrawide-3440x1440p240-hevc-hdr10-50mbps

Status: REGRESSION

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 50.947 Mbps. Encoder target: 50.000 Mbps; measured/target: 101.9%.

- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=59; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 4800 / 4800 | 240.024 | 0 / 0 | 63.642 | 0.623 (4800) | 2.136 (4800) | 2.519 |
| candidate / 1 | 4800 / 4800 | 240.023 | 0 / 0 | 71.427 | 0.627 (4800) | 2.142 (4800) | 2.557 |
| candidate / 2 | 4800 / 4800 | 240.024 | 0 / 0 | 69.680 | 0.636 (4800) | 2.155 (4800) | 2.560 |
| baseline / 2 | 4800 / 4800 | 240.023 | 0 / 0 | 69.635 | 0.682 (4799) | 2.222 (4800) | 2.621 |
| baseline / 3 | 4800 / 4800 | 240.026 | 0 / 0 | 74.013 | 0.609 (4800) | 2.106 (4800) | 2.538 |
| candidate / 3 | 4740 / 4800 | 237.023 | 59 / 1 | 264.278 | 0.605 (4739) | 2.107 (4740) | 2.358 |
| candidate / 4 | 4800 / 4800 | 240.023 | 0 / 0 | 69.443 | 0.579 (4799) | 2.058 (4800) | 2.478 |
| baseline / 4 | 4800 / 4800 | 240.022 | 0 / 0 | 68.668 | 0.597 (4800) | 2.095 (4800) | 2.507 |
| baseline / 5 | 4800 / 4800 | 240.023 | 0 / 0 | 70.651 | 0.593 (4800) | 2.083 (4800) | 2.505 |
| candidate / 5 | 4800 / 4800 | 240.025 | 0 / 0 | 72.860 | 0.596 (4800) | 2.087 (4800) | 2.515 |
| candidate / 6 | 4800 / 4800 | 240.024 | 0 / 0 | 70.118 | 0.622 (4800) | 2.139 (4800) | 2.551 |
| baseline / 6 | 4800 / 4800 | 240.024 | 0 / 0 | 72.680 | 0.617 (4800) | 2.127 (4800) | 2.550 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 4800 / 4800 | 240.006 | 0 / 0 | 65.783 | 0.659 (4800) | 2.738 (4800) | 3.676 |
| baseline / 1 | 4742 / 4800 | 237.111 | 56 / 2 | 71.941 | 0.683 (4742) | 2.766 (4742) | 3.503 |
| baseline / 2 | 4745 / 4800 | 237.263 | 54 / 1 | 66.981 | 0.547 (4743) | 2.569 (4745) | 3.360 |
| candidate / 2 | 4745 / 4800 | 237.259 | 54 / 1 | 67.467 | 0.722 (4744) | 2.830 (4745) | 3.620 |
| candidate / 3 | 4744 / 4800 | 237.209 | 55 / 1 | 68.414 | 0.660 (4744) | 2.737 (4744) | 3.495 |
| baseline / 3 | 4744 / 4800 | 237.216 | 55 / 1 | 68.646 | 0.661 (4744) | 2.740 (4744) | 3.505 |
| baseline / 4 | 4745 / 4800 | 237.265 | 54 / 1 | 67.518 | 0.683 (4745) | 2.774 (4745) | 3.553 |
| candidate / 4 | 4800 / 4800 | 240.022 | 0 / 0 | 65.758 | 0.673 (4800) | 2.757 (4800) | 3.691 |
| candidate / 5 | 4744 / 4800 | 237.203 | 55 / 1 | 68.391 | 0.648 (4744) | 2.713 (4744) | 3.482 |
| baseline / 5 | 4744 / 4800 | 237.218 | 54 / 2 | 68.036 | 0.692 (4744) | 2.781 (4744) | 3.538 |
| baseline / 6 | 4743 / 4800 | 237.165 | 55 / 2 | 69.117 | 0.703 (4743) | 2.799 (4743) | 3.550 |
| candidate / 6 | 4744 / 4800 | 237.205 | 54 / 2 | 68.099 | 0.708 (4744) | 2.809 (4744) | 3.575 |

