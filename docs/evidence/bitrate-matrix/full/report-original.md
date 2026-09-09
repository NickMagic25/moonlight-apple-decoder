# Decoder comparison

Overall: **FAIL** (paired).

Cases: 96; repetitions per build: 3; requested seconds per trial: 10; warmup offered frames: 120.

Alternating baseline/candidate order by repetition and case; identical fixture bytes; all correctness gates before serial paced timing; paired differences across repetitions, not pooled frames. Configured thresholds are observational gates, not statistical equivalence or significance tests. Steady samples exclude offered warmup IDs and first successful output per decoder generation. Failures and startup losses remain in accounting. Headless decode does not measure rendering or network.

Machine-readable evidence: [results.json](results.json). Bitrates use decimal megabits per second (1 Mbps = 1,000,000 bits/s). Requested bitrate is an encoder target; measured bitrate is the encoded payload rate, excluding transport overhead. A clean decode run outside the configured bitrate tolerance is INCONCLUSIVE for the requested workload.

| Case | Result | Requested Mbps | Measured Mbps | Baseline VT median / p95 / p99 ms | Candidate VT median / p95 / p99 ms | Paired median delta |
|---|---|---:|---:|---:|---:|---:|
| 1080p-1920x1080p60-av1-sdr-50mbps | PASS | 50.000 | 57.204 | 4.910 / 5.639 / 8.029 | 4.914 / 5.617 / 8.026 | 0.873% |
| 1080p-1920x1080p60-av1-sdr-100mbps | PASS | 100.000 | 106.491 | 5.608 / 6.127 / 12.816 | 5.574 / 6.075 / 12.749 | -0.721% |
| 1080p-1920x1080p60-av1-sdr-250mbps | PASS | 250.000 | 252.061 | 6.990 / 7.399 / 19.909 | 7.050 / 7.548 / 19.941 | -0.064% |
| 1080p-1920x1080p60-av1-sdr-350mbps | PASS | 350.000 | 341.410 | 8.068 / 8.596 / 21.415 | 8.040 / 8.371 / 21.358 | -0.345% |
| 1080p-1920x1080p60-av1-hdr10-50mbps | PASS | 50.000 | 55.689 | 5.435 / 6.422 / 8.263 | 5.515 / 6.551 / 8.387 | 1.474% |
| 1080p-1920x1080p60-av1-hdr10-100mbps | PASS | 100.000 | 105.017 | 5.658 / 6.223 / 12.793 | 5.640 / 6.230 / 13.127 | 0.462% |
| 1080p-1920x1080p60-av1-hdr10-250mbps | PASS | 250.000 | 251.854 | 7.084 / 7.640 / 20.004 | 7.281 / 7.972 / 20.120 | 1.094% |
| 1080p-1920x1080p60-av1-hdr10-350mbps | PASS | 350.000 | 336.219 | 8.313 / 8.793 / 21.862 | 8.347 / 8.715 / 21.925 | 0.934% |
| 1080p-1920x1080p60-hevc-sdr-50mbps | PASS | 50.000 | 46.760 | 1.764 / 7.506 / 9.747 | 1.731 / 7.432 / 9.701 | -3.866% |
| 1080p-1920x1080p60-hevc-sdr-100mbps | PASS | 100.000 | 85.816 | 2.388 / 8.981 / 10.804 | 2.397 / 8.972 / 10.759 | 1.297% |
| 1080p-1920x1080p60-hevc-sdr-250mbps | PASS | 250.000 | 210.975 | 4.920 / 10.374 / 12.654 | 4.840 / 10.250 / 12.627 | -2.239% |
| 1080p-1920x1080p60-hevc-sdr-350mbps | PASS | 350.000 | 292.960 | 5.795 / 10.971 / 13.191 | 5.739 / 10.840 / 13.139 | -0.148% |
| 1080p-1920x1080p60-hevc-hdr10-50mbps | PASS | 50.000 | 46.775 | 1.816 / 7.630 / 9.851 | 1.818 / 7.468 / 9.759 | -0.811% |
| 1080p-1920x1080p60-hevc-hdr10-100mbps | PASS | 100.000 | 86.171 | 2.426 / 9.070 / 10.801 | 2.477 / 8.941 / 10.998 | 3.118% |
| 1080p-1920x1080p60-hevc-hdr10-250mbps | PASS | 250.000 | 211.013 | 4.879 / 10.081 / 12.563 | 4.868 / 10.449 / 12.464 | -0.059% |
| 1080p-1920x1080p60-hevc-hdr10-350mbps | PASS | 350.000 | 293.593 | 5.823 / 10.558 / 13.105 | 5.843 / 10.700 / 13.124 | 1.204% |
| 1080p-1920x1080p120-av1-sdr-50mbps | INCONCLUSIVE | 50.000 | 86.448 | 4.957 / 5.732 / 9.868 | 4.949 / 5.636 / 9.774 | 0.613% |
| 1080p-1920x1080p120-av1-sdr-100mbps | PASS | 100.000 | 119.333 | 4.816 / 5.729 / 14.898 | 4.867 / 5.778 / 14.956 | 1.377% |
| 1080p-1920x1080p120-av1-sdr-250mbps | PASS | 250.000 | 261.791 | 5.766 / 8.374 / 23.248 | 5.716 / 8.674 / 23.428 | -1.574% |
| 1080p-1920x1080p120-av1-sdr-350mbps | PASS | 350.000 | 360.073 | 6.236 / 10.254 / 25.913 | 6.263 / 10.238 / 25.897 | 0.433% |
| 1080p-1920x1080p120-av1-hdr10-50mbps | INCONCLUSIVE | 50.000 | 73.130 | 4.245 / 5.697 / 9.902 | 4.248 / 5.582 / 9.788 | 0.083% |
| 1080p-1920x1080p120-av1-hdr10-100mbps | INCONCLUSIVE | 100.000 | 122.612 | 5.379 / 6.492 / 14.945 | 5.342 / 6.543 / 15.025 | 0.073% |
| 1080p-1920x1080p120-av1-hdr10-250mbps | PASS | 250.000 | 260.393 | 5.749 / 7.065 / 23.174 | 5.826 / 7.104 / 23.423 | 1.339% |
| 1080p-1920x1080p120-av1-hdr10-350mbps | PASS | 350.000 | 360.356 | 6.258 / 10.208 / 25.748 | 6.292 / 10.172 / 25.934 | 0.122% |
| 1080p-1920x1080p120-hevc-sdr-50mbps | INCONCLUSIVE | 50.000 | 62.494 | 1.527 / 6.053 / 8.846 | 1.509 / 5.967 / 8.839 | -3.366% |
| 1080p-1920x1080p120-hevc-sdr-100mbps | PASS | 100.000 | 101.643 | 1.708 / 7.575 / 9.776 | 1.678 / 7.681 / 9.685 | -1.796% |
| 1080p-1920x1080p120-hevc-sdr-250mbps | PASS | 250.000 | 221.925 | 2.549 / 9.279 / 11.066 | 2.526 / 9.257 / 11.114 | -1.012% |
| 1080p-1920x1080p120-hevc-sdr-350mbps | PASS | 350.000 | 304.845 | 3.532 / 9.649 / 11.767 | 3.499 / 9.573 / 11.773 | -2.100% |
| 1080p-1920x1080p120-hevc-hdr10-50mbps | PASS | 50.000 | 59.055 | 1.564 / 6.066 / 8.419 | 1.616 / 5.952 / 8.355 | 3.274% |
| 1080p-1920x1080p120-hevc-hdr10-100mbps | PASS | 100.000 | 99.018 | 1.794 / 7.437 / 9.672 | 1.781 / 7.496 / 9.643 | -0.046% |
| 1080p-1920x1080p120-hevc-hdr10-250mbps | PASS | 250.000 | 219.167 | 3.025 / 9.207 / 10.966 | 3.036 / 9.330 / 11.081 | 1.134% |
| 1080p-1920x1080p120-hevc-hdr10-350mbps | PASS | 350.000 | 303.668 | 3.885 / 9.637 / 11.492 | 3.971 / 9.513 / 11.608 | 2.206% |
| ultrawide-3440x1440p120-av1-sdr-50mbps | INCONCLUSIVE | 50.000 | 141.911 | 3.642 / 11.371 / 22.505 | 3.640 / 11.357 / 22.504 | 0.851% |
| ultrawide-3440x1440p120-av1-sdr-100mbps | INCONCLUSIVE | 100.000 | 185.744 | 10.300 / 12.978 / 26.233 | 10.113 / 12.825 / 26.155 | -1.457% |
| ultrawide-3440x1440p120-av1-sdr-250mbps | BASELINE_FAILURE | 250.000 | 297.394 | 17.365 / 20.256 / 39.533 | 17.366 / 20.244 / 38.730 | 0.005% |
| ultrawide-3440x1440p120-av1-sdr-350mbps | BASELINE_FAILURE | 350.000 | 388.371 | 18.684 / 23.315 / 50.369 | 18.678 / 23.486 / 50.863 | -0.015% |
| ultrawide-3440x1440p120-av1-hdr10-50mbps | INCONCLUSIVE | 50.000 | 142.056 | 4.124 / 12.327 / 22.301 | 4.143 / 12.270 / 22.305 | 0.462% |
| ultrawide-3440x1440p120-av1-hdr10-100mbps | INCONCLUSIVE | 100.000 | 170.713 | 8.530 / 13.614 / 26.146 | 8.499 / 13.597 / 26.151 | -0.013% |
| ultrawide-3440x1440p120-av1-hdr10-250mbps | PASS | 250.000 | 283.131 | 11.540 / 20.228 / 39.918 | 11.477 / 19.999 / 39.963 | -0.117% |
| ultrawide-3440x1440p120-av1-hdr10-350mbps | BASELINE_FAILURE | 350.000 | 385.138 | 18.589 / 22.121 / 50.134 | 18.592 / 22.128 / 49.935 | 0.015% |
| ultrawide-3440x1440p120-hevc-sdr-50mbps | INCONCLUSIVE | 50.000 | 70.255 | 1.992 / 4.825 / 10.806 | 1.965 / 4.978 / 10.741 | 1.161% |
| ultrawide-3440x1440p120-hevc-sdr-100mbps | PASS | 100.000 | 98.189 | 2.071 / 5.789 / 12.000 | 2.027 / 5.952 / 11.977 | -5.664% |
| ultrawide-3440x1440p120-hevc-sdr-250mbps | PASS | 250.000 | 225.307 | 2.917 / 13.827 / 20.096 | 2.911 / 13.919 / 20.021 | -0.537% |
| ultrawide-3440x1440p120-hevc-sdr-350mbps | PASS | 350.000 | 305.886 | 3.464 / 15.612 / 21.494 | 3.457 / 15.562 / 21.289 | -0.191% |
| ultrawide-3440x1440p120-hevc-hdr10-50mbps | INCONCLUSIVE | 50.000 | 64.800 | 2.082 / 4.580 / 9.978 | 2.070 / 4.448 / 10.051 | 1.534% |
| ultrawide-3440x1440p120-hevc-hdr10-100mbps | PASS | 100.000 | 94.186 | 2.125 / 5.316 / 11.114 | 2.103 / 5.367 / 11.140 | -1.038% |
| ultrawide-3440x1440p120-hevc-hdr10-250mbps | PASS | 250.000 | 222.388 | 3.086 / 12.052 / 18.005 | 3.082 / 12.051 / 18.017 | -0.136% |
| ultrawide-3440x1440p120-hevc-hdr10-350mbps | PASS | 350.000 | 304.476 | 3.624 / 14.873 / 20.392 | 3.565 / 14.590 / 20.431 | -1.028% |
| ultrawide-3440x1440p240-av1-sdr-50mbps | BASELINE_FAILURE | 50.000 | 225.205 | 8.045 / 10.959 / 16.960 | 7.987 / 10.886 / 16.939 | -0.719% |
| ultrawide-3440x1440p240-av1-sdr-100mbps | BASELINE_FAILURE | 100.000 | 239.685 | 8.025 / 11.264 / 20.636 | 8.037 / 11.327 / 20.605 | 0.679% |
| ultrawide-3440x1440p240-av1-sdr-250mbps | BASELINE_FAILURE | 250.000 | 377.887 | 10.939 / 22.013 / 36.631 | 10.958 / 22.067 / 35.559 | -0.434% |
| ultrawide-3440x1440p240-av1-sdr-350mbps | BASELINE_FAILURE | 350.000 | 440.119 | 14.333 / 23.077 / 42.922 | 14.321 / 23.064 / 42.942 | -0.083% |
| ultrawide-3440x1440p240-av1-hdr10-50mbps | BASELINE_FAILURE | 50.000 | 205.582 | 6.118 / 11.668 / 17.178 | 6.124 / 11.632 / 17.105 | -0.109% |
| ultrawide-3440x1440p240-av1-hdr10-100mbps | BASELINE_FAILURE | 100.000 | 260.701 | 8.769 / 11.689 / 21.263 | 8.792 / 11.733 / 21.260 | 0.689% |
| ultrawide-3440x1440p240-av1-hdr10-250mbps | BASELINE_FAILURE | 250.000 | 369.541 | 8.720 / 20.294 / 23.906 | 8.753 / 20.428 / 24.009 | 0.376% |
| ultrawide-3440x1440p240-av1-hdr10-350mbps | BASELINE_FAILURE | 350.000 | 479.101 | 11.383 / 24.149 / 42.741 | 11.332 / 24.115 / 42.744 | -0.657% |
| ultrawide-3440x1440p240-hevc-sdr-50mbps | PASS | 50.000 | 55.488 | 1.891 / 2.594 / 8.423 | 1.902 / 2.621 / 8.400 | 0.561% |
| ultrawide-3440x1440p240-hevc-sdr-100mbps | PASS | 100.000 | 95.374 | 1.920 / 3.021 / 11.604 | 1.896 / 3.033 / 11.609 | -1.039% |
| ultrawide-3440x1440p240-hevc-sdr-250mbps | BASELINE_FAILURE | 250.000 | 213.959 | 2.437 / 3.285 / 15.345 | 2.369 / 3.309 / 15.346 | -0.465% |
| ultrawide-3440x1440p240-hevc-sdr-350mbps | BASELINE_FAILURE | 350.000 | 297.695 | 2.845 / 3.547 / 16.962 | 2.795 / 3.429 / 16.974 | -1.770% |
| ultrawide-3440x1440p240-hevc-hdr10-50mbps | BASELINE_FAILURE | 50.000 | 50.947 | 1.981 / 2.878 / 6.294 | 1.984 / 2.886 / 6.340 | 1.047% |
| ultrawide-3440x1440p240-hevc-hdr10-100mbps | PASS | 100.000 | 92.181 | 2.017 / 3.122 / 10.622 | 2.000 / 3.096 / 10.630 | -0.853% |
| ultrawide-3440x1440p240-hevc-hdr10-250mbps | REGRESSION | 250.000 | 213.563 | 2.525 / 3.392 / 13.565 | 2.581 / 3.403 / 13.502 | 2.212% |
| ultrawide-3440x1440p240-hevc-hdr10-350mbps | BASELINE_FAILURE | 350.000 | 297.753 | 2.933 / 3.825 / 15.983 | 2.881 / 3.743 / 16.242 | -1.722% |
| 4k-3840x2160p60-av1-sdr-50mbps | INCONCLUSIVE | 50.000 | 131.636 | 3.951 / 21.626 / 38.003 | 3.837 / 21.471 / 37.962 | -2.494% |
| 4k-3840x2160p60-av1-sdr-100mbps | INCONCLUSIVE | 100.000 | 167.610 | 16.889 / 22.316 / 46.600 | 16.896 / 22.280 / 46.527 | -0.295% |
| 4k-3840x2160p60-av1-sdr-250mbps | PASS | 250.000 | 276.966 | 17.187 / 30.481 / 71.923 | 16.838 / 30.462 / 71.355 | -2.031% |
| 4k-3840x2160p60-av1-sdr-350mbps | BASELINE_FAILURE | 350.000 | 655.946 | 38.339 / 38.636 / 88.745 | 38.335 / 38.611 / 89.128 | 0.007% |
| 4k-3840x2160p60-av1-hdr10-50mbps | INCONCLUSIVE | 50.000 | 122.846 | 3.965 / 19.282 / 37.516 | 3.814 / 19.217 / 37.531 | -4.294% |
| 4k-3840x2160p60-av1-hdr10-100mbps | INCONCLUSIVE | 100.000 | 133.382 | 13.392 / 19.015 / 45.794 | 13.377 / 19.051 / 45.263 | -0.214% |
| 4k-3840x2160p60-av1-hdr10-250mbps | PASS | 250.000 | 274.818 | 16.339 / 30.138 / 71.982 | 16.337 / 30.156 / 72.040 | -0.006% |
| 4k-3840x2160p60-av1-hdr10-350mbps | BASELINE_FAILURE | 350.000 | 642.298 | 37.708 / 37.951 / 66.879 | 37.703 / 37.947 / 67.908 | -0.013% |
| 4k-3840x2160p60-hevc-sdr-50mbps | INCONCLUSIVE | 50.000 | 60.820 | 2.672 / 7.948 / 17.833 | 2.628 / 7.507 / 17.610 | -2.129% |
| 4k-3840x2160p60-hevc-sdr-100mbps | PASS | 100.000 | 92.471 | 2.653 / 10.501 / 20.967 | 2.690 / 10.432 / 20.873 | 4.311% |
| 4k-3840x2160p60-hevc-sdr-250mbps | PASS | 250.000 | 214.384 | 4.488 / 19.066 / 27.025 | 4.394 / 18.736 / 26.956 | -2.169% |
| 4k-3840x2160p60-hevc-sdr-350mbps | PASS | 350.000 | 296.923 | 5.783 / 21.194 / 29.136 | 5.768 / 21.181 / 29.292 | -0.127% |
| 4k-3840x2160p60-hevc-hdr10-50mbps | INCONCLUSIVE | 50.000 | 83.905 | 2.731 / 12.812 / 25.568 | 2.686 / 12.825 / 25.605 | 0.056% |
| 4k-3840x2160p60-hevc-hdr10-100mbps | PASS | 100.000 | 91.768 | 2.762 / 10.257 / 20.287 | 2.863 / 10.497 / 20.398 | 1.478% |
| 4k-3840x2160p60-hevc-hdr10-250mbps | PASS | 250.000 | 214.240 | 4.604 / 18.139 / 25.845 | 4.526 / 18.079 / 26.532 | -1.293% |
| 4k-3840x2160p60-hevc-hdr10-350mbps | PASS | 350.000 | 296.411 | 5.978 / 19.610 / 27.496 | 6.137 / 20.089 / 27.963 | 2.660% |
| 4k-3840x2160p120-av1-sdr-50mbps | INCONCLUSIVE | 50.000 | 218.276 | 10.904 / 17.860 / 35.609 | 10.920 / 17.841 / 35.577 | 0.138% |
| 4k-3840x2160p120-av1-sdr-100mbps | INCONCLUSIVE | 100.000 | 263.272 | 13.478 / 29.586 / 38.088 | 13.258 / 29.493 / 38.085 | -1.813% |
| 4k-3840x2160p120-av1-sdr-250mbps | BASELINE_FAILURE | 250.000 | 358.597 | 16.937 / 39.524 / 67.372 | 16.929 / 39.427 / 67.359 | -0.083% |
| 4k-3840x2160p120-av1-sdr-350mbps | BASELINE_FAILURE | 350.000 | 433.243 | 25.160 / 42.351 / 76.789 | 25.164 / 42.474 / 76.624 | 0.018% |
| 4k-3840x2160p120-av1-hdr10-50mbps | INCONCLUSIVE | 50.000 | 177.539 | 7.524 / 19.048 / 35.155 | 7.517 / 19.007 / 35.226 | 1.936% |
| 4k-3840x2160p120-av1-hdr10-100mbps | INCONCLUSIVE | 100.000 | 245.692 | 12.392 / 20.179 / 37.553 | 12.489 / 20.160 / 37.509 | -0.107% |
| 4k-3840x2160p120-av1-hdr10-250mbps | BASELINE_FAILURE | 250.000 | 342.189 | 17.865 / 36.731 / 66.982 | 18.076 / 36.745 / 67.039 | 1.282% |
| 4k-3840x2160p120-av1-hdr10-350mbps | BASELINE_FAILURE | 350.000 | 436.031 | 19.049 / 32.262 / 40.318 | 19.082 / 32.892 / 40.324 | 0.169% |
| 4k-3840x2160p120-hevc-sdr-50mbps | INCONCLUSIVE | 50.000 | 82.298 | 2.526 / 4.848 / 14.240 | 2.491 / 4.777 / 14.209 | 0.072% |
| 4k-3840x2160p120-hevc-sdr-100mbps | INCONCLUSIVE | 100.000 | 122.563 | 2.555 / 6.830 / 17.292 | 2.529 / 6.854 / 17.285 | -1.681% |
| 4k-3840x2160p120-hevc-sdr-250mbps | PASS | 250.000 | 238.909 | 2.725 / 12.597 / 22.101 | 2.767 / 12.784 / 22.202 | 1.564% |
| 4k-3840x2160p120-hevc-sdr-350mbps | PASS | 350.000 | 323.482 | 3.507 / 15.739 / 24.431 | 3.482 / 15.568 / 24.356 | -0.957% |
| 4k-3840x2160p120-hevc-hdr10-50mbps | INCONCLUSIVE | 50.000 | 82.866 | 2.632 / 5.094 / 13.960 | 2.642 / 4.853 / 13.794 | 0.405% |
| 4k-3840x2160p120-hevc-hdr10-100mbps | INCONCLUSIVE | 100.000 | 122.444 | 2.617 / 7.100 / 16.756 | 2.632 / 7.116 / 16.897 | 0.705% |
| 4k-3840x2160p120-hevc-hdr10-250mbps | PASS | 250.000 | 237.735 | 2.939 / 12.395 / 21.188 | 2.922 / 12.586 / 21.539 | 1.659% |
| 4k-3840x2160p120-hevc-hdr10-350mbps | PASS | 350.000 | 316.323 | 3.704 / 14.155 / 23.426 | 3.685 / 14.171 / 22.910 | -0.267% |

