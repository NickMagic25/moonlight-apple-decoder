# Decoder comparison

Overall: **FAIL** (paired).

Cases: 16; repetitions per build: 3; requested seconds per trial: 10; warmup offered frames: 120.

Alternating baseline/candidate order by repetition and case; identical fixture bytes; all correctness gates before serial paced timing; paired differences across repetitions, not pooled frames. Configured thresholds are observational gates, not statistical equivalence or significance tests. Steady samples exclude offered warmup IDs and first successful output per decoder generation. Failures and startup losses remain in accounting. Headless decode does not measure rendering or network.

Machine-readable evidence: [results.json](results.json). Bitrates use decimal megabits per second (1 Mbps = 1,000,000 bits/s). Requested bitrate is an encoder target; measured bitrate is the encoded payload rate, excluding transport overhead. A clean decode run outside the configured bitrate tolerance is INCONCLUSIVE for the requested workload.

| Case | Result | Requested Mbps | Measured Mbps | Baseline VT median / p95 / p99 ms | Candidate VT median / p95 / p99 ms | Paired median delta |
|---|---|---:|---:|---:|---:|---:|
| ultrawide-3440x1440p240-hevc-sdr-50mbps | PASS | 50.000 | 55.488 | 1.948 / 2.775 / 8.481 | 1.975 / 2.832 / 8.389 | 1.210% |
| ultrawide-3440x1440p240-hevc-sdr-100mbps | PASS | 100.000 | 95.374 | 1.999 / 3.196 / 11.665 | 2.002 / 3.176 / 11.688 | 0.198% |
| ultrawide-3440x1440p240-hevc-sdr-250mbps | PASS | 250.000 | 213.959 | 2.480 / 3.632 / 15.310 | 2.504 / 3.606 / 15.400 | 0.405% |
| ultrawide-3440x1440p240-hevc-sdr-350mbps | PASS | 350.000 | 297.695 | 2.902 / 4.086 / 17.143 | 2.910 / 4.155 / 17.066 | 0.258% |
| ultrawide-3440x1440p240-hevc-hdr10-50mbps | PASS | 50.000 | 50.947 | 2.033 / 3.048 / 6.285 | 2.040 / 3.038 / 6.481 | 0.056% |
| ultrawide-3440x1440p240-hevc-hdr10-100mbps | PASS | 100.000 | 92.181 | 2.067 / 3.276 / 10.740 | 2.052 / 3.256 / 10.589 | -0.800% |
| ultrawide-3440x1440p240-hevc-hdr10-250mbps | PASS | 250.000 | 213.563 | 2.583 / 3.868 / 13.773 | 2.598 / 3.665 / 13.622 | 0.464% |
| ultrawide-3440x1440p240-hevc-hdr10-350mbps | PASS | 350.000 | 297.753 | 2.947 / 4.492 / 16.034 | 2.959 / 4.163 / 16.108 | -0.243% |
| 4k-3840x2160p60-hevc-sdr-50mbps | INCONCLUSIVE | 50.000 | 60.820 | 2.893 / 7.497 / 18.079 | 2.890 / 7.748 / 18.006 | -0.084% |
| 4k-3840x2160p60-hevc-sdr-100mbps | PASS | 100.000 | 92.471 | 2.981 / 11.105 / 21.396 | 2.973 / 11.214 / 21.294 | -0.270% |
| 4k-3840x2160p60-hevc-sdr-250mbps | PASS | 250.000 | 214.384 | 4.696 / 19.595 / 27.594 | 4.769 / 19.686 / 27.661 | 1.571% |
| 4k-3840x2160p60-hevc-sdr-350mbps | PASS | 350.000 | 296.923 | 5.881 / 21.749 / 29.781 | 5.795 / 22.281 / 29.833 | -2.514% |
| 4k-3840x2160p60-hevc-hdr10-50mbps | INCONCLUSIVE | 50.000 | 83.905 | 2.995 / 13.535 / 26.069 | 2.995 / 13.782 / 26.059 | 0.017% |
| 4k-3840x2160p60-hevc-hdr10-100mbps | PASS | 100.000 | 91.768 | 3.050 / 10.779 / 21.083 | 3.071 / 11.129 / 21.004 | 0.686% |
| 4k-3840x2160p60-hevc-hdr10-250mbps | PASS | 250.000 | 214.240 | 4.827 / 18.739 / 27.110 | 4.932 / 18.561 / 27.137 | 1.380% |
| 4k-3840x2160p60-hevc-hdr10-350mbps | PASS | 350.000 | 296.411 | 6.406 / 20.341 / 28.839 | 6.237 / 20.372 / 28.811 | -3.201% |

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
| ultrawide-3440x1440p240-hevc-sdr-50mbps | PASS | 0.610 / 0.634 | 2.105 / 2.139 | 2.807 / 2.893 | 7184 / 7184 | 7200 / 7200 |
| ultrawide-3440x1440p240-hevc-sdr-100mbps | PASS | 0.633 / 0.637 | 2.283 / 2.287 | 3.279 / 3.303 | 7187 / 7188 | 7200 / 7200 |
| ultrawide-3440x1440p240-hevc-sdr-250mbps | PASS | 0.709 / 0.718 | 2.754 / 2.770 | 4.307 / 4.324 | 7188 / 7188 | 7200 / 7200 |
| ultrawide-3440x1440p240-hevc-sdr-350mbps | PASS | 0.675 / 0.684 | 3.138 / 3.165 | 5.087 / 5.063 | 7193 / 7196 | 7200 / 7200 |
| ultrawide-3440x1440p240-hevc-hdr10-50mbps | PASS | 0.659 / 0.652 | 2.169 / 2.154 | 2.841 / 2.823 | 7185 / 7186 | 7200 / 7200 |
| ultrawide-3440x1440p240-hevc-hdr10-100mbps | PASS | 0.684 / 0.671 | 2.328 / 2.313 | 3.212 / 3.222 | 7190 / 7189 | 7200 / 7200 |
| ultrawide-3440x1440p240-hevc-hdr10-250mbps | PASS | 0.730 / 0.743 | 2.813 / 2.832 | 4.169 / 4.123 | 7191 / 7189 | 7200 / 7200 |
| ultrawide-3440x1440p240-hevc-hdr10-350mbps | PASS | 0.711 / 0.700 | 3.215 / 3.207 | 5.045 / 5.137 | 7191 / 7192 | 7200 / 7200 |
| 4k-3840x2160p60-hevc-sdr-50mbps | INCONCLUSIVE | 0.931 / 0.944 | 3.646 / 3.660 | 4.516 / 4.546 | 1800 / 1799 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-sdr-100mbps | PASS | 0.979 / 0.971 | 4.000 / 3.977 | 4.944 / 4.906 | 1800 / 1798 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-sdr-250mbps | PASS | 1.166 / 1.178 | 5.885 / 5.921 | 7.045 / 7.063 | 1798 / 1799 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-sdr-350mbps | PASS | 1.202 / 1.177 | 7.077 / 7.034 | 8.306 / 8.318 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-50mbps | INCONCLUSIVE | 1.022 / 1.018 | 4.224 / 4.228 | 5.297 / 5.271 | 1799 / 1798 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-100mbps | PASS | 1.036 / 1.047 | 4.077 / 4.055 | 4.995 / 5.007 | 1798 / 1798 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-250mbps | PASS | 1.187 / 1.197 | 5.944 / 5.974 | 7.131 / 7.131 | 1799 / 1797 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-350mbps | PASS | 1.303 / 1.276 | 7.246 / 7.194 | 8.508 / 8.477 | 1800 / 1800 | 1800 / 1800 |

