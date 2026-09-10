# Decoder comparison

Overall: **FAIL** (paired).

Cases: 16; repetitions per build: 3; requested seconds per trial: 10; warmup offered frames: 120.

Alternating baseline/candidate order by repetition and case; identical fixture bytes; all correctness gates before serial paced timing; paired differences across repetitions, not pooled frames. Configured thresholds are observational gates, not statistical equivalence or significance tests. Steady samples exclude offered warmup IDs and first successful output per decoder generation. Failures and startup losses remain in accounting. Headless decode does not measure rendering or network.

Machine-readable evidence: [results.json](results.json). Bitrates use decimal megabits per second (1 Mbps = 1,000,000 bits/s). Requested bitrate is an encoder target; measured bitrate is the encoded payload rate, excluding transport overhead. A clean decode run outside the configured bitrate tolerance is INCONCLUSIVE for the requested workload.

| Case | Result | Requested Mbps | Measured Mbps | Baseline VT median / p95 / p99 ms | Candidate VT median / p95 / p99 ms | Paired median delta |
|---|---|---:|---:|---:|---:|---:|
| ultrawide-3440x1440p240-hevc-sdr-50mbps | BASELINE_FAILURE | 50.000 | 55.488 | 1.938 / 2.725 / 8.474 | 1.945 / 2.721 / 8.423 | 0.440% |
| ultrawide-3440x1440p240-hevc-sdr-100mbps | BASELINE_FAILURE | 100.000 | 95.374 | 1.971 / 3.140 / 11.654 | 1.954 / 3.133 / 11.685 | -0.363% |
| ultrawide-3440x1440p240-hevc-sdr-250mbps | BASELINE_FAILURE | 250.000 | 213.959 | 2.474 / 3.579 / 15.414 | 2.480 / 3.599 / 15.463 | -0.279% |
| ultrawide-3440x1440p240-hevc-sdr-350mbps | BASELINE_FAILURE | 350.000 | 297.695 | 2.877 / 4.092 / 17.061 | 2.893 / 3.962 / 17.067 | 0.534% |
| ultrawide-3440x1440p240-hevc-hdr10-50mbps | BASELINE_FAILURE | 50.000 | 50.947 | 2.029 / 3.012 / 6.367 | 2.040 / 3.108 / 6.451 | 0.525% |
| ultrawide-3440x1440p240-hevc-hdr10-100mbps | BASELINE_FAILURE | 100.000 | 92.181 | 2.057 / 3.201 / 10.701 | 2.060 / 3.276 / 10.662 | 0.259% |
| ultrawide-3440x1440p240-hevc-hdr10-250mbps | BASELINE_FAILURE | 250.000 | 213.563 | 2.586 / 3.825 / 13.546 | 2.590 / 3.808 / 13.721 | 0.116% |
| ultrawide-3440x1440p240-hevc-hdr10-350mbps | BASELINE_FAILURE | 350.000 | 297.753 | 2.941 / 4.144 / 16.193 | 2.978 / 4.439 / 16.097 | 0.488% |
| 4k-3840x2160p60-hevc-sdr-50mbps | INCONCLUSIVE | 50.000 | 60.820 | 2.908 / 8.407 / 17.962 | 2.885 / 7.634 / 18.038 | -0.655% |
| 4k-3840x2160p60-hevc-sdr-100mbps | PASS | 100.000 | 92.471 | 2.961 / 11.055 / 21.372 | 2.953 / 11.234 / 21.549 | -0.625% |
| 4k-3840x2160p60-hevc-sdr-250mbps | PASS | 250.000 | 214.384 | 4.772 / 20.866 / 27.932 | 4.761 / 19.312 / 27.589 | 0.848% |
| 4k-3840x2160p60-hevc-sdr-350mbps | PASS | 350.000 | 296.923 | 5.975 / 21.888 / 30.050 | 5.983 / 22.095 / 30.065 | 3.498% |
| 4k-3840x2160p60-hevc-hdr10-50mbps | INCONCLUSIVE | 50.000 | 83.905 | 2.990 / 13.559 / 25.982 | 2.979 / 13.674 / 26.033 | -0.369% |
| 4k-3840x2160p60-hevc-hdr10-100mbps | PASS | 100.000 | 91.768 | 3.043 / 11.031 / 20.744 | 3.076 / 11.076 / 20.525 | 1.262% |
| 4k-3840x2160p60-hevc-hdr10-250mbps | PASS | 250.000 | 214.240 | 4.856 / 18.819 / 27.492 | 4.976 / 18.875 / 27.435 | 1.099% |
| 4k-3840x2160p60-hevc-hdr10-350mbps | PASS | 350.000 | 296.411 | 6.334 / 19.990 / 28.600 | 6.329 / 20.377 / 28.628 | 0.322% |

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
| ultrawide-3440x1440p240-hevc-sdr-50mbps | BASELINE_FAILURE | 0.596 / 0.614 | 2.081 / 2.093 | 2.623 / 2.387 | 7124 / 7012 | 7140 / 7020 |
| ultrawide-3440x1440p240-hevc-sdr-100mbps | BASELINE_FAILURE | 0.635 / 0.633 | 2.262 / 2.250 | 2.787 / 2.758 | 7012 / 7009 | 7023 / 7021 |
| ultrawide-3440x1440p240-hevc-sdr-250mbps | BASELINE_FAILURE | 0.705 / 0.705 | 2.732 / 2.748 | 3.736 / 3.735 | 7009 / 7016 | 7023 / 7025 |
| ultrawide-3440x1440p240-hevc-sdr-350mbps | BASELINE_FAILURE | 0.706 / 0.700 | 3.179 / 3.169 | 4.507 / 4.483 | 7023 / 7020 | 7025 / 7024 |
| ultrawide-3440x1440p240-hevc-hdr10-50mbps | BASELINE_FAILURE | 0.623 / 0.679 | 2.106 / 2.183 | 2.548 / 2.465 | 7063 / 7002 | 7080 / 7020 |
| ultrawide-3440x1440p240-hevc-hdr10-100mbps | BASELINE_FAILURE | 0.693 / 0.697 | 2.318 / 2.329 | 2.726 / 2.766 | 7010 / 7001 | 7020 / 7022 |
| ultrawide-3440x1440p240-hevc-hdr10-250mbps | BASELINE_FAILURE | 0.757 / 0.750 | 2.844 / 2.828 | 3.671 / 3.632 | 7011 / 7013 | 7026 / 7026 |
| ultrawide-3440x1440p240-hevc-hdr10-350mbps | BASELINE_FAILURE | 0.722 / 0.740 | 3.225 / 3.241 | 4.464 / 4.440 | 7018 / 7005 | 7025 / 7021 |
| 4k-3840x2160p60-hevc-sdr-50mbps | INCONCLUSIVE | 0.926 / 0.886 | 3.647 / 3.610 | 4.542 / 4.532 | 1797 / 1796 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-sdr-100mbps | PASS | 0.971 / 0.987 | 3.984 / 3.981 | 4.947 / 4.955 | 1798 / 1796 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-sdr-250mbps | PASS | 1.200 / 1.172 | 5.944 / 5.905 | 7.133 / 7.031 | 1800 / 1799 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-sdr-350mbps | PASS | 1.168 / 1.262 | 7.038 / 7.142 | 8.320 / 8.399 | 1799 / 1799 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-50mbps | INCONCLUSIVE | 1.018 / 1.000 | 4.209 / 4.205 | 5.339 / 5.284 | 1793 / 1793 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-100mbps | PASS | 1.041 / 1.046 | 4.056 / 4.084 | 4.978 / 5.037 | 1798 / 1795 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-250mbps | PASS | 1.242 / 1.225 | 6.028 / 5.982 | 7.366 / 7.300 | 1799 / 1798 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-350mbps | PASS | 1.276 / 1.249 | 7.212 / 7.165 | 8.518 / 8.413 | 1800 / 1800 | 1800 / 1800 |