Threshold: the median paired increase must exceed both the absolute allowance (0.1 ms) and relative allowance (5.0% of baseline median) to flag a latency regression. Applied independently to VT and public completion median/p95/p99. All output accounting and delivered-rate gates must also pass.

Explicit bitrate targets require measured payload rate within ±20%. A null target retains the legacy encoder policy and does not impose a bitrate coverage gate.

A PASS means the configured gates passed in this sample. It does not prove absence of a smaller regression. Public latency includes scheduled arrival, queuing and callback delivery; VT latency ends at the internal decoder callback.

## 1080p-1920x1080p60-av1-sdr-50mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, SDR. Measured bitrate: 57.204 Mbps. Encoder target: 50.000 Mbps; measured/target: 114.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.067 | 0 / 0 | 69.030 |
| candidate / 1 | 600 / 600 | 60.069 | 0 / 0 | 71.742 |
| candidate / 2 | 600 / 600 | 60.069 | 0 / 0 | 70.091 |
| baseline / 2 | 600 / 600 | 60.067 | 0 / 0 | 70.198 |
| baseline / 3 | 600 / 600 | 60.070 | 0 / 0 | 70.219 |
| candidate / 3 | 600 / 600 | 60.069 | 0 / 0 | 73.210 |

## 1080p-1920x1080p60-av1-sdr-100mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, SDR. Measured bitrate: 106.491 Mbps. Encoder target: 100.000 Mbps; measured/target: 106.5%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.065 | 0 / 0 | 74.489 |
| baseline / 1 | 600 / 600 | 60.064 | 0 / 0 | 80.648 |
| baseline / 2 | 600 / 600 | 60.066 | 0 / 0 | 75.580 |
| candidate / 2 | 600 / 600 | 60.066 | 0 / 0 | 75.693 |
| candidate / 3 | 600 / 600 | 60.064 | 0 / 0 | 76.013 |
| baseline / 3 | 600 / 600 | 60.066 | 0 / 0 | 75.459 |

## 1080p-1920x1080p60-av1-sdr-250mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, SDR. Measured bitrate: 252.061 Mbps. Encoder target: 250.000 Mbps; measured/target: 100.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.055 | 0 / 0 | 79.422 |
| candidate / 1 | 600 / 600 | 60.055 | 0 / 0 | 81.922 |
| candidate / 2 | 600 / 600 | 60.060 | 0 / 0 | 80.041 |
| baseline / 2 | 600 / 600 | 60.056 | 0 / 0 | 79.654 |
| baseline / 3 | 600 / 600 | 60.057 | 0 / 0 | 80.448 |
| candidate / 3 | 600 / 600 | 60.057 | 0 / 0 | 81.107 |

