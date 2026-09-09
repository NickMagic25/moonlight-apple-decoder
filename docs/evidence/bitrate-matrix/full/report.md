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

## Decode time shown by Moonlight

The native Apple adapter displays **“Frame-ready mean (VT submit -> callback)”**: the arithmetic mean from VideoToolbox submission to its decoded-image callback, in milliseconds. This is the same measurement previously labeled “VT submit-to-callback mean”; the machine-readable key remains `native_vt`. These values include cold/startup and warmup outputs, matching the adapter’s cumulative counter; they are not the steady-state medians in the table above. Case means below sum durations and divide by eligible output counts across all captured timed trials, so trials with different output counts are weighted correctly. Each trial includes its own startup. Per-trial means and their sample counts appear below each case.

**“VT submission mean (submit -> return)”** separately measures how long the VideoToolbox API call takes to return. It is not completed decoding or presentation latency. Submission and frame-ready intervals share the same start; do not add their means or interpret their difference as hardware execution time. A callback can occur before the call returns, so some saved completions lack a return timestamp. Those outputs remain eligible for frame-ready timing but are omitted from submission timing, with independent sample counts shown explicitly. Missing return timestamps are never replaced with zero or a callback timestamp.

The regular Qt/FFmpeg **“Average decoding time”** includes input-queue and decoder delivery time and uses recent statistics windows. The queue-inclusive proxy below uses recorded complete-frame arrival to the harness output callback. It approximates that broader boundary; it is not an actual live overlay reading and does not include the app’s output wrapping or rendering. The native frame-ready column matches this repository’s native Apple overlay formula. On Intel/other GPU backends, FFmpeg output-surface delivery need not guarantee GPU completion; the proxy does not establish a common hardware-readiness endpoint across platforms.

Dropped/cancelled frames add no decode sample, so a low mean does not imply smooth delivery. Original PASS/FAIL, bitrate coverage and latency gates are unchanged. A dash means the necessary trace-derived values are unavailable. Machine-readable means and sample counts: [moonlight-decode-times.json](moonlight-decode-times.json).

| Case | Result | VT submission mean ms (baseline / candidate) | Frame-ready mean ms (baseline / candidate) | Queue-inclusive proxy ms (baseline / candidate) | Submission samples (baseline / candidate) | Frame-ready samples (baseline / candidate) |
|---|---|---:|---:|---:|---:|---:|
| 1080p-1920x1080p60-av1-sdr-50mbps | PASS | 0.782 / 0.807 | 5.083 / 5.112 | 5.656 / 5.696 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-av1-sdr-100mbps | PASS | 0.840 / 0.770 | 5.879 / 5.787 | 6.510 / 6.410 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-av1-sdr-250mbps | PASS | 0.896 / 0.919 | 7.371 / 7.406 | 8.005 / 8.048 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-av1-sdr-350mbps | PASS | 0.984 / 0.946 | 8.466 / 8.405 | 9.104 / 9.039 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-av1-hdr10-50mbps | PASS | 0.899 / 0.943 | 4.214 / 4.260 | 4.800 / 4.867 | 1800 / 1798 | 1800 / 1800 |
| 1080p-1920x1080p60-av1-hdr10-100mbps | PASS | 0.913 / 0.888 | 5.993 / 5.967 | 6.617 / 6.577 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-av1-hdr10-250mbps | PASS | 0.998 / 1.013 | 7.530 / 7.579 | 8.230 / 8.286 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-av1-hdr10-350mbps | PASS | 1.047 / 1.013 | 8.720 / 8.681 | 9.440 / 9.373 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-hevc-sdr-50mbps | PASS | 0.757 / 0.745 | 2.251 / 2.233 | 2.837 / 2.819 | 1800 / 1799 | 1800 / 1800 |
| 1080p-1920x1080p60-hevc-sdr-100mbps | PASS | 0.815 / 0.807 | 2.990 / 2.971 | 3.587 / 3.584 | 1799 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-hevc-sdr-250mbps | PASS | 0.968 / 0.926 | 5.194 / 5.135 | 5.863 / 5.803 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-hevc-sdr-350mbps | PASS | 0.925 / 0.942 | 6.058 / 6.077 | 6.816 / 6.798 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-hevc-hdr10-50mbps | PASS | 0.874 / 0.788 | 2.434 / 2.323 | 3.071 / 2.928 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-hevc-hdr10-100mbps | PASS | 0.830 / 0.886 | 3.029 / 3.099 | 3.625 / 3.747 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-hevc-hdr10-250mbps | PASS | 0.979 / 0.955 | 5.198 / 5.172 | 5.875 / 5.872 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p60-hevc-hdr10-350mbps | PASS | 0.977 / 1.022 | 6.127 / 6.184 | 6.901 / 6.931 | 1800 / 1800 | 1800 / 1800 |
| 1080p-1920x1080p120-av1-sdr-50mbps | INCONCLUSIVE | 0.710 / 0.689 | 3.709 / 3.676 | 4.315 / 4.251 | 3600 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-av1-sdr-100mbps | PASS | 0.677 / 0.735 | 5.086 / 5.170 | 5.888 / 5.878 | 3600 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-av1-sdr-250mbps | PASS | 0.794 / 0.707 | 6.316 / 6.191 | 7.341 / 7.175 | 3599 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-av1-sdr-350mbps | PASS | 0.786 / 0.784 | 6.824 / 6.828 | 8.047 / 8.060 | 3600 / 3598 | 3600 / 3600 |
| 1080p-1920x1080p120-av1-hdr10-50mbps | INCONCLUSIVE | 0.750 / 0.732 | 3.510 / 3.485 | 4.175 / 4.118 | 3600 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-av1-hdr10-100mbps | INCONCLUSIVE | 0.752 / 0.740 | 4.218 / 4.193 | 4.948 / 4.966 | 3600 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-av1-hdr10-250mbps | PASS | 0.694 / 0.798 | 6.139 / 6.304 | 7.144 / 7.364 | 3600 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-av1-hdr10-350mbps | PASS | 0.753 / 0.765 | 6.771 / 6.789 | 7.995 / 8.015 | 3600 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-hevc-sdr-50mbps | INCONCLUSIVE | 0.614 / 0.628 | 1.877 / 1.906 | 2.424 / 2.421 | 3599 / 3599 | 3600 / 3600 |
| 1080p-1920x1080p120-hevc-sdr-100mbps | PASS | 0.695 / 0.698 | 2.205 / 2.212 | 2.763 / 2.778 | 3600 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-hevc-sdr-250mbps | PASS | 0.761 / 0.758 | 3.357 / 3.351 | 4.091 / 4.081 | 3600 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-hevc-sdr-350mbps | PASS | 0.760 / 0.713 | 4.117 / 4.047 | 4.887 / 4.801 | 3600 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-hevc-hdr10-50mbps | PASS | 0.634 / 0.630 | 1.930 / 1.912 | 2.492 / 2.484 | 3600 / 3599 | 3600 / 3600 |
| 1080p-1920x1080p120-hevc-hdr10-100mbps | PASS | 0.719 / 0.712 | 2.264 / 2.261 | 2.901 / 2.877 | 3599 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-hevc-hdr10-250mbps | PASS | 0.803 / 0.808 | 3.396 / 3.409 | 4.185 / 4.175 | 3599 / 3600 | 3600 / 3600 |
| 1080p-1920x1080p120-hevc-hdr10-350mbps | PASS | 0.806 / 0.812 | 4.145 / 4.152 | 4.952 / 4.976 | 3600 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p120-av1-sdr-50mbps | INCONCLUSIVE | 0.702 / 0.715 | 6.359 / 6.386 | 7.478 / 7.516 | 3600 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p120-av1-sdr-100mbps | INCONCLUSIVE | 0.724 / 0.640 | 8.062 / 7.955 | 10.466 / 10.219 | 3600 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p120-av1-sdr-250mbps | BASELINE_FAILURE | 0.829 / 0.842 | 17.978 / 17.937 | 95.049 / 92.593 | 2776 / 2686 | 2776 / 2686 |
| ultrawide-3440x1440p120-av1-sdr-350mbps | BASELINE_FAILURE | 1.016 / 1.028 | 19.698 / 19.699 | 78.653 / 78.555 | 2453 / 2456 | 2453 / 2456 |
| ultrawide-3440x1440p120-av1-hdr10-50mbps | INCONCLUSIVE | 0.783 / 0.791 | 6.250 / 6.264 | 7.439 / 7.467 | 3600 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p120-av1-hdr10-100mbps | INCONCLUSIVE | 0.805 / 0.784 | 7.125 / 7.095 | 8.948 / 8.921 | 3600 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p120-av1-hdr10-250mbps | PASS | 0.799 / 0.766 | 12.684 / 12.601 | 23.898 / 23.678 | 3600 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p120-av1-hdr10-350mbps | BASELINE_FAILURE | 1.099 / 1.087 | 19.484 / 19.483 | 80.368 / 80.325 | 2579 / 2580 | 2579 / 2580 |
| ultrawide-3440x1440p120-hevc-sdr-50mbps | INCONCLUSIVE | 0.649 / 0.661 | 2.424 / 2.448 | 2.992 / 3.023 | 3600 / 3599 | 3600 / 3600 |
| ultrawide-3440x1440p120-hevc-sdr-100mbps | PASS | 0.658 / 0.568 | 2.518 / 2.359 | 3.196 / 2.984 | 3600 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p120-hevc-sdr-250mbps | PASS | 0.707 / 0.735 | 3.731 / 3.771 | 4.936 / 5.003 | 3600 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p120-hevc-sdr-350mbps | PASS | 0.757 / 0.755 | 4.446 / 4.433 | 6.037 / 6.020 | 3600 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p120-hevc-hdr10-50mbps | INCONCLUSIVE | 0.702 / 0.712 | 2.489 / 2.500 | 3.077 / 3.107 | 3600 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p120-hevc-hdr10-100mbps | PASS | 0.697 / 0.716 | 2.566 / 2.603 | 3.217 / 3.234 | 3600 / 3599 | 3600 / 3600 |
| ultrawide-3440x1440p120-hevc-hdr10-250mbps | PASS | 0.786 / 0.783 | 3.821 / 3.818 | 4.851 / 4.878 | 3599 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p120-hevc-hdr10-350mbps | PASS | 0.817 / 0.808 | 4.501 / 4.490 | 6.031 / 5.929 | 3600 / 3600 | 3600 / 3600 |
| ultrawide-3440x1440p240-av1-sdr-50mbps | BASELINE_FAILURE | 0.628 / 0.562 | 7.389 / 7.329 | 11.260 / 11.097 | 7026 / 7024 | 7026 / 7024 |
| ultrawide-3440x1440p240-av1-sdr-100mbps | BASELINE_FAILURE | 0.613 / 0.631 | 7.592 / 7.641 | 14.196 / 14.489 | 7022 / 7022 | 7022 / 7022 |
| ultrawide-3440x1440p240-av1-sdr-250mbps | BASELINE_FAILURE | 1.313 / 1.279 | 13.032 / 12.994 | 56.006 / 56.067 | 2649 / 2673 | 2649 / 2673 |
| ultrawide-3440x1440p240-av1-sdr-350mbps | BASELINE_FAILURE | 1.881 / 1.907 | 16.911 / 16.898 | 54.757 / 54.775 | 1454 / 1456 | 1454 / 1456 |
| ultrawide-3440x1440p240-av1-hdr10-50mbps | BASELINE_FAILURE | 0.686 / 0.679 | 6.324 / 6.302 | 8.154 / 8.060 | 7026 / 7023 | 7026 / 7024 |
| ultrawide-3440x1440p240-av1-hdr10-100mbps | BASELINE_FAILURE | 0.588 / 0.613 | 7.708 / 7.746 | 18.726 / 19.376 | 7022 / 7020 | 7022 / 7020 |
| ultrawide-3440x1440p240-av1-hdr10-250mbps | BASELINE_FAILURE | 1.019 / 1.091 | 10.716 / 10.883 | 48.993 / 48.805 | 3540 / 3342 | 3540 / 3342 |
| ultrawide-3440x1440p240-av1-hdr10-350mbps | BASELINE_FAILURE | 1.784 / 1.727 | 14.538 / 14.410 | 57.145 / 56.864 | 1925 / 1976 | 1925 / 1976 |
| ultrawide-3440x1440p240-hevc-sdr-50mbps | PASS | 0.563 / 0.575 | 2.058 / 2.071 | 2.649 / 2.664 | 7200 / 7199 | 7200 / 7200 |
| ultrawide-3440x1440p240-hevc-sdr-100mbps | PASS | 0.579 / 0.572 | 2.218 / 2.207 | 3.083 / 3.060 | 7200 / 7199 | 7200 / 7200 |
| ultrawide-3440x1440p240-hevc-sdr-250mbps | BASELINE_FAILURE | 0.603 / 0.618 | 2.623 / 2.642 | 3.623 / 3.663 | 7031 / 7030 | 7031 / 7030 |
| ultrawide-3440x1440p240-hevc-sdr-350mbps | BASELINE_FAILURE | 0.614 / 0.596 | 3.068 / 3.038 | 4.350 / 4.300 | 7029 / 7027 | 7029 / 7027 |
| ultrawide-3440x1440p240-hevc-hdr10-50mbps | BASELINE_FAILURE | 0.613 / 0.625 | 2.118 / 2.141 | 2.568 / 2.654 | 7141 / 7199 | 7141 / 7200 |
| ultrawide-3440x1440p240-hevc-hdr10-100mbps | PASS | 0.646 / 0.615 | 2.295 / 2.252 | 3.052 / 3.036 | 7200 / 7200 | 7200 / 7200 |
| ultrawide-3440x1440p240-hevc-hdr10-250mbps | REGRESSION | 0.662 / 0.680 | 2.748 / 2.772 | 3.901 / 3.808 | 7200 / 7145 | 7200 / 7145 |
| ultrawide-3440x1440p240-hevc-hdr10-350mbps | BASELINE_FAILURE | 0.687 / 0.643 | 3.189 / 3.111 | 4.396 / 4.280 | 7026 / 7024 | 7026 / 7025 |
| 4k-3840x2160p60-av1-sdr-50mbps | INCONCLUSIVE | 0.973 / 0.907 | 9.720 / 9.632 | 11.095 / 10.911 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-av1-sdr-100mbps | INCONCLUSIVE | 0.945 / 0.958 | 12.036 / 12.059 | 14.287 / 14.308 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-av1-sdr-250mbps | PASS | 1.025 / 0.958 | 23.392 / 23.249 | 37.544 / 36.914 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-av1-sdr-350mbps | BASELINE_FAILURE | 1.439 / 1.463 | 39.341 / 39.331 | 212.263 / 212.002 | 1181 / 1180 | 1181 / 1180 |
| 4k-3840x2160p60-av1-hdr10-50mbps | INCONCLUSIVE | 0.964 / 0.945 | 9.474 / 9.461 | 10.723 / 10.701 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-av1-hdr10-100mbps | INCONCLUSIVE | 0.968 / 0.905 | 10.293 / 10.210 | 12.329 / 12.182 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-av1-hdr10-250mbps | PASS | 1.056 / 1.033 | 21.841 / 21.821 | 33.237 / 33.285 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-av1-hdr10-350mbps | BASELINE_FAILURE | 1.542 / 1.585 | 38.662 / 38.664 | 211.541 / 211.798 | 1323 / 1320 | 1323 / 1320 |
| 4k-3840x2160p60-hevc-sdr-50mbps | INCONCLUSIVE | 0.829 / 0.763 | 3.527 / 3.427 | 4.235 / 4.156 | 1799 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-sdr-100mbps | PASS | 0.740 / 0.756 | 3.650 / 3.675 | 4.422 / 4.461 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-sdr-250mbps | PASS | 0.974 / 0.903 | 5.620 / 5.521 | 6.606 / 6.538 | 1799 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-sdr-350mbps | PASS | 1.047 / 1.015 | 6.848 / 6.797 | 7.924 / 7.904 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-50mbps | INCONCLUSIVE | 0.823 / 0.810 | 3.955 / 3.936 | 4.868 / 4.817 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-100mbps | PASS | 0.826 / 0.878 | 3.774 / 3.844 | 4.555 / 4.624 | 1799 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-250mbps | PASS | 0.995 / 0.984 | 5.667 / 5.653 | 6.648 / 6.624 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p60-hevc-hdr10-350mbps | PASS | 0.989 / 1.115 | 6.800 / 6.989 | 7.866 / 8.158 | 1800 / 1800 | 1800 / 1800 |
| 4k-3840x2160p120-av1-sdr-50mbps | INCONCLUSIVE | 0.745 / 0.769 | 11.741 / 11.768 | 16.221 / 16.332 | 3600 / 3600 | 3600 / 3600 |
| 4k-3840x2160p120-av1-sdr-100mbps | INCONCLUSIVE | 0.773 / 0.742 | 13.376 / 13.357 | 24.086 / 24.141 | 3600 / 3600 | 3600 / 3600 |
| 4k-3840x2160p120-av1-sdr-250mbps | BASELINE_FAILURE | 1.091 / 1.096 | 19.884 / 19.874 | 78.146 / 78.149 | 1907 / 1906 | 1907 / 1906 |
| 4k-3840x2160p120-av1-sdr-350mbps | BASELINE_FAILURE | 1.953 / 1.912 | 29.103 / 29.097 | 101.101 / 100.705 | 1038 / 1030 | 1038 / 1030 |
| 4k-3840x2160p120-av1-hdr10-50mbps | INCONCLUSIVE | 0.761 / 0.821 | 9.533 / 9.597 | 12.791 / 12.921 | 3600 / 3600 | 3600 / 3600 |
| 4k-3840x2160p120-av1-hdr10-100mbps | INCONCLUSIVE | 0.837 / 0.850 | 12.617 / 12.620 | 21.017 / 20.851 | 3600 / 3600 | 3600 / 3600 |
| 4k-3840x2160p120-av1-hdr10-250mbps | BASELINE_FAILURE | 1.154 / 1.205 | 18.801 / 19.225 | 98.868 / 98.823 | 2514 / 2425 | 2514 / 2425 |
| 4k-3840x2160p120-av1-hdr10-350mbps | BASELINE_FAILURE | 1.236 / 1.264 | 20.487 / 20.514 | 108.492 / 108.163 | 1785 / 1776 | 1785 / 1776 |
| 4k-3840x2160p120-hevc-sdr-50mbps | INCONCLUSIVE | 0.671 / 0.661 | 3.043 / 3.035 | 3.686 / 3.686 | 3600 / 3600 | 3600 / 3600 |
| 4k-3840x2160p120-hevc-sdr-100mbps | INCONCLUSIVE | 0.683 / 0.680 | 3.305 / 3.301 | 4.115 / 4.180 | 3600 / 3599 | 3600 / 3600 |
| 4k-3840x2160p120-hevc-sdr-250mbps | PASS | 0.689 / 0.754 | 3.883 / 3.980 | 5.549 / 5.684 | 3600 / 3600 | 3600 / 3600 |
| 4k-3840x2160p120-hevc-sdr-350mbps | PASS | 0.772 / 0.751 | 4.646 / 4.619 | 7.091 / 7.038 | 3600 / 3600 | 3600 / 3600 |
| 4k-3840x2160p120-hevc-hdr10-50mbps | INCONCLUSIVE | 0.734 / 0.745 | 3.152 / 3.175 | 3.872 / 3.903 | 3600 / 3600 | 3600 / 3600 |
| 4k-3840x2160p120-hevc-hdr10-100mbps | INCONCLUSIVE | 0.750 / 0.737 | 3.423 / 3.406 | 4.284 / 4.278 | 3600 / 3600 | 3600 / 3600 |
| 4k-3840x2160p120-hevc-hdr10-250mbps | PASS | 0.784 / 0.823 | 4.052 / 4.099 | 5.689 / 5.765 | 3600 / 3600 | 3600 / 3600 |
| 4k-3840x2160p120-hevc-hdr10-350mbps | PASS | 0.836 / 0.810 | 4.774 / 4.740 | 6.902 / 6.808 | 3600 / 3600 | 3600 / 3600 |