## ultrawide-3440x1440p240-hevc-sdr-50mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 55.488 Mbps. Encoder target: 50.000 Mbps; measured/target: 111.0%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 66.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| baseline / 1 | 2400 / 2400 | 240.045 | 0 / 0 | 69.356 | 56.772 | PASS | 0 / 0 / 0 / 0 | 0.606 (2396) | 2.094 (2400) | 2.750 |
| candidate / 1 | 2400 / 2400 | 240.043 | 0 / 0 | 76.330 | 63.867 | PASS | 0 / 0 / 0 / 0 | 0.638 (2397) | 2.139 (2400) | 2.880 |
| candidate / 2 | 2400 / 2400 | 240.048 | 0 / 0 | 76.148 | 63.817 | PASS | 0 / 0 / 0 / 0 | 0.625 (2393) | 2.135 (2400) | 2.856 |
| baseline / 2 | 2400 / 2400 | 240.047 | 0 / 0 | 74.857 | 62.605 | PASS | 0 / 0 / 0 / 0 | 0.613 (2394) | 2.113 (2400) | 2.826 |
| baseline / 3 | 2400 / 2400 | 240.054 | 0 / 0 | 77.233 | 64.697 | PASS | 0 / 0 / 0 / 0 | 0.611 (2394) | 2.109 (2400) | 2.845 |
| candidate / 3 | 2400 / 2400 | 240.044 | 0 / 0 | 81.736 | 69.321 | PASS | 0 / 0 / 0 / 0 | 0.638 (2394) | 2.145 (2400) | 2.943 |