## 1080p-1920x1080p60-av1-sdr-350mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, SDR. Measured bitrate: 341.410 Mbps. Encoder target: 350.000 Mbps; measured/target: 97.5%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.048 | 0 / 0 | 81.065 |
| baseline / 1 | 600 / 600 | 60.048 | 0 / 0 | 80.623 |
| baseline / 2 | 600 / 600 | 60.049 | 0 / 0 | 80.782 |
| candidate / 2 | 600 / 600 | 60.049 | 0 / 0 | 80.527 |
| candidate / 3 | 600 / 600 | 60.045 | 0 / 0 | 80.611 |
| baseline / 3 | 600 / 600 | 60.049 | 0 / 0 | 81.689 |

## 1080p-1920x1080p60-av1-hdr10-50mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, HDR10. Measured bitrate: 55.689 Mbps. Encoder target: 50.000 Mbps; measured/target: 111.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.062 | 0 / 0 | 69.688 |
| candidate / 1 | 600 / 600 | 60.065 | 0 / 0 | 70.561 |
| candidate / 2 | 600 / 600 | 60.062 | 0 / 0 | 71.431 |
| baseline / 2 | 600 / 600 | 60.063 | 0 / 0 | 73.502 |
| baseline / 3 | 600 / 600 | 60.063 | 0 / 0 | 72.664 |
| candidate / 3 | 600 / 600 | 60.065 | 0 / 0 | 74.211 |

## 1080p-1920x1080p60-av1-hdr10-100mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, HDR10. Measured bitrate: 105.017 Mbps. Encoder target: 100.000 Mbps; measured/target: 105.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.063 | 0 / 0 | 81.074 |
| baseline / 1 | 600 / 600 | 60.063 | 0 / 0 | 77.375 |
| baseline / 2 | 600 / 600 | 60.066 | 0 / 0 | 79.130 |
| candidate / 2 | 600 / 600 | 60.064 | 0 / 0 | 74.173 |
| candidate / 3 | 600 / 600 | 60.061 | 0 / 0 | 74.951 |
| baseline / 3 | 600 / 600 | 60.065 | 0 / 0 | 75.347 |

## 1080p-1920x1080p60-av1-hdr10-250mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, HDR10. Measured bitrate: 251.854 Mbps. Encoder target: 250.000 Mbps; measured/target: 100.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.056 | 0 / 0 | 80.714 |
| candidate / 1 | 600 / 600 | 60.055 | 0 / 0 | 81.576 |
| candidate / 2 | 600 / 600 | 60.056 | 0 / 0 | 81.163 |
| baseline / 2 | 600 / 600 | 60.055 | 0 / 0 | 88.862 |
| baseline / 3 | 600 / 600 | 60.055 | 0 / 0 | 82.272 |
| candidate / 3 | 600 / 600 | 60.055 | 0 / 0 | 88.012 |

## 1080p-1920x1080p60-av1-hdr10-350mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, HDR10. Measured bitrate: 336.219 Mbps. Encoder target: 350.000 Mbps; measured/target: 96.1%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.047 | 0 / 0 | 92.322 |
| baseline / 1 | 600 / 600 | 60.047 | 0 / 0 | 82.217 |
| baseline / 2 | 600 / 600 | 60.050 | 0 / 0 | 87.518 |
| candidate / 2 | 600 / 600 | 60.048 | 0 / 0 | 83.458 |
| candidate / 3 | 600 / 600 | 60.049 | 0 / 0 | 81.788 |
| baseline / 3 | 600 / 600 | 60.048 | 0 / 0 | 87.246 |

## 1080p-1920x1080p60-hevc-sdr-50mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, SDR. Measured bitrate: 46.760 Mbps. Encoder target: 50.000 Mbps; measured/target: 93.5%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.085 | 0 / 0 | 63.997 |
| candidate / 1 | 600 / 600 | 60.085 | 0 / 0 | 65.211 |
| candidate / 2 | 600 / 600 | 60.085 | 0 / 0 | 63.702 |
| baseline / 2 | 600 / 600 | 60.086 | 0 / 0 | 64.043 |
| baseline / 3 | 600 / 600 | 60.086 | 0 / 0 | 64.943 |
| candidate / 3 | 600 / 600 | 60.085 | 0 / 0 | 60.486 |

## 1080p-1920x1080p60-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, SDR. Measured bitrate: 85.816 Mbps. Encoder target: 100.000 Mbps; measured/target: 85.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.082 | 0 / 0 | 65.111 |
| baseline / 1 | 600 / 600 | 60.083 | 0 / 0 | 65.089 |
| baseline / 2 | 600 / 600 | 60.084 | 0 / 0 | 62.719 |
| candidate / 2 | 600 / 600 | 60.084 | 0 / 0 | 61.942 |
| candidate / 3 | 600 / 600 | 60.084 | 0 / 0 | 63.497 |
| baseline / 3 | 600 / 600 | 60.086 | 0 / 0 | 62.351 |

## 1080p-1920x1080p60-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, SDR. Measured bitrate: 210.975 Mbps. Encoder target: 250.000 Mbps; measured/target: 84.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.065 | 0 / 0 | 63.807 |
| candidate / 1 | 600 / 600 | 60.065 | 0 / 0 | 64.819 |
| candidate / 2 | 600 / 600 | 60.067 | 0 / 0 | 62.845 |
| baseline / 2 | 600 / 600 | 60.066 | 0 / 0 | 64.118 |
| baseline / 3 | 600 / 600 | 60.066 | 0 / 0 | 64.544 |
| candidate / 3 | 600 / 600 | 60.065 | 0 / 0 | 64.862 |

## 1080p-1920x1080p60-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, SDR. Measured bitrate: 292.960 Mbps. Encoder target: 350.000 Mbps; measured/target: 83.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.063 | 0 / 0 | 63.150 |
| baseline / 1 | 600 / 600 | 60.062 | 0 / 0 | 68.867 |
| baseline / 2 | 600 / 600 | 60.065 | 0 / 0 | 62.962 |
| candidate / 2 | 600 / 600 | 60.061 | 0 / 0 | 63.497 |
| candidate / 3 | 600 / 600 | 60.066 | 0 / 0 | 63.628 |
| baseline / 3 | 600 / 600 | 60.062 | 0 / 0 | 72.900 |

## 1080p-1920x1080p60-hevc-hdr10-50mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, HDR10. Measured bitrate: 46.775 Mbps. Encoder target: 50.000 Mbps; measured/target: 93.6%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.081 | 0 / 0 | 65.012 |
| candidate / 1 | 600 / 600 | 60.082 | 0 / 0 | 65.752 |
| candidate / 2 | 600 / 600 | 60.081 | 0 / 0 | 67.674 |
| baseline / 2 | 600 / 600 | 60.084 | 0 / 0 | 69.092 |
| baseline / 3 | 600 / 600 | 60.084 | 0 / 0 | 71.520 |
| candidate / 3 | 600 / 600 | 60.088 | 0 / 0 | 65.273 |

## 1080p-1920x1080p60-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, HDR10. Measured bitrate: 86.171 Mbps. Encoder target: 100.000 Mbps; measured/target: 86.2%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.078 | 0 / 0 | 62.564 |
| baseline / 1 | 600 / 600 | 60.078 | 0 / 0 | 62.954 |
| baseline / 2 | 600 / 600 | 60.079 | 0 / 0 | 63.148 |
| candidate / 2 | 600 / 600 | 60.079 | 0 / 0 | 64.248 |
| candidate / 3 | 600 / 600 | 60.079 | 0 / 0 | 74.550 |
| baseline / 3 | 600 / 600 | 60.078 | 0 / 0 | 63.724 |

## 1080p-1920x1080p60-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, HDR10. Measured bitrate: 211.013 Mbps. Encoder target: 250.000 Mbps; measured/target: 84.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.066 | 0 / 0 | 63.781 |
| candidate / 1 | 600 / 600 | 60.067 | 0 / 0 | 70.936 |
| candidate / 2 | 600 / 600 | 60.065 | 0 / 0 | 65.157 |
| baseline / 2 | 600 / 600 | 60.066 | 0 / 0 | 63.615 |
| baseline / 3 | 600 / 600 | 60.066 | 0 / 0 | 65.081 |
| candidate / 3 | 600 / 600 | 60.064 | 0 / 0 | 63.783 |

## 1080p-1920x1080p60-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, HDR10. Measured bitrate: 293.593 Mbps. Encoder target: 350.000 Mbps; measured/target: 83.9%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.063 | 0 / 0 | 64.365 |
| baseline / 1 | 600 / 600 | 60.060 | 0 / 0 | 69.857 |
| baseline / 2 | 600 / 600 | 60.060 | 0 / 0 | 70.803 |
| candidate / 2 | 600 / 600 | 60.059 | 0 / 0 | 63.681 |
| candidate / 3 | 600 / 600 | 60.062 | 0 / 0 | 64.066 |
| baseline / 3 | 600 / 600 | 60.063 | 0 / 0 | 64.405 |

## 1080p-1920x1080p120-av1-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, SDR. Measured bitrate: 86.448 Mbps. Encoder target: 50.000 Mbps; measured/target: 172.9%.

measured payload bitrate 86.448 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.079 | 0 / 0 | 66.998 |
| candidate / 1 | 1200 / 1200 | 120.079 | 0 / 0 | 64.362 |
| candidate / 2 | 1200 / 1200 | 120.073 | 0 / 0 | 67.187 |
| baseline / 2 | 1200 / 1200 | 120.072 | 0 / 0 | 67.778 |
| baseline / 3 | 1200 / 1200 | 120.074 | 0 / 0 | 67.720 |
| candidate / 3 | 1200 / 1200 | 120.075 | 0 / 0 | 67.901 |

## 1080p-1920x1080p120-av1-sdr-100mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, SDR. Measured bitrate: 119.333 Mbps. Encoder target: 100.000 Mbps; measured/target: 119.3%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.046 | 0 / 0 | 69.131 |
| baseline / 1 | 1200 / 1200 | 120.038 | 0 / 0 | 79.808 |
| baseline / 2 | 1200 / 1200 | 120.042 | 0 / 0 | 71.348 |
| candidate / 2 | 1200 / 1200 | 120.037 | 0 / 0 | 71.525 |
| candidate / 3 | 1200 / 1200 | 120.036 | 0 / 0 | 69.724 |
| baseline / 3 | 1200 / 1200 | 120.035 | 0 / 0 | 87.029 |

## 1080p-1920x1080p120-av1-sdr-250mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, SDR. Measured bitrate: 261.791 Mbps. Encoder target: 250.000 Mbps; measured/target: 104.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.026 | 0 / 0 | 77.321 |
| candidate / 1 | 1200 / 1200 | 120.031 | 0 / 0 | 77.040 |
| candidate / 2 | 1200 / 1200 | 120.025 | 0 / 0 | 75.400 |
| baseline / 2 | 1200 / 1200 | 120.034 | 0 / 0 | 76.660 |
| baseline / 3 | 1200 / 1200 | 120.033 | 0 / 0 | 78.238 |
| candidate / 3 | 1200 / 1200 | 120.025 | 0 / 0 | 75.584 |

## 1080p-1920x1080p120-av1-sdr-350mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, SDR. Measured bitrate: 360.073 Mbps. Encoder target: 350.000 Mbps; measured/target: 102.9%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.024 | 0 / 0 | 78.665 |
| baseline / 1 | 1200 / 1200 | 120.018 | 0 / 0 | 81.384 |
| baseline / 2 | 1200 / 1200 | 120.017 | 0 / 0 | 77.958 |
| candidate / 2 | 1200 / 1200 | 120.017 | 0 / 0 | 77.644 |
| candidate / 3 | 1200 / 1200 | 120.020 | 0 / 0 | 82.709 |
| baseline / 3 | 1200 / 1200 | 120.020 | 0 / 0 | 78.635 |

## 1080p-1920x1080p120-av1-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, HDR10. Measured bitrate: 73.130 Mbps. Encoder target: 50.000 Mbps; measured/target: 146.3%.

measured payload bitrate 73.130 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.077 | 0 / 0 | 67.361 |
| candidate / 1 | 1200 / 1200 | 120.076 | 0 / 0 | 67.792 |
| candidate / 2 | 1200 / 1200 | 120.077 | 0 / 0 | 66.796 |
| baseline / 2 | 1200 / 1200 | 120.078 | 0 / 0 | 68.603 |
| baseline / 3 | 1200 / 1200 | 120.075 | 0 / 0 | 68.727 |
| candidate / 3 | 1200 / 1200 | 120.072 | 0 / 0 | 67.839 |