## ultrawide-3440x1440p240-hevc-sdr-50mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 55.488 Mbps. Encoder target: 50.000 Mbps; measured/target: 111.0%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=1; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=1; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 2400 / 2400 | 240.039 | 0 / 0 | 70.584 | 0.583 (2394) | 2.069 (2400) | 2.737 |
| candidate / 1 | 2340 / 2400 | 234.053 | 58 / 2 | 259.487 | 0.615 (2337) | 2.099 (2340) | 2.401 |
| candidate / 2 | 2340 / 2400 | 234.070 | 58 / 2 | 259.094 | 0.607 (2337) | 2.078 (2340) | 2.363 |
| baseline / 2 | 2400 / 2400 | 240.044 | 0 / 0 | 69.786 | 0.585 (2394) | 2.061 (2400) | 2.704 |
| baseline / 3 | 2340 / 2400 | 234.044 | 58 / 2 | 261.324 | 0.620 (2336) | 2.112 (2340) | 2.423 |
| candidate / 3 | 2340 / 2400 | 234.049 | 58 / 2 | 257.190 | 0.619 (2338) | 2.101 (2340) | 2.397 |

## ultrawide-3440x1440p240-hevc-sdr-100mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 95.374 Mbps. Encoder target: 100.000 Mbps; measured/target: 95.4%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=59; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 2340 / 2400 | 234.053 | 59 / 1 | 259.349 | 0.623 (2335) | 2.241 (2340) | 2.736 |
| baseline / 1 | 2341 / 2400 | 234.143 | 58 / 1 | 75.418 | 0.631 (2336) | 2.256 (2341) | 2.776 |
| baseline / 2 | 2342 / 2400 | 234.243 | 56 / 2 | 74.855 | 0.632 (2339) | 2.257 (2342) | 2.805 |
| candidate / 2 | 2340 / 2400 | 234.046 | 58 / 2 | 258.949 | 0.625 (2338) | 2.226 (2340) | 2.714 |
| candidate / 3 | 2341 / 2400 | 234.145 | 58 / 1 | 75.196 | 0.651 (2336) | 2.282 (2341) | 2.825 |
| baseline / 3 | 2340 / 2400 | 234.052 | 58 / 2 | 258.906 | 0.643 (2337) | 2.273 (2340) | 2.782 |