## ultrawide-3440x1440p240-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 95.374 Mbps. Encoder target: 100.000 Mbps; measured/target: 95.4%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 66.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| candidate / 1 | 2400 / 2400 | 240.048 | 0 / 0 | 75.369 | 60.677 | PASS | 0 / 0 / 0 / 0 | 0.630 (2394) | 2.276 (2400) | 3.270 |
| baseline / 1 | 2400 / 2400 | 240.050 | 0 / 0 | 75.857 | 61.344 | PASS | 0 / 0 / 0 / 0 | 0.626 (2398) | 2.274 (2400) | 3.288 |
| baseline / 2 | 2400 / 2400 | 240.048 | 0 / 0 | 75.402 | 60.772 | PASS | 0 / 0 / 0 / 0 | 0.645 (2396) | 2.296 (2400) | 3.294 |
| candidate / 2 | 2400 / 2400 | 240.049 | 0 / 0 | 75.480 | 60.972 | PASS | 0 / 0 / 0 / 0 | 0.639 (2397) | 2.286 (2400) | 3.288 |
| candidate / 3 | 2400 / 2400 | 240.034 | 0 / 0 | 79.493 | 65.163 | PASS | 0 / 0 / 0 / 0 | 0.641 (2397) | 2.299 (2400) | 3.349 |
| baseline / 3 | 2400 / 2400 | 240.044 | 0 / 0 | 74.942 | 60.389 | PASS | 0 / 0 / 0 / 0 | 0.627 (2393) | 2.278 (2400) | 3.255 |

## ultrawide-3440x1440p240-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 213.959 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.6%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 66.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| baseline / 1 | 2400 / 2400 | 240.035 | 0 / 0 | 74.407 | 58.131 | PASS | 0 / 0 / 0 / 0 | 0.705 (2396) | 2.749 (2400) | 4.308 |
| candidate / 1 | 2400 / 2400 | 240.030 | 0 / 0 | 73.230 | 56.951 | PASS | 0 / 0 / 0 / 0 | 0.716 (2394) | 2.764 (2400) | 4.266 |
| candidate / 2 | 2400 / 2400 | 240.035 | 0 / 0 | 73.875 | 57.548 | PASS | 0 / 0 / 0 / 0 | 0.718 (2399) | 2.780 (2400) | 4.389 |
| baseline / 2 | 2400 / 2400 | 240.036 | 0 / 0 | 75.364 | 58.952 | PASS | 0 / 0 / 0 / 0 | 0.717 (2395) | 2.765 (2400) | 4.308 |
| baseline / 3 | 2400 / 2400 | 240.025 | 0 / 0 | 73.577 | 57.416 | PASS | 0 / 0 / 0 / 0 | 0.704 (2397) | 2.747 (2400) | 4.305 |
| candidate / 3 | 2400 / 2400 | 240.048 | 0 / 0 | 73.976 | 57.667 | PASS | 0 / 0 / 0 / 0 | 0.721 (2395) | 2.765 (2400) | 4.316 |