## 1080p-1920x1080p60-av1-sdr-50mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, SDR. Measured bitrate: 57.204 Mbps. Encoder target: 50.000 Mbps; measured/target: 114.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.067 | 0 / 0 | 69.030 | 0.781 (600) | 5.080 (600) | 5.649 |
| candidate / 1 | 600 / 600 | 60.069 | 0 / 0 | 71.742 | 0.773 (600) | 5.065 (600) | 5.651 |
| candidate / 2 | 600 / 600 | 60.069 | 0 / 0 | 70.091 | 0.791 (600) | 5.088 (600) | 5.661 |
| baseline / 2 | 600 / 600 | 60.067 | 0 / 0 | 70.198 | 0.769 (600) | 5.061 (600) | 5.635 |
| baseline / 3 | 600 / 600 | 60.070 | 0 / 0 | 70.219 | 0.797 (600) | 5.109 (600) | 5.683 |
| candidate / 3 | 600 / 600 | 60.069 | 0 / 0 | 73.210 | 0.857 (600) | 5.184 (600) | 5.774 |

## 1080p-1920x1080p60-av1-sdr-100mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, SDR. Measured bitrate: 106.491 Mbps. Encoder target: 100.000 Mbps; measured/target: 106.5%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.065 | 0 / 0 | 74.489 | 0.676 (600) | 5.639 (600) | 6.294 |
| baseline / 1 | 600 / 600 | 60.064 | 0 / 0 | 80.648 | 0.820 (600) | 5.865 (600) | 6.518 |
| baseline / 2 | 600 / 600 | 60.066 | 0 / 0 | 75.580 | 0.846 (600) | 5.870 (600) | 6.511 |
| candidate / 2 | 600 / 600 | 60.066 | 0 / 0 | 75.693 | 0.801 (600) | 5.846 (600) | 6.463 |
| candidate / 3 | 600 / 600 | 60.064 | 0 / 0 | 76.013 | 0.834 (600) | 5.874 (600) | 6.474 |
| baseline / 3 | 600 / 600 | 60.066 | 0 / 0 | 75.459 | 0.854 (600) | 5.903 (600) | 6.501 |

## 1080p-1920x1080p60-av1-sdr-250mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, SDR. Measured bitrate: 252.061 Mbps. Encoder target: 250.000 Mbps; measured/target: 100.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.055 | 0 / 0 | 79.422 | 0.971 (600) | 7.471 (600) | 8.103 |
| candidate / 1 | 600 / 600 | 60.055 | 0 / 0 | 81.922 | 0.919 (600) | 7.411 (600) | 8.072 |
| candidate / 2 | 600 / 600 | 60.060 | 0 / 0 | 80.041 | 0.866 (600) | 7.325 (600) | 7.960 |
| baseline / 2 | 600 / 600 | 60.056 | 0 / 0 | 79.654 | 0.816 (600) | 7.263 (600) | 7.902 |
| baseline / 3 | 600 / 600 | 60.057 | 0 / 0 | 80.448 | 0.901 (600) | 7.379 (600) | 8.009 |
| candidate / 3 | 600 / 600 | 60.057 | 0 / 0 | 81.107 | 0.973 (600) | 7.482 (600) | 8.112 |

## 1080p-1920x1080p60-av1-sdr-350mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, SDR. Measured bitrate: 341.410 Mbps. Encoder target: 350.000 Mbps; measured/target: 97.5%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.048 | 0 / 0 | 81.065 | 0.956 (600) | 8.419 (600) | 9.049 |
| baseline / 1 | 600 / 600 | 60.048 | 0 / 0 | 80.623 | 0.983 (600) | 8.461 (600) | 9.090 |
| baseline / 2 | 600 / 600 | 60.049 | 0 / 0 | 80.782 | 0.926 (600) | 8.379 (600) | 9.030 |
| candidate / 2 | 600 / 600 | 60.049 | 0 / 0 | 80.527 | 0.940 (600) | 8.396 (600) | 9.034 |
| candidate / 3 | 600 / 600 | 60.045 | 0 / 0 | 80.611 | 0.943 (600) | 8.401 (600) | 9.033 |
| baseline / 3 | 600 / 600 | 60.049 | 0 / 0 | 81.689 | 1.041 (600) | 8.560 (600) | 9.193 |

## 1080p-1920x1080p60-av1-hdr10-50mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, HDR10. Measured bitrate: 55.689 Mbps. Encoder target: 50.000 Mbps; measured/target: 111.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.062 | 0 / 0 | 69.688 | 0.817 (600) | 4.105 (600) | 4.666 |
| candidate / 1 | 600 / 600 | 60.065 | 0 / 0 | 70.561 | 0.858 (600) | 4.169 (600) | 4.740 |
| candidate / 2 | 600 / 600 | 60.062 | 0 / 0 | 71.431 | 0.923 (600) | 4.247 (600) | 4.812 |
| baseline / 2 | 600 / 600 | 60.063 | 0 / 0 | 73.502 | 0.915 (600) | 4.233 (600) | 4.835 |
| baseline / 3 | 600 / 600 | 60.063 | 0 / 0 | 72.664 | 0.966 (600) | 4.304 (600) | 4.898 |
| candidate / 3 | 600 / 600 | 60.065 | 0 / 0 | 74.211 | 1.048 (598) | 4.364 (600) | 5.047 |

## 1080p-1920x1080p60-av1-hdr10-100mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, HDR10. Measured bitrate: 105.017 Mbps. Encoder target: 100.000 Mbps; measured/target: 105.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.063 | 0 / 0 | 81.074 | 0.959 (600) | 6.082 (600) | 6.738 |
| baseline / 1 | 600 / 600 | 60.063 | 0 / 0 | 77.375 | 0.912 (600) | 5.981 (600) | 6.611 |
| baseline / 2 | 600 / 600 | 60.066 | 0 / 0 | 79.130 | 0.944 (600) | 6.031 (600) | 6.676 |
| candidate / 2 | 600 / 600 | 60.064 | 0 / 0 | 74.173 | 0.834 (600) | 5.879 (600) | 6.465 |
| candidate / 3 | 600 / 600 | 60.061 | 0 / 0 | 74.951 | 0.871 (600) | 5.941 (600) | 6.528 |
| baseline / 3 | 600 / 600 | 60.065 | 0 / 0 | 75.347 | 0.885 (600) | 5.967 (600) | 6.564 |

## 1080p-1920x1080p60-av1-hdr10-250mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, HDR10. Measured bitrate: 251.854 Mbps. Encoder target: 250.000 Mbps; measured/target: 100.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.056 | 0 / 0 | 80.714 | 1.102 (600) | 7.698 (600) | 8.351 |
| candidate / 1 | 600 / 600 | 60.055 | 0 / 0 | 81.576 | 1.093 (600) | 7.693 (600) | 8.388 |
| candidate / 2 | 600 / 600 | 60.056 | 0 / 0 | 81.163 | 0.983 (600) | 7.531 (600) | 8.232 |
| baseline / 2 | 600 / 600 | 60.055 | 0 / 0 | 88.862 | 0.925 (600) | 7.446 (600) | 8.180 |
| baseline / 3 | 600 / 600 | 60.055 | 0 / 0 | 82.272 | 0.967 (600) | 7.445 (600) | 8.160 |
| candidate / 3 | 600 / 600 | 60.055 | 0 / 0 | 88.012 | 0.964 (600) | 7.514 (600) | 8.239 |

## 1080p-1920x1080p60-av1-hdr10-350mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; AV1, HDR10. Measured bitrate: 336.219 Mbps. Encoder target: 350.000 Mbps; measured/target: 96.1%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.047 | 0 / 0 | 92.322 | 1.012 (600) | 8.686 (600) | 9.454 |
| baseline / 1 | 600 / 600 | 60.047 | 0 / 0 | 82.217 | 0.993 (600) | 8.645 (600) | 9.335 |
| baseline / 2 | 600 / 600 | 60.050 | 0 / 0 | 87.518 | 1.124 (600) | 8.822 (600) | 9.593 |
| candidate / 2 | 600 / 600 | 60.048 | 0 / 0 | 83.458 | 0.958 (600) | 8.589 (600) | 9.265 |
| candidate / 3 | 600 / 600 | 60.049 | 0 / 0 | 81.788 | 1.068 (600) | 8.767 (600) | 9.400 |
| baseline / 3 | 600 / 600 | 60.048 | 0 / 0 | 87.246 | 1.024 (600) | 8.693 (600) | 9.393 |

## 1080p-1920x1080p60-hevc-sdr-50mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, SDR. Measured bitrate: 46.760 Mbps. Encoder target: 50.000 Mbps; measured/target: 93.5%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.085 | 0 / 0 | 63.997 | 0.726 (600) | 2.198 (600) | 2.791 |
| candidate / 1 | 600 / 600 | 60.085 | 0 / 0 | 65.211 | 0.747 (600) | 2.245 (600) | 2.839 |
| candidate / 2 | 600 / 600 | 60.085 | 0 / 0 | 63.702 | 0.734 (600) | 2.218 (600) | 2.810 |
| baseline / 2 | 600 / 600 | 60.086 | 0 / 0 | 64.043 | 0.746 (600) | 2.240 (600) | 2.826 |
| baseline / 3 | 600 / 600 | 60.086 | 0 / 0 | 64.943 | 0.799 (600) | 2.315 (600) | 2.894 |
| candidate / 3 | 600 / 600 | 60.085 | 0 / 0 | 60.486 | 0.753 (599) | 2.236 (600) | 2.808 |

## 1080p-1920x1080p60-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, SDR. Measured bitrate: 85.816 Mbps. Encoder target: 100.000 Mbps; measured/target: 85.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.082 | 0 / 0 | 65.111 | 0.785 (600) | 2.935 (600) | 3.603 |
| baseline / 1 | 600 / 600 | 60.083 | 0 / 0 | 65.089 | 0.819 (599) | 2.997 (600) | 3.608 |
| baseline / 2 | 600 / 600 | 60.084 | 0 / 0 | 62.719 | 0.814 (600) | 2.987 (600) | 3.573 |
| candidate / 2 | 600 / 600 | 60.084 | 0 / 0 | 61.942 | 0.790 (600) | 2.947 (600) | 3.530 |
| candidate / 3 | 600 / 600 | 60.084 | 0 / 0 | 63.497 | 0.846 (600) | 3.032 (600) | 3.620 |
| baseline / 3 | 600 / 600 | 60.086 | 0 / 0 | 62.351 | 0.813 (600) | 2.986 (600) | 3.580 |

