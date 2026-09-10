# Independent full bitrate matrix audit

Audit result: **PASS**. Dataset result remains **FAIL**; a successful evidence audit does not make every workload pass.

All 192 software-reference correctness checks passed with 205,037,568,000 compared YUV samples and 26,880 decoded outputs. Maximum observed code error was 0. Exact sample counts, unchanged 2-code SDR/8-code HDR tolerances, hardware decoding, native correctness, Metal/IOSurface, retention, zero loss, reference binding and all 576 native JSON/CSV/log hashes were independently checked.

Case statuses: `{"BASELINE_FAILURE": 21, "INCONCLUSIVE": 24, "PASS": 50, "REGRESSION": 1}`. Bitrate coverage: `{"OUTSIDE_TOLERANCE": 38, "PASS": 58}` at the unchanged 20% tolerance.

Source provenance confirms 48 realtime AV1 fixtures, 47 realtime HEVC fixtures, and the single offline HEVC 4K60 HDR 50 Mbps fixture. Each archived source manifest hashes correctly; derived manifests only change the documented validation pattern and add reference provenance.

## Bitrate cases outside tolerance

| Case | Requested Mbps | Measured Mbps | Dataset status |
|---|---:|---:|---|
| 1080p-1920x1080p120-av1-sdr-50mbps | 50 | 86.448 | INCONCLUSIVE |
| 1080p-1920x1080p120-av1-hdr10-50mbps | 50 | 73.130 | INCONCLUSIVE |
| 1080p-1920x1080p120-av1-hdr10-100mbps | 100 | 122.612 | INCONCLUSIVE |
| 1080p-1920x1080p120-hevc-sdr-50mbps | 50 | 62.494 | INCONCLUSIVE |
| ultrawide-3440x1440p120-av1-sdr-50mbps | 50 | 141.911 | INCONCLUSIVE |
| ultrawide-3440x1440p120-av1-sdr-100mbps | 100 | 185.744 | INCONCLUSIVE |
| ultrawide-3440x1440p120-av1-hdr10-50mbps | 50 | 142.056 | INCONCLUSIVE |
| ultrawide-3440x1440p120-av1-hdr10-100mbps | 100 | 170.713 | INCONCLUSIVE |
| ultrawide-3440x1440p120-hevc-sdr-50mbps | 50 | 70.255 | INCONCLUSIVE |
| ultrawide-3440x1440p120-hevc-hdr10-50mbps | 50 | 64.800 | INCONCLUSIVE |
| ultrawide-3440x1440p240-av1-sdr-50mbps | 50 | 225.205 | BASELINE_FAILURE |
| ultrawide-3440x1440p240-av1-sdr-100mbps | 100 | 239.685 | BASELINE_FAILURE |
| ultrawide-3440x1440p240-av1-sdr-250mbps | 250 | 377.887 | BASELINE_FAILURE |
| ultrawide-3440x1440p240-av1-sdr-350mbps | 350 | 440.119 | BASELINE_FAILURE |
| ultrawide-3440x1440p240-av1-hdr10-50mbps | 50 | 205.582 | BASELINE_FAILURE |
| ultrawide-3440x1440p240-av1-hdr10-100mbps | 100 | 260.701 | BASELINE_FAILURE |
| ultrawide-3440x1440p240-av1-hdr10-250mbps | 250 | 369.541 | BASELINE_FAILURE |
| ultrawide-3440x1440p240-av1-hdr10-350mbps | 350 | 479.101 | BASELINE_FAILURE |
| 4k-3840x2160p60-av1-sdr-50mbps | 50 | 131.636 | INCONCLUSIVE |
| 4k-3840x2160p60-av1-sdr-100mbps | 100 | 167.610 | INCONCLUSIVE |
| 4k-3840x2160p60-av1-sdr-350mbps | 350 | 655.946 | BASELINE_FAILURE |
| 4k-3840x2160p60-av1-hdr10-50mbps | 50 | 122.846 | INCONCLUSIVE |
| 4k-3840x2160p60-av1-hdr10-100mbps | 100 | 133.382 | INCONCLUSIVE |
| 4k-3840x2160p60-av1-hdr10-350mbps | 350 | 642.298 | BASELINE_FAILURE |
| 4k-3840x2160p60-hevc-sdr-50mbps | 50 | 60.820 | INCONCLUSIVE |
| 4k-3840x2160p60-hevc-hdr10-50mbps | 50 | 83.905 | INCONCLUSIVE |
| 4k-3840x2160p120-av1-sdr-50mbps | 50 | 218.276 | INCONCLUSIVE |
| 4k-3840x2160p120-av1-sdr-100mbps | 100 | 263.272 | INCONCLUSIVE |
| 4k-3840x2160p120-av1-sdr-250mbps | 250 | 358.597 | BASELINE_FAILURE |
| 4k-3840x2160p120-av1-sdr-350mbps | 350 | 433.243 | BASELINE_FAILURE |
| 4k-3840x2160p120-av1-hdr10-50mbps | 50 | 177.539 | INCONCLUSIVE |
| 4k-3840x2160p120-av1-hdr10-100mbps | 100 | 245.692 | INCONCLUSIVE |
| 4k-3840x2160p120-av1-hdr10-250mbps | 250 | 342.189 | BASELINE_FAILURE |
| 4k-3840x2160p120-av1-hdr10-350mbps | 350 | 436.031 | BASELINE_FAILURE |
| 4k-3840x2160p120-hevc-sdr-50mbps | 50 | 82.298 | INCONCLUSIVE |
| 4k-3840x2160p120-hevc-sdr-100mbps | 100 | 122.563 | INCONCLUSIVE |
| 4k-3840x2160p120-hevc-hdr10-50mbps | 50 | 82.866 | INCONCLUSIVE |
| 4k-3840x2160p120-hevc-hdr10-100mbps | 100 | 122.444 | INCONCLUSIVE |

## Audit scope

- Compressed payload hashes were compared across provenance but payload bytes were not rehashed in this bounded audit; the root analyzer already validated them.
- HDR metadata checks execute inside the native correctness sink; JSON records depth, fallback metadata flags and PASS, with no separate per-frame HDR-output flag.
- No hardware tests or timing runs were executed by this audit.