## ultrawide-3440x1440p240-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 297.695 Mbps. Encoder target: 350.000 Mbps; measured/target: 85.1%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 66.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| candidate / 1 | 2400 / 2400 | 240.019 | 0 / 0 | 73.062 | 56.091 | PASS | 0 / 0 / 0 / 0 | 0.687 (2398) | 3.174 (2400) | 5.077 |
| baseline / 1 | 2400 / 2400 | 240.017 | 0 / 0 | 72.086 | 55.259 | PASS | 0 / 0 / 0 / 0 | 0.707 (2396) | 3.185 (2400) | 5.122 |
| baseline / 2 | 2400 / 2400 | 240.038 | 0 / 0 | 76.311 | 59.181 | PASS | 0 / 0 / 0 / 0 | 0.595 (2397) | 3.018 (2400) | 4.997 |
| candidate / 2 | 2400 / 2400 | 240.011 | 0 / 0 | 72.933 | 55.727 | PASS | 0 / 0 / 0 / 0 | 0.706 (2399) | 3.197 (2400) | 5.093 |
| candidate / 3 | 2400 / 2400 | 240.023 | 0 / 0 | 71.093 | 54.170 | PASS | 0 / 0 / 0 / 0 | 0.660 (2399) | 3.124 (2400) | 5.019 |
| baseline / 3 | 2400 / 2400 | 240.017 | 0 / 0 | 73.738 | 56.607 | PASS | 0 / 0 / 0 / 0 | 0.724 (2400) | 3.212 (2400) | 5.142 |

## ultrawide-3440x1440p240-hevc-hdr10-50mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 50.947 Mbps. Encoder target: 50.000 Mbps; measured/target: 101.9%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 66.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| baseline / 1 | 2400 / 2400 | 240.051 | 0 / 0 | 74.937 | 63.351 | PASS | 0 / 0 / 0 / 0 | 0.665 (2395) | 2.175 (2400) | 2.841 |
| candidate / 1 | 2400 / 2400 | 240.052 | 0 / 0 | 74.621 | 62.937 | PASS | 0 / 0 / 0 / 0 | 0.680 (2394) | 2.188 (2400) | 2.852 |
| candidate / 2 | 2400 / 2400 | 240.047 | 0 / 0 | 75.273 | 63.771 | PASS | 0 / 0 / 0 / 0 | 0.663 (2394) | 2.180 (2400) | 2.842 |
| baseline / 2 | 2400 / 2400 | 240.045 | 0 / 0 | 76.195 | 64.645 | PASS | 0 / 0 / 0 / 0 | 0.654 (2395) | 2.168 (2400) | 2.846 |
| baseline / 3 | 2400 / 2400 | 240.026 | 0 / 0 | 74.754 | 63.233 | PASS | 0 / 0 / 0 / 0 | 0.657 (2395) | 2.164 (2400) | 2.836 |
| candidate / 3 | 2400 / 2400 | 240.044 | 0 / 0 | 74.992 | 63.615 | PASS | 0 / 0 / 0 / 0 | 0.614 (2398) | 2.093 (2400) | 2.776 |