## 1080p-1920x1080p60-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, SDR. Measured bitrate: 210.975 Mbps. Encoder target: 250.000 Mbps; measured/target: 84.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.065 | 0 / 0 | 63.807 | 0.934 (600) | 5.142 (600) | 5.804 |
| candidate / 1 | 600 / 600 | 60.065 | 0 / 0 | 64.819 | 0.920 (600) | 5.124 (600) | 5.793 |
| candidate / 2 | 600 / 600 | 60.067 | 0 / 0 | 62.845 | 0.929 (600) | 5.144 (600) | 5.805 |
| baseline / 2 | 600 / 600 | 60.066 | 0 / 0 | 64.118 | 0.954 (600) | 5.174 (600) | 5.836 |
| baseline / 3 | 600 / 600 | 60.066 | 0 / 0 | 64.544 | 1.016 (600) | 5.265 (600) | 5.950 |
| candidate / 3 | 600 / 600 | 60.065 | 0 / 0 | 64.862 | 0.929 (600) | 5.137 (600) | 5.811 |

## 1080p-1920x1080p60-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, SDR. Measured bitrate: 292.960 Mbps. Encoder target: 350.000 Mbps; measured/target: 83.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.063 | 0 / 0 | 63.150 | 0.927 (600) | 6.053 (600) | 6.768 |
| baseline / 1 | 600 / 600 | 60.062 | 0 / 0 | 68.867 | 0.921 (600) | 6.052 (600) | 6.825 |
| baseline / 2 | 600 / 600 | 60.065 | 0 / 0 | 62.962 | 0.972 (600) | 6.124 (600) | 6.823 |
| candidate / 2 | 600 / 600 | 60.061 | 0 / 0 | 63.497 | 0.928 (600) | 6.065 (600) | 6.777 |
| candidate / 3 | 600 / 600 | 60.066 | 0 / 0 | 63.628 | 0.970 (600) | 6.114 (600) | 6.849 |
| baseline / 3 | 600 / 600 | 60.062 | 0 / 0 | 72.900 | 0.883 (600) | 5.998 (600) | 6.801 |

## 1080p-1920x1080p60-hevc-hdr10-50mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, HDR10. Measured bitrate: 46.775 Mbps. Encoder target: 50.000 Mbps; measured/target: 93.6%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.081 | 0 / 0 | 65.012 | 0.802 (600) | 2.356 (600) | 2.943 |
| candidate / 1 | 600 / 600 | 60.082 | 0 / 0 | 65.752 | 0.767 (600) | 2.303 (600) | 2.908 |
| candidate / 2 | 600 / 600 | 60.081 | 0 / 0 | 67.674 | 0.793 (600) | 2.320 (600) | 2.940 |
| baseline / 2 | 600 / 600 | 60.084 | 0 / 0 | 69.092 | 0.749 (600) | 2.230 (600) | 2.866 |
| baseline / 3 | 600 / 600 | 60.084 | 0 / 0 | 71.520 | 1.070 (600) | 2.716 (600) | 3.402 |
| candidate / 3 | 600 / 600 | 60.088 | 0 / 0 | 65.273 | 0.804 (600) | 2.344 (600) | 2.936 |

## 1080p-1920x1080p60-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, HDR10. Measured bitrate: 86.171 Mbps. Encoder target: 100.000 Mbps; measured/target: 86.2%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.078 | 0 / 0 | 62.564 | 0.826 (600) | 3.020 (600) | 3.615 |
| baseline / 1 | 600 / 600 | 60.078 | 0 / 0 | 62.954 | 0.839 (600) | 3.042 (600) | 3.634 |
| baseline / 2 | 600 / 600 | 60.079 | 0 / 0 | 63.148 | 0.800 (600) | 2.982 (600) | 3.575 |
| candidate / 2 | 600 / 600 | 60.079 | 0 / 0 | 64.248 | 0.974 (600) | 3.200 (600) | 3.853 |
| candidate / 3 | 600 / 600 | 60.079 | 0 / 0 | 74.550 | 0.857 (600) | 3.078 (600) | 3.775 |
| baseline / 3 | 600 / 600 | 60.078 | 0 / 0 | 63.724 | 0.850 (600) | 3.063 (600) | 3.665 |

## 1080p-1920x1080p60-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, HDR10. Measured bitrate: 211.013 Mbps. Encoder target: 250.000 Mbps; measured/target: 84.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.066 | 0 / 0 | 63.781 | 1.002 (600) | 5.224 (600) | 5.901 |
| candidate / 1 | 600 / 600 | 60.067 | 0 / 0 | 70.936 | 0.968 (600) | 5.196 (600) | 5.937 |
| candidate / 2 | 600 / 600 | 60.065 | 0 / 0 | 65.157 | 0.974 (600) | 5.195 (600) | 5.885 |
| baseline / 2 | 600 / 600 | 60.066 | 0 / 0 | 63.615 | 0.924 (600) | 5.122 (600) | 5.789 |
| baseline / 3 | 600 / 600 | 60.066 | 0 / 0 | 65.081 | 1.011 (600) | 5.248 (600) | 5.936 |
| candidate / 3 | 600 / 600 | 60.064 | 0 / 0 | 63.783 | 0.924 (600) | 5.126 (600) | 5.794 |

## 1080p-1920x1080p60-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 60 fps; HEVC, HDR10. Measured bitrate: 293.593 Mbps. Encoder target: 350.000 Mbps; measured/target: 83.9%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.063 | 0 / 0 | 64.365 | 1.099 (600) | 6.276 (600) | 7.050 |
| baseline / 1 | 600 / 600 | 60.060 | 0 / 0 | 69.857 | 1.000 (600) | 6.167 (600) | 6.964 |
| baseline / 2 | 600 / 600 | 60.060 | 0 / 0 | 70.803 | 0.992 (600) | 6.148 (600) | 6.936 |
| candidate / 2 | 600 / 600 | 60.059 | 0 / 0 | 63.681 | 0.988 (600) | 6.151 (600) | 6.885 |
| candidate / 3 | 600 / 600 | 60.062 | 0 / 0 | 64.066 | 0.980 (600) | 6.127 (600) | 6.858 |
| baseline / 3 | 600 / 600 | 60.063 | 0 / 0 | 64.405 | 0.939 (600) | 6.066 (600) | 6.804 |

## 1080p-1920x1080p120-av1-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, SDR. Measured bitrate: 86.448 Mbps. Encoder target: 50.000 Mbps; measured/target: 172.9%.

measured payload bitrate 86.448 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.079 | 0 / 0 | 66.998 | 0.677 (1200) | 3.658 (1200) | 4.223 |
| candidate / 1 | 1200 / 1200 | 120.079 | 0 / 0 | 64.362 | 0.678 (1200) | 3.660 (1200) | 4.190 |
| candidate / 2 | 1200 / 1200 | 120.073 | 0 / 0 | 67.187 | 0.687 (1200) | 3.675 (1200) | 4.266 |
| baseline / 2 | 1200 / 1200 | 120.072 | 0 / 0 | 67.778 | 0.746 (1200) | 3.761 (1200) | 4.397 |
| baseline / 3 | 1200 / 1200 | 120.074 | 0 / 0 | 67.720 | 0.706 (1200) | 3.706 (1200) | 4.326 |
| candidate / 3 | 1200 / 1200 | 120.075 | 0 / 0 | 67.901 | 0.703 (1200) | 3.692 (1200) | 4.297 |

## 1080p-1920x1080p120-av1-sdr-100mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, SDR. Measured bitrate: 119.333 Mbps. Encoder target: 100.000 Mbps; measured/target: 119.3%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.046 | 0 / 0 | 69.131 | 0.702 (1200) | 5.128 (1200) | 5.820 |
| baseline / 1 | 1200 / 1200 | 120.038 | 0 / 0 | 79.808 | 0.680 (1200) | 5.095 (1200) | 5.930 |
| baseline / 2 | 1200 / 1200 | 120.042 | 0 / 0 | 71.348 | 0.657 (1200) | 5.055 (1200) | 5.750 |
| candidate / 2 | 1200 / 1200 | 120.037 | 0 / 0 | 71.525 | 0.771 (1200) | 5.221 (1200) | 5.956 |
| candidate / 3 | 1200 / 1200 | 120.036 | 0 / 0 | 69.724 | 0.733 (1200) | 5.161 (1200) | 5.859 |
| baseline / 3 | 1200 / 1200 | 120.035 | 0 / 0 | 87.029 | 0.695 (1200) | 5.108 (1200) | 5.985 |

## 1080p-1920x1080p120-av1-sdr-250mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, SDR. Measured bitrate: 261.791 Mbps. Encoder target: 250.000 Mbps; measured/target: 104.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.026 | 0 / 0 | 77.321 | 0.734 (1200) | 6.234 (1200) | 7.228 |
| candidate / 1 | 1200 / 1200 | 120.031 | 0 / 0 | 77.040 | 0.732 (1200) | 6.222 (1200) | 7.217 |
| candidate / 2 | 1200 / 1200 | 120.025 | 0 / 0 | 75.400 | 0.753 (1200) | 6.263 (1200) | 7.260 |
| baseline / 2 | 1200 / 1200 | 120.034 | 0 / 0 | 76.660 | 0.887 (1200) | 6.450 (1200) | 7.498 |
| baseline / 3 | 1200 / 1200 | 120.033 | 0 / 0 | 78.238 | 0.762 (1199) | 6.264 (1200) | 7.296 |
| candidate / 3 | 1200 / 1200 | 120.025 | 0 / 0 | 75.584 | 0.636 (1200) | 6.089 (1200) | 7.048 |

## 1080p-1920x1080p120-av1-sdr-350mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, SDR. Measured bitrate: 360.073 Mbps. Encoder target: 350.000 Mbps; measured/target: 102.9%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.024 | 0 / 0 | 78.665 | 0.703 (1198) | 6.714 (1200) | 7.862 |
| baseline / 1 | 1200 / 1200 | 120.018 | 0 / 0 | 81.384 | 0.803 (1200) | 6.852 (1200) | 8.122 |
| baseline / 2 | 1200 / 1200 | 120.017 | 0 / 0 | 77.958 | 0.768 (1200) | 6.796 (1200) | 7.966 |
| candidate / 2 | 1200 / 1200 | 120.017 | 0 / 0 | 77.644 | 0.856 (1200) | 6.927 (1200) | 8.163 |
| candidate / 3 | 1200 / 1200 | 120.020 | 0 / 0 | 82.709 | 0.792 (1200) | 6.844 (1200) | 8.154 |
| baseline / 3 | 1200 / 1200 | 120.020 | 0 / 0 | 78.635 | 0.788 (1200) | 6.825 (1200) | 8.052 |

## 1080p-1920x1080p120-av1-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, HDR10. Measured bitrate: 73.130 Mbps. Encoder target: 50.000 Mbps; measured/target: 146.3%.

measured payload bitrate 73.130 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.077 | 0 / 0 | 67.361 | 0.706 (1200) | 3.442 (1200) | 4.083 |
| candidate / 1 | 1200 / 1200 | 120.076 | 0 / 0 | 67.792 | 0.740 (1200) | 3.500 (1200) | 4.148 |
| candidate / 2 | 1200 / 1200 | 120.077 | 0 / 0 | 66.796 | 0.736 (1200) | 3.491 (1200) | 4.113 |
| baseline / 2 | 1200 / 1200 | 120.078 | 0 / 0 | 68.603 | 0.791 (1200) | 3.565 (1200) | 4.236 |
| baseline / 3 | 1200 / 1200 | 120.075 | 0 / 0 | 68.727 | 0.753 (1200) | 3.521 (1200) | 4.207 |
| candidate / 3 | 1200 / 1200 | 120.072 | 0 / 0 | 67.839 | 0.721 (1200) | 3.465 (1200) | 4.092 |

## 1080p-1920x1080p120-av1-hdr10-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, HDR10. Measured bitrate: 122.612 Mbps. Encoder target: 100.000 Mbps; measured/target: 122.6%.

measured payload bitrate 122.612 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.073 | 0 / 0 | 70.594 | 0.763 (1200) | 4.233 (1200) | 4.970 |
| baseline / 1 | 1200 / 1200 | 120.071 | 0 / 0 | 70.038 | 0.732 (1200) | 4.192 (1200) | 4.898 |
| baseline / 2 | 1200 / 1200 | 120.077 | 0 / 0 | 69.916 | 0.781 (1200) | 4.254 (1200) | 4.981 |
| candidate / 2 | 1200 / 1200 | 120.066 | 0 / 0 | 79.546 | 0.802 (1200) | 4.297 (1200) | 5.131 |
| candidate / 3 | 1200 / 1200 | 120.068 | 0 / 0 | 74.311 | 0.656 (1200) | 4.049 (1200) | 4.796 |
| baseline / 3 | 1200 / 1200 | 120.075 | 0 / 0 | 74.883 | 0.744 (1200) | 4.207 (1200) | 4.965 |

## 1080p-1920x1080p120-av1-hdr10-250mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, HDR10. Measured bitrate: 260.393 Mbps. Encoder target: 250.000 Mbps; measured/target: 104.2%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.022 | 0 / 0 | 77.022 | 0.740 (1200) | 6.206 (1200) | 7.198 |
| candidate / 1 | 1200 / 1200 | 120.027 | 0 / 0 | 78.055 | 0.811 (1200) | 6.328 (1200) | 7.404 |
| candidate / 2 | 1200 / 1200 | 120.023 | 0 / 0 | 77.244 | 0.806 (1200) | 6.314 (1200) | 7.360 |
| baseline / 2 | 1200 / 1200 | 120.027 | 0 / 0 | 77.272 | 0.606 (1200) | 5.999 (1200) | 6.935 |
| baseline / 3 | 1200 / 1200 | 120.024 | 0 / 0 | 84.031 | 0.736 (1200) | 6.212 (1200) | 7.299 |
| candidate / 3 | 1200 / 1200 | 120.025 | 0 / 0 | 78.195 | 0.775 (1200) | 6.270 (1200) | 7.326 |

## 1080p-1920x1080p120-av1-hdr10-350mbps

Status: PASS

Full-frame software reference: libdav1d; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; AV1, HDR10. Measured bitrate: 360.356 Mbps. Encoder target: 350.000 Mbps; measured/target: 103.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.019 | 0 / 0 | 79.454 | 0.719 (1200) | 6.717 (1200) | 7.898 |
| baseline / 1 | 1200 / 1200 | 120.027 | 0 / 0 | 83.956 | 0.771 (1200) | 6.795 (1200) | 8.073 |
| baseline / 2 | 1200 / 1200 | 120.033 | 0 / 0 | 79.310 | 0.682 (1200) | 6.667 (1200) | 7.822 |
| candidate / 2 | 1200 / 1200 | 120.018 | 0 / 0 | 78.198 | 0.791 (1200) | 6.825 (1200) | 8.005 |
| candidate / 3 | 1200 / 1200 | 120.018 | 0 / 0 | 84.094 | 0.787 (1200) | 6.826 (1200) | 8.142 |
| baseline / 3 | 1200 / 1200 | 120.018 | 0 / 0 | 80.119 | 0.806 (1200) | 6.850 (1200) | 8.089 |

## 1080p-1920x1080p120-hevc-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, SDR. Measured bitrate: 62.494 Mbps. Encoder target: 50.000 Mbps; measured/target: 125.0%.

