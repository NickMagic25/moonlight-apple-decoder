# Focused HEVC rerun: frame-loss and correctness audit

Offline analysis of saved evidence. No tests or benchmarks were rerun by this audit. **Evidence accounting verified; the decoder comparison is not an all-pass result.**

All 32 correctness checks passed with zero maximum and mean pixel-code error. All 96 timed native results reported nominal thermal state (`0`) at the end of their trials; this is not continuous thermal monitoring.

| Mode | Build | Timed passes | Timed failures |
|---|---|---:|---:|
| 3440x1440@240 | baseline | 3 | 21 |
| 3440x1440@240 | candidate | 0 | 24 |
| 3840x2160@60 | baseline | 24 | 0 |
| 3840x2160@60 | candidate | 24 | 0 |

All 45 failed trials lost outputs before zero-based frame ID 120. Every frame at ID 120 onward produced an output: 132,480 of 132,480. Initial losses remain failures and are not erased by warmup.

Timed accounting: 144,000 offered = 141,417 submitted + 2,583 scheduler drops + 0 rejected. Every accepted submission completed: 141,341 outputs and 76 failed/cancelled/dropped completions.

## Loss locations

IDs start at **0** and ranges are inclusive. Missing CSV IDs reconcile with scheduler drops. Nonoutput rows below have cancellation status `4`. Recovery means the first output after the last missing ID; it may differ from the first output of the trial.