## 1080p-1920x1080p120-av1-hdr10-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, HDR10. Measured bitrate: 122.612 Mbps. Encoder target: 100.000 Mbps; measured/target: 122.6%.

measured payload bitrate 122.612 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.073 | 0 / 0 | 70.594 |
| baseline / 1 | 1200 / 1200 | 120.071 | 0 / 0 | 70.038 |
| baseline / 2 | 1200 / 1200 | 120.077 | 0 / 0 | 69.916 |
| candidate / 2 | 1200 / 1200 | 120.066 | 0 / 0 | 79.546 |
| candidate / 3 | 1200 / 1200 | 120.068 | 0 / 0 | 74.311 |
| baseline / 3 | 1200 / 1200 | 120.075 | 0 / 0 | 74.883 |

## 1080p-1920x1080p120-av1-hdr10-250mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, HDR10. Measured bitrate: 260.393 Mbps. Encoder target: 250.000 Mbps; measured/target: 104.2%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.022 | 0 / 0 | 77.022 |
| candidate / 1 | 1200 / 1200 | 120.027 | 0 / 0 | 78.055 |
| candidate / 2 | 1200 / 1200 | 120.023 | 0 / 0 | 77.244 |
| baseline / 2 | 1200 / 1200 | 120.027 | 0 / 0 | 77.272 |
| baseline / 3 | 1200 / 1200 | 120.024 | 0 / 0 | 84.031 |
| candidate / 3 | 1200 / 1200 | 120.025 | 0 / 0 | 78.195 |

## 1080p-1920x1080p120-av1-hdr10-350mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, HDR10. Measured bitrate: 360.356 Mbps. Encoder target: 350.000 Mbps; measured/target: 103.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.019 | 0 / 0 | 79.454 |
| baseline / 1 | 1200 / 1200 | 120.027 | 0 / 0 | 83.956 |
| baseline / 2 | 1200 / 1200 | 120.033 | 0 / 0 | 79.310 |
| candidate / 2 | 1200 / 1200 | 120.018 | 0 / 0 | 78.198 |
| candidate / 3 | 1200 / 1200 | 120.018 | 0 / 0 | 84.094 |
| baseline / 3 | 1200 / 1200 | 120.018 | 0 / 0 | 80.119 |

## 1080p-1920x1080p120-hevc-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, SDR. Measured bitrate: 62.494 Mbps. Encoder target: 50.000 Mbps; measured/target: 125.0%.

measured payload bitrate 62.494 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.075 | 0 / 0 | 62.424 |
| candidate / 1 | 1200 / 1200 | 120.077 | 0 / 0 | 64.118 |
| candidate / 2 | 1200 / 1200 | 120.078 | 0 / 0 | 64.734 |
| baseline / 2 | 1200 / 1200 | 120.076 | 0 / 0 | 64.257 |
| baseline / 3 | 1200 / 1200 | 120.078 | 0 / 0 | 65.019 |
| candidate / 3 | 1200 / 1200 | 120.080 | 0 / 0 | 67.238 |

## 1080p-1920x1080p120-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, SDR. Measured bitrate: 101.643 Mbps. Encoder target: 100.000 Mbps; measured/target: 101.6%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.075 | 0 / 0 | 62.177 |
| baseline / 1 | 1200 / 1200 | 120.072 | 0 / 0 | 63.894 |
| baseline / 2 | 1200 / 1200 | 120.075 | 0 / 0 | 63.644 |
| candidate / 2 | 1200 / 1200 | 120.075 | 0 / 0 | 64.211 |
| candidate / 3 | 1200 / 1200 | 120.074 | 0 / 0 | 62.559 |
| baseline / 3 | 1200 / 1200 | 120.075 | 0 / 0 | 62.917 |

## 1080p-1920x1080p120-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, SDR. Measured bitrate: 221.925 Mbps. Encoder target: 250.000 Mbps; measured/target: 88.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.057 | 0 / 0 | 63.189 |
| candidate / 1 | 1200 / 1200 | 120.056 | 0 / 0 | 66.548 |
| candidate / 2 | 1200 / 1200 | 120.049 | 0 / 0 | 62.347 |
| baseline / 2 | 1200 / 1200 | 120.055 | 0 / 0 | 69.416 |
| baseline / 3 | 1200 / 1200 | 120.048 | 0 / 0 | 61.772 |
| candidate / 3 | 1200 / 1200 | 120.051 | 0 / 0 | 62.017 |

## 1080p-1920x1080p120-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, SDR. Measured bitrate: 304.845 Mbps. Encoder target: 350.000 Mbps; measured/target: 87.1%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.039 | 0 / 0 | 63.417 |
| baseline / 1 | 1200 / 1200 | 120.039 | 0 / 0 | 63.422 |
| baseline / 2 | 1200 / 1200 | 120.037 | 0 / 0 | 62.716 |
| candidate / 2 | 1200 / 1200 | 120.041 | 0 / 0 | 63.825 |
| candidate / 3 | 1200 / 1200 | 120.039 | 0 / 0 | 63.391 |
| baseline / 3 | 1200 / 1200 | 120.048 | 0 / 0 | 65.115 |

## 1080p-1920x1080p120-hevc-hdr10-50mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, HDR10. Measured bitrate: 59.055 Mbps. Encoder target: 50.000 Mbps; measured/target: 118.1%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.091 | 0 / 0 | 65.476 |
| candidate / 1 | 1200 / 1200 | 120.077 | 0 / 0 | 62.295 |
| candidate / 2 | 1200 / 1200 | 120.077 | 0 / 0 | 69.534 |
| baseline / 2 | 1200 / 1200 | 120.071 | 0 / 0 | 70.231 |
| baseline / 3 | 1200 / 1200 | 120.081 | 0 / 0 | 65.191 |
| candidate / 3 | 1200 / 1200 | 120.073 | 0 / 0 | 65.124 |

## 1080p-1920x1080p120-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, HDR10. Measured bitrate: 99.018 Mbps. Encoder target: 100.000 Mbps; measured/target: 99.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.070 | 0 / 0 | 64.820 |
| baseline / 1 | 1200 / 1200 | 120.069 | 0 / 0 | 65.471 |
| baseline / 2 | 1200 / 1200 | 120.076 | 0 / 0 | 64.979 |
| candidate / 2 | 1200 / 1200 | 120.076 | 0 / 0 | 68.495 |
| candidate / 3 | 1200 / 1200 | 120.068 | 0 / 0 | 67.509 |
| baseline / 3 | 1200 / 1200 | 120.079 | 0 / 0 | 69.943 |

## 1080p-1920x1080p120-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, HDR10. Measured bitrate: 219.167 Mbps. Encoder target: 250.000 Mbps; measured/target: 87.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.057 | 0 / 0 | 74.831 |
| candidate / 1 | 1200 / 1200 | 120.047 | 0 / 0 | 65.603 |
| candidate / 2 | 1200 / 1200 | 120.062 | 0 / 0 | 63.695 |
| baseline / 2 | 1200 / 1200 | 120.055 | 0 / 0 | 63.868 |
| baseline / 3 | 1200 / 1200 | 120.065 | 0 / 0 | 61.906 |
| candidate / 3 | 1200 / 1200 | 120.064 | 0 / 0 | 65.663 |

## 1080p-1920x1080p120-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, HDR10. Measured bitrate: 303.668 Mbps. Encoder target: 350.000 Mbps; measured/target: 86.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.042 | 0 / 0 | 63.304 |
| baseline / 1 | 1200 / 1200 | 120.051 | 0 / 0 | 62.813 |
| baseline / 2 | 1200 / 1200 | 120.042 | 0 / 0 | 63.977 |
| candidate / 2 | 1200 / 1200 | 120.041 | 0 / 0 | 64.904 |
| candidate / 3 | 1200 / 1200 | 120.048 | 0 / 0 | 64.183 |
| baseline / 3 | 1200 / 1200 | 120.043 | 0 / 0 | 64.159 |

## ultrawide-3440x1440p120-av1-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, SDR. Measured bitrate: 141.911 Mbps. Encoder target: 50.000 Mbps; measured/target: 283.8%.

measured payload bitrate 141.911 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.068 | 0 / 0 | 73.690 |
| candidate / 1 | 1200 / 1200 | 120.067 | 0 / 0 | 74.218 |
| candidate / 2 | 1200 / 1200 | 120.073 | 0 / 0 | 72.826 |
| baseline / 2 | 1200 / 1200 | 120.065 | 0 / 0 | 73.245 |
| baseline / 3 | 1200 / 1200 | 120.067 | 0 / 0 | 72.174 |
| candidate / 3 | 1200 / 1200 | 120.076 | 0 / 0 | 72.228 |

## ultrawide-3440x1440p120-av1-sdr-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, SDR. Measured bitrate: 185.744 Mbps. Encoder target: 100.000 Mbps; measured/target: 185.7%.

measured payload bitrate 185.744 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.059 | 0 / 0 | 77.883 |
| baseline / 1 | 1200 / 1200 | 120.058 | 0 / 0 | 86.149 |
| baseline / 2 | 1200 / 1200 | 120.058 | 0 / 0 | 78.625 |
| candidate / 2 | 1200 / 1200 | 120.058 | 0 / 0 | 78.170 |
| candidate / 3 | 1200 / 1200 | 120.058 | 0 / 0 | 77.245 |
| baseline / 3 | 1200 / 1200 | 120.061 | 0 / 0 | 78.933 |

## ultrawide-3440x1440p120-av1-sdr-250mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, SDR. Measured bitrate: 297.394 Mbps. Encoder target: 250.000 Mbps; measured/target: 119.0%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=252; failed_or_cancelled_or_dropped=9; expected_display_mismatches=9; resets=21; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=293; failed_or_cancelled_or_dropped=11; expected_display_mismatches=11; resets=29; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=295; failed_or_cancelled_or_dropped=11; expected_display_mismatches=11; resets=26; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=250; failed_or_cancelled_or_dropped=9; expected_display_mismatches=9; resets=21; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=293; failed_or_cancelled_or_dropped=11; expected_display_mismatches=11; resets=29; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=294; failed_or_cancelled_or_dropped=10; expected_display_mismatches=10; resets=25; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 939 / 1200 | 92.653 | 252 / 9 | 97.097 |
| candidate / 1 | 896 / 1200 | 89.177 | 293 / 11 | 89.533 |
| candidate / 2 | 894 / 1200 | 89.015 | 295 / 11 | 91.154 |
| baseline / 2 | 941 / 1200 | 92.879 | 250 / 9 | 96.488 |
| baseline / 3 | 896 / 1200 | 89.183 | 293 / 11 | 89.722 |
| candidate / 3 | 896 / 1200 | 89.191 | 294 / 10 | 91.209 |

## ultrawide-3440x1440p120-av1-sdr-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, SDR. Measured bitrate: 388.371 Mbps. Encoder target: 350.000 Mbps; measured/target: 111.0%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=369; failed_or_cancelled_or_dropped=12; expected_display_mismatches=12; resets=30; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=374; failed_or_cancelled_or_dropped=12; expected_display_mismatches=12; resets=30; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=374; failed_or_cancelled_or_dropped=10; expected_display_mismatches=10; resets=30; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=362; failed_or_cancelled_or_dropped=10; expected_display_mismatches=10; resets=30; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=379; failed_or_cancelled_or_dropped=12; expected_display_mismatches=12; resets=30; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=366; failed_or_cancelled_or_dropped=11; expected_display_mismatches=11; resets=30; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 819 / 1200 | 81.245 | 369 / 12 | 97.365 |
| baseline / 1 | 814 / 1200 | 80.770 | 374 / 12 | 101.275 |
| baseline / 2 | 816 / 1200 | 80.958 | 374 / 10 | 99.748 |
| candidate / 2 | 828 / 1200 | 82.151 | 362 / 10 | 97.824 |
| candidate / 3 | 809 / 1200 | 80.251 | 379 / 12 | 96.287 |
| baseline / 3 | 823 / 1200 | 81.640 | 366 / 11 | 97.728 |

## ultrawide-3440x1440p120-av1-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, HDR10. Measured bitrate: 142.056 Mbps. Encoder target: 50.000 Mbps; measured/target: 284.1%.