measured payload bitrate 62.494 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.075 | 0 / 0 | 62.424 | 0.575 (1200) | 1.820 (1200) | 2.308 |
| candidate / 1 | 1200 / 1200 | 120.077 | 0 / 0 | 64.118 | 0.653 (1199) | 1.950 (1200) | 2.454 |
| candidate / 2 | 1200 / 1200 | 120.078 | 0 / 0 | 64.734 | 0.650 (1200) | 1.941 (1200) | 2.456 |
| baseline / 2 | 1200 / 1200 | 120.076 | 0 / 0 | 64.257 | 0.661 (1199) | 1.951 (1200) | 2.538 |
| baseline / 3 | 1200 / 1200 | 120.078 | 0 / 0 | 65.019 | 0.606 (1200) | 1.860 (1200) | 2.427 |
| candidate / 3 | 1200 / 1200 | 120.080 | 0 / 0 | 67.238 | 0.579 (1200) | 1.827 (1200) | 2.353 |

## 1080p-1920x1080p120-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, SDR. Measured bitrate: 101.643 Mbps. Encoder target: 100.000 Mbps; measured/target: 101.6%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.075 | 0 / 0 | 62.177 | 0.678 (1200) | 2.182 (1200) | 2.727 |
| baseline / 1 | 1200 / 1200 | 120.072 | 0 / 0 | 63.894 | 0.703 (1200) | 2.213 (1200) | 2.776 |
| baseline / 2 | 1200 / 1200 | 120.075 | 0 / 0 | 63.644 | 0.684 (1200) | 2.188 (1200) | 2.744 |
| candidate / 2 | 1200 / 1200 | 120.075 | 0 / 0 | 64.211 | 0.752 (1200) | 2.285 (1200) | 2.899 |
| candidate / 3 | 1200 / 1200 | 120.074 | 0 / 0 | 62.559 | 0.665 (1200) | 2.168 (1200) | 2.708 |
| baseline / 3 | 1200 / 1200 | 120.075 | 0 / 0 | 62.917 | 0.699 (1200) | 2.212 (1200) | 2.768 |

## 1080p-1920x1080p120-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, SDR. Measured bitrate: 221.925 Mbps. Encoder target: 250.000 Mbps; measured/target: 88.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.057 | 0 / 0 | 63.189 | 0.709 (1200) | 3.280 (1200) | 3.960 |
| candidate / 1 | 1200 / 1200 | 120.056 | 0 / 0 | 66.548 | 0.761 (1200) | 3.360 (1200) | 4.124 |
| candidate / 2 | 1200 / 1200 | 120.049 | 0 / 0 | 62.347 | 0.765 (1200) | 3.361 (1200) | 4.082 |
| baseline / 2 | 1200 / 1200 | 120.055 | 0 / 0 | 69.416 | 0.790 (1200) | 3.404 (1200) | 4.216 |
| baseline / 3 | 1200 / 1200 | 120.048 | 0 / 0 | 61.772 | 0.783 (1200) | 3.387 (1200) | 4.097 |
| candidate / 3 | 1200 / 1200 | 120.051 | 0 / 0 | 62.017 | 0.748 (1200) | 3.333 (1200) | 4.036 |

## 1080p-1920x1080p120-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, SDR. Measured bitrate: 304.845 Mbps. Encoder target: 350.000 Mbps; measured/target: 87.1%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.039 | 0 / 0 | 63.417 | 0.764 (1200) | 4.118 (1200) | 4.904 |
| baseline / 1 | 1200 / 1200 | 120.039 | 0 / 0 | 63.422 | 0.747 (1200) | 4.102 (1200) | 4.863 |
| baseline / 2 | 1200 / 1200 | 120.037 | 0 / 0 | 62.716 | 0.775 (1200) | 4.135 (1200) | 4.886 |
| candidate / 2 | 1200 / 1200 | 120.041 | 0 / 0 | 63.825 | 0.749 (1200) | 4.102 (1200) | 4.867 |
| candidate / 3 | 1200 / 1200 | 120.039 | 0 / 0 | 63.391 | 0.626 (1200) | 3.921 (1200) | 4.631 |
| baseline / 3 | 1200 / 1200 | 120.048 | 0 / 0 | 65.115 | 0.759 (1200) | 4.114 (1200) | 4.913 |

## 1080p-1920x1080p120-hevc-hdr10-50mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, HDR10. Measured bitrate: 59.055 Mbps. Encoder target: 50.000 Mbps; measured/target: 118.1%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.091 | 0 / 0 | 65.476 | 0.638 (1200) | 1.939 (1200) | 2.468 |
| candidate / 1 | 1200 / 1200 | 120.077 | 0 / 0 | 62.295 | 0.584 (1200) | 1.845 (1200) | 2.347 |
| candidate / 2 | 1200 / 1200 | 120.077 | 0 / 0 | 69.534 | 0.643 (1200) | 1.927 (1200) | 2.551 |
| baseline / 2 | 1200 / 1200 | 120.071 | 0 / 0 | 70.231 | 0.636 (1200) | 1.932 (1200) | 2.527 |
| baseline / 3 | 1200 / 1200 | 120.081 | 0 / 0 | 65.191 | 0.629 (1200) | 1.917 (1200) | 2.481 |
| candidate / 3 | 1200 / 1200 | 120.073 | 0 / 0 | 65.124 | 0.662 (1199) | 1.964 (1200) | 2.553 |

## 1080p-1920x1080p120-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, HDR10. Measured bitrate: 99.018 Mbps. Encoder target: 100.000 Mbps; measured/target: 99.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.070 | 0 / 0 | 64.820 | 0.707 (1200) | 2.260 (1200) | 2.835 |
| baseline / 1 | 1200 / 1200 | 120.069 | 0 / 0 | 65.471 | 0.677 (1199) | 2.211 (1200) | 2.816 |
| baseline / 2 | 1200 / 1200 | 120.076 | 0 / 0 | 64.979 | 0.761 (1200) | 2.320 (1200) | 2.959 |
| candidate / 2 | 1200 / 1200 | 120.076 | 0 / 0 | 68.495 | 0.702 (1200) | 2.249 (1200) | 2.872 |
| candidate / 3 | 1200 / 1200 | 120.068 | 0 / 0 | 67.509 | 0.728 (1200) | 2.274 (1200) | 2.924 |
| baseline / 3 | 1200 / 1200 | 120.079 | 0 / 0 | 69.943 | 0.720 (1200) | 2.262 (1200) | 2.929 |

## 1080p-1920x1080p120-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, HDR10. Measured bitrate: 219.167 Mbps. Encoder target: 250.000 Mbps; measured/target: 87.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.057 | 0 / 0 | 74.831 | 0.813 (1199) | 3.401 (1200) | 4.276 |
| candidate / 1 | 1200 / 1200 | 120.047 | 0 / 0 | 65.603 | 0.778 (1200) | 3.365 (1200) | 4.122 |
| candidate / 2 | 1200 / 1200 | 120.062 | 0 / 0 | 63.695 | 0.855 (1200) | 3.472 (1200) | 4.253 |
| baseline / 2 | 1200 / 1200 | 120.055 | 0 / 0 | 63.868 | 0.793 (1200) | 3.389 (1200) | 4.154 |
| baseline / 3 | 1200 / 1200 | 120.065 | 0 / 0 | 61.906 | 0.803 (1200) | 3.397 (1200) | 4.126 |
| candidate / 3 | 1200 / 1200 | 120.064 | 0 / 0 | 65.663 | 0.792 (1200) | 3.388 (1200) | 4.150 |

## 1080p-1920x1080p120-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 373,248,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 1920×1080 at 120 fps; HEVC, HDR10. Measured bitrate: 303.668 Mbps. Encoder target: 350.000 Mbps; measured/target: 86.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.042 | 0 / 0 | 63.304 | 0.817 (1200) | 4.165 (1200) | 4.988 |
| baseline / 1 | 1200 / 1200 | 120.051 | 0 / 0 | 62.813 | 0.788 (1200) | 4.122 (1200) | 4.901 |
| baseline / 2 | 1200 / 1200 | 120.042 | 0 / 0 | 63.977 | 0.865 (1200) | 4.227 (1200) | 5.068 |
| candidate / 2 | 1200 / 1200 | 120.041 | 0 / 0 | 64.904 | 0.773 (1200) | 4.090 (1200) | 4.890 |
| candidate / 3 | 1200 / 1200 | 120.048 | 0 / 0 | 64.183 | 0.847 (1200) | 4.201 (1200) | 5.049 |
| baseline / 3 | 1200 / 1200 | 120.043 | 0 / 0 | 64.159 | 0.765 (1200) | 4.087 (1200) | 4.887 |

## ultrawide-3440x1440p120-av1-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, SDR. Measured bitrate: 141.911 Mbps. Encoder target: 50.000 Mbps; measured/target: 283.8%.

measured payload bitrate 141.911 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.068 | 0 / 0 | 73.690 | 0.713 (1200) | 6.376 (1200) | 7.503 |
| candidate / 1 | 1200 / 1200 | 120.067 | 0 / 0 | 74.218 | 0.701 (1200) | 6.349 (1200) | 7.484 |
| candidate / 2 | 1200 / 1200 | 120.073 | 0 / 0 | 72.826 | 0.741 (1200) | 6.442 (1200) | 7.595 |
| baseline / 2 | 1200 / 1200 | 120.065 | 0 / 0 | 73.245 | 0.710 (1200) | 6.376 (1200) | 7.502 |
| baseline / 3 | 1200 / 1200 | 120.067 | 0 / 0 | 72.174 | 0.683 (1200) | 6.327 (1200) | 7.430 |
| candidate / 3 | 1200 / 1200 | 120.076 | 0 / 0 | 72.228 | 0.704 (1200) | 6.367 (1200) | 7.468 |

## ultrawide-3440x1440p120-av1-sdr-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, SDR. Measured bitrate: 185.744 Mbps. Encoder target: 100.000 Mbps; measured/target: 185.7%.

measured payload bitrate 185.744 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.059 | 0 / 0 | 77.883 | 0.574 (1200) | 7.872 (1200) | 10.110 |
| baseline / 1 | 1200 / 1200 | 120.058 | 0 / 0 | 86.149 | 0.720 (1200) | 8.052 (1200) | 10.569 |
| baseline / 2 | 1200 / 1200 | 120.058 | 0 / 0 | 78.625 | 0.735 (1200) | 8.086 (1200) | 10.440 |
| candidate / 2 | 1200 / 1200 | 120.058 | 0 / 0 | 78.170 | 0.635 (1200) | 7.949 (1200) | 10.220 |
| candidate / 3 | 1200 / 1200 | 120.058 | 0 / 0 | 77.245 | 0.710 (1200) | 8.043 (1200) | 10.329 |
| baseline / 3 | 1200 / 1200 | 120.061 | 0 / 0 | 78.933 | 0.717 (1200) | 8.048 (1200) | 10.388 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 939 / 1200 | 92.653 | 252 / 9 | 97.097 | 0.849 (939) | 18.020 (939) | 96.598 |
| candidate / 1 | 896 / 1200 | 89.177 | 293 / 11 | 89.533 | 0.839 (896) | 17.895 (896) | 93.329 |
| candidate / 2 | 894 / 1200 | 89.015 | 295 / 11 | 91.154 | 0.855 (894) | 17.949 (894) | 92.210 |
| baseline / 2 | 941 / 1200 | 92.879 | 250 / 9 | 96.488 | 0.797 (941) | 18.013 (941) | 95.074 |
| baseline / 3 | 896 / 1200 | 89.183 | 293 / 11 | 89.722 | 0.843 (896) | 17.896 (896) | 93.398 |
| candidate / 3 | 896 / 1200 | 89.191 | 294 / 10 | 91.209 | 0.832 (896) | 17.967 (896) | 92.237 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 819 / 1200 | 81.245 | 369 / 12 | 97.365 | 1.028 (819) | 19.700 (819) | 78.567 |
| baseline / 1 | 814 / 1200 | 80.770 | 374 / 12 | 101.275 | 1.011 (814) | 19.699 (814) | 78.707 |
| baseline / 2 | 816 / 1200 | 80.958 | 374 / 10 | 99.748 | 1.029 (816) | 19.700 (816) | 78.644 |
| candidate / 2 | 828 / 1200 | 82.151 | 362 / 10 | 97.824 | 1.006 (828) | 19.681 (828) | 78.563 |
| candidate / 3 | 809 / 1200 | 80.251 | 379 / 12 | 96.287 | 1.048 (809) | 19.718 (809) | 78.535 |
| baseline / 3 | 823 / 1200 | 81.640 | 366 / 11 | 97.728 | 1.008 (823) | 19.696 (823) | 78.610 |

## ultrawide-3440x1440p120-av1-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, HDR10. Measured bitrate: 142.056 Mbps. Encoder target: 50.000 Mbps; measured/target: 284.1%.

measured payload bitrate 142.056 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 119.954 | 0 / 0 | 77.193 | 0.808 (1200) | 6.293 (1200) | 7.519 |
| candidate / 1 | 1200 / 1200 | 119.963 | 0 / 0 | 74.683 | 0.818 (1200) | 6.310 (1200) | 7.503 |
| candidate / 2 | 1200 / 1200 | 119.952 | 0 / 0 | 79.558 | 0.782 (1200) | 6.251 (1200) | 7.493 |
| baseline / 2 | 1200 / 1200 | 119.952 | 0 / 0 | 74.119 | 0.793 (1200) | 6.265 (1200) | 7.445 |
| baseline / 3 | 1200 / 1200 | 119.955 | 0 / 0 | 74.350 | 0.747 (1200) | 6.190 (1200) | 7.354 |
| candidate / 3 | 1200 / 1200 | 119.951 | 0 / 0 | 73.885 | 0.772 (1200) | 6.233 (1200) | 7.404 |

## ultrawide-3440x1440p120-av1-hdr10-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, HDR10. Measured bitrate: 170.713 Mbps. Encoder target: 100.000 Mbps; measured/target: 170.7%.

measured payload bitrate 170.713 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 119.991 | 0 / 0 | 78.498 | 0.721 (1200) | 6.995 (1200) | 8.769 |
| baseline / 1 | 1200 / 1200 | 119.993 | 0 / 0 | 77.891 | 0.855 (1200) | 7.204 (1200) | 9.043 |
| baseline / 2 | 1200 / 1200 | 119.996 | 0 / 0 | 78.621 | 0.809 (1200) | 7.135 (1200) | 8.958 |
| candidate / 2 | 1200 / 1200 | 119.992 | 0 / 0 | 79.879 | 0.826 (1200) | 7.161 (1200) | 9.039 |
| candidate / 3 | 1200 / 1200 | 119.991 | 0 / 0 | 78.767 | 0.806 (1200) | 7.129 (1200) | 8.954 |
| baseline / 3 | 1200 / 1200 | 119.990 | 0 / 0 | 78.928 | 0.751 (1200) | 7.035 (1200) | 8.844 |

## ultrawide-3440x1440p120-av1-hdr10-250mbps

Status: PASS