## ultrawide-3440x1440p240-hevc-sdr-250mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 213.959 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.6%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 2341 / 2400 | 234.133 | 57 / 2 | 74.809 | 0.681 (2334) | 2.705 (2341) | 3.729 |
| candidate / 1 | 2342 / 2400 | 234.223 | 57 / 1 | 73.976 | 0.710 (2342) | 2.757 (2342) | 3.733 |
| candidate / 2 | 2341 / 2400 | 234.138 | 57 / 2 | 74.592 | 0.684 (2333) | 2.713 (2341) | 3.721 |
| baseline / 2 | 2341 / 2400 | 234.131 | 57 / 2 | 74.918 | 0.723 (2339) | 2.751 (2341) | 3.762 |
| baseline / 3 | 2341 / 2400 | 234.136 | 57 / 2 | 74.290 | 0.712 (2336) | 2.741 (2341) | 3.717 |
| candidate / 3 | 2342 / 2400 | 234.233 | 56 / 2 | 72.656 | 0.722 (2341) | 2.773 (2342) | 3.751 |

## ultrawide-3440x1440p240-hevc-sdr-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 297.695 Mbps. Encoder target: 350.000 Mbps; measured/target: 85.1%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 2341 / 2400 | 234.124 | 58 / 1 | 75.710 | 0.682 (2340) | 3.137 (2341) | 4.447 |
| baseline / 1 | 2342 / 2400 | 234.220 | 57 / 1 | 73.371 | 0.713 (2341) | 3.189 (2342) | 4.550 |
| baseline / 2 | 2342 / 2400 | 234.228 | 57 / 1 | 73.325 | 0.708 (2341) | 3.190 (2342) | 4.510 |
| candidate / 2 | 2341 / 2400 | 234.119 | 57 / 2 | 73.761 | 0.710 (2339) | 3.184 (2341) | 4.480 |
| candidate / 3 | 2342 / 2400 | 234.203 | 57 / 1 | 73.256 | 0.710 (2341) | 3.185 (2342) | 4.523 |
| baseline / 3 | 2341 / 2400 | 234.118 | 57 / 2 | 74.927 | 0.698 (2341) | 3.158 (2341) | 4.461 |