| Workload | Build / trial | Missing CSV IDs | Cancelled IDs | Missing output IDs | First output ID | Recovery ID / ms | Missing IDs ≥120 |
|---|---|---|---|---|---:|---:|---:|
| sdr-50mbps | candidate / 1 | 2–59 | 0–1 | 0–59 | 60 | 60 / 259.487 | 0 |
| sdr-50mbps | candidate / 2 | 2–59 | 0–1 | 0–59 | 60 | 60 / 259.094 | 0 |
| sdr-50mbps | baseline / 3 | 2–59 | 0–1 | 0–59 | 60 | 60 / 261.324 | 0 |
| sdr-50mbps | candidate / 3 | 2–59 | 0–1 | 0–59 | 60 | 60 / 257.190 | 0 |
| sdr-100mbps | candidate / 1 | 1–59 | 0 | 0–59 | 60 | 60 / 259.349 | 0 |
| sdr-100mbps | baseline / 1 | 2–59 | 1 | 1–59 | 0 | 60 / 258.874 | 0 |
| sdr-100mbps | baseline / 2 | 4–59 | 2–3 | 2–59 | 0 | 60 / 258.990 | 0 |
| sdr-100mbps | candidate / 2 | 2–59 | 0–1 | 0–59 | 60 | 60 / 258.949 | 0 |
| sdr-100mbps | candidate / 3 | 2–59 | 1 | 1–59 | 0 | 60 / 258.673 | 0 |
| sdr-100mbps | baseline / 3 | 2–59 | 0–1 | 0–59 | 60 | 60 / 258.906 | 0 |
| sdr-250mbps | baseline / 1 | 3–59 | 1–2 | 1–59 | 0 | 60 / 259.284 | 0 |
| sdr-250mbps | candidate / 1 | 3–59 | 2 | 2–59 | 0 | 60 / 257.433 | 0 |
| sdr-250mbps | candidate / 2 | 3–59 | 1–2 | 1–59 | 0 | 60 / 258.928 | 0 |
| sdr-250mbps | baseline / 2 | 3–59 | 1–2 | 1–59 | 0 | 60 / 261.049 | 0 |
| sdr-250mbps | baseline / 3 | 3–59 | 1–2 | 1–59 | 0 | 60 / 259.216 | 0 |
| sdr-250mbps | candidate / 3 | 4–59 | 2–3 | 2–59 | 0 | 60 / 259.413 | 0 |
| sdr-350mbps | candidate / 1 | 2–59 | 1 | 1–59 | 0 | 60 / 260.953 | 0 |
| sdr-350mbps | baseline / 1 | 3–59 | 2 | 2–59 | 0 | 60 / 262.458 | 0 |
| sdr-350mbps | baseline / 2 | 3–59 | 2 | 2–59 | 0 | 60 / 260.431 | 0 |
| sdr-350mbps | candidate / 2 | 3–59 | 1–2 | 1–59 | 0 | 60 / 259.467 | 0 |
| sdr-350mbps | candidate / 3 | 3–59 | 2 | 2–59 | 0 | 60 / 260.281 | 0 |
| sdr-350mbps | baseline / 3 | 3–59 | 1–2 | 1–59 | 0 | 60 / 260.513 | 0 |
| hdr10-50mbps | baseline / 1 | 2–59 | 0–1 | 0–59 | 60 | 60 / 261.661 | 0 |
| hdr10-50mbps | candidate / 1 | 2–59 | 0–1 | 0–59 | 60 | 60 / 263.498 | 0 |
| hdr10-50mbps | candidate / 2 | 1–59 | 0 | 0–59 | 60 | 60 / 264.740 | 0 |
| hdr10-50mbps | baseline / 3 | 2–59 | 0–1 | 0–59 | 60 | 60 / 261.529 | 0 |
| hdr10-50mbps | candidate / 3 | 2–59 | 0–1 | 0–59 | 60 | 60 / 263.078 | 0 |
| hdr10-100mbps | candidate / 1 | 2–59 | 1 | 1–59 | 0 | 60 / 260.099 | 0 |
| hdr10-100mbps | baseline / 1 | 2–59 | 0–1 | 0–59 | 60 | 60 / 262.098 | 0 |
| hdr10-100mbps | baseline / 2 | 2–59 | 0–1 | 0–59 | 60 | 60 / 260.652 | 0 |
| hdr10-100mbps | candidate / 2 | 2–59 | 1 | 1–59 | 0 | 60 / 262.101 | 0 |
| hdr10-100mbps | candidate / 3 | 2–59 | 0–1 | 0–59 | 60 | 60 / 261.486 | 0 |
| hdr10-100mbps | baseline / 3 | 2–59 | 0–1 | 0–59 | 60 | 60 / 262.459 | 0 |
| hdr10-250mbps | baseline / 1 | 4–59 | 2–3 | 2–59 | 0 | 60 / 260.877 | 0 |
| hdr10-250mbps | candidate / 1 | 3–59 | 2 | 2–59 | 0 | 60 / 261.572 | 0 |
| hdr10-250mbps | candidate / 2 | 3–59 | 2 | 2–59 | 0 | 60 / 262.643 | 0 |
| hdr10-250mbps | baseline / 2 | 4–59 | 2–3 | 2–59 | 0 | 60 / 259.839 | 0 |
| hdr10-250mbps | baseline / 3 | 4–59 | 2–3 | 2–59 | 0 | 60 / 262.142 | 0 |
| hdr10-250mbps | candidate / 3 | 4–59 | 2–3 | 2–59 | 0 | 60 / 263.436 | 0 |
| hdr10-350mbps | candidate / 1 | 2–59 | 0–1 | 0–59 | 60 | 60 / 261.607 | 0 |
| hdr10-350mbps | baseline / 1 | 3–59 | 1–2 | 1–59 | 0 | 60 / 261.715 | 0 |
| hdr10-350mbps | baseline / 2 | 4–59 | 2–3 | 2–59 | 0 | 60 / 263.639 | 0 |
| hdr10-350mbps | candidate / 2 | 2–59 | 0–1 | 0–59 | 60 | 60 / 263.714 | 0 |
| hdr10-350mbps | candidate / 3 | 3–59 | 1–2 | 1–59 | 0 | 60 / 262.967 | 0 |
| hdr10-350mbps | baseline / 3 | 3–59 | 2 | 2–59 | 0 | 60 / 276.546 | 0 |

The causes of these startup losses remain unknown. Recovery at a random-access frame does not establish why the scheduler first fell behind. Missing terminal CSV rows cannot distinguish each scheduler-drop branch.

## Previous selected workloads

| Status | Previous full run, selected 16 | Focused rerun |
|---|---:|---:|
| PASS | 9 | 6 |
| INCONCLUSIVE | 2 | 2 |
| BASELINE_FAILURE | 4 | 8 |
| REGRESSION | 1 | 0 |

These are separate executions. The rerun does not overwrite the previous evidence or establish clean ultrawide performance. See the [generated report](report.md) for bitrate coverage and latency gates.

## Provenance

Source plan SHA-256: `b3833fb644b8e202d4ad16e9f2e311dfedcb6dc61118f459886f5a45af22e075`.

Source results SHA-256: `c034cf7ffa8d894393b61472994ed08b5dce9e4de30d577a6ab3ba399fb4d677`.

[loss-audit.json](loss-audit.json) retains all per-run accounting and ranges, correctness sample counts, methods and SHA-256 identities for every analyzed native JSON/CSV/log and reference/fixture manifest. The ID population was verified against manifests and the replay loop-stride formula. Independent software-reference bytes had been deleted by the runner; this audit verifies recorded pixel comparisons and hash linkage without decoding again.