Full-frame software reference: libdav1d; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; AV1, HDR10. Measured bitrate: 283.131 Mbps. Encoder target: 250.000 Mbps; measured/target: 113.3%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 119.959 | 0 / 0 | 91.594 | 0.831 (1200) | 12.636 (1200) | 23.541 |
| candidate / 1 | 1200 / 1200 | 119.966 | 0 / 0 | 97.346 | 0.849 (1200) | 12.687 (1200) | 24.078 |
| candidate / 2 | 1200 / 1200 | 119.974 | 0 / 0 | 93.507 | 0.686 (1200) | 12.543 (1200) | 23.354 |
| baseline / 2 | 1200 / 1200 | 119.964 | 0 / 0 | 101.606 | 0.755 (1200) | 12.696 (1200) | 24.341 |
| baseline / 3 | 1200 / 1200 | 119.965 | 0 / 0 | 91.765 | 0.812 (1200) | 12.721 (1200) | 23.813 |
| candidate / 3 | 1200 / 1200 | 119.973 | 0 / 0 | 92.976 | 0.761 (1200) | 12.573 (1200) | 23.602 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 874 / 1200 | 86.742 | 314 / 12 | 102.772 | 1.069 (874) | 19.473 (874) | 79.987 |
| baseline / 1 | 863 / 1200 | 85.628 | 325 / 12 | 98.709 | 1.088 (863) | 19.474 (863) | 80.292 |
| baseline / 2 | 867 / 1200 | 86.034 | 320 / 13 | 99.270 | 1.117 (867) | 19.489 (867) | 80.294 |
| candidate / 2 | 850 / 1200 | 84.373 | 340 / 10 | 97.991 | 1.105 (850) | 19.503 (850) | 80.464 |
| candidate / 3 | 856 / 1200 | 84.954 | 333 / 11 | 97.807 | 1.087 (856) | 19.474 (856) | 80.532 |
| baseline / 3 | 849 / 1200 | 84.256 | 338 / 13 | 97.333 | 1.093 (849) | 19.489 (849) | 80.521 |

## ultrawide-3440x1440p120-hevc-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, SDR. Measured bitrate: 70.255 Mbps. Encoder target: 50.000 Mbps; measured/target: 140.5%.

measured payload bitrate 70.255 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.073 | 0 / 0 | 66.455 | 0.649 (1200) | 2.422 (1200) | 2.997 |
| candidate / 1 | 1200 / 1200 | 120.076 | 0 / 0 | 66.573 | 0.721 (1199) | 2.539 (1200) | 3.190 |
| candidate / 2 | 1200 / 1200 | 120.076 | 0 / 0 | 65.210 | 0.620 (1200) | 2.387 (1200) | 2.925 |
| baseline / 2 | 1200 / 1200 | 120.074 | 0 / 0 | 67.479 | 0.664 (1200) | 2.448 (1200) | 3.036 |
| baseline / 3 | 1200 / 1200 | 120.076 | 0 / 0 | 66.998 | 0.632 (1200) | 2.401 (1200) | 2.943 |
| candidate / 3 | 1200 / 1200 | 120.076 | 0 / 0 | 65.555 | 0.641 (1200) | 2.418 (1200) | 2.953 |

## ultrawide-3440x1440p120-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, SDR. Measured bitrate: 98.189 Mbps. Encoder target: 100.000 Mbps; measured/target: 98.2%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.077 | 0 / 0 | 66.490 | 0.659 (1200) | 2.537 (1200) | 3.156 |
| baseline / 1 | 1200 / 1200 | 120.067 | 0 / 0 | 66.778 | 0.734 (1200) | 2.649 (1200) | 3.348 |
| baseline / 2 | 1200 / 1200 | 120.071 | 0 / 0 | 66.508 | 0.690 (1200) | 2.585 (1200) | 3.233 |
| candidate / 2 | 1200 / 1200 | 120.070 | 0 / 0 | 67.250 | 0.686 (1200) | 2.587 (1200) | 3.233 |
| candidate / 3 | 1200 / 1200 | 120.083 | 0 / 0 | 66.968 | 0.360 (1200) | 1.951 (1200) | 2.563 |
| baseline / 3 | 1200 / 1200 | 120.070 | 0 / 0 | 73.888 | 0.551 (1200) | 2.319 (1200) | 3.008 |

## ultrawide-3440x1440p120-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, SDR. Measured bitrate: 225.307 Mbps. Encoder target: 250.000 Mbps; measured/target: 90.1%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.051 | 0 / 0 | 68.653 | 0.711 (1200) | 3.737 (1200) | 4.957 |
| candidate / 1 | 1200 / 1200 | 120.047 | 0 / 0 | 68.601 | 0.741 (1200) | 3.782 (1200) | 5.031 |
| candidate / 2 | 1200 / 1200 | 120.050 | 0 / 0 | 69.052 | 0.718 (1200) | 3.749 (1200) | 4.969 |
| baseline / 2 | 1200 / 1200 | 120.050 | 0 / 0 | 68.487 | 0.725 (1200) | 3.753 (1200) | 4.973 |
| baseline / 3 | 1200 / 1200 | 120.050 | 0 / 0 | 69.194 | 0.685 (1200) | 3.704 (1200) | 4.877 |
| candidate / 3 | 1200 / 1200 | 120.049 | 0 / 0 | 68.395 | 0.745 (1200) | 3.782 (1200) | 5.011 |

## ultrawide-3440x1440p120-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, SDR. Measured bitrate: 305.886 Mbps. Encoder target: 350.000 Mbps; measured/target: 87.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.046 | 0 / 0 | 66.866 | 0.729 (1200) | 4.397 (1200) | 5.923 |
| baseline / 1 | 1200 / 1200 | 120.042 | 0 / 0 | 69.019 | 0.823 (1200) | 4.533 (1200) | 6.140 |
| baseline / 2 | 1200 / 1200 | 120.044 | 0 / 0 | 71.803 | 0.752 (1200) | 4.439 (1200) | 6.074 |
| candidate / 2 | 1200 / 1200 | 120.047 | 0 / 0 | 69.628 | 0.764 (1200) | 4.451 (1200) | 6.063 |
| candidate / 3 | 1200 / 1200 | 120.057 | 0 / 0 | 69.367 | 0.773 (1200) | 4.452 (1200) | 6.074 |
| baseline / 3 | 1200 / 1200 | 120.044 | 0 / 0 | 68.813 | 0.697 (1200) | 4.366 (1200) | 5.898 |

## ultrawide-3440x1440p120-hevc-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, HDR10. Measured bitrate: 64.800 Mbps. Encoder target: 50.000 Mbps; measured/target: 129.6%.

measured payload bitrate 64.800 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.068 | 0 / 0 | 67.463 | 0.714 (1200) | 2.504 (1200) | 3.112 |
| candidate / 1 | 1200 / 1200 | 120.068 | 0 / 0 | 65.539 | 0.757 (1200) | 2.570 (1200) | 3.230 |
| candidate / 2 | 1200 / 1200 | 120.074 | 0 / 0 | 66.808 | 0.675 (1200) | 2.440 (1200) | 3.001 |
| baseline / 2 | 1200 / 1200 | 120.074 | 0 / 0 | 66.801 | 0.714 (1200) | 2.506 (1200) | 3.098 |
| baseline / 3 | 1200 / 1200 | 120.067 | 0 / 0 | 67.652 | 0.679 (1200) | 2.457 (1200) | 3.020 |
| candidate / 3 | 1200 / 1200 | 120.074 | 0 / 0 | 66.394 | 0.704 (1200) | 2.488 (1200) | 3.088 |

## ultrawide-3440x1440p120-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, HDR10. Measured bitrate: 94.186 Mbps. Encoder target: 100.000 Mbps; measured/target: 94.2%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.062 | 0 / 0 | 66.338 | 0.747 (1200) | 2.646 (1200) | 3.311 |
| baseline / 1 | 1200 / 1200 | 120.077 | 0 / 0 | 66.476 | 0.668 (1200) | 2.518 (1200) | 3.170 |
| baseline / 2 | 1200 / 1200 | 120.064 | 0 / 0 | 63.564 | 0.691 (1200) | 2.557 (1200) | 3.176 |
| candidate / 2 | 1200 / 1200 | 120.070 | 0 / 0 | 65.549 | 0.703 (1199) | 2.583 (1200) | 3.205 |
| candidate / 3 | 1200 / 1200 | 120.066 | 0 / 0 | 65.941 | 0.697 (1200) | 2.578 (1200) | 3.185 |
| baseline / 3 | 1200 / 1200 | 120.060 | 0 / 0 | 68.086 | 0.731 (1200) | 2.624 (1200) | 3.305 |

## ultrawide-3440x1440p120-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, HDR10. Measured bitrate: 222.388 Mbps. Encoder target: 250.000 Mbps; measured/target: 89.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.046 | 0 / 0 | 68.839 | 0.798 (1199) | 3.833 (1200) | 4.849 |
| candidate / 1 | 1200 / 1200 | 120.050 | 0 / 0 | 75.202 | 0.821 (1200) | 3.869 (1200) | 5.024 |
| candidate / 2 | 1200 / 1200 | 120.052 | 0 / 0 | 67.649 | 0.746 (1200) | 3.774 (1200) | 4.759 |
| baseline / 2 | 1200 / 1200 | 120.054 | 0 / 0 | 70.721 | 0.757 (1200) | 3.783 (1200) | 4.801 |
| baseline / 3 | 1200 / 1200 | 120.042 | 0 / 0 | 68.709 | 0.803 (1200) | 3.846 (1200) | 4.902 |
| candidate / 3 | 1200 / 1200 | 120.047 | 0 / 0 | 69.476 | 0.782 (1200) | 3.812 (1200) | 4.852 |

## ultrawide-3440x1440p120-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 891,648,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 120 fps; HEVC, HDR10. Measured bitrate: 304.476 Mbps. Encoder target: 350.000 Mbps; measured/target: 87.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.043 | 0 / 0 | 68.852 | 0.871 (1200) | 4.575 (1200) | 6.057 |
| baseline / 1 | 1200 / 1200 | 120.045 | 0 / 0 | 75.157 | 0.823 (1200) | 4.512 (1200) | 6.056 |
| baseline / 2 | 1200 / 1200 | 120.047 | 0 / 0 | 69.832 | 0.824 (1200) | 4.508 (1200) | 5.992 |
| candidate / 2 | 1200 / 1200 | 120.045 | 0 / 0 | 69.980 | 0.789 (1200) | 4.462 (1200) | 5.915 |
| candidate / 3 | 1200 / 1200 | 120.045 | 0 / 0 | 68.490 | 0.764 (1200) | 4.433 (1200) | 5.814 |
| baseline / 3 | 1200 / 1200 | 120.044 | 0 / 0 | 76.788 | 0.805 (1200) | 4.485 (1200) | 6.045 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 2342 / 2400 | 234.181 | 56 / 2 | 70.246 | 0.637 (2342) | 7.392 (2342) | 11.284 |
| candidate / 1 | 2341 / 2400 | 234.068 | 57 / 2 | 74.249 | 0.602 (2341) | 7.423 (2341) | 11.585 |
| candidate / 2 | 2341 / 2400 | 234.072 | 57 / 2 | 74.768 | 0.604 (2341) | 7.355 (2341) | 11.075 |
| baseline / 2 | 2342 / 2400 | 234.168 | 56 / 2 | 69.548 | 0.623 (2342) | 7.402 (2342) | 11.407 |
| baseline / 3 | 2342 / 2400 | 234.164 | 56 / 2 | 69.632 | 0.625 (2342) | 7.373 (2342) | 11.090 |
| candidate / 3 | 2342 / 2400 | 234.171 | 56 / 2 | 69.508 | 0.481 (2342) | 7.211 (2342) | 10.631 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 2341 / 2400 | 233.935 | 57 / 2 | 72.599 | 0.639 (2341) | 7.669 (2341) | 14.762 |
| baseline / 1 | 2340 / 2400 | 233.837 | 58 / 2 | 266.234 | 0.608 (2340) | 7.598 (2340) | 14.108 |
| baseline / 2 | 2341 / 2400 | 233.936 | 57 / 2 | 72.811 | 0.601 (2341) | 7.571 (2341) | 14.206 |
| candidate / 2 | 2340 / 2400 | 233.826 | 58 / 2 | 266.504 | 0.633 (2340) | 7.636 (2340) | 14.374 |
| candidate / 3 | 2341 / 2400 | 233.941 | 57 / 2 | 74.977 | 0.620 (2341) | 7.618 (2341) | 14.330 |
| baseline / 3 | 2341 / 2400 | 233.941 | 57 / 2 | 72.439 | 0.628 (2341) | 7.607 (2341) | 14.275 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 860 / 2400 | 86.032 | 1471 / 69 | 272.602 | 1.364 (860) | 13.158 (860) | 56.130 |
| candidate / 1 | 868 / 2400 | 86.833 | 1465 / 67 | 273.535 | 1.325 (868) | 13.106 (868) | 56.421 |
| candidate / 2 | 889 / 2400 | 88.936 | 1441 / 70 | 273.649 | 1.313 (889) | 13.049 (889) | 56.031 |
| baseline / 2 | 883 / 2400 | 88.333 | 1448 / 69 | 272.700 | 1.340 (883) | 13.050 (883) | 56.174 |
| baseline / 3 | 906 / 2400 | 90.634 | 1421 / 73 | 272.358 | 1.238 (906) | 12.895 (906) | 55.725 |
| candidate / 3 | 916 / 2400 | 91.635 | 1418 / 66 | 272.814 | 1.202 (916) | 12.834 (916) | 55.767 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 485 / 2400 | 48.518 | 1841 / 74 | 272.717 | 1.883 (485) | 16.916 (485) | 54.828 |
| baseline / 1 | 489 / 2400 | 48.919 | 1836 / 75 | 271.836 | 1.778 (489) | 16.894 (489) | 54.729 |
| baseline / 2 | 483 / 2400 | 48.318 | 1841 / 76 | 271.622 | 1.921 (483) | 16.917 (483) | 54.689 |
| candidate / 2 | 486 / 2400 | 48.618 | 1839 / 75 | 268.884 | 1.959 (486) | 16.898 (486) | 54.798 |
| candidate / 3 | 485 / 2400 | 48.518 | 1845 / 70 | 273.916 | 1.878 (485) | 16.880 (485) | 54.698 |
| baseline / 3 | 482 / 2400 | 48.218 | 1847 / 71 | 272.154 | 1.945 (482) | 16.921 (482) | 54.853 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 2342 / 2400 | 234.222 | 57 / 1 | 71.168 | 0.717 (2342) | 6.372 (2342) | 8.259 |
| candidate / 1 | 2342 / 2400 | 234.220 | 56 / 2 | 69.696 | 0.693 (2342) | 6.324 (2342) | 8.119 |
| candidate / 2 | 2342 / 2400 | 234.219 | 56 / 2 | 70.116 | 0.678 (2342) | 6.302 (2342) | 8.043 |
| baseline / 2 | 2342 / 2400 | 234.221 | 57 / 1 | 71.093 | 0.661 (2342) | 6.283 (2342) | 8.042 |
| baseline / 3 | 2342 / 2400 | 234.219 | 56 / 2 | 69.959 | 0.680 (2342) | 6.317 (2342) | 8.161 |
| candidate / 3 | 2340 / 2400 | 234.024 | 59 / 1 | 266.698 | 0.666 (2339) | 6.280 (2340) | 8.019 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 2340 / 2400 | 233.868 | 58 / 2 | 266.328 | 0.623 (2340) | 7.797 (2340) | 19.892 |
| baseline / 1 | 2340 / 2400 | 233.881 | 59 / 1 | 265.921 | 0.646 (2340) | 7.739 (2340) | 19.029 |
| baseline / 2 | 2341 / 2400 | 233.974 | 57 / 2 | 73.962 | 0.566 (2341) | 7.715 (2341) | 18.992 |
| candidate / 2 | 2340 / 2400 | 233.879 | 58 / 2 | 266.700 | 0.590 (2340) | 7.694 (2340) | 18.958 |
| candidate / 3 | 2340 / 2400 | 233.893 | 58 / 2 | 268.591 | 0.626 (2340) | 7.747 (2340) | 19.278 |
| baseline / 3 | 2341 / 2400 | 233.965 | 58 / 1 | 75.873 | 0.552 (2341) | 7.671 (2341) | 18.159 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1171 / 2400 | 116.334 | 1185 / 44 | 274.826 | 1.035 (1171) | 10.767 (1171) | 48.985 |
| candidate / 1 | 1140 / 2400 | 114.043 | 1212 / 48 | 275.168 | 1.074 (1140) | 10.803 (1140) | 48.895 |
| candidate / 2 | 1136 / 2400 | 113.643 | 1216 / 48 | 275.029 | 1.088 (1136) | 10.851 (1136) | 49.104 |
| baseline / 2 | 1246 / 2400 | 123.857 | 1112 / 42 | 274.388 | 0.958 (1246) | 10.526 (1246) | 49.461 |
| baseline / 3 | 1123 / 2400 | 112.343 | 1233 / 44 | 274.635 | 1.068 (1123) | 10.874 (1123) | 48.482 |
| candidate / 3 | 1066 / 2400 | 106.639 | 1284 / 50 | 274.978 | 1.112 (1066) | 11.001 (1066) | 48.388 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 645 / 2400 | 64.524 | 1680 / 75 | 274.720 | 1.788 (645) | 14.512 (645) | 57.212 |
| baseline / 1 | 664 / 2400 | 66.425 | 1660 / 76 | 275.387 | 1.703 (664) | 14.397 (664) | 56.878 |
| baseline / 2 | 632 / 2400 | 63.223 | 1697 / 71 | 275.202 | 1.825 (632) | 14.594 (632) | 57.163 |
| candidate / 2 | 666 / 2400 | 66.625 | 1659 / 75 | 274.934 | 1.683 (666) | 14.351 (666) | 56.634 |
| candidate / 3 | 665 / 2400 | 66.525 | 1667 / 68 | 273.714 | 1.713 (665) | 14.370 (665) | 56.758 |
| baseline / 3 | 629 / 2400 | 62.924 | 1701 / 70 | 275.395 | 1.827 (629) | 14.630 (629) | 57.410 |