## ultrawide-3440x1440p240-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 92.181 Mbps. Encoder target: 100.000 Mbps; measured/target: 92.2%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 66.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| candidate / 1 | 2400 / 2400 | 240.043 | 0 / 0 | 74.730 | 60.438 | PASS | 0 / 0 / 0 / 0 | 0.667 (2397) | 2.315 (2400) | 3.201 |
| baseline / 1 | 2400 / 2400 | 240.051 | 0 / 0 | 77.327 | 63.181 | PASS | 0 / 0 / 0 / 0 | 0.678 (2394) | 2.320 (2400) | 3.219 |
| baseline / 2 | 2400 / 2400 | 240.042 | 0 / 0 | 75.741 | 61.202 | PASS | 0 / 0 / 0 / 0 | 0.680 (2399) | 2.332 (2400) | 3.212 |
| candidate / 2 | 2400 / 2400 | 240.044 | 0 / 0 | 75.653 | 61.433 | PASS | 0 / 0 / 0 / 0 | 0.674 (2394) | 2.322 (2400) | 3.209 |
| candidate / 3 | 2400 / 2400 | 240.040 | 0 / 0 | 82.048 | 67.901 | PASS | 0 / 0 / 0 / 0 | 0.671 (2398) | 2.302 (2400) | 3.257 |
| baseline / 3 | 2400 / 2400 | 240.047 | 0 / 0 | 75.680 | 61.393 | PASS | 0 / 0 / 0 / 0 | 0.694 (2397) | 2.333 (2400) | 3.204 |

## ultrawide-3440x1440p240-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 213.563 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.4%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 66.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| baseline / 1 | 2400 / 2400 | 240.041 | 0 / 0 | 73.355 | 57.248 | PASS | 0 / 0 / 0 / 0 | 0.732 (2399) | 2.812 (2400) | 4.137 |
| candidate / 1 | 2400 / 2400 | 240.036 | 0 / 0 | 73.695 | 57.376 | PASS | 0 / 0 / 0 / 0 | 0.748 (2396) | 2.842 (2400) | 4.141 |
| candidate / 2 | 2400 / 2400 | 240.034 | 0 / 0 | 73.862 | 57.727 | PASS | 0 / 0 / 0 / 0 | 0.736 (2398) | 2.829 (2400) | 4.129 |
| baseline / 2 | 2400 / 2400 | 240.029 | 0 / 0 | 76.831 | 60.610 | PASS | 0 / 0 / 0 / 0 | 0.723 (2397) | 2.808 (2400) | 4.176 |
| baseline / 3 | 2400 / 2400 | 240.025 | 0 / 0 | 79.327 | 62.556 | PASS | 0 / 0 / 0 / 0 | 0.736 (2395) | 2.820 (2400) | 4.192 |
| candidate / 3 | 2400 / 2400 | 240.016 | 0 / 0 | 73.246 | 57.142 | PASS | 0 / 0 / 0 / 0 | 0.745 (2395) | 2.825 (2400) | 4.099 |

## ultrawide-3440x1440p240-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 297.753 Mbps. Encoder target: 350.000 Mbps; measured/target: 85.1%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 66.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| candidate / 1 | 2400 / 2400 | 240.007 | 0 / 0 | 86.094 | 68.491 | PASS | 0 / 0 / 0 / 0 | 0.718 (2396) | 3.231 (2400) | 5.218 |
| baseline / 1 | 2400 / 2400 | 240.009 | 0 / 0 | 74.271 | 56.850 | PASS | 0 / 0 / 0 / 0 | 0.735 (2396) | 3.255 (2400) | 5.149 |
| baseline / 2 | 2400 / 2400 | 240.037 | 0 / 0 | 73.974 | 56.424 | PASS | 0 / 0 / 0 / 0 | 0.694 (2398) | 3.185 (2400) | 5.001 |
| candidate / 2 | 2400 / 2400 | 240.015 | 0 / 0 | 85.605 | 66.858 | PASS | 0 / 0 / 0 / 0 | 0.660 (2398) | 3.158 (2400) | 5.126 |
| candidate / 3 | 2400 / 2400 | 240.017 | 0 / 0 | 77.759 | 60.528 | PASS | 0 / 0 / 0 / 0 | 0.722 (2398) | 3.232 (2400) | 5.067 |
| baseline / 3 | 2400 / 2400 | 240.028 | 0 / 0 | 72.964 | 55.660 | PASS | 0 / 0 / 0 / 0 | 0.705 (2397) | 3.206 (2400) | 4.985 |

