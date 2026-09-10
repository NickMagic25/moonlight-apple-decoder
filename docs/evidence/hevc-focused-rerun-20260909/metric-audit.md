# Independent metric audit

Status: **PASS**. Recomputed all 96 timed CSVs without importing the benchmark analysis or report generator.

Verified integer duration sums/counts, per-trial means, weighted case means, both machine-readable reports and rounded human-readable mean tables. Missing return timestamps were excluded, not zero-filled. All 96 six-metric steady distributions and all 16 six-metric paired comparisons match saved evidence.

| Build | Frame-ready samples | Submission samples | Missing returns |
|---|---:|---:|---:|
| baseline | 70762 | 70654 | 108 |
| candidate | 70579 | 70454 | 125 |

Two observed threshold breaches remain; neither is hidden by the case status:

| Case | Status | Metric | Paired delta ms | Paired delta % | Allowance ms |
|---|---|---|---:|---:|---:|
| ultrawide-3440x1440p240-hevc-hdr10-350mbps | BASELINE_FAILURE | vt_p95_ms | 0.222442300 | 5.192598 | 0.207185298 |
| 4k-3840x2160p60-hevc-sdr-50mbps | INCONCLUSIVE | public_p95_ms | 1.004556450 | 10.230811 | 0.490946647 |

The six fully PASS 4K60 cases clear every latency gate. The 4K60 SDR 50 Mbps case has a public p95 increase despite its INCONCLUSIVE bitrate status. Ultrawide HDR10 350 Mbps has a VT p95 increase in a BASELINE_FAILURE workload; it is descriptive evidence rather than a qualified regression comparison.

Source hashes and every recomputed trial are in [metric-audit.json](metric-audit.json).