## ultrawide-3440x1440p240-hevc-hdr10-50mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 50.947 Mbps. Encoder target: 50.000 Mbps; measured/target: 101.9%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=1; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=1; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=59; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=1; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=1; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 2340 / 2400 | 234.039 | 58 / 2 | 261.661 | 0.670 (2333) | 2.182 (2340) | 2.532 |
| candidate / 1 | 2340 / 2400 | 234.049 | 58 / 2 | 263.498 | 0.679 (2334) | 2.184 (2340) | 2.474 |
| candidate / 2 | 2340 / 2400 | 234.044 | 59 / 1 | 264.740 | 0.697 (2336) | 2.204 (2340) | 2.478 |
| baseline / 2 | 2400 / 2400 | 240.046 | 0 / 0 | 74.403 | 0.557 (2396) | 1.997 (2400) | 2.677 |
| baseline / 3 | 2340 / 2400 | 234.052 | 58 / 2 | 261.529 | 0.643 (2334) | 2.141 (2340) | 2.433 |
| candidate / 3 | 2340 / 2400 | 234.045 | 58 / 2 | 263.078 | 0.661 (2332) | 2.160 (2340) | 2.445 |

## ultrawide-3440x1440p240-hevc-hdr10-100mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 92.181 Mbps. Encoder target: 100.000 Mbps; measured/target: 92.2%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=1; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=1; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 2341 / 2400 | 234.144 | 58 / 1 | 75.681 | 0.686 (2333) | 2.317 (2341) | 2.762 |
| baseline / 1 | 2340 / 2400 | 234.039 | 58 / 2 | 262.098 | 0.695 (2335) | 2.319 (2340) | 2.722 |
| baseline / 2 | 2340 / 2400 | 233.999 | 58 / 2 | 260.652 | 0.690 (2339) | 2.312 (2340) | 2.717 |
| candidate / 2 | 2341 / 2400 | 234.146 | 58 / 1 | 75.486 | 0.706 (2335) | 2.339 (2341) | 2.792 |
| candidate / 3 | 2340 / 2400 | 234.042 | 58 / 2 | 261.486 | 0.700 (2333) | 2.332 (2340) | 2.744 |
| baseline / 3 | 2340 / 2400 | 234.049 | 58 / 2 | 262.459 | 0.694 (2336) | 2.324 (2340) | 2.739 |

## ultrawide-3440x1440p240-hevc-hdr10-250mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 213.563 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.4%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 2342 / 2400 | 234.230 | 56 / 2 | 73.620 | 0.749 (2336) | 2.837 (2342) | 3.647 |
| candidate / 1 | 2342 / 2400 | 234.223 | 57 / 1 | 74.547 | 0.755 (2340) | 2.837 (2342) | 3.639 |
| candidate / 2 | 2342 / 2400 | 234.234 | 57 / 1 | 74.390 | 0.746 (2337) | 2.821 (2342) | 3.617 |
| baseline / 2 | 2342 / 2400 | 234.241 | 56 / 2 | 74.216 | 0.751 (2339) | 2.832 (2342) | 3.631 |
| baseline / 3 | 2342 / 2400 | 234.247 | 56 / 2 | 72.753 | 0.772 (2336) | 2.863 (2342) | 3.734 |
| candidate / 3 | 2342 / 2400 | 234.226 | 56 / 2 | 74.134 | 0.749 (2336) | 2.826 (2342) | 3.641 |

## ultrawide-3440x1440p240-hevc-hdr10-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 297.753 Mbps. Encoder target: 350.000 Mbps; measured/target: 85.1%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 2340 / 2400 | 234.015 | 58 / 2 | 261.607 | 0.753 (2332) | 3.260 (2340) | 4.485 |
| baseline / 1 | 2341 / 2400 | 234.121 | 57 / 2 | 73.747 | 0.720 (2340) | 3.222 (2341) | 4.422 |
| baseline / 2 | 2342 / 2400 | 234.217 | 56 / 2 | 72.145 | 0.732 (2341) | 3.239 (2342) | 4.467 |
| candidate / 2 | 2340 / 2400 | 234.024 | 58 / 2 | 263.714 | 0.728 (2337) | 3.213 (2340) | 4.368 |
| candidate / 3 | 2341 / 2400 | 234.120 | 57 / 2 | 74.487 | 0.740 (2336) | 3.250 (2341) | 4.466 |
| baseline / 3 | 2342 / 2400 | 234.213 | 57 / 1 | 73.394 | 0.714 (2337) | 3.214 (2342) | 4.502 |