## ultrawide-3440x1440p240-hevc-sdr-50mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 55.488 Mbps. Encoder target: 50.000 Mbps; measured/target: 111.0%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 2400 / 2400 | 240.049 | 0 / 0 | 66.994 | 0.569 (2400) | 2.068 (2400) | 2.675 |
| candidate / 1 | 2400 / 2400 | 240.047 | 0 / 0 | 64.955 | 0.579 (2399) | 2.076 (2400) | 2.663 |
| candidate / 2 | 2400 / 2400 | 240.051 | 0 / 0 | 63.948 | 0.562 (2400) | 2.053 (2400) | 2.636 |
| baseline / 2 | 2400 / 2400 | 240.048 | 0 / 0 | 64.646 | 0.558 (2400) | 2.052 (2400) | 2.642 |
| baseline / 3 | 2400 / 2400 | 240.047 | 0 / 0 | 63.975 | 0.561 (2400) | 2.053 (2400) | 2.632 |
| candidate / 3 | 2400 / 2400 | 240.051 | 0 / 0 | 67.358 | 0.583 (2400) | 2.083 (2400) | 2.694 |

## ultrawide-3440x1440p240-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, SDR. Measured bitrate: 95.374 Mbps. Encoder target: 100.000 Mbps; measured/target: 95.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 2400 / 2400 | 240.052 | 0 / 0 | 64.399 | 0.562 (2400) | 2.193 (2400) | 3.043 |
| baseline / 1 | 2400 / 2400 | 240.049 | 0 / 0 | 65.563 | 0.574 (2400) | 2.211 (2400) | 3.072 |
| baseline / 2 | 2400 / 2400 | 240.051 | 0 / 0 | 65.226 | 0.591 (2400) | 2.235 (2400) | 3.088 |
| candidate / 2 | 2400 / 2400 | 240.042 | 0 / 0 | 64.878 | 0.583 (2399) | 2.222 (2400) | 3.079 |
| candidate / 3 | 2400 / 2400 | 240.044 | 0 / 0 | 64.797 | 0.570 (2400) | 2.205 (2400) | 3.058 |
| baseline / 3 | 2400 / 2400 | 240.052 | 0 / 0 | 67.994 | 0.573 (2400) | 2.207 (2400) | 3.090 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 2345 / 2400 | 234.534 | 54 / 1 | 64.079 | 0.640 (2345) | 2.687 (2345) | 3.729 |
| candidate / 1 | 2344 / 2400 | 234.434 | 55 / 1 | 66.108 | 0.589 (2344) | 2.602 (2344) | 3.639 |
| candidate / 2 | 2343 / 2400 | 234.335 | 55 / 2 | 66.981 | 0.672 (2343) | 2.725 (2343) | 3.779 |
| baseline / 2 | 2343 / 2400 | 234.337 | 55 / 2 | 68.741 | 0.662 (2343) | 2.698 (2343) | 3.668 |
| baseline / 3 | 2343 / 2400 | 234.346 | 56 / 1 | 69.961 | 0.508 (2343) | 2.485 (2343) | 3.470 |
| candidate / 3 | 2343 / 2400 | 234.339 | 56 / 1 | 69.994 | 0.594 (2343) | 2.600 (2343) | 3.571 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 2342 / 2400 | 234.221 | 57 / 1 | 72.751 | 0.583 (2342) | 3.023 (2342) | 4.275 |
| baseline / 1 | 2343 / 2400 | 234.325 | 55 / 2 | 66.988 | 0.618 (2343) | 3.072 (2343) | 4.360 |
| baseline / 2 | 2343 / 2400 | 234.317 | 55 / 2 | 67.399 | 0.577 (2343) | 3.010 (2343) | 4.298 |
| candidate / 2 | 2343 / 2400 | 234.322 | 55 / 2 | 67.116 | 0.618 (2343) | 3.077 (2343) | 4.359 |
| candidate / 3 | 2342 / 2400 | 234.221 | 56 / 2 | 70.067 | 0.586 (2342) | 3.014 (2342) | 4.267 |
| baseline / 3 | 2343 / 2400 | 234.325 | 55 / 2 | 66.944 | 0.647 (2343) | 3.122 (2343) | 4.394 |

## ultrawide-3440x1440p240-hevc-hdr10-50mbps

Status: BASELINE_FAILURE

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 50.947 Mbps. Encoder target: 50.000 Mbps; measured/target: 101.9%.

baseline failed; latency is descriptive and cannot establish a clean regression result

- timed / baseline / 1: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=58; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=1; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 2341 / 2400 | 234.141 | 58 / 1 | 75.299 | 0.618 (2341) | 2.117 (2341) | 2.390 |
| candidate / 1 | 2400 / 2400 | 240.042 | 0 / 0 | 64.123 | 0.613 (2400) | 2.124 (2400) | 2.652 |
| candidate / 2 | 2400 / 2400 | 240.046 | 0 / 0 | 60.138 | 0.619 (2400) | 2.135 (2400) | 2.630 |
| baseline / 2 | 2400 / 2400 | 240.048 | 0 / 0 | 64.705 | 0.604 (2400) | 2.107 (2400) | 2.650 |
| baseline / 3 | 2400 / 2400 | 240.047 | 0 / 0 | 64.312 | 0.617 (2400) | 2.129 (2400) | 2.660 |
| candidate / 3 | 2400 / 2400 | 240.045 | 0 / 0 | 62.986 | 0.643 (2399) | 2.163 (2400) | 2.680 |

## ultrawide-3440x1440p240-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 92.181 Mbps. Encoder target: 100.000 Mbps; measured/target: 92.2%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 2400 / 2400 | 240.057 | 0 / 0 | 69.596 | 0.615 (2400) | 2.246 (2400) | 3.028 |
| baseline / 1 | 2400 / 2400 | 240.048 | 0 / 0 | 72.772 | 0.634 (2400) | 2.288 (2400) | 3.102 |
| baseline / 2 | 2400 / 2400 | 240.047 | 0 / 0 | 66.625 | 0.618 (2400) | 2.244 (2400) | 2.988 |
| candidate / 2 | 2400 / 2400 | 240.047 | 0 / 0 | 72.847 | 0.595 (2400) | 2.231 (2400) | 3.050 |
| candidate / 3 | 2400 / 2400 | 240.050 | 0 / 0 | 67.794 | 0.635 (2400) | 2.280 (2400) | 3.028 |
| baseline / 3 | 2400 / 2400 | 240.061 | 0 / 0 | 64.730 | 0.685 (2400) | 2.353 (2400) | 3.067 |

## ultrawide-3440x1440p240-hevc-hdr10-250mbps

Status: REGRESSION

Full-frame software reference: hevc; 1,783,296,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3440×1440 at 240 fps; HEVC, HDR10. Measured bitrate: 213.563 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.4%.

- timed / candidate / 3: native FAIL: accounting/hardware gate failed; process FINISHED, exit 1; not every offered frame produced an output; scheduler_drops=54; failed_or_cancelled_or_dropped=1; expected_display_mismatches=1; resets=2; CSV contains a non-output terminal completion; delivered frame rate below configured ratio

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 2400 / 2400 | 240.033 | 0 / 0 | 66.820 | 0.650 (2400) | 2.729 (2400) | 3.893 |
| candidate / 1 | 2400 / 2400 | 240.033 | 0 / 0 | 65.996 | 0.698 (2400) | 2.792 (2400) | 3.935 |
| candidate / 2 | 2400 / 2400 | 240.036 | 0 / 0 | 65.360 | 0.620 (2400) | 2.683 (2400) | 3.817 |
| baseline / 2 | 2400 / 2400 | 240.031 | 0 / 0 | 66.886 | 0.688 (2400) | 2.789 (2400) | 3.942 |
| baseline / 3 | 2400 / 2400 | 240.035 | 0 / 0 | 66.064 | 0.650 (2400) | 2.727 (2400) | 3.869 |
| candidate / 3 | 2345 / 2400 | 234.529 | 54 / 1 | 67.538 | 0.724 (2345) | 2.844 (2345) | 3.668 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 2343 / 2400 | 234.320 | 55 / 2 | 67.560 | 0.649 (2343) | 3.134 (2343) | 4.313 |
| baseline / 1 | 2343 / 2400 | 234.320 | 56 / 1 | 69.059 | 0.678 (2343) | 3.178 (2343) | 4.342 |
| baseline / 2 | 2342 / 2400 | 234.221 | 56 / 2 | 71.826 | 0.656 (2342) | 3.160 (2342) | 4.306 |
| candidate / 2 | 2342 / 2400 | 234.219 | 56 / 2 | 71.840 | 0.667 (2342) | 3.138 (2342) | 4.257 |
| candidate / 3 | 2340 / 2400 | 234.021 | 58 / 2 | 262.653 | 0.613 (2339) | 3.061 (2340) | 4.269 |
| baseline / 3 | 2341 / 2400 | 234.117 | 57 / 2 | 74.738 | 0.728 (2341) | 3.228 (2341) | 4.541 |

## 4k-3840x2160p60-av1-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, SDR. Measured bitrate: 131.636 Mbps. Encoder target: 50.000 Mbps; measured/target: 263.3%.

measured payload bitrate 131.636 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.075 | 0 / 0 | 103.637 | 1.009 (600) | 9.748 (600) | 11.232 |
| candidate / 1 | 600 / 600 | 60.076 | 0 / 0 | 95.299 | 0.909 (600) | 9.629 (600) | 10.916 |
| candidate / 2 | 600 / 600 | 60.077 | 0 / 0 | 95.878 | 0.922 (600) | 9.657 (600) | 10.949 |
| baseline / 2 | 600 / 600 | 60.075 | 0 / 0 | 91.880 | 0.874 (600) | 9.584 (600) | 10.810 |
| baseline / 3 | 600 / 600 | 60.074 | 0 / 0 | 100.552 | 1.036 (600) | 9.827 (600) | 11.243 |
| candidate / 3 | 600 / 600 | 60.078 | 0 / 0 | 94.566 | 0.890 (600) | 9.609 (600) | 10.868 |

## 4k-3840x2160p60-av1-sdr-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, SDR. Measured bitrate: 167.610 Mbps. Encoder target: 100.000 Mbps; measured/target: 167.6%.

measured payload bitrate 167.610 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.080 | 0 / 0 | 107.584 | 0.911 (600) | 11.967 (600) | 14.263 |
| baseline / 1 | 600 / 600 | 60.082 | 0 / 0 | 107.770 | 0.928 (600) | 12.031 (600) | 14.338 |
| baseline / 2 | 600 / 600 | 60.083 | 0 / 0 | 101.752 | 0.993 (600) | 12.082 (600) | 14.233 |
| candidate / 2 | 600 / 600 | 60.082 | 0 / 0 | 104.441 | 1.031 (600) | 12.186 (600) | 14.461 |
| candidate / 3 | 600 / 600 | 60.081 | 0 / 0 | 103.251 | 0.930 (600) | 12.023 (600) | 14.200 |
| baseline / 3 | 600 / 600 | 60.078 | 0 / 0 | 107.140 | 0.915 (600) | 11.996 (600) | 14.291 |

## 4k-3840x2160p60-av1-sdr-250mbps

Status: PASS

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, SDR. Measured bitrate: 276.966 Mbps. Encoder target: 250.000 Mbps; measured/target: 110.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 59.999 | 0 / 0 | 126.040 | 0.862 (600) | 23.199 (600) | 36.720 |
| candidate / 1 | 600 / 600 | 59.999 | 0 / 0 | 130.508 | 0.951 (600) | 23.252 (600) | 37.299 |
| candidate / 2 | 600 / 600 | 59.998 | 0 / 0 | 124.628 | 0.943 (600) | 23.214 (600) | 36.599 |
| baseline / 2 | 600 / 600 | 59.998 | 0 / 0 | 133.427 | 1.207 (600) | 23.630 (600) | 38.336 |
| baseline / 3 | 600 / 600 | 59.999 | 0 / 0 | 130.500 | 1.007 (600) | 23.346 (600) | 37.577 |
| candidate / 3 | 600 / 600 | 59.998 | 0 / 0 | 124.897 | 0.979 (600) | 23.280 (600) | 36.843 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 391 / 600 | 39.165 | 201 / 8 | 141.650 | 1.490 (391) | 39.319 (391) | 212.465 |
| baseline / 1 | 395 / 600 | 39.565 | 200 / 5 | 139.175 | 1.473 (395) | 39.336 (395) | 212.388 |
| baseline / 2 | 395 / 600 | 39.566 | 197 / 8 | 137.205 | 1.464 (395) | 39.331 (395) | 212.436 |
| candidate / 2 | 394 / 600 | 39.465 | 199 / 7 | 137.147 | 1.454 (394) | 39.347 (394) | 212.398 |
| candidate / 3 | 395 / 600 | 39.564 | 196 / 9 | 136.898 | 1.446 (395) | 39.326 (395) | 211.148 |
| baseline / 3 | 391 / 600 | 39.164 | 199 / 10 | 137.893 | 1.380 (391) | 39.357 (391) | 211.963 |