measured payload bitrate 142.056 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 119.954 | 0 / 0 | 77.193 |
| candidate / 1 | 1200 / 1200 | 119.963 | 0 / 0 | 74.683 |
| candidate / 2 | 1200 / 1200 | 119.952 | 0 / 0 | 79.558 |
| baseline / 2 | 1200 / 1200 | 119.952 | 0 / 0 | 74.119 |
| baseline / 3 | 1200 / 1200 | 119.955 | 0 / 0 | 74.350 |
| candidate / 3 | 1200 / 1200 | 119.951 | 0 / 0 | 73.885 |

## ultrawide-3440x1440p120-av1-hdr10-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, HDR10. Measured bitrate: 170.713 Mbps. Encoder target: 100.000 Mbps; measured/target: 170.7%.

measured payload bitrate 170.713 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 119.991 | 0 / 0 | 78.498 |
| baseline / 1 | 1200 / 1200 | 119.993 | 0 / 0 | 77.891 |
| baseline / 2 | 1200 / 1200 | 119.996 | 0 / 0 | 78.621 |
| candidate / 2 | 1200 / 1200 | 119.992 | 0 / 0 | 79.879 |
| candidate / 3 | 1200 / 1200 | 119.991 | 0 / 0 | 78.767 |
| baseline / 3 | 1200 / 1200 | 119.990 | 0 / 0 | 78.928 |

## ultrawide-3440x1440p120-av1-hdr10-250mbps

Status: PASS

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, HDR10. Measured bitrate: 283.131 Mbps. Encoder target: 250.000 Mbps; measured/target: 113.3%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 119.959 | 0 / 0 | 91.594 |
| candidate / 1 | 1200 / 1200 | 119.966 | 0 / 0 | 97.346 |
| candidate / 2 | 1200 / 1200 | 119.974 | 0 / 0 | 93.507 |
| baseline / 2 | 1200 / 1200 | 119.964 | 0 / 0 | 101.606 |
| baseline / 3 | 1200 / 1200 | 119.965 | 0 / 0 | 91.765 |
| candidate / 3 | 1200 / 1200 | 119.973 | 0 / 0 | 92.976 |

## ultrawide-3440x1440p120-av1-hdr10-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, HDR10. Measured bitrate: 385.138 Mbps. Encoder target: 350.000 Mbps; measured/target: 110.0%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=314; failed_or_cancelled_or_dropped=12; expected_display_mismatches=12; resets=20; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=325; failed_or_cancelled_or_dropped=12; expected_display_mismatches=12; resets=20; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=320; failed_or_cancelled_or_dropped=13; expected_display_mismatches=13; resets=20; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=340; failed_or_cancelled_or_dropped=10; expected_display_mismatches=10; resets=20; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=333; failed_or_cancelled_or_dropped=11; expected_display_mismatches=11; resets=20; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=338; failed_or_cancelled_or_dropped=13; expected_display_mismatches=13; resets=20; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 874 / 1200 | 86.742 | 314 / 12 | 102.772 |
| baseline / 1 | 863 / 1200 | 85.628 | 325 / 12 | 98.709 |
| baseline / 2 | 867 / 1200 | 86.034 | 320 / 13 | 99.270 |
| candidate / 2 | 850 / 1200 | 84.373 | 340 / 10 | 97.991 |
| candidate / 3 | 856 / 1200 | 84.954 | 333 / 11 | 97.807 |
| baseline / 3 | 849 / 1200 | 84.256 | 338 / 13 | 97.333 |

## ultrawide-3440x1440p120-hevc-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, SDR. Measured bitrate: 70.255 Mbps. Encoder target: 50.000 Mbps; measured/target: 140.5%.

measured payload bitrate 70.255 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.073 | 0 / 0 | 66.455 |
| candidate / 1 | 1200 / 1200 | 120.076 | 0 / 0 | 66.573 |
| candidate / 2 | 1200 / 1200 | 120.076 | 0 / 0 | 65.210 |
| baseline / 2 | 1200 / 1200 | 120.074 | 0 / 0 | 67.479 |
| baseline / 3 | 1200 / 1200 | 120.076 | 0 / 0 | 66.998 |
| candidate / 3 | 1200 / 1200 | 120.076 | 0 / 0 | 65.555 |

## ultrawide-3440x1440p120-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, SDR. Measured bitrate: 98.189 Mbps. Encoder target: 100.000 Mbps; measured/target: 98.2%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.077 | 0 / 0 | 66.490 |
| baseline / 1 | 1200 / 1200 | 120.067 | 0 / 0 | 66.778 |
| baseline / 2 | 1200 / 1200 | 120.071 | 0 / 0 | 66.508 |
| candidate / 2 | 1200 / 1200 | 120.070 | 0 / 0 | 67.250 |
| candidate / 3 | 1200 / 1200 | 120.083 | 0 / 0 | 66.968 |
| baseline / 3 | 1200 / 1200 | 120.070 | 0 / 0 | 73.888 |

## ultrawide-3440x1440p120-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, SDR. Measured bitrate: 225.307 Mbps. Encoder target: 250.000 Mbps; measured/target: 90.1%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.051 | 0 / 0 | 68.653 |
| candidate / 1 | 1200 / 1200 | 120.047 | 0 / 0 | 68.601 |
| candidate / 2 | 1200 / 1200 | 120.050 | 0 / 0 | 69.052 |
| baseline / 2 | 1200 / 1200 | 120.050 | 0 / 0 | 68.487 |
| baseline / 3 | 1200 / 1200 | 120.050 | 0 / 0 | 69.194 |
| candidate / 3 | 1200 / 1200 | 120.049 | 0 / 0 | 68.395 |

## ultrawide-3440x1440p120-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, SDR. Measured bitrate: 305.886 Mbps. Encoder target: 350.000 Mbps; measured/target: 87.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.046 | 0 / 0 | 66.866 |
| baseline / 1 | 1200 / 1200 | 120.042 | 0 / 0 | 69.019 |
| baseline / 2 | 1200 / 1200 | 120.044 | 0 / 0 | 71.803 |
| candidate / 2 | 1200 / 1200 | 120.047 | 0 / 0 | 69.628 |
| candidate / 3 | 1200 / 1200 | 120.057 | 0 / 0 | 69.367 |
| baseline / 3 | 1200 / 1200 | 120.044 | 0 / 0 | 68.813 |

## ultrawide-3440x1440p120-hevc-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, HDR10. Measured bitrate: 64.800 Mbps. Encoder target: 50.000 Mbps; measured/target: 129.6%.

measured payload bitrate 64.800 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.068 | 0 / 0 | 67.463 |
| candidate / 1 | 1200 / 1200 | 120.068 | 0 / 0 | 65.539 |
| candidate / 2 | 1200 / 1200 | 120.074 | 0 / 0 | 66.808 |
| baseline / 2 | 1200 / 1200 | 120.074 | 0 / 0 | 66.801 |
| baseline / 3 | 1200 / 1200 | 120.067 | 0 / 0 | 67.652 |
| candidate / 3 | 1200 / 1200 | 120.074 | 0 / 0 | 66.394 |

## ultrawide-3440x1440p120-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, HDR10. Measured bitrate: 94.186 Mbps. Encoder target: 100.000 Mbps; measured/target: 94.2%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.062 | 0 / 0 | 66.338 |
| baseline / 1 | 1200 / 1200 | 120.077 | 0 / 0 | 66.476 |
| baseline / 2 | 1200 / 1200 | 120.064 | 0 / 0 | 63.564 |
| candidate / 2 | 1200 / 1200 | 120.070 | 0 / 0 | 65.549 |
| candidate / 3 | 1200 / 1200 | 120.066 | 0 / 0 | 65.941 |
| baseline / 3 | 1200 / 1200 | 120.060 | 0 / 0 | 68.086 |

## ultrawide-3440x1440p120-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, HDR10. Measured bitrate: 222.388 Mbps. Encoder target: 250.000 Mbps; measured/target: 89.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.046 | 0 / 0 | 68.839 |
| candidate / 1 | 1200 / 1200 | 120.050 | 0 / 0 | 75.202 |
| candidate / 2 | 1200 / 1200 | 120.052 | 0 / 0 | 67.649 |
| baseline / 2 | 1200 / 1200 | 120.054 | 0 / 0 | 70.721 |
| baseline / 3 | 1200 / 1200 | 120.042 | 0 / 0 | 68.709 |
| candidate / 3 | 1200 / 1200 | 120.047 | 0 / 0 | 69.476 |

## ultrawide-3440x1440p120-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, HDR10. Measured bitrate: 304.476 Mbps. Encoder target: 350.000 Mbps; measured/target: 87.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.043 | 0 / 0 | 68.852 |
| baseline / 1 | 1200 / 1200 | 120.045 | 0 / 0 | 75.157 |
| baseline / 2 | 1200 / 1200 | 120.047 | 0 / 0 | 69.832 |
| candidate / 2 | 1200 / 1200 | 120.045 | 0 / 0 | 69.980 |
| candidate / 3 | 1200 / 1200 | 120.045 | 0 / 0 | 68.490 |
| baseline / 3 | 1200 / 1200 | 120.044 | 0 / 0 | 76.788 |

## ultrawide-3440x1440p240-av1-sdr-50mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; AV1, SDR. Measured bitrate: 225.205 Mbps. Encoder target: 50.000 Mbps; measured/target: 450.4%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 2342 / 2400 | 234.181 | 56 / 2 | 70.246 |
| candidate / 1 | 2341 / 2400 | 234.068 | 57 / 2 | 74.249 |
| candidate / 2 | 2341 / 2400 | 234.072 | 57 / 2 | 74.768 |
| baseline / 2 | 2342 / 2400 | 234.168 | 56 / 2 | 69.548 |
| baseline / 3 | 2342 / 2400 | 234.164 | 56 / 2 | 69.632 |
| candidate / 3 | 2342 / 2400 | 234.171 | 56 / 2 | 69.508 |

## ultrawide-3440x1440p240-av1-sdr-100mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; AV1, SDR. Measured bitrate: 239.685 Mbps. Encoder target: 100.000 Mbps; measured/target: 239.7%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=5; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 2341 / 2400 | 233.935 | 57 / 2 | 72.599 |
| baseline / 1 | 2340 / 2400 | 233.837 | 58 / 2 | 266.234 |
| baseline / 2 | 2341 / 2400 | 233.936 | 57 / 2 | 72.811 |
| candidate / 2 | 2340 / 2400 | 233.826 | 58 / 2 | 266.504 |
| candidate / 3 | 2341 / 2400 | 233.941 | 57 / 2 | 74.977 |
| baseline / 3 | 2341 / 2400 | 233.941 | 57 / 2 | 72.439 |

## ultrawide-3440x1440p240-av1-sdr-250mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; AV1, SDR. Measured bitrate: 377.887 Mbps. Encoder target: 250.000 Mbps; measured/target: 151.2%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1471; failed_or_cancelled_or_dropped=69; expected_display_mismatches=69; resets=141; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1465; failed_or_cancelled_or_dropped=67; expected_display_mismatches=67; resets=136; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1441; failed_or_cancelled_or_dropped=70; expected_display_mismatches=70; resets=141; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1448; failed_or_cancelled_or_dropped=69; expected_display_mismatches=69; resets=136; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1421; failed_or_cancelled_or_dropped=73; expected_display_mismatches=73; resets=131; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1418; failed_or_cancelled_or_dropped=66; expected_display_mismatches=66; resets=137; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 860 / 2400 | 86.032 | 1471 / 69 | 272.602 |
| candidate / 1 | 868 / 2400 | 86.833 | 1465 / 67 | 273.535 |
| candidate / 2 | 889 / 2400 | 88.936 | 1441 / 70 | 273.649 |
| baseline / 2 | 883 / 2400 | 88.333 | 1448 / 69 | 272.700 |
| baseline / 3 | 906 / 2400 | 90.634 | 1421 / 73 | 272.358 |
| candidate / 3 | 916 / 2400 | 91.635 | 1418 / 66 | 272.814 |

