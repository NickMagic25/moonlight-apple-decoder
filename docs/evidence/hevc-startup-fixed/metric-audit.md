# Independent metric audit

Status: **PASS**. Recomputed all 96 timed CSVs without importing the benchmark analysis or report generator.

Verified integer duration sums/counts, per-trial means, weighted case means, both machine-readable reports and rounded human-readable mean tables. Missing return timestamps were excluded, not zero-filled. All 96 six-metric steady distributions and all 16 six-metric paired comparisons match saved evidence.

| Build | Frame-ready samples | Submission samples | Missing returns |
|---|---:|---:|---:|
| baseline | 72000 | 71903 | 97 |
| candidate | 72000 | 71901 | 99 |

Observed paired threshold breaches: 0. All six latency gates were independently recomputed for all 16 cases, regardless of case status.

| Case | Status | Metric | Paired delta ms | Paired delta % | Allowance ms |
|---|---|---|---:|---:|---:|

All 16 workloads clear all six latency gates. Fourteen cases are PASS; 4K60 SDR and HDR10 at the 50 Mbps target remain INCONCLUSIVE because their retained fixture payload rates are outside the bitrate tolerance. Clearing observational gates does not establish statistical equivalence or rule out smaller regressions.

Source hashes and every recomputed trial are in [metric-audit.json](metric-audit.json).
