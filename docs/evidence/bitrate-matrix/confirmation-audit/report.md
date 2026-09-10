# Independent confirmation audit

Audit result: **PASS**. The confirmation dataset remains **FAIL**.

All four full-frame correctness checks passed: 7,133,184,000 YUV samples and 960 outputs, with maximum pixel error 0. Exact sample counts, unchanged HDR tolerance8, hardware, HDR-validity flags, Metal/IOSurface, retention, zero loss, and reference binding were verified. All 84 native JSON/CSV/log hashes matched the plan.

The two fixtures preserve the original full-run source manifest hashes, compressed payload identities, and independent software-reference pixel hashes. Both were originally encoded with realtime HEVC.

The 24 timed trials contain **13 native PASS and 11 native FAIL**. No aggregate latency gate exceeded its unchanged threshold. Delivery failures therefore remain unresolved; these measurements do not establish an all-pass regression result.

| Case | Dataset status | Native timed counts |
|---|---|---|
| ultrawide-3440x1440p240-hevc-hdr10-50mbps | REGRESSION | {"baseline/PASS": 6, "candidate/FAIL": 1, "candidate/PASS": 5} |
| ultrawide-3440x1440p240-hevc-hdr10-250mbps | BASELINE_FAILURE | {"baseline/FAIL": 6, "candidate/FAIL": 4, "candidate/PASS": 2} |

Audit scope: Bounded read-only audit; compressed payload bytes not rehashed. HDR output checks execute inside native correctness mode and are implied by PASS; native JSON additionally records depth and fallback HDR-validity flags.