## ultrawide-3440x1440p240-av1-sdr-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; AV1, SDR. Measured bitrate: 440.119 Mbps. Encoder target: 350.000 Mbps; measured/target: 125.7%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1841; failed_or_cancelled_or_dropped=74; expected_display_mismatches=74; resets=171; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1836; failed_or_cancelled_or_dropped=75; expected_display_mismatches=75; resets=165; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1841; failed_or_cancelled_or_dropped=76; expected_display_mismatches=76; resets=174; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1839; failed_or_cancelled_or_dropped=75; expected_display_mismatches=75; resets=174; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1845; failed_or_cancelled_or_dropped=70; expected_display_mismatches=70; resets=163; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1847; failed_or_cancelled_or_dropped=71; expected_display_mismatches=71; resets=161; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 485 / 2400 | 48.518 | 1841 / 74 | 272.717 |
| baseline / 1 | 489 / 2400 | 48.919 | 1836 / 75 | 271.836 |
| baseline / 2 | 483 / 2400 | 48.318 | 1841 / 76 | 271.622 |
| candidate / 2 | 486 / 2400 | 48.618 | 1839 / 75 | 268.884 |
| candidate / 3 | 485 / 2400 | 48.518 | 1845 / 70 | 273.916 |
| baseline / 3 | 482 / 2400 | 48.218 | 1847 / 71 | 272.154 |

## ultrawide-3440x1440p240-av1-hdr10-50mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; AV1, HDR10. Measured bitrate: 205.582 Mbps. Encoder target: 50.000 Mbps; measured/target: 411.2%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=59; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=6; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 2342 / 2400 | 234.222 | 57 / 1 | 71.168 |
| candidate / 1 | 2342 / 2400 | 234.220 | 56 / 2 | 69.696 |
| candidate / 2 | 2342 / 2400 | 234.219 | 56 / 2 | 70.116 |
| baseline / 2 | 2342 / 2400 | 234.221 | 57 / 1 | 71.093 |
| baseline / 3 | 2342 / 2400 | 234.219 | 56 / 2 | 69.959 |
| candidate / 3 | 2340 / 2400 | 234.024 | 59 / 1 | 266.698 |

## ultrawide-3440x1440p240-av1-hdr10-100mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; AV1, HDR10. Measured bitrate: 260.701 Mbps. Encoder target: 100.000 Mbps; measured/target: 260.7%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=59; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=6; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 2340 / 2400 | 233.868 | 58 / 2 | 266.328 |
| baseline / 1 | 2340 / 2400 | 233.881 | 59 / 1 | 265.921 |
| baseline / 2 | 2341 / 2400 | 233.974 | 57 / 2 | 73.962 |
| candidate / 2 | 2340 / 2400 | 233.879 | 58 / 2 | 266.700 |
| candidate / 3 | 2340 / 2400 | 233.893 | 58 / 2 | 268.591 |
| baseline / 3 | 2341 / 2400 | 233.965 | 58 / 1 | 75.873 |

Observed threshold breach: public_median_ms: +1.640 ms (+10.46%).

## ultrawide-3440x1440p240-av1-hdr10-250mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; AV1, HDR10. Measured bitrate: 369.541 Mbps. Encoder target: 250.000 Mbps; measured/target: 147.8%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1185; failed_or_cancelled_or_dropped=44; expected_display_mismatches=44; resets=58; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1212; failed_or_cancelled_or_dropped=48; expected_display_mismatches=48; resets=58; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1216; failed_or_cancelled_or_dropped=48; expected_display_mismatches=48; resets=57; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1112; failed_or_cancelled_or_dropped=42; expected_display_mismatches=42; resets=63; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1233; failed_or_cancelled_or_dropped=44; expected_display_mismatches=44; resets=57; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1284; failed_or_cancelled_or_dropped=50; expected_display_mismatches=50; resets=59; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1171 / 2400 | 116.334 | 1185 / 44 | 274.826 |
| candidate / 1 | 1140 / 2400 | 114.043 | 1212 / 48 | 275.168 |
| candidate / 2 | 1136 / 2400 | 113.643 | 1216 / 48 | 275.029 |
| baseline / 2 | 1246 / 2400 | 123.857 | 1112 / 42 | 274.388 |
| baseline / 3 | 1123 / 2400 | 112.343 | 1233 / 44 | 274.635 |
| candidate / 3 | 1066 / 2400 | 106.639 | 1284 / 50 | 274.978 |

Observed threshold breach: vt_p95_ms: +1.047 ms (+5.40%).

## ultrawide-3440x1440p240-av1-hdr10-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; AV1, HDR10. Measured bitrate: 479.101 Mbps. Encoder target: 350.000 Mbps; measured/target: 136.9%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1680; failed_or_cancelled_or_dropped=75; expected_display_mismatches=75; resets=76; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1660; failed_or_cancelled_or_dropped=76; expected_display_mismatches=76; resets=76; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1697; failed_or_cancelled_or_dropped=71; expected_display_mismatches=71; resets=74; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1659; failed_or_cancelled_or_dropped=75; expected_display_mismatches=75; resets=79; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1667; failed_or_cancelled_or_dropped=68; expected_display_mismatches=68; resets=73; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=1701; failed_or_cancelled_or_dropped=70; expected_display_mismatches=70; resets=78; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 645 / 2400 | 64.524 | 1680 / 75 | 274.720 |
| baseline / 1 | 664 / 2400 | 66.425 | 1660 / 76 | 275.387 |
| baseline / 2 | 632 / 2400 | 63.223 | 1697 / 71 | 275.202 |
| candidate / 2 | 666 / 2400 | 66.625 | 1659 / 75 | 274.934 |
| candidate / 3 | 665 / 2400 | 66.525 | 1667 / 68 | 273.714 |
| baseline / 3 | 629 / 2400 | 62.924 | 1701 / 70 | 275.395 |

## ultrawide-3440x1440p240-hevc-sdr-50mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 55.488 Mbps. Encoder target: 50.000 Mbps; measured/target: 111.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 2400 / 2400 | 240.049 | 0 / 0 | 66.994 |
| candidate / 1 | 2400 / 2400 | 240.047 | 0 / 0 | 64.955 |
| candidate / 2 | 2400 / 2400 | 240.051 | 0 / 0 | 63.948 |
| baseline / 2 | 2400 / 2400 | 240.048 | 0 / 0 | 64.646 |
| baseline / 3 | 2400 / 2400 | 240.047 | 0 / 0 | 63.975 |
| candidate / 3 | 2400 / 2400 | 240.051 | 0 / 0 | 67.358 |

## ultrawide-3440x1440p240-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 95.374 Mbps. Encoder target: 100.000 Mbps; measured/target: 95.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 2400 / 2400 | 240.052 | 0 / 0 | 64.399 |
| baseline / 1 | 2400 / 2400 | 240.049 | 0 / 0 | 65.563 |
| baseline / 2 | 2400 / 2400 | 240.051 | 0 / 0 | 65.226 |
| candidate / 2 | 2400 / 2400 | 240.042 | 0 / 0 | 64.878 |
| candidate / 3 | 2400 / 2400 | 240.044 | 0 / 0 | 64.797 |
| baseline / 3 | 2400 / 2400 | 240.052 | 0 / 0 | 67.994 |

## ultrawide-3440x1440p240-hevc-sdr-250mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 213.959 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.6%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=54; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 2345 / 2400 | 234.534 | 54 / 1 | 64.079 |
| candidate / 1 | 2344 / 2400 | 234.434 | 55 / 1 | 66.108 |
| candidate / 2 | 2343 / 2400 | 234.335 | 55 / 2 | 66.981 |
| baseline / 2 | 2343 / 2400 | 234.337 | 55 / 2 | 68.741 |
| baseline / 3 | 2343 / 2400 | 234.346 | 56 / 1 | 69.961 |
| candidate / 3 | 2343 / 2400 | 234.339 | 56 / 1 | 69.994 |

## ultrawide-3440x1440p240-hevc-sdr-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 297.695 Mbps. Encoder target: 350.000 Mbps; measured/target: 85.1%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=4; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 2342 / 2400 | 234.221 | 57 / 1 | 72.751 |
| baseline / 1 | 2343 / 2400 | 234.325 | 55 / 2 | 66.988 |
| baseline / 2 | 2343 / 2400 | 234.317 | 55 / 2 | 67.399 |
| candidate / 2 | 2343 / 2400 | 234.322 | 55 / 2 | 67.116 |
| candidate / 3 | 2342 / 2400 | 234.221 | 56 / 2 | 70.067 |
| baseline / 3 | 2343 / 2400 | 234.325 | 55 / 2 | 66.944 |

## ultrawide-3440x1440p240-hevc-hdr10-50mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 50.947 Mbps. Encoder target: 50.000 Mbps; measured/target: 101.9%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=1; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 2341 / 2400 | 234.141 | 58 / 1 | 75.299 |
| candidate / 1 | 2400 / 2400 | 240.042 | 0 / 0 | 64.123 |
| candidate / 2 | 2400 / 2400 | 240.046 | 0 / 0 | 60.138 |
| baseline / 2 | 2400 / 2400 | 240.048 | 0 / 0 | 64.705 |
| baseline / 3 | 2400 / 2400 | 240.047 | 0 / 0 | 64.312 |
| candidate / 3 | 2400 / 2400 | 240.045 | 0 / 0 | 62.986 |

## ultrawide-3440x1440p240-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 92.181 Mbps. Encoder target: 100.000 Mbps; measured/target: 92.2%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 2400 / 2400 | 240.057 | 0 / 0 | 69.596 |
| baseline / 1 | 2400 / 2400 | 240.048 | 0 / 0 | 72.772 |
| baseline / 2 | 2400 / 2400 | 240.047 | 0 / 0 | 66.625 |
| candidate / 2 | 2400 / 2400 | 240.047 | 0 / 0 | 72.847 |
| candidate / 3 | 2400 / 2400 | 240.050 | 0 / 0 | 67.794 |
| baseline / 3 | 2400 / 2400 | 240.061 | 0 / 0 | 64.730 |

## ultrawide-3440x1440p240-hevc-hdr10-250mbps

Status: REGRESSION

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 213.563 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.4%.

- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=54; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 2400 / 2400 | 240.033 | 0 / 0 | 66.820 |
| candidate / 1 | 2400 / 2400 | 240.033 | 0 / 0 | 65.996 |
| candidate / 2 | 2400 / 2400 | 240.036 | 0 / 0 | 65.360 |
| baseline / 2 | 2400 / 2400 | 240.031 | 0 / 0 | 66.886 |
| baseline / 3 | 2400 / 2400 | 240.035 | 0 / 0 | 66.064 |
| candidate / 3 | 2345 / 2400 | 234.529 | 54 / 1 | 67.538 |

## ultrawide-3440x1440p240-hevc-hdr10-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 297.753 Mbps. Encoder target: 350.000 Mbps; measured/target: 85.1%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=55; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=56; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=57; failed_or_cancelled_or_dropped=2; expected_display_mismatches=2; resets=3; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 2343 / 2400 | 234.320 | 55 / 2 | 67.560 |
| baseline / 1 | 2343 / 2400 | 234.320 | 56 / 1 | 69.059 |
| baseline / 2 | 2342 / 2400 | 234.221 | 56 / 2 | 71.826 |
| candidate / 2 | 2342 / 2400 | 234.219 | 56 / 2 | 71.840 |
| candidate / 3 | 2340 / 2400 | 234.021 | 58 / 2 | 262.653 |
| baseline / 3 | 2341 / 2400 | 234.117 | 57 / 2 | 74.738 |

## 4k-3840x2160p60-av1-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, SDR. Measured bitrate: 131.636 Mbps. Encoder target: 50.000 Mbps; measured/target: 263.3%.

measured payload bitrate 131.636 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.075 | 0 / 0 | 103.637 |
| candidate / 1 | 600 / 600 | 60.076 | 0 / 0 | 95.299 |
| candidate / 2 | 600 / 600 | 60.077 | 0 / 0 | 95.878 |
| baseline / 2 | 600 / 600 | 60.075 | 0 / 0 | 91.880 |
| baseline / 3 | 600 / 600 | 60.074 | 0 / 0 | 100.552 |
| candidate / 3 | 600 / 600 | 60.078 | 0 / 0 | 94.566 |

## 4k-3840x2160p60-av1-sdr-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, SDR. Measured bitrate: 167.610 Mbps. Encoder target: 100.000 Mbps; measured/target: 167.6%.

measured payload bitrate 167.610 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.080 | 0 / 0 | 107.584 |
| baseline / 1 | 600 / 600 | 60.082 | 0 / 0 | 107.770 |
| baseline / 2 | 600 / 600 | 60.083 | 0 / 0 | 101.752 |
| candidate / 2 | 600 / 600 | 60.082 | 0 / 0 | 104.441 |
| candidate / 3 | 600 / 600 | 60.081 | 0 / 0 | 103.251 |
| baseline / 3 | 600 / 600 | 60.078 | 0 / 0 | 107.140 |