Observed threshold breach: vt_p95_ms: +0.222 ms (+5.19%).

## 4k-3840x2160p60-hevc-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 60.820 Mbps. Encoder target: 50.000 Mbps; measured/target: 121.6%.

measured payload bitrate 60.820 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.082 | 0 / 0 | 90.534 | 0.874 (598) | 3.554 (600) | 4.503 |
| candidate / 1 | 600 / 600 | 60.081 | 0 / 0 | 88.412 | 0.834 (598) | 3.518 (600) | 4.468 |
| candidate / 2 | 600 / 600 | 60.080 | 0 / 0 | 88.538 | 0.883 (599) | 3.630 (600) | 4.564 |
| baseline / 2 | 600 / 600 | 60.080 | 0 / 0 | 88.210 | 0.949 (599) | 3.703 (600) | 4.573 |
| baseline / 3 | 600 / 600 | 60.079 | 0 / 0 | 87.473 | 0.955 (600) | 3.682 (600) | 4.549 |
| candidate / 3 | 600 / 600 | 60.085 | 0 / 0 | 87.032 | 0.940 (599) | 3.681 (600) | 4.564 |

Observed threshold breach: public_p95_ms: +1.005 ms (+10.23%).

## 4k-3840x2160p60-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 92.471 Mbps. Encoder target: 100.000 Mbps; measured/target: 92.5%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.080 | 0 / 0 | 93.145 | 0.966 (600) | 3.957 (600) | 4.982 |
| baseline / 1 | 600 / 600 | 60.079 | 0 / 0 | 88.424 | 0.942 (600) | 3.949 (600) | 4.882 |
| baseline / 2 | 600 / 600 | 60.077 | 0 / 0 | 93.622 | 0.989 (600) | 3.992 (600) | 5.037 |
| candidate / 2 | 600 / 600 | 60.079 | 0 / 0 | 90.463 | 0.988 (598) | 3.979 (600) | 4.954 |
| candidate / 3 | 600 / 600 | 60.085 | 0 / 0 | 87.642 | 1.008 (598) | 4.006 (600) | 4.929 |
| baseline / 3 | 600 / 600 | 60.078 | 0 / 0 | 87.780 | 0.981 (598) | 4.011 (600) | 4.922 |

## 4k-3840x2160p60-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 214.384 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.061 | 0 / 0 | 95.855 | 1.195 (600) | 5.956 (600) | 7.160 |
| candidate / 1 | 600 / 600 | 60.067 | 0 / 0 | 89.520 | 1.160 (600) | 5.870 (600) | 6.979 |
| candidate / 2 | 600 / 600 | 60.065 | 0 / 0 | 91.890 | 1.202 (599) | 5.954 (600) | 7.089 |
| baseline / 2 | 600 / 600 | 60.064 | 0 / 0 | 93.775 | 1.197 (600) | 5.935 (600) | 7.146 |
| baseline / 3 | 600 / 600 | 60.064 | 0 / 0 | 92.255 | 1.210 (600) | 5.940 (600) | 7.093 |
| candidate / 3 | 600 / 600 | 60.064 | 0 / 0 | 91.580 | 1.154 (600) | 5.890 (600) | 7.024 |

## 4k-3840x2160p60-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 296.923 Mbps. Encoder target: 350.000 Mbps; measured/target: 84.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.054 | 0 / 0 | 94.868 | 1.279 (600) | 7.163 (600) | 8.459 |
| baseline / 1 | 600 / 600 | 60.059 | 0 / 0 | 92.476 | 1.037 (600) | 6.860 (600) | 8.128 |
| baseline / 2 | 600 / 600 | 60.055 | 0 / 0 | 94.000 | 1.218 (599) | 7.109 (600) | 8.409 |
| candidate / 2 | 600 / 600 | 60.056 | 0 / 0 | 89.919 | 1.242 (600) | 7.118 (600) | 8.309 |
| candidate / 3 | 600 / 600 | 60.055 | 0 / 0 | 94.273 | 1.265 (599) | 7.145 (600) | 8.429 |
| baseline / 3 | 600 / 600 | 60.054 | 0 / 0 | 92.397 | 1.250 (600) | 7.145 (600) | 8.422 |

