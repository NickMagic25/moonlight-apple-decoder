# HEVC startup scheduling fix

The replay's strict 16-frame arrival-age limit allowed 66.7 ms of backlog at
240 fps. Cold session setup exhausted that allowance, causing the harness to
reset the decoder, cancel pending outputs, and skip dependent frames until
frame 60. The live Qt adapter has different capacity handling; these replay
failures did not establish identical losses in the client.

Commit `a181a0090f746445c3daa62e5ea0bc3ead318119` adds an explicit, bounded
startup admission allowance. The [HEVC preset](../benchmarks/hevc-startup.yaml)
uses `decoder.startup_grace_ms: 250` and a separate
`thresholds.first_output_max_ms: 250`. The allowance is anchored to the original
scheduled start and never restarts after a reset, keyframe, or fixture loop.
Original arrival timestamps, the steady 16-frame limit, all offered frames,
delivery gates, and latency thresholds remain in effect. A zero allowance
retains the old strict behavior, including in existing presets.

This fixes the replay's startup handling. It does not accelerate VideoToolbox
or change production decoder behavior. Every production decoder object and
the symbol table are byte-identical to the corresponding pre-fix build; only
the archive container bytes differ. The
[library identity check](evidence/hevc-startup-fixed/library-identity.json)
records both archive and member hashes.

## Hardware controls

Eight two-second trials compared strict and startup-aware scheduling using
the same C++23 binary and saved ultrawide streams: SDR at a 100 Mbps target and
HDR10 at a 350 Mbps target, two repetitions per policy with alternating order.
All four strict trials lost startup frames and delivered 420/480 outputs.
All four startup-aware trials delivered 480/480, with first output in
76.058–80.781 ms, versus 255.226–259.311 ms after the strict-policy reset.
No arrival timestamps or startup samples were removed.

The [control report](evidence/hevc-startup-fixed/controls/report.md),
[commands and hashes](evidence/hevc-startup-fixed/controls/controls.json), and
[independent framework checks](evidence/hevc-startup-fixed/controls/controls-analysis.json)
retain all eight trials, including failures and exact scheduler-drop causes.

## Full paired comparison

The focused comparison reused all 16 original HEVC fixtures: 3440×1440 at
240 fps and 3840×2160 at 60 fps, SDR/HDR10, and 50/100/250/350 Mbps targets.
Both builds used the same updated replay sources, with three 10-second trials
per build and 120 statistical warmup frames. The C++17 baseline decoder source
remains revision `5e482b0392df5d56008be51ca0f6ea6431f4f03a`; its replay harness
was overlaid from the candidate and rebuilt. The
[overlay manifest](evidence/hevc-startup-fixed/replay-harness-overlay.json)
records original and replacement source hashes. Earlier sources, binaries,
reports, and strict failures remain preserved separately.

All **32 correctness checks passed with zero pixel difference**. All **96 timed
trials passed delivery, raw-trace validation, and the first-output limit**.
The run delivered **144,000/144,000 frames**, with zero scheduler drops,
cancellations, rejections, or resets. Every timed trial recorded nominal
thermal state at completion. No VT or public-completion median/p95/p99
comparison exceeded its configured latency threshold.

| Mode | Timed delivery passes | Delivered frames | C++17 first-output range ms | C++23 first-output range ms | Case verdicts |
|---|---:|---:|---:|---:|---|
| 3440×1440 at 240 fps | 48/48 | 115,200/115,200 | 69.356–79.327 | 71.093–86.094 | 8 PASS |
| 3840×2160 at 60 fps | 48/48 | 28,800/28,800 | 86.337–96.783 | 87.698–95.392 | 6 PASS, 2 INCONCLUSIVE |

The overall report still exits with **FAIL**, solely because the two 4K 50 Mbps
fixtures exceed the ±20% bitrate tolerance: measured SDR is 60.820 Mbps and
HDR10 is 83.905 Mbps. They passed decoding and latency checks but do not
establish coverage at the requested 50 Mbps target. The aggregate verdicts
are **14 PASS and 2 INCONCLUSIVE**. No prior failed result is overwritten or
retroactively reclassified.

Read the [generated Markdown report](evidence/hevc-startup-fixed/report.md),
[machine-readable results](evidence/hevc-startup-fixed/results.json), and
[Moonlight timing means](evidence/hevc-startup-fixed/moonlight-decode-times.json).
The [startup audit](evidence/hevc-startup-fixed/startup-audit.md) checks the
recorded policy, absolute arrivals, first-output and setup timestamps,
accounting, hardware correctness, and fixture identity. The
[metric audit](evidence/hevc-startup-fixed/metric-audit.md) independently
recomputes all 96 timing traces and all six comparisons per case.

This is evidence for the selected streams and hardware. It does not establish
zero performance change, behavior for every game, or live client presentation
on a Mac, iPhone, or Apple TV. Startup allowance and first-output latency are
separate from steady decode latency.

## Local and CI checks

Local checks passed all six CTest tests in Debug and Release. The standalone
startup policy tests also passed in C++17 Debug and C++23 Release with `NDEBUG`
and warnings treated as errors. The Python framework ran 99 tests: 98 passed,
with the optional real-encoder process test skipped because its tool path was
not enabled for that invocation.

[Hosted CI passed for the code commit](https://github.com/NickMagic25/moonlight-apple-decoder/actions/runs/34422076617):
99 framework tests on each platform with one tool-dependent skip, all six
native tests, all five separate macOS encoder-process checks, and the Swift
6.3.3 package/C ABI smoke. The separate encoder stage covers that skipped
native-tool check. The updated physical CI workflow can apply the same replay
harness to an older baseline and preserves the overlay hashes; that workflow
was not dispatched for this local hardware comparison.

The [archive manifest](evidence/hevc-startup-fixed/archive.json) records the
unchanged generated reports, control evidence, audit files, and local test
logs. Complete raw fixtures, traces, logs, and harness snapshots remain under
`results/hevc-startup-fixed`, `results/hevc-startup-controls`, and
`results/hevc-startup-fix-setup` locally. See the
[framework guide](testing-framework.md#startup-admission-and-first-output-checks)
for local and CI configuration.