## 4k-3840x2160p60-av1-sdr-250mbps

Status: PASS

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, SDR. Measured bitrate: 276.966 Mbps. Encoder target: 250.000 Mbps; measured/target: 110.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 59.999 | 0 / 0 | 126.040 |
| candidate / 1 | 600 / 600 | 59.999 | 0 / 0 | 130.508 |
| candidate / 2 | 600 / 600 | 59.998 | 0 / 0 | 124.628 |
| baseline / 2 | 600 / 600 | 59.998 | 0 / 0 | 133.427 |
| baseline / 3 | 600 / 600 | 59.999 | 0 / 0 | 130.500 |
| candidate / 3 | 600 / 600 | 59.998 | 0 / 0 | 124.897 |

## 4k-3840x2160p60-av1-sdr-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, SDR. Measured bitrate: 655.946 Mbps. Encoder target: 350.000 Mbps; measured/target: 187.4%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=201; failed_or_cancelled_or_dropped=8; expected_display_mismatches=8; resets=11; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=200; failed_or_cancelled_or_dropped=5; expected_display_mismatches=5; resets=10; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=197; failed_or_cancelled_or_dropped=8; expected_display_mismatches=8; resets=11; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=199; failed_or_cancelled_or_dropped=7; expected_display_mismatches=7; resets=10; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=196; failed_or_cancelled_or_dropped=9; expected_display_mismatches=9; resets=10; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=199; failed_or_cancelled_or_dropped=10; expected_display_mismatches=10; resets=10; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 391 / 600 | 39.165 | 201 / 8 | 141.650 |
| baseline / 1 | 395 / 600 | 39.565 | 200 / 5 | 139.175 |
| baseline / 2 | 395 / 600 | 39.566 | 197 / 8 | 137.205 |
| candidate / 2 | 394 / 600 | 39.465 | 199 / 7 | 137.147 |
| candidate / 3 | 395 / 600 | 39.564 | 196 / 9 | 136.898 |
| baseline / 3 | 391 / 600 | 39.164 | 199 / 10 | 137.893 |

## 4k-3840x2160p60-av1-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, HDR10. Measured bitrate: 122.846 Mbps. Encoder target: 50.000 Mbps; measured/target: 245.7%.

measured payload bitrate 122.846 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.080 | 0 / 0 | 102.708 |
| candidate / 1 | 600 / 600 | 60.078 | 0 / 0 | 98.163 |
| candidate / 2 | 600 / 600 | 60.079 | 0 / 0 | 92.762 |
| baseline / 2 | 600 / 600 | 60.078 | 0 / 0 | 92.053 |
| baseline / 3 | 600 / 600 | 60.081 | 0 / 0 | 91.893 |
| candidate / 3 | 600 / 600 | 60.079 | 0 / 0 | 93.194 |

## 4k-3840x2160p60-av1-hdr10-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, HDR10. Measured bitrate: 133.382 Mbps. Encoder target: 100.000 Mbps; measured/target: 133.4%.

measured payload bitrate 133.382 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.076 | 0 / 0 | 103.283 |
| baseline / 1 | 600 / 600 | 60.076 | 0 / 0 | 107.967 |
| baseline / 2 | 600 / 600 | 60.077 | 0 / 0 | 108.924 |
| candidate / 2 | 600 / 600 | 60.077 | 0 / 0 | 103.015 |
| candidate / 3 | 600 / 600 | 60.076 | 0 / 0 | 107.809 |
| baseline / 3 | 600 / 600 | 60.078 | 0 / 0 | 106.773 |

## 4k-3840x2160p60-av1-hdr10-250mbps

Status: PASS

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, HDR10. Measured bitrate: 274.818 Mbps. Encoder target: 250.000 Mbps; measured/target: 109.9%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.000 | 0 / 0 | 125.234 |
| candidate / 1 | 600 / 600 | 60.000 | 0 / 0 | 130.598 |
| candidate / 2 | 600 / 600 | 60.001 | 0 / 0 | 125.794 |
| baseline / 2 | 600 / 600 | 59.998 | 0 / 0 | 131.624 |
| baseline / 3 | 600 / 600 | 59.999 | 0 / 0 | 125.782 |
| candidate / 3 | 600 / 600 | 60.000 | 0 / 0 | 126.979 |

## 4k-3840x2160p60-av1-hdr10-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, HDR10. Measured bitrate: 642.298 Mbps. Encoder target: 350.000 Mbps; measured/target: 183.5%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=151; failed_or_cancelled_or_dropped=6; expected_display_mismatches=6; resets=10; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=152; failed_or_cancelled_or_dropped=9; expected_display_mismatches=9; resets=10; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=151; failed_or_cancelled_or_dropped=7; expected_display_mismatches=7; resets=10; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=153; failed_or_cancelled_or_dropped=7; expected_display_mismatches=7; resets=10; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=155; failed_or_cancelled_or_dropped=8; expected_display_mismatches=8; resets=10; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=151; failed_or_cancelled_or_dropped=7; expected_display_mismatches=7; resets=10; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 443 / 600 | 44.372 | 151 / 6 | 137.644 |
| baseline / 1 | 439 / 600 | 43.973 | 152 / 9 | 141.966 |
| baseline / 2 | 442 / 600 | 44.273 | 151 / 7 | 139.639 |
| candidate / 2 | 440 / 600 | 44.072 | 153 / 7 | 138.021 |
| candidate / 3 | 437 / 600 | 43.771 | 155 / 8 | 145.808 |
| baseline / 3 | 442 / 600 | 44.272 | 151 / 7 | 138.689 |

## 4k-3840x2160p60-hevc-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 60.820 Mbps. Encoder target: 50.000 Mbps; measured/target: 121.6%.

measured payload bitrate 60.820 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.081 | 0 / 0 | 77.010 |
| candidate / 1 | 600 / 600 | 60.082 | 0 / 0 | 76.581 |
| candidate / 2 | 600 / 600 | 60.083 | 0 / 0 | 76.276 |
| baseline / 2 | 600 / 600 | 60.084 | 0 / 0 | 78.369 |
| baseline / 3 | 600 / 600 | 60.082 | 0 / 0 | 74.189 |
| candidate / 3 | 600 / 600 | 60.082 | 0 / 0 | 79.911 |

## 4k-3840x2160p60-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 92.471 Mbps. Encoder target: 100.000 Mbps; measured/target: 92.5%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.082 | 0 / 0 | 78.172 |
| baseline / 1 | 600 / 600 | 60.080 | 0 / 0 | 79.040 |
| baseline / 2 | 600 / 600 | 60.081 | 0 / 0 | 79.304 |
| candidate / 2 | 600 / 600 | 60.079 | 0 / 0 | 79.882 |
| candidate / 3 | 600 / 600 | 60.081 | 0 / 0 | 83.243 |
| baseline / 3 | 600 / 600 | 60.085 | 0 / 0 | 78.302 |

## 4k-3840x2160p60-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 214.384 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.066 | 0 / 0 | 85.996 |
| candidate / 1 | 600 / 600 | 60.068 | 0 / 0 | 84.417 |
| candidate / 2 | 600 / 600 | 60.067 | 0 / 0 | 88.779 |
| baseline / 2 | 600 / 600 | 60.068 | 0 / 0 | 82.612 |
| baseline / 3 | 600 / 600 | 60.068 | 0 / 0 | 88.848 |
| candidate / 3 | 600 / 600 | 60.068 | 0 / 0 | 89.671 |

## 4k-3840x2160p60-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 296.923 Mbps. Encoder target: 350.000 Mbps; measured/target: 84.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.056 | 0 / 0 | 84.918 |
| baseline / 1 | 600 / 600 | 60.055 | 0 / 0 | 85.129 |
| baseline / 2 | 600 / 600 | 60.057 | 0 / 0 | 84.697 |
| candidate / 2 | 600 / 600 | 60.057 | 0 / 0 | 90.677 |
| candidate / 3 | 600 / 600 | 60.056 | 0 / 0 | 84.978 |
| baseline / 3 | 600 / 600 | 60.056 | 0 / 0 | 84.509 |

## 4k-3840x2160p60-hevc-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 83.905 Mbps. Encoder target: 50.000 Mbps; measured/target: 167.8%.

measured payload bitrate 83.905 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.087 | 0 / 0 | 85.377 |
| candidate / 1 | 600 / 600 | 60.083 | 0 / 0 | 84.925 |
| candidate / 2 | 600 / 600 | 60.081 | 0 / 0 | 85.588 |
| baseline / 2 | 600 / 600 | 60.082 | 0 / 0 | 87.265 |
| baseline / 3 | 600 / 600 | 60.082 | 0 / 0 | 89.407 |
| candidate / 3 | 600 / 600 | 60.082 | 0 / 0 | 85.525 |

## 4k-3840x2160p60-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 91.768 Mbps. Encoder target: 100.000 Mbps; measured/target: 91.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.081 | 0 / 0 | 79.490 |
| baseline / 1 | 600 / 600 | 60.082 | 0 / 0 | 79.722 |
| baseline / 2 | 600 / 600 | 60.082 | 0 / 0 | 79.160 |
| candidate / 2 | 600 / 600 | 60.081 | 0 / 0 | 80.085 |
| candidate / 3 | 600 / 600 | 60.081 | 0 / 0 | 82.757 |
| baseline / 3 | 600 / 600 | 60.082 | 0 / 0 | 80.148 |

## 4k-3840x2160p60-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 214.240 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.067 | 0 / 0 | 84.105 |
| candidate / 1 | 600 / 600 | 60.068 | 0 / 0 | 85.426 |
| candidate / 2 | 600 / 600 | 60.062 | 0 / 0 | 85.956 |
| baseline / 2 | 600 / 600 | 60.066 | 0 / 0 | 91.115 |
| baseline / 3 | 600 / 600 | 60.068 | 0 / 0 | 85.640 |
| candidate / 3 | 600 / 600 | 60.065 | 0 / 0 | 86.883 |

## 4k-3840x2160p60-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 296.411 Mbps. Encoder target: 350.000 Mbps; measured/target: 84.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.050 | 0 / 0 | 84.485 |
| baseline / 1 | 600 / 600 | 60.055 | 0 / 0 | 91.227 |
| baseline / 2 | 600 / 600 | 60.049 | 0 / 0 | 87.242 |
| candidate / 2 | 600 / 600 | 60.047 | 0 / 0 | 101.015 |
| candidate / 3 | 600 / 600 | 60.051 | 0 / 0 | 89.919 |
| baseline / 3 | 600 / 600 | 60.049 | 0 / 0 | 85.501 |

## 4k-3840x2160p120-av1-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, SDR. Measured bitrate: 218.276 Mbps. Encoder target: 50.000 Mbps; measured/target: 436.6%.

measured payload bitrate 218.276 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 119.967 | 0 / 0 | 85.169 |
| candidate / 1 | 1200 / 1200 | 119.972 | 0 / 0 | 85.543 |
| candidate / 2 | 1200 / 1200 | 119.966 | 0 / 0 | 86.532 |
| baseline / 2 | 1200 / 1200 | 119.965 | 0 / 0 | 85.546 |
| baseline / 3 | 1200 / 1200 | 119.967 | 0 / 0 | 85.225 |
| candidate / 3 | 1200 / 1200 | 119.967 | 0 / 0 | 85.905 |

## 4k-3840x2160p120-av1-sdr-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, SDR. Measured bitrate: 263.272 Mbps. Encoder target: 100.000 Mbps; measured/target: 263.3%.

measured payload bitrate 263.272 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.031 | 0 / 0 | 91.827 |
| baseline / 1 | 1200 / 1200 | 120.025 | 0 / 0 | 90.700 |
| baseline / 2 | 1200 / 1200 | 120.030 | 0 / 0 | 91.466 |
| candidate / 2 | 1200 / 1200 | 120.026 | 0 / 0 | 93.998 |
| candidate / 3 | 1200 / 1200 | 120.026 | 0 / 0 | 92.234 |
| baseline / 3 | 1200 / 1200 | 120.032 | 0 / 0 | 90.689 |