## 4k-3840x2160p60-hevc-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 83.905 Mbps. Encoder target: 50.000 Mbps; measured/target: 167.8%.

measured payload bitrate 83.905 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.080 | 0 / 0 | 96.618 | 1.017 (596) | 4.207 (600) | 5.311 |
| candidate / 1 | 600 / 600 | 60.076 | 0 / 0 | 95.989 | 1.041 (596) | 4.243 (600) | 5.366 |
| candidate / 2 | 600 / 600 | 60.080 | 0 / 0 | 94.851 | 0.998 (598) | 4.217 (600) | 5.289 |
| baseline / 2 | 600 / 600 | 60.081 | 0 / 0 | 96.349 | 0.998 (598) | 4.176 (600) | 5.332 |
| baseline / 3 | 600 / 600 | 60.080 | 0 / 0 | 98.811 | 1.040 (599) | 4.244 (600) | 5.372 |
| candidate / 3 | 600 / 600 | 60.083 | 0 / 0 | 94.204 | 0.964 (599) | 4.154 (600) | 5.197 |

## 4k-3840x2160p60-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 91.768 Mbps. Encoder target: 100.000 Mbps; measured/target: 91.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.077 | 0 / 0 | 90.572 | 1.037 (600) | 4.071 (600) | 5.035 |
| baseline / 1 | 600 / 600 | 60.079 | 0 / 0 | 88.634 | 1.030 (599) | 4.026 (600) | 4.935 |
| baseline / 2 | 600 / 600 | 60.084 | 0 / 0 | 89.359 | 1.055 (600) | 4.095 (600) | 5.041 |
| candidate / 2 | 600 / 600 | 60.077 | 0 / 0 | 89.597 | 1.054 (599) | 4.103 (600) | 5.039 |
| candidate / 3 | 600 / 600 | 60.080 | 0 / 0 | 90.208 | 1.049 (596) | 4.077 (600) | 5.038 |
| baseline / 3 | 600 / 600 | 60.082 | 0 / 0 | 88.701 | 1.038 (599) | 4.048 (600) | 4.958 |

## 4k-3840x2160p60-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 214.240 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.064 | 0 / 0 | 93.440 | 1.260 (600) | 6.042 (600) | 7.211 |
| candidate / 1 | 600 / 600 | 60.069 | 0 / 0 | 93.544 | 1.253 (600) | 6.015 (600) | 7.189 |
| candidate / 2 | 600 / 600 | 60.061 | 0 / 0 | 103.006 | 1.196 (600) | 5.947 (600) | 7.325 |
| baseline / 2 | 600 / 600 | 60.064 | 0 / 0 | 110.341 | 1.238 (599) | 6.035 (600) | 7.536 |
| baseline / 3 | 600 / 600 | 60.065 | 0 / 0 | 102.672 | 1.227 (600) | 6.005 (600) | 7.350 |
| candidate / 3 | 600 / 600 | 60.065 | 0 / 0 | 106.435 | 1.225 (598) | 5.984 (600) | 7.386 |

## 4k-3840x2160p60-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 296.411 Mbps. Encoder target: 350.000 Mbps; measured/target: 84.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.045 | 0 / 0 | 94.833 | 1.127 (600) | 6.977 (600) | 8.210 |
| baseline / 1 | 600 / 600 | 60.048 | 0 / 0 | 98.921 | 1.210 (600) | 7.126 (600) | 8.429 |
| baseline / 2 | 600 / 600 | 60.045 | 0 / 0 | 96.732 | 1.311 (600) | 7.251 (600) | 8.561 |
| candidate / 2 | 600 / 600 | 60.044 | 0 / 0 | 94.695 | 1.309 (600) | 7.266 (600) | 8.536 |
| candidate / 3 | 600 / 600 | 60.050 | 0 / 0 | 93.701 | 1.311 (600) | 7.251 (600) | 8.495 |
| baseline / 3 | 600 / 600 | 60.048 | 0 / 0 | 95.231 | 1.309 (600) | 7.259 (600) | 8.565 |