## 4k-3840x2160p60-hevc-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 60.820 Mbps. Encoder target: 50.000 Mbps; measured/target: 121.6%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 266.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

measured payload bitrate 60.820 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.079 | 0 / 0 | 86.615 | 64.929 | PASS | 0 / 0 / 0 / 0 | 0.927 (600) | 3.639 (600) | 4.516 |
| candidate / 1 | 600 / 600 | 60.082 | 0 / 0 | 87.698 | 65.906 | PASS | 0 / 0 / 0 / 0 | 0.943 (599) | 3.667 (600) | 4.543 |
| candidate / 2 | 600 / 600 | 60.082 | 0 / 0 | 89.493 | 67.787 | PASS | 0 / 0 / 0 / 0 | 0.924 (600) | 3.636 (600) | 4.519 |
| baseline / 2 | 600 / 600 | 60.081 | 0 / 0 | 86.337 | 64.775 | PASS | 0 / 0 / 0 / 0 | 0.923 (600) | 3.620 (600) | 4.478 |
| baseline / 3 | 600 / 600 | 60.084 | 0 / 0 | 87.276 | 65.392 | PASS | 0 / 0 / 0 / 0 | 0.943 (600) | 3.677 (600) | 4.555 |
| candidate / 3 | 600 / 600 | 60.080 | 0 / 0 | 87.838 | 66.073 | PASS | 0 / 0 / 0 / 0 | 0.964 (600) | 3.677 (600) | 4.575 |

## 4k-3840x2160p60-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 92.471 Mbps. Encoder target: 100.000 Mbps; measured/target: 92.5%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 266.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.078 | 0 / 0 | 88.632 | 63.668 | PASS | 0 / 0 / 0 / 0 | 0.961 (600) | 3.982 (600) | 4.903 |
| baseline / 1 | 600 / 600 | 60.078 | 0 / 0 | 92.768 | 67.971 | PASS | 0 / 0 / 0 / 0 | 1.005 (600) | 3.998 (600) | 5.010 |
| baseline / 2 | 600 / 600 | 60.080 | 0 / 0 | 87.264 | 62.322 | PASS | 0 / 0 / 0 / 0 | 0.964 (600) | 4.008 (600) | 4.916 |
| candidate / 2 | 600 / 600 | 60.080 | 0 / 0 | 88.703 | 63.687 | PASS | 0 / 0 / 0 / 0 | 0.968 (599) | 3.967 (600) | 4.916 |
| candidate / 3 | 600 / 600 | 60.079 | 0 / 0 | 88.073 | 63.390 | PASS | 0 / 0 / 0 / 0 | 0.983 (599) | 3.984 (600) | 4.900 |
| baseline / 3 | 600 / 600 | 60.081 | 0 / 0 | 88.440 | 63.565 | PASS | 0 / 0 / 0 / 0 | 0.967 (600) | 3.995 (600) | 4.907 |

## 4k-3840x2160p60-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 214.384 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.8%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 266.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.065 | 0 / 0 | 90.570 | 60.357 | PASS | 0 / 0 / 0 / 0 | 1.179 (598) | 5.911 (600) | 7.059 |
| candidate / 1 | 600 / 600 | 60.064 | 0 / 0 | 91.553 | 61.085 | PASS | 0 / 0 / 0 / 0 | 1.205 (600) | 5.957 (600) | 7.118 |
| candidate / 2 | 600 / 600 | 60.063 | 0 / 0 | 91.100 | 60.902 | PASS | 0 / 0 / 0 / 0 | 1.170 (599) | 5.902 (600) | 7.021 |
| baseline / 2 | 600 / 600 | 60.064 | 0 / 0 | 91.588 | 61.479 | PASS | 0 / 0 / 0 / 0 | 1.136 (600) | 5.846 (600) | 7.013 |
| baseline / 3 | 600 / 600 | 60.066 | 0 / 0 | 90.953 | 60.886 | PASS | 0 / 0 / 0 / 0 | 1.185 (600) | 5.899 (600) | 7.062 |
| candidate / 3 | 600 / 600 | 60.065 | 0 / 0 | 92.118 | 61.894 | PASS | 0 / 0 / 0 / 0 | 1.158 (600) | 5.905 (600) | 7.052 |