## 4k-3840x2160p120-av1-sdr-250mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, SDR. Measured bitrate: 358.597 Mbps. Encoder target: 250.000 Mbps; measured/target: 143.4%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=545; failed_or_cancelled_or_dropped=20; expected_display_mismatches=20; resets=39; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=545; failed_or_cancelled_or_dropped=19; expected_display_mismatches=19; resets=41; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=544; failed_or_cancelled_or_dropped=19; expected_display_mismatches=19; resets=41; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=544; failed_or_cancelled_or_dropped=18; expected_display_mismatches=18; resets=40; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=546; failed_or_cancelled_or_dropped=20; expected_display_mismatches=20; resets=39; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=547; failed_or_cancelled_or_dropped=20; expected_display_mismatches=20; resets=42; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 635 / 1200 | 63.057 | 545 / 20 | 104.492 |
| candidate / 1 | 636 / 1200 | 63.160 | 545 / 19 | 105.316 |
| candidate / 2 | 637 / 1200 | 63.265 | 544 / 19 | 106.129 |
| baseline / 2 | 638 / 1200 | 63.357 | 544 / 18 | 106.542 |
| baseline / 3 | 634 / 1200 | 62.963 | 546 / 20 | 106.319 |
| candidate / 3 | 633 / 1200 | 62.893 | 547 / 20 | 108.258 |

## 4k-3840x2160p120-av1-sdr-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, SDR. Measured bitrate: 433.243 Mbps. Encoder target: 350.000 Mbps; measured/target: 123.8%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=817; failed_or_cancelled_or_dropped=40; expected_display_mismatches=40; resets=71; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=814; failed_or_cancelled_or_dropped=40; expected_display_mismatches=40; resets=77; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=815; failed_or_cancelled_or_dropped=40; expected_display_mismatches=40; resets=77; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=818; failed_or_cancelled_or_dropped=38; expected_display_mismatches=38; resets=72; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=817; failed_or_cancelled_or_dropped=40; expected_display_mismatches=40; resets=73; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=814; failed_or_cancelled_or_dropped=39; expected_display_mismatches=39; resets=78; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 343 / 1200 | 34.328 | 817 / 40 | 118.287 |
| baseline / 1 | 346 / 1200 | 34.628 | 814 / 40 | 114.638 |
| baseline / 2 | 345 / 1200 | 34.528 | 815 / 40 | 113.212 |
| candidate / 2 | 344 / 1200 | 34.428 | 818 / 38 | 120.088 |
| candidate / 3 | 343 / 1200 | 34.328 | 817 / 40 | 114.189 |
| baseline / 3 | 347 / 1200 | 34.728 | 814 / 39 | 114.611 |

## 4k-3840x2160p120-av1-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, HDR10. Measured bitrate: 177.539 Mbps. Encoder target: 50.000 Mbps; measured/target: 355.1%.

measured payload bitrate 177.539 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.002 | 0 / 0 | 85.878 |
| candidate / 1 | 1200 / 1200 | 120.008 | 0 / 0 | 89.585 |
| candidate / 2 | 1200 / 1200 | 120.002 | 0 / 0 | 87.778 |
| baseline / 2 | 1200 / 1200 | 120.002 | 0 / 0 | 90.455 |
| baseline / 3 | 1200 / 1200 | 120.012 | 0 / 0 | 86.538 |
| candidate / 3 | 1200 / 1200 | 120.005 | 0 / 0 | 90.197 |

## 4k-3840x2160p120-av1-hdr10-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, HDR10. Measured bitrate: 245.692 Mbps. Encoder target: 100.000 Mbps; measured/target: 245.7%.

measured payload bitrate 245.692 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 119.956 | 0 / 0 | 91.014 |
| baseline / 1 | 1200 / 1200 | 119.957 | 0 / 0 | 93.637 |
| baseline / 2 | 1200 / 1200 | 119.959 | 0 / 0 | 98.439 |
| candidate / 2 | 1200 / 1200 | 119.959 | 0 / 0 | 92.787 |
| candidate / 3 | 1200 / 1200 | 119.958 | 0 / 0 | 91.665 |
| baseline / 3 | 1200 / 1200 | 119.957 | 0 / 0 | 93.389 |

## 4k-3840x2160p120-av1-hdr10-250mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, HDR10. Measured bitrate: 342.189 Mbps. Encoder target: 250.000 Mbps; measured/target: 136.9%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=403; failed_or_cancelled_or_dropped=22; expected_display_mismatches=22; resets=22; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=372; failed_or_cancelled_or_dropped=23; expected_display_mismatches=23; resets=19; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=326; failed_or_cancelled_or_dropped=21; expected_display_mismatches=21; resets=13; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=296; failed_or_cancelled_or_dropped=15; expected_display_mismatches=15; resets=14; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=332; failed_or_cancelled_or_dropped=18; expected_display_mismatches=18; resets=18; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=412; failed_or_cancelled_or_dropped=21; expected_display_mismatches=21; resets=21; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 775 / 1200 | 77.562 | 403 / 22 | 106.816 |
| candidate / 1 | 805 / 1200 | 80.270 | 372 / 23 | 110.310 |
| candidate / 2 | 853 / 1200 | 84.589 | 326 / 21 | 106.769 |
| baseline / 2 | 889 / 1200 | 88.441 | 296 / 15 | 113.912 |
| baseline / 3 | 850 / 1200 | 84.391 | 332 / 18 | 106.617 |
| candidate / 3 | 767 / 1200 | 76.532 | 412 / 21 | 106.114 |

## 4k-3840x2160p120-av1-hdr10-350mbps

Status: BASELINE_FAILURE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, HDR10. Measured bitrate: 436.031 Mbps. Encoder target: 350.000 Mbps; measured/target: 124.6%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / candidate / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=584; failed_or_cancelled_or_dropped=17; expected_display_mismatches=17; resets=64; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=583; failed_or_cancelled_or_dropped=19; expected_display_mismatches=19; resets=68; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=590; failed_or_cancelled_or_dropped=21; expected_display_mismatches=21; resets=77; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 2: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=587; failed_or_cancelled_or_dropped=21; expected_display_mismatches=21; resets=66; hardware decoding was not validated; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=594; failed_or_cancelled_or_dropped=21; expected_display_mismatches=21; resets=72; CSV contains a non-output terminal completion; delivered frame rate below configured ratio
- timed / baseline / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=583; failed_or_cancelled_or_dropped=19; expected_display_mismatches=19; resets=71; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 599 / 1200 | 59.056 | 584 / 17 | 115.368 |
| baseline / 1 | 598 / 1200 | 59.231 | 583 / 19 | 115.496 |
| baseline / 2 | 589 / 1200 | 58.089 | 590 / 21 | 120.693 |
| candidate / 2 | 592 / 1200 | 58.439 | 587 / 21 | 114.833 |
| candidate / 3 | 585 / 1200 | 57.677 | 594 / 21 | 120.844 |
| baseline / 3 | 598 / 1200 | 58.963 | 583 / 19 | 114.394 |

## 4k-3840x2160p120-hevc-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, SDR. Measured bitrate: 82.298 Mbps. Encoder target: 50.000 Mbps; measured/target: 164.6%.

measured payload bitrate 82.298 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.068 | 0 / 0 | 74.512 |
| candidate / 1 | 1200 / 1200 | 120.067 | 0 / 0 | 76.021 |
| candidate / 2 | 1200 / 1200 | 120.068 | 0 / 0 | 75.833 |
| baseline / 2 | 1200 / 1200 | 120.070 | 0 / 0 | 73.033 |
| baseline / 3 | 1200 / 1200 | 120.063 | 0 / 0 | 74.846 |
| candidate / 3 | 1200 / 1200 | 120.067 | 0 / 0 | 74.276 |

## 4k-3840x2160p120-hevc-sdr-100mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, SDR. Measured bitrate: 122.563 Mbps. Encoder target: 100.000 Mbps; measured/target: 122.6%.

measured payload bitrate 122.563 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.064 | 0 / 0 | 91.194 |
| baseline / 1 | 1200 / 1200 | 120.062 | 0 / 0 | 74.638 |
| baseline / 2 | 1200 / 1200 | 120.064 | 0 / 0 | 76.510 |
| candidate / 2 | 1200 / 1200 | 120.061 | 0 / 0 | 74.825 |
| candidate / 3 | 1200 / 1200 | 120.066 | 0 / 0 | 78.867 |
| baseline / 3 | 1200 / 1200 | 120.065 | 0 / 0 | 74.711 |

## 4k-3840x2160p120-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, SDR. Measured bitrate: 238.909 Mbps. Encoder target: 250.000 Mbps; measured/target: 95.6%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.052 | 0 / 0 | 79.583 |
| candidate / 1 | 1200 / 1200 | 120.051 | 0 / 0 | 82.353 |
| candidate / 2 | 1200 / 1200 | 120.056 | 0 / 0 | 80.071 |
| baseline / 2 | 1200 / 1200 | 120.056 | 0 / 0 | 79.793 |
| baseline / 3 | 1200 / 1200 | 120.055 | 0 / 0 | 81.785 |
| candidate / 3 | 1200 / 1200 | 120.048 | 0 / 0 | 79.526 |

## 4k-3840x2160p120-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, SDR. Measured bitrate: 323.482 Mbps. Encoder target: 350.000 Mbps; measured/target: 92.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.040 | 0 / 0 | 80.995 |
| baseline / 1 | 1200 / 1200 | 120.039 | 0 / 0 | 81.440 |
| baseline / 2 | 1200 / 1200 | 120.041 | 0 / 0 | 81.640 |
| candidate / 2 | 1200 / 1200 | 120.040 | 0 / 0 | 82.510 |
| candidate / 3 | 1200 / 1200 | 120.040 | 0 / 0 | 80.631 |
| baseline / 3 | 1200 / 1200 | 120.039 | 0 / 0 | 81.384 |

## 4k-3840x2160p120-hevc-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, HDR10. Measured bitrate: 82.866 Mbps. Encoder target: 50.000 Mbps; measured/target: 165.7%.

measured payload bitrate 82.866 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.055 | 0 / 0 | 75.228 |
| candidate / 1 | 1200 / 1200 | 120.050 | 0 / 0 | 74.508 |
| candidate / 2 | 1200 / 1200 | 120.054 | 0 / 0 | 74.361 |
| baseline / 2 | 1200 / 1200 | 120.052 | 0 / 0 | 74.209 |
| baseline / 3 | 1200 / 1200 | 120.057 | 0 / 0 | 73.806 |
| candidate / 3 | 1200 / 1200 | 120.050 | 0 / 0 | 76.815 |

## 4k-3840x2160p120-hevc-hdr10-100mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, HDR10. Measured bitrate: 122.444 Mbps. Encoder target: 100.000 Mbps; measured/target: 122.4%.

measured payload bitrate 122.444 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.066 | 0 / 0 | 80.638 |
| baseline / 1 | 1200 / 1200 | 120.061 | 0 / 0 | 76.045 |
| baseline / 2 | 1200 / 1200 | 120.067 | 0 / 0 | 78.361 |
| candidate / 2 | 1200 / 1200 | 120.066 | 0 / 0 | 76.584 |
| candidate / 3 | 1200 / 1200 | 120.064 | 0 / 0 | 76.592 |
| baseline / 3 | 1200 / 1200 | 120.070 | 0 / 0 | 76.428 |

## 4k-3840x2160p120-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, HDR10. Measured bitrate: 237.735 Mbps. Encoder target: 250.000 Mbps; measured/target: 95.1%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.047 | 0 / 0 | 81.051 |
| candidate / 1 | 1200 / 1200 | 120.053 | 0 / 0 | 81.230 |
| candidate / 2 | 1200 / 1200 | 120.047 | 0 / 0 | 80.991 |
| baseline / 2 | 1200 / 1200 | 120.050 | 0 / 0 | 82.506 |
| baseline / 3 | 1200 / 1200 | 120.049 | 0 / 0 | 79.867 |
| candidate / 3 | 1200 / 1200 | 120.044 | 0 / 0 | 80.511 |

## 4k-3840x2160p120-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, HDR10. Measured bitrate: 316.323 Mbps. Encoder target: 350.000 Mbps; measured/target: 90.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |
|---|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.035 | 0 / 0 | 83.504 |
| baseline / 1 | 1200 / 1200 | 120.044 | 0 / 0 | 87.656 |
| baseline / 2 | 1200 / 1200 | 120.042 | 0 / 0 | 81.008 |
| candidate / 2 | 1200 / 1200 | 120.042 | 0 / 0 | 82.643 |
| candidate / 3 | 1200 / 1200 | 120.042 | 0 / 0 | 80.981 |
| baseline / 3 | 1200 / 1200 | 120.040 | 0 / 0 | 80.329 |

