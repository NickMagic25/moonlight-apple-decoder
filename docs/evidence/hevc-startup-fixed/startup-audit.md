# Fixed startup policy: independent audit

Offline audit only; no tests, decoding or benchmarks were run by this audit. **All 32 correctness checks and 96 timed native trials passed.** The overall workload results remain 14 PASS and 2 INCONCLUSIVE because bitrate coverage is a separate gate.

All 144,000 offered timed frames produced outputs. There were no scheduler drops, rejected inputs, cancellations, resets or missing completions. All 132,480 outputs from zero-based ID120 onward arrived. All first outputs were ID0 and met the 250 ms first-output SLA. All 96 trials reported nominal thermal state at their end.

| Mode | Build | Trials | First output min–max ms | Initial setup min–max ms |
|---|---|---:|---:|---:|
| 3440x1440@240 | baseline | 24 | 69.356–79.327 | 55.259–64.697 |
| 3440x1440@240 | candidate | 24 | 71.093–86.094 | 54.170–69.321 |
| 3840x2160@60 | baseline | 24 | 86.337–96.783 | 57.597–67.971 |
| 3840x2160@60 | candidate | 24 | 87.698–95.392 | 60.451–67.787 |

Initial setup is the first frame interval from parser/preparation end to VT submission; it includes session configuration and other work, so it is not isolated session-creation time. First output is measured from the original scheduled epoch to the earliest successful completion callback entry.

## Policy and reproducibility

Both builds used the same replay harness source files and the fixed-initial-deadline-v1 policy. Native decoder builds retained C++17 and C++23 respectively. Timed invocations used 250 ms startup grace, queue depth 16 and two in-flight frames. Correctness invocations retained zero startup grace.

The admission deadline is `max(frame arrival + 16 frame periods, original scheduled start + 250 ms)`. All timed raw CSV arrival timestamps matched the original schedule exactly. No first-frame loss or clock rebasing can improve these first-output measurements. All scheduler event lists were empty, matching zero reason counters and complete raw frame identities. This run consequently does not exercise the deadline-drop event branches.

All 16 compressed payloads were hashed in both this run and the earlier strict comparison and matched byte for byte. All 128 native JSON/CSV/log hashes matched their recorded plan/result identities. Both current replay binaries and source aggregates matched captured provenance; the three shared harness files matched the overlay manifest.

Every correctness check verified the full expected YUV420 sample population against the independent FFmpeg software reference with zero maximum and mean code error, plus hardware, IOSurface/Metal and retained-buffer checks. Deleted raw reference files were not regenerated; this audit verifies stored comparison results and reference metadata/hash linkage.

## Evidence

- Source plan SHA-256: `eda2d8524cbb8a3771638ed9707a630f25fde864fbd04dc2b72017f73d2410e6`.
- Source results SHA-256: `065fc0d08f991f02df5a0656e90f2b1dd3278183a133e05ccfcfc8f616244d42`.
- [startup-audit.json](startup-audit.json) contains per-run counts and timings, source identities, harness and fixture hashes, and the formulas used.
- [report.md](report.md) preserves the original bitrate coverage and latency comparison gates.

The earlier strict comparison remains evidence for its original policy. This headless run does not measure live Qt rendering, network or presentation. Thermal readings are end-of-trial observations rather than continuous monitoring.