## 4k-3840x2160p60-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 296.923 Mbps. Encoder target: 350.000 Mbps; measured/target: 84.8%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 266.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.057 | 0 / 0 | 92.286 | 60.451 | PASS | 0 / 0 / 0 / 0 | 1.074 (600) | 6.888 (600) | 8.125 |
| baseline / 1 | 600 / 600 | 60.054 | 0 / 0 | 93.098 | 60.804 | PASS | 0 / 0 / 0 / 0 | 1.228 (600) | 7.122 (600) | 8.379 |
| baseline / 2 | 600 / 600 | 60.055 | 0 / 0 | 93.322 | 61.607 | PASS | 0 / 0 / 0 / 0 | 1.221 (600) | 7.091 (600) | 8.322 |
| candidate / 2 | 600 / 600 | 60.054 | 0 / 0 | 93.544 | 61.156 | PASS | 0 / 0 / 0 / 0 | 1.207 (600) | 7.066 (600) | 8.376 |
| candidate / 3 | 600 / 600 | 60.056 | 0 / 0 | 94.517 | 62.292 | PASS | 0 / 0 / 0 / 0 | 1.250 (600) | 7.149 (600) | 8.454 |
| baseline / 3 | 600 / 600 | 60.054 | 0 / 0 | 89.071 | 57.597 | PASS | 0 / 0 / 0 / 0 | 1.156 (600) | 7.017 (600) | 8.215 |

## 4k-3840x2160p60-hevc-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 83.905 Mbps. Encoder target: 50.000 Mbps; measured/target: 167.8%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 266.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

measured payload bitrate 83.905 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.078 | 0 / 0 | 96.783 | 65.966 | PASS | 0 / 0 / 0 / 0 | 1.033 (599) | 4.244 (600) | 5.358 |
| candidate / 1 | 600 / 600 | 60.079 | 0 / 0 | 93.844 | 63.343 | PASS | 0 / 0 / 0 / 0 | 1.019 (599) | 4.226 (600) | 5.262 |
| candidate / 2 | 600 / 600 | 60.078 | 0 / 0 | 93.647 | 63.364 | PASS | 0 / 0 / 0 / 0 | 1.000 (599) | 4.209 (600) | 5.267 |
| baseline / 2 | 600 / 600 | 60.081 | 0 / 0 | 93.250 | 62.713 | PASS | 0 / 0 / 0 / 0 | 1.036 (600) | 4.228 (600) | 5.267 |
| baseline / 3 | 600 / 600 | 60.080 | 0 / 0 | 94.979 | 64.649 | PASS | 0 / 0 / 0 / 0 | 0.998 (600) | 4.200 (600) | 5.266 |
| candidate / 3 | 600 / 600 | 60.081 | 0 / 0 | 94.295 | 63.973 | PASS | 0 / 0 / 0 / 0 | 1.035 (600) | 4.250 (600) | 5.284 |

## 4k-3840x2160p60-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 91.768 Mbps. Encoder target: 100.000 Mbps; measured/target: 91.8%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 266.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.080 | 0 / 0 | 89.522 | 64.019 | PASS | 0 / 0 / 0 / 0 | 1.041 (600) | 4.046 (600) | 5.003 |
| baseline / 1 | 600 / 600 | 60.077 | 0 / 0 | 88.895 | 63.441 | PASS | 0 / 0 / 0 / 0 | 1.032 (600) | 4.083 (600) | 5.010 |
| baseline / 2 | 600 / 600 | 60.079 | 0 / 0 | 88.633 | 63.507 | PASS | 0 / 0 / 0 / 0 | 1.030 (598) | 4.065 (600) | 4.971 |
| candidate / 2 | 600 / 600 | 60.079 | 0 / 0 | 91.799 | 66.151 | PASS | 0 / 0 / 0 / 0 | 1.046 (599) | 4.067 (600) | 5.043 |
| candidate / 3 | 600 / 600 | 60.077 | 0 / 0 | 88.965 | 63.480 | PASS | 0 / 0 / 0 / 0 | 1.054 (599) | 4.051 (600) | 4.976 |
| baseline / 3 | 600 / 600 | 60.082 | 0 / 0 | 88.892 | 63.041 | PASS | 0 / 0 / 0 / 0 | 1.046 (600) | 4.085 (600) | 5.004 |