## 4k-3840x2160p60-av1-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, HDR10. Measured bitrate: 122.846 Mbps. Encoder target: 50.000 Mbps; measured/target: 245.7%.

measured payload bitrate 122.846 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.080 | 0 / 0 | 102.708 | 0.968 (600) | 9.482 (600) | 10.873 |
| candidate / 1 | 600 / 600 | 60.078 | 0 / 0 | 98.163 | 0.912 (600) | 9.407 (600) | 10.748 |
| candidate / 2 | 600 / 600 | 60.079 | 0 / 0 | 92.762 | 0.971 (600) | 9.507 (600) | 10.695 |
| baseline / 2 | 600 / 600 | 60.078 | 0 / 0 | 92.053 | 0.936 (600) | 9.433 (600) | 10.617 |
| baseline / 3 | 600 / 600 | 60.081 | 0 / 0 | 91.893 | 0.986 (600) | 9.506 (600) | 10.678 |
| candidate / 3 | 600 / 600 | 60.079 | 0 / 0 | 93.194 | 0.952 (600) | 9.467 (600) | 10.658 |

## 4k-3840x2160p60-av1-hdr10-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, HDR10. Measured bitrate: 133.382 Mbps. Encoder target: 100.000 Mbps; measured/target: 133.4%.

measured payload bitrate 133.382 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.076 | 0 / 0 | 103.283 | 0.782 (600) | 10.034 (600) | 11.954 |
| baseline / 1 | 600 / 600 | 60.076 | 0 / 0 | 107.967 | 0.964 (600) | 10.287 (600) | 12.342 |
| baseline / 2 | 600 / 600 | 60.077 | 0 / 0 | 108.924 | 0.978 (600) | 10.308 (600) | 12.369 |
| candidate / 2 | 600 / 600 | 60.077 | 0 / 0 | 103.015 | 0.900 (600) | 10.188 (600) | 12.120 |
| candidate / 3 | 600 / 600 | 60.076 | 0 / 0 | 107.809 | 1.034 (600) | 10.409 (600) | 12.472 |
| baseline / 3 | 600 / 600 | 60.078 | 0 / 0 | 106.773 | 0.964 (600) | 10.284 (600) | 12.275 |

## 4k-3840x2160p60-av1-hdr10-250mbps

Status: PASS

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; AV1, HDR10. Measured bitrate: 274.818 Mbps. Encoder target: 250.000 Mbps; measured/target: 109.9%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.000 | 0 / 0 | 125.234 | 1.039 (600) | 21.810 (600) | 32.996 |
| candidate / 1 | 600 / 600 | 60.000 | 0 / 0 | 130.598 | 1.038 (600) | 21.871 (600) | 33.743 |
| candidate / 2 | 600 / 600 | 60.001 | 0 / 0 | 125.794 | 1.045 (600) | 21.839 (600) | 33.092 |
| baseline / 2 | 600 / 600 | 59.998 | 0 / 0 | 131.624 | 1.054 (600) | 21.873 (600) | 33.715 |
| baseline / 3 | 600 / 600 | 59.999 | 0 / 0 | 125.782 | 1.077 (600) | 21.838 (600) | 33.001 |
| candidate / 3 | 600 / 600 | 60.000 | 0 / 0 | 126.979 | 1.015 (600) | 21.755 (600) | 33.018 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 443 / 600 | 44.372 | 151 / 6 | 137.644 | 1.546 (443) | 38.655 (443) | 211.394 |
| baseline / 1 | 439 / 600 | 43.973 | 152 / 9 | 141.966 | 1.559 (439) | 38.669 (439) | 211.625 |
| baseline / 2 | 442 / 600 | 44.273 | 151 / 7 | 139.639 | 1.539 (442) | 38.653 (442) | 211.524 |
| candidate / 2 | 440 / 600 | 44.072 | 153 / 7 | 138.021 | 1.586 (440) | 38.669 (440) | 211.850 |
| candidate / 3 | 437 / 600 | 43.771 | 155 / 8 | 145.808 | 1.625 (437) | 38.668 (437) | 212.156 |
| baseline / 3 | 442 / 600 | 44.272 | 151 / 7 | 138.689 | 1.530 (442) | 38.664 (442) | 211.475 |

## 4k-3840x2160p60-hevc-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 60.820 Mbps. Encoder target: 50.000 Mbps; measured/target: 121.6%.

measured payload bitrate 60.820 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.081 | 0 / 0 | 77.010 | 0.775 (599) | 3.468 (600) | 4.177 |
| candidate / 1 | 600 / 600 | 60.082 | 0 / 0 | 76.581 | 0.761 (600) | 3.422 (600) | 4.141 |
| candidate / 2 | 600 / 600 | 60.083 | 0 / 0 | 76.276 | 0.769 (600) | 3.439 (600) | 4.136 |
| baseline / 2 | 600 / 600 | 60.084 | 0 / 0 | 78.369 | 0.936 (600) | 3.665 (600) | 4.398 |
| baseline / 3 | 600 / 600 | 60.082 | 0 / 0 | 74.189 | 0.777 (600) | 3.449 (600) | 4.129 |
| candidate / 3 | 600 / 600 | 60.082 | 0 / 0 | 79.911 | 0.758 (600) | 3.421 (600) | 4.189 |

## 4k-3840x2160p60-hevc-sdr-100mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 92.471 Mbps. Encoder target: 100.000 Mbps; measured/target: 92.5%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.082 | 0 / 0 | 78.172 | 0.643 (600) | 3.509 (600) | 4.275 |
| baseline / 1 | 600 / 600 | 60.080 | 0 / 0 | 79.040 | 0.769 (600) | 3.688 (600) | 4.469 |
| baseline / 2 | 600 / 600 | 60.081 | 0 / 0 | 79.304 | 0.780 (600) | 3.715 (600) | 4.487 |
| candidate / 2 | 600 / 600 | 60.079 | 0 / 0 | 79.882 | 0.840 (600) | 3.793 (600) | 4.560 |
| candidate / 3 | 600 / 600 | 60.081 | 0 / 0 | 83.243 | 0.784 (600) | 3.724 (600) | 4.548 |
| baseline / 3 | 600 / 600 | 60.085 | 0 / 0 | 78.302 | 0.670 (600) | 3.548 (600) | 4.309 |

## 4k-3840x2160p60-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 214.384 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.066 | 0 / 0 | 85.996 | 0.928 (600) | 5.553 (600) | 6.545 |
| candidate / 1 | 600 / 600 | 60.068 | 0 / 0 | 84.417 | 0.865 (600) | 5.477 (600) | 6.431 |
| candidate / 2 | 600 / 600 | 60.067 | 0 / 0 | 88.779 | 0.936 (600) | 5.561 (600) | 6.603 |
| baseline / 2 | 600 / 600 | 60.068 | 0 / 0 | 82.612 | 0.986 (599) | 5.638 (600) | 6.566 |
| baseline / 3 | 600 / 600 | 60.068 | 0 / 0 | 88.848 | 1.010 (600) | 5.669 (600) | 6.707 |
| candidate / 3 | 600 / 600 | 60.068 | 0 / 0 | 89.671 | 0.907 (600) | 5.523 (600) | 6.579 |

## 4k-3840x2160p60-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, SDR. Measured bitrate: 296.923 Mbps. Encoder target: 350.000 Mbps; measured/target: 84.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.056 | 0 / 0 | 84.918 | 0.967 (600) | 6.728 (600) | 7.808 |
| baseline / 1 | 600 / 600 | 60.055 | 0 / 0 | 85.129 | 0.958 (600) | 6.719 (600) | 7.801 |
| baseline / 2 | 600 / 600 | 60.057 | 0 / 0 | 84.697 | 1.203 (600) | 7.077 (600) | 8.175 |
| candidate / 2 | 600 / 600 | 60.057 | 0 / 0 | 90.677 | 1.101 (600) | 6.919 (600) | 8.087 |
| candidate / 3 | 600 / 600 | 60.056 | 0 / 0 | 84.978 | 0.979 (600) | 6.745 (600) | 7.816 |
| baseline / 3 | 600 / 600 | 60.056 | 0 / 0 | 84.509 | 0.981 (600) | 6.748 (600) | 7.796 |

## 4k-3840x2160p60-hevc-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 83.905 Mbps. Encoder target: 50.000 Mbps; measured/target: 167.8%.

measured payload bitrate 83.905 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.087 | 0 / 0 | 85.377 | 0.825 (600) | 3.959 (600) | 4.844 |
| candidate / 1 | 600 / 600 | 60.083 | 0 / 0 | 84.925 | 0.790 (600) | 3.909 (600) | 4.786 |
| candidate / 2 | 600 / 600 | 60.081 | 0 / 0 | 85.588 | 0.848 (600) | 3.984 (600) | 4.855 |
| baseline / 2 | 600 / 600 | 60.082 | 0 / 0 | 87.265 | 0.849 (600) | 3.992 (600) | 4.905 |
| baseline / 3 | 600 / 600 | 60.082 | 0 / 0 | 89.407 | 0.797 (600) | 3.913 (600) | 4.855 |
| candidate / 3 | 600 / 600 | 60.082 | 0 / 0 | 85.525 | 0.792 (600) | 3.914 (600) | 4.810 |

## 4k-3840x2160p60-hevc-hdr10-100mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 91.768 Mbps. Encoder target: 100.000 Mbps; measured/target: 91.8%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.081 | 0 / 0 | 79.490 | 0.837 (600) | 3.789 (600) | 4.548 |
| baseline / 1 | 600 / 600 | 60.082 | 0 / 0 | 79.722 | 0.787 (600) | 3.716 (600) | 4.487 |
| baseline / 2 | 600 / 600 | 60.082 | 0 / 0 | 79.160 | 0.830 (600) | 3.778 (600) | 4.548 |
| candidate / 2 | 600 / 600 | 60.081 | 0 / 0 | 80.085 | 0.918 (600) | 3.897 (600) | 4.658 |
| candidate / 3 | 600 / 600 | 60.081 | 0 / 0 | 82.757 | 0.879 (600) | 3.845 (600) | 4.665 |
| baseline / 3 | 600 / 600 | 60.082 | 0 / 0 | 80.148 | 0.860 (599) | 3.828 (600) | 4.632 |

## 4k-3840x2160p60-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 214.240 Mbps. Encoder target: 250.000 Mbps; measured/target: 85.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 600 / 600 | 60.067 | 0 / 0 | 84.105 | 0.984 (600) | 5.644 (600) | 6.586 |
| candidate / 1 | 600 / 600 | 60.068 | 0 / 0 | 85.426 | 0.975 (600) | 5.647 (600) | 6.614 |
| candidate / 2 | 600 / 600 | 60.062 | 0 / 0 | 85.956 | 1.003 (600) | 5.673 (600) | 6.645 |
| baseline / 2 | 600 / 600 | 60.066 | 0 / 0 | 91.115 | 1.021 (600) | 5.709 (600) | 6.759 |
| baseline / 3 | 600 / 600 | 60.068 | 0 / 0 | 85.640 | 0.981 (600) | 5.648 (600) | 6.600 |
| candidate / 3 | 600 / 600 | 60.065 | 0 / 0 | 86.883 | 0.975 (600) | 5.640 (600) | 6.614 |

## 4k-3840x2160p60-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 60 fps; HEVC, HDR10. Measured bitrate: 296.411 Mbps. Encoder target: 350.000 Mbps; measured/target: 84.7%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 600 / 600 | 60.050 | 0 / 0 | 84.485 | 1.015 (600) | 6.841 (600) | 7.856 |
| baseline / 1 | 600 / 600 | 60.055 | 0 / 0 | 91.227 | 1.049 (600) | 6.876 (600) | 8.005 |
| baseline / 2 | 600 / 600 | 60.049 | 0 / 0 | 87.242 | 0.918 (600) | 6.708 (600) | 7.759 |
| candidate / 2 | 600 / 600 | 60.047 | 0 / 0 | 101.015 | 1.237 (600) | 7.172 (600) | 8.555 |
| candidate / 3 | 600 / 600 | 60.051 | 0 / 0 | 89.919 | 1.094 (600) | 6.955 (600) | 8.063 |
| baseline / 3 | 600 / 600 | 60.049 | 0 / 0 | 85.501 | 1.000 (600) | 6.815 (600) | 7.833 |

## 4k-3840x2160p120-av1-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, SDR. Measured bitrate: 218.276 Mbps. Encoder target: 50.000 Mbps; measured/target: 436.6%.

measured payload bitrate 218.276 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 119.967 | 0 / 0 | 85.169 | 0.744 (1200) | 11.742 (1200) | 16.257 |
| candidate / 1 | 1200 / 1200 | 119.972 | 0 / 0 | 85.543 | 0.778 (1200) | 11.770 (1200) | 16.321 |
| candidate / 2 | 1200 / 1200 | 119.966 | 0 / 0 | 86.532 | 0.782 (1200) | 11.783 (1200) | 16.394 |
| baseline / 2 | 1200 / 1200 | 119.965 | 0 / 0 | 85.546 | 0.751 (1200) | 11.741 (1200) | 16.169 |
| baseline / 3 | 1200 / 1200 | 119.967 | 0 / 0 | 85.225 | 0.740 (1200) | 11.739 (1200) | 16.238 |
| candidate / 3 | 1200 / 1200 | 119.967 | 0 / 0 | 85.905 | 0.748 (1200) | 11.750 (1200) | 16.281 |

## 4k-3840x2160p120-av1-sdr-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, SDR. Measured bitrate: 263.272 Mbps. Encoder target: 100.000 Mbps; measured/target: 263.3%.