## 4k-3840x2160p60-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 214.240 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.7%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 266.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.064 | 0 / 0 | 92.461 | 61.772 | PASS | 0 / 0 / 0 / 0 | 1.240 (600) | 6.012 (600) | 7.165 |
| candidate / 1 | 600 / 600 | 60.066 | 0 / 0 | 93.607 | 62.981 | PASS | 0 / 0 / 0 / 0 | 1.202 (598) | 6.007 (600) | 7.145 |
| candidate / 2 | 600 / 600 | 60.065 | 0 / 0 | 93.337 | 63.249 | PASS | 0 / 0 / 0 / 0 | 1.235 (600) | 6.019 (600) | 7.156 |
| baseline / 2 | 600 / 600 | 60.063 | 0 / 0 | 92.969 | 61.734 | PASS | 0 / 0 / 0 / 0 | 1.189 (600) | 5.960 (600) | 7.119 |
| baseline / 3 | 600 / 600 | 60.064 | 0 / 0 | 93.702 | 62.695 | PASS | 0 / 0 / 0 / 0 | 1.131 (599) | 5.860 (600) | 7.110 |
| candidate / 3 | 600 / 600 | 60.063 | 0 / 0 | 94.469 | 63.441 | PASS | 0 / 0 / 0 / 0 | 1.155 (599) | 5.897 (600) | 7.091 |

## 4k-3840x2160p60-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 296.411 Mbps. Encoder target: 350.000 Mbps; measured/target: 84.7%.

Startup admission grace: 250 ms from the fixed initial scheduled start; normal queue lateness budget: 266.667 ms. The effective deadline is the later of scheduled arrival plus that budget and the initial grace deadline. The grace never restarts after resets or loops. First-output SLA: at most 250.000 ms from that initial start. Every lost/cancelled frame and reset still fails delivery gates. Legacy first-output values use the earliest admitted arrival when the original scheduled start was not captured.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | Initial setup ms | First-output SLA | Drop causes: arrival / capacity / keyframe wait / injected | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.052 | 0 / 0 | 94.335 | 61.775 | PASS | 0 / 0 / 0 / 0 | 1.182 (600) | 7.071 (600) | 8.346 |
| baseline / 1 | 600 / 600 | 60.046 | 0 / 0 | 93.519 | 61.300 | PASS | 0 / 0 / 0 / 0 | 1.321 (600) | 7.279 (600) | 8.535 |
| baseline / 2 | 600 / 600 | 60.050 | 0 / 0 | 93.981 | 61.884 | PASS | 0 / 0 / 0 / 0 | 1.266 (600) | 7.181 (600) | 8.430 |
| candidate / 2 | 600 / 600 | 60.050 | 0 / 0 | 94.601 | 62.146 | PASS | 0 / 0 / 0 / 0 | 1.313 (600) | 7.264 (600) | 8.556 |
| candidate / 3 | 600 / 600 | 60.043 | 0 / 0 | 95.392 | 63.044 | PASS | 0 / 0 / 0 / 0 | 1.334 (600) | 7.249 (600) | 8.528 |
| baseline / 3 | 600 / 600 | 60.049 | 0 / 0 | 94.110 | 61.859 | PASS | 0 / 0 / 0 / 0 | 1.323 (600) | 7.277 (600) | 8.558 |