measured payload bitrate 263.272 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.031 | 0 / 0 | 91.827 | 0.739 (1200) | 13.344 (1200) | 24.045 |
| baseline / 1 | 1200 / 1200 | 120.025 | 0 / 0 | 90.700 | 0.756 (1200) | 13.363 (1200) | 24.029 |
| baseline / 2 | 1200 / 1200 | 120.030 | 0 / 0 | 91.466 | 0.802 (1200) | 13.399 (1200) | 24.206 |
| candidate / 2 | 1200 / 1200 | 120.026 | 0 / 0 | 93.998 | 0.740 (1200) | 13.369 (1200) | 24.258 |
| candidate / 3 | 1200 / 1200 | 120.026 | 0 / 0 | 92.234 | 0.749 (1200) | 13.358 (1200) | 24.121 |
| baseline / 3 | 1200 / 1200 | 120.032 | 0 / 0 | 90.689 | 0.762 (1200) | 13.365 (1200) | 24.025 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 635 / 1200 | 63.057 | 545 / 20 | 104.492 | 1.127 (635) | 19.877 (635) | 79.210 |
| candidate / 1 | 636 / 1200 | 63.160 | 545 / 19 | 105.316 | 1.107 (636) | 19.888 (636) | 78.553 |
| candidate / 2 | 637 / 1200 | 63.265 | 544 / 19 | 106.129 | 1.079 (637) | 19.914 (637) | 77.624 |
| baseline / 2 | 638 / 1200 | 63.357 | 544 / 18 | 106.542 | 1.048 (638) | 19.938 (638) | 77.108 |
| baseline / 3 | 634 / 1200 | 62.963 | 546 / 20 | 106.319 | 1.098 (634) | 19.836 (634) | 78.125 |
| candidate / 3 | 633 / 1200 | 62.893 | 547 / 20 | 108.258 | 1.102 (633) | 19.821 (633) | 78.270 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 343 / 1200 | 34.328 | 817 / 40 | 118.287 | 1.844 (343) | 29.065 (343) | 100.140 |
| baseline / 1 | 346 / 1200 | 34.628 | 814 / 40 | 114.638 | 2.000 (346) | 29.110 (346) | 101.280 |
| baseline / 2 | 345 / 1200 | 34.528 | 815 / 40 | 113.212 | 1.975 (345) | 29.099 (345) | 101.217 |
| candidate / 2 | 344 / 1200 | 34.428 | 818 / 38 | 120.088 | 1.970 (344) | 29.079 (344) | 100.984 |
| candidate / 3 | 343 / 1200 | 34.328 | 817 / 40 | 114.189 | 1.921 (343) | 29.145 (343) | 100.989 |
| baseline / 3 | 347 / 1200 | 34.728 | 814 / 39 | 114.611 | 1.883 (347) | 29.100 (347) | 100.808 |

## 4k-3840x2160p120-av1-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, HDR10. Measured bitrate: 177.539 Mbps. Encoder target: 50.000 Mbps; measured/target: 355.1%.

measured payload bitrate 177.539 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.002 | 0 / 0 | 85.878 | 0.822 (1200) | 9.605 (1200) | 12.857 |
| candidate / 1 | 1200 / 1200 | 120.008 | 0 / 0 | 89.585 | 0.810 (1200) | 9.571 (1200) | 12.908 |
| candidate / 2 | 1200 / 1200 | 120.002 | 0 / 0 | 87.778 | 0.861 (1200) | 9.670 (1200) | 12.972 |
| baseline / 2 | 1200 / 1200 | 120.002 | 0 / 0 | 90.455 | 0.797 (1200) | 9.565 (1200) | 12.917 |
| baseline / 3 | 1200 / 1200 | 120.012 | 0 / 0 | 86.538 | 0.664 (1200) | 9.429 (1200) | 12.598 |
| candidate / 3 | 1200 / 1200 | 120.005 | 0 / 0 | 90.197 | 0.794 (1200) | 9.550 (1200) | 12.884 |

## 4k-3840x2160p120-av1-hdr10-100mbps

Status: INCONCLUSIVE

Full-frame software reference: libdav1d; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; AV1, HDR10. Measured bitrate: 245.692 Mbps. Encoder target: 100.000 Mbps; measured/target: 245.7%.

measured payload bitrate 245.692 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 119.956 | 0 / 0 | 91.014 | 0.838 (1200) | 12.590 (1200) | 20.761 |
| baseline / 1 | 1200 / 1200 | 119.957 | 0 / 0 | 93.637 | 0.779 (1200) | 12.564 (1200) | 20.773 |
| baseline / 2 | 1200 / 1200 | 119.959 | 0 / 0 | 98.439 | 0.900 (1200) | 12.697 (1200) | 21.475 |
| candidate / 2 | 1200 / 1200 | 119.959 | 0 / 0 | 92.787 | 0.864 (1200) | 12.636 (1200) | 20.925 |
| candidate / 3 | 1200 / 1200 | 119.958 | 0 / 0 | 91.665 | 0.849 (1200) | 12.633 (1200) | 20.867 |
| baseline / 3 | 1200 / 1200 | 119.957 | 0 / 0 | 93.389 | 0.830 (1200) | 12.589 (1200) | 20.803 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 775 / 1200 | 77.562 | 403 / 22 | 106.816 | 1.152 (775) | 19.145 (775) | 99.606 |
| candidate / 1 | 805 / 1200 | 80.270 | 372 / 23 | 110.310 | 1.218 (805) | 19.201 (805) | 99.106 |
| candidate / 2 | 853 / 1200 | 84.589 | 326 / 21 | 106.769 | 1.208 (853) | 19.077 (853) | 98.856 |
| baseline / 2 | 889 / 1200 | 88.441 | 296 / 15 | 113.912 | 1.173 (889) | 18.570 (889) | 96.855 |
| baseline / 3 | 850 / 1200 | 84.391 | 332 / 18 | 106.617 | 1.136 (850) | 18.730 (850) | 100.302 |
| candidate / 3 | 767 / 1200 | 76.532 | 412 / 21 | 106.114 | 1.189 (767) | 19.415 (767) | 98.489 |

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

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 599 / 1200 | 59.056 | 584 / 17 | 115.368 | 1.265 (599) | 20.483 (599) | 109.054 |
| baseline / 1 | 598 / 1200 | 59.231 | 583 / 19 | 115.496 | 1.201 (598) | 20.485 (598) | 108.223 |
| baseline / 2 | 589 / 1200 | 58.089 | 590 / 21 | 120.693 | 1.305 (589) | 20.493 (589) | 108.914 |
| candidate / 2 | 592 / 1200 | 58.439 | 587 / 21 | 114.833 | 1.244 (592) | 20.540 (592) | 106.973 |
| candidate / 3 | 585 / 1200 | 57.677 | 594 / 21 | 120.844 | 1.284 (585) | 20.520 (585) | 108.456 |
| baseline / 3 | 598 / 1200 | 58.963 | 583 / 19 | 114.394 | 1.203 (598) | 20.483 (598) | 108.347 |

## 4k-3840x2160p120-hevc-sdr-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, SDR. Measured bitrate: 82.298 Mbps. Encoder target: 50.000 Mbps; measured/target: 164.6%.

measured payload bitrate 82.298 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.068 | 0 / 0 | 74.512 | 0.679 (1200) | 3.058 (1200) | 3.691 |
| candidate / 1 | 1200 / 1200 | 120.067 | 0 / 0 | 76.021 | 0.689 (1200) | 3.080 (1200) | 3.771 |
| candidate / 2 | 1200 / 1200 | 120.068 | 0 / 0 | 75.833 | 0.649 (1200) | 3.015 (1200) | 3.660 |
| baseline / 2 | 1200 / 1200 | 120.070 | 0 / 0 | 73.033 | 0.685 (1200) | 3.064 (1200) | 3.713 |
| baseline / 3 | 1200 / 1200 | 120.063 | 0 / 0 | 74.846 | 0.648 (1200) | 3.007 (1200) | 3.654 |
| candidate / 3 | 1200 / 1200 | 120.067 | 0 / 0 | 74.276 | 0.645 (1200) | 3.009 (1200) | 3.628 |

## 4k-3840x2160p120-hevc-sdr-100mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, SDR. Measured bitrate: 122.563 Mbps. Encoder target: 100.000 Mbps; measured/target: 122.6%.

measured payload bitrate 122.563 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.064 | 0 / 0 | 91.194 | 0.675 (1200) | 3.297 (1200) | 4.300 |
| baseline / 1 | 1200 / 1200 | 120.062 | 0 / 0 | 74.638 | 0.713 (1200) | 3.356 (1200) | 4.188 |
| baseline / 2 | 1200 / 1200 | 120.064 | 0 / 0 | 76.510 | 0.678 (1200) | 3.294 (1200) | 4.110 |
| candidate / 2 | 1200 / 1200 | 120.061 | 0 / 0 | 74.825 | 0.684 (1200) | 3.303 (1200) | 4.095 |
| candidate / 3 | 1200 / 1200 | 120.066 | 0 / 0 | 78.867 | 0.679 (1199) | 3.304 (1200) | 4.145 |
| baseline / 3 | 1200 / 1200 | 120.065 | 0 / 0 | 74.711 | 0.658 (1200) | 3.265 (1200) | 4.047 |

## 4k-3840x2160p120-hevc-sdr-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, SDR. Measured bitrate: 238.909 Mbps. Encoder target: 250.000 Mbps; measured/target: 95.6%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.052 | 0 / 0 | 79.583 | 0.600 (1200) | 3.748 (1200) | 5.305 |
| candidate / 1 | 1200 / 1200 | 120.051 | 0 / 0 | 82.353 | 0.808 (1200) | 4.062 (1200) | 5.817 |
| candidate / 2 | 1200 / 1200 | 120.056 | 0 / 0 | 80.071 | 0.744 (1200) | 3.957 (1200) | 5.648 |
| baseline / 2 | 1200 / 1200 | 120.056 | 0 / 0 | 79.793 | 0.722 (1200) | 3.934 (1200) | 5.613 |
| baseline / 3 | 1200 / 1200 | 120.055 | 0 / 0 | 81.785 | 0.744 (1200) | 3.969 (1200) | 5.730 |
| candidate / 3 | 1200 / 1200 | 120.048 | 0 / 0 | 79.526 | 0.711 (1200) | 3.920 (1200) | 5.586 |

## 4k-3840x2160p120-hevc-sdr-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, SDR. Measured bitrate: 323.482 Mbps. Encoder target: 350.000 Mbps; measured/target: 92.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.040 | 0 / 0 | 80.995 | 0.752 (1200) | 4.625 (1200) | 7.053 |
| baseline / 1 | 1200 / 1200 | 120.039 | 0 / 0 | 81.440 | 0.820 (1200) | 4.713 (1200) | 7.190 |
| baseline / 2 | 1200 / 1200 | 120.041 | 0 / 0 | 81.640 | 0.758 (1200) | 4.630 (1200) | 7.086 |
| candidate / 2 | 1200 / 1200 | 120.040 | 0 / 0 | 82.510 | 0.749 (1200) | 4.614 (1200) | 7.019 |
| candidate / 3 | 1200 / 1200 | 120.040 | 0 / 0 | 80.631 | 0.752 (1200) | 4.618 (1200) | 7.041 |
| baseline / 3 | 1200 / 1200 | 120.039 | 0 / 0 | 81.384 | 0.739 (1200) | 4.593 (1200) | 6.996 |

## 4k-3840x2160p120-hevc-hdr10-50mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, HDR10. Measured bitrate: 82.866 Mbps. Encoder target: 50.000 Mbps; measured/target: 165.7%.

measured payload bitrate 82.866 Mbps is outside the 50 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.055 | 0 / 0 | 75.228 | 0.717 (1200) | 3.124 (1200) | 3.843 |
| candidate / 1 | 1200 / 1200 | 120.050 | 0 / 0 | 74.508 | 0.786 (1200) | 3.233 (1200) | 3.970 |
| candidate / 2 | 1200 / 1200 | 120.054 | 0 / 0 | 74.361 | 0.713 (1200) | 3.128 (1200) | 3.830 |
| baseline / 2 | 1200 / 1200 | 120.052 | 0 / 0 | 74.209 | 0.747 (1200) | 3.171 (1200) | 3.911 |
| baseline / 3 | 1200 / 1200 | 120.057 | 0 / 0 | 73.806 | 0.738 (1200) | 3.161 (1200) | 3.862 |
| candidate / 3 | 1200 / 1200 | 120.050 | 0 / 0 | 76.815 | 0.737 (1200) | 3.162 (1200) | 3.909 |

## 4k-3840x2160p120-hevc-hdr10-100mbps

Status: INCONCLUSIVE

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, HDR10. Measured bitrate: 122.444 Mbps. Encoder target: 100.000 Mbps; measured/target: 122.4%.

measured payload bitrate 122.444 Mbps is outside the 100 Mbps target ±20%; decode checks passed, but requested bitrate coverage was not established

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.066 | 0 / 0 | 80.638 | 0.736 (1200) | 3.402 (1200) | 4.297 |
| baseline / 1 | 1200 / 1200 | 120.061 | 0 / 0 | 76.045 | 0.793 (1200) | 3.488 (1200) | 4.365 |
| baseline / 2 | 1200 / 1200 | 120.067 | 0 / 0 | 78.361 | 0.729 (1200) | 3.389 (1200) | 4.259 |
| candidate / 2 | 1200 / 1200 | 120.066 | 0 / 0 | 76.584 | 0.719 (1200) | 3.376 (1200) | 4.235 |
| candidate / 3 | 1200 / 1200 | 120.064 | 0 / 0 | 76.592 | 0.756 (1200) | 3.439 (1200) | 4.303 |
| baseline / 3 | 1200 / 1200 | 120.070 | 0 / 0 | 76.428 | 0.727 (1200) | 3.392 (1200) | 4.228 |

## 4k-3840x2160p120-hevc-hdr10-250mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, HDR10. Measured bitrate: 237.735 Mbps. Encoder target: 250.000 Mbps; measured/target: 95.1%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline / 1 | 1200 / 1200 | 120.047 | 0 / 0 | 81.051 | 0.822 (1200) | 4.109 (1200) | 5.765 |
| candidate / 1 | 1200 / 1200 | 120.053 | 0 / 0 | 81.230 | 0.849 (1200) | 4.134 (1200) | 5.785 |
| candidate / 2 | 1200 / 1200 | 120.047 | 0 / 0 | 80.991 | 0.814 (1200) | 4.083 (1200) | 5.767 |
| baseline / 2 | 1200 / 1200 | 120.050 | 0 / 0 | 82.506 | 0.741 (1200) | 3.989 (1200) | 5.616 |
| baseline / 3 | 1200 / 1200 | 120.049 | 0 / 0 | 79.867 | 0.790 (1200) | 4.058 (1200) | 5.686 |
| candidate / 3 | 1200 / 1200 | 120.044 | 0 / 0 | 80.511 | 0.807 (1200) | 4.081 (1200) | 5.743 |

## 4k-3840x2160p120-hevc-hdr10-350mbps

Status: PASS

Full-frame software reference: hevc; 1,492,992,000 samples expected per build; observed maximum code errors: 0, 0.

Stream: 3840×2160 at 120 fps; HEVC, HDR10. Measured bitrate: 316.323 Mbps. Encoder target: 350.000 Mbps; measured/target: 90.4%.

| Build / run | Outputs / offered | FPS | Drops / failed | First output ms | VT submission mean ms (samples) | Frame-ready mean ms (samples) | Queue-inclusive proxy ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| candidate / 1 | 1200 / 1200 | 120.035 | 0 / 0 | 83.504 | 0.840 (1200) | 4.788 (1200) | 6.884 |
| baseline / 1 | 1200 / 1200 | 120.044 | 0 / 0 | 87.656 | 0.874 (1200) | 4.830 (1200) | 7.087 |
| baseline / 2 | 1200 / 1200 | 120.042 | 0 / 0 | 81.008 | 0.816 (1200) | 4.755 (1200) | 6.822 |
| candidate / 2 | 1200 / 1200 | 120.042 | 0 / 0 | 82.643 | 0.813 (1200) | 4.747 (1200) | 6.831 |
| candidate / 3 | 1200 / 1200 | 120.042 | 0 / 0 | 80.981 | 0.777 (1200) | 4.686 (1200) | 6.710 |
| baseline / 3 | 1200 / 1200 | 120.040 | 0 / 0 | 80.329 | 0.817 (1200) | 4.736 (1200) | 6.797 |

