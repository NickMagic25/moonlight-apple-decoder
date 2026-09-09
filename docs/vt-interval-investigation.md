# Inside the 4K60 VideoToolbox interval

The new measurements place most steady decoding latency inside VideoToolbox,
before the native public callback and before any Qt wrapping. The first fully
aligned HEVC System Trace finds that the submitting thread spends most of its
`VTDecompressionSessionDecodeFrame` interval blocked, including a condition
variable wait and synchronous XPC request/reply work. This identifies a more
specific target than ordinary parser or frame-wrapper allocation. It does not
identify the hardware engine's execution time or establish a removable 1 ms cost.

The repeated paced 4K cadence/output comparison remains above 2.5 ms median VT
latency, and every completed setting remains above 1 ms. Neither continuous
submission nor native lossless output reproduces
the older 1080p saturation result near 0.67 ms at 4K. The 1 ms paced objective
remains unmet in the completed cohorts documented here.

## Scope, provenance, and timing boundaries

These tests use Apple M3 / Mac15,3, macOS 26.6.2, SDK 26.5, Release arm64,
hardware-required sessions, and the four saved 3840×2160p60 AV1/HEVC SDR8/HDR10
4:2:0 fixtures. Source starts at `2935fce`; the experiment binaries additionally
contain the uncommitted diagnostic changes identified by source and binary
hashes. The normal build keeps `MAV_VT_EXPERIMENTS=OFF`. No production default
or Qt integration is promoted by this report.

The earlier scanner and parser-state improvements are already on main; they
are not new gains from this investigation. See [main adoption](main-adoption.md)
and [historical experiments](experiment-results.md). Historical measurements,
new experimental binaries, and separately instrumented captures remain distinct.

The [aggregate timing evidence](evidence/vt-interval-investigation.json) retains
cohort identities, source/binary/fixture hashes, aggregate timing distributions,
and complete outcome totals. The original local `results/*/evidence.json` and
`summary.json` retain commands, explicit environment, individual outcomes, and
raw-artifact hashes; CSV and logs remain under ignored `results/`.

Measured endpoints:

- **VT interval:** timestamp immediately before `VTDecompressionSessionDecodeFrame`
  through timestamp at callback entry. It includes API/driver work, decoding,
  waiting, and callback dispatch; it is not hardware-only time.
- **API call:** the same submission timestamp through return from the call.
- **After return:** ordered return through callback entry. Inline callbacks and
  missing/invalid return timestamps are counted separately rather than subtracted
  as unsigned values.
- **Public output:** scheduled complete-AU availability through the harness's
  entry to the native public callback. This includes replay arrival scheduling
  and admission. Qt, rendering, GPU completion, and presentation are absent.

`scripts/investigate-vt.py` runs cases serially and refuses an existing result
directory. It verifies expected offered/submitted/completed/displayed counts,
actual hardware outputs and formats, zero losses/drops/resets/trace overflow,
and reproduces reported timing counts and percentiles from CSV. Failed or
incomplete cohorts receive no aggregate timing claim. First successful outputs
of each generation and the first 120 offered IDs are excluded only from steady
timings, never from outcome accounting.

All tables below use milliseconds. Repeated results are medians of per-run
percentiles, not pooled percentiles. Phase percentiles are not additive.

## Current baseline and where its time goes

The default-output rows in `vt-output-screen` use three six-second paced runs,
360 offered AUs per run, 240 steady timing samples per run, in-flight limit two,
queue depth 32, and one continuous session. Each case displayed 1,080/1,080 AUs.

| 4K60 stream | VT p50 | VT p95 | VT p99 | Public output p50 |
| --- | ---: | ---: | ---: | ---: |
| AV1 SDR | 2.668 | 2.881 | 17.195 | 2.941 |
| AV1 HDR | 2.810 | 2.999 | 18.046 | 3.089 |
| HEVC SDR | 2.747 | 3.154 | 5.696 | 3.037 |
| HEVC HDR | 2.718 | 3.119 | 5.429 | 2.996 |

| Median phase | AV1 SDR | AV1 HDR | HEVC SDR | HEVC HDR |
| --- | ---: | ---: | ---: | ---: |
| Inside VT call | 0.732 | 0.812 | 0.802 | 0.762 |
| Return to VT callback | 1.930 | 1.991 | 1.949 | 1.937 |
| Parser preparation | 0.004 | 0.005 | 0.017 | 0.015 |
| Post-parser work before VT | 0.008 | 0.008 | 0.009 | 0.009 |
| VT callback to public callback | 0.014 | 0.019 | 0.015 | 0.019 |

Application-controlled preparation and native callback work are measured in
tens of microseconds per ordinary frame. Qt wrapping runs later on the adapter's
handoff worker and cannot explain an interval that ends before wrapping starts.
The new client's renderer may have its own costs, but removing Qt does not
remove this measured 2.7–2.8 ms interval.

## Same-stream 4K cadence and output format

`vt-output-screen` compares default canonical output against the decoder's
native output, in paced and throughput modes, on the same experiment binary
and compressed bytes. There are three repetitions per case/format/mode:
**48/48 runs, 95,040/95,040 AUs displayed**, with no drops, rejection, cancelled
outputs, reset, or overflow.

Paced runs offer 360 AUs over six seconds. Throughput runs offer 3,600 AUs
(30 fixture loops), leaving 3,480 steady samples, and take roughly 5.2–5.8
seconds for the default cases. Throughput offers immediately when capacity
permits, so its nominal 60 fps does not impose arrival pacing. Actual default
throughput is approximately 622–698 decoded fps. Occupancy, CPU activity, and
offered-frame count differ; these are cadence diagnostics, not interchangeable
caller-visible latency populations.

| Stream | Output | Paced VT p50 / p95 / p99 | Throughput VT p50 / p95 / p99 |
| --- | --- | ---: | ---: |
| AV1 SDR | Canonical | 2.668 / 2.881 / 17.195 | 2.607 / 2.761 / 17.114 |
| AV1 SDR | Native | 2.639 / 2.927 / 17.232 | 2.602 / 2.753 / 17.006 |
| AV1 HDR | Canonical | 2.810 / 2.999 / 18.046 | 2.652 / 2.804 / 17.490 |
| AV1 HDR | Native | 2.743 / 2.936 / 17.682 | 2.598 / 2.747 / 17.390 |
| HEVC SDR | Canonical | 2.747 / 3.154 / 5.696 | 2.632 / 3.519 / 9.418 |
| HEVC SDR | Native | 2.556 / 3.020 / 5.857 | 2.631 / 3.412 / 9.362 |
| HEVC HDR | Canonical | 2.718 / 3.119 / 5.429 | 2.627 / 2.833 / 8.545 |
| HEVC HDR | Native | 2.682 / 3.139 / 5.841 | 2.626 / 2.811 / 8.360 |

Native output selected Apple's lossless `&8v0` for SDR and `&xv0` for HDR,
instead of canonical `420v` / `x420`. Independent visible-sample comparisons
passed exactly for all four codecs/depth cases. The diagnostic correctness
path converts these opaque GPU-compatible buffers to linear NV12/P010 using
`VTPixelTransferSessionTransferImage` before sample comparison; it does not
treat compressed storage as linear CPU planes. Metal texture views are checked
separately on the original output buffers.
Explicit lossless requests and native selection with output attributes removed
were also checked separately. Removing both output attributes caused native
selection to return canonical SDR buffers; HDR still selected lossless `&xv0`.
Pixel-transfer equality and successful Metal view creation do not establish
correct shader sampling or presentation of compressed 10-bit output. A future
client must validate that rendering path and visible HDR separately.

Thus a real output-format change was tested. Its gains are mixed and much
smaller than the gap to 1 ms. AV1 random-access VT medians remain about 17.5 ms
SDR / 18.1 ms HDR paced, and about 16.9 / 17.3 ms under saturation. Each short
paced run contains only four steady random-access pictures; p99 estimates are
specific to these streams and populations.

The runner rotates the four combined format/mode settings over three
repetitions. This varies ordering but is not a complete four-position balance.

## Public controls and retained outputs: screening only

The separate `vt-control-screen` uses a later experimental binary, one
six-second paced run per setting/case, in-flight two, and the same 120-AU
warmup. **40/40 runs displayed 14,400/14,400 AUs**. These single repetitions
identify candidates for confirmation; small differences do not establish a
repeatable optimization.

| Setting | AV1 SDR VT p50 | AV1 HDR VT p50 | HEVC SDR VT p50 | HEVC HDR VT p50 |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 2.704 | 2.844 | 2.637 | 2.220 |
| RealTime off | 2.589 | 2.857 | 2.589 | 2.722 |
| User-initiated process activity | 2.626 | 2.747 | 2.584 | 2.723 |
| Latency-critical process activity | 2.684 | 2.790 | 2.641 | 2.714 |
| Omit Metal output attribute | 2.640 | 2.805 | 2.645 | 2.678 |
| Omit Metal and IOSurface attributes | 2.596 | 2.795 | 2.615 | 2.692 |
| Power-efficiency preference off | 2.664 | 2.846 | 2.580 | 2.956 |
| RealTime and power preference off | 2.687 | 2.827 | 2.703 | 2.584 |
| Retain one latest output | 2.712 | 2.869 | 2.671 | 2.885 |
| Retain three latest outputs | 2.878 | 3.049 | 2.729 | 2.815 |

The unusually low HEVC HDR baseline in this screen is a single run, not a new
floor. No setting meets the objective, and retaining buffers does not reveal a
large missing output-pool saving. Retention is a bounded diagnostic queue of
recent outputs, not a measurement of a live Metal renderer or display queue.

RealTime readback confirms the requested boolean. Power-efficiency writes
return success but effective-value readback is unavailable (`-12900`); an
accepted write is not proof of a particular hardware power state. Thread-count
and performance-ordered pixel-format-list queries report unavailable for both
codecs. The quality-ordered list is available for AV1 and returns canonical
`420v` / `x420`; it is unavailable for HEVC. Supported-property dictionaries
and readback are preserved as diagnostics; undocumented dictionary entries
are not treated as supported public tuning APIs.

Final exact-binary HDR baseline gates also read
`GeneratePerFrameHDRDisplayMetadata` successfully as **false** for both AV1 and
HEVC. Per-frame HDR metadata generation is already disabled in those sessions;
turning it off is not an untested saving here. SDR readback is unavailable.
The portable gate evidence retains these public-property readbacks and actual
output formats, without session addresses or private property listings.

## One frame in flight

`vt-inflight-one` is another screening cohort: one repetition per
case/format/mode, with one frame in flight, six-second paced runs and 30-loop
throughput runs. **16/16 runs displayed 31,680/31,680 AUs**, without accounting
failures. The binary matches `vt-control-screen`, not the earlier output screen.

| Stream | Canonical paced p50 | Canonical throughput p50 | Native paced p50 | Native throughput p50 |
| --- | ---: | ---: | ---: | ---: |
| AV1 SDR | 2.723 | 2.504 | 2.521 | 2.455 |
| AV1 HDR | 2.813 | 2.615 | 2.684 | 2.577 |
| HEVC SDR | 2.589 | 2.425 | 2.693 | 2.288 |
| HEVC HDR | 2.656 | 2.479 | 2.561 | 2.469 |

Reducing the outstanding-submission bound still does not produce a 1 ms
result. Comparisons to the earlier two-frame output screen involve a separate
binary/cohort and are not a paired causal estimate of the in-flight change.

## Aligned System Trace: blocked time inside the API

The new `VTDecodeCall` and `VTFrame` signposts carry the exact raw
submission/return/callback timestamps used in replay CSV. The analyzer joins by
those timestamps, checks return and callback equality, and overlaps the
trace-native call interval with the submitting thread's state intervals. No
offset is guessed from process start, wall-clock date, or first sample.

Both initial launch-mode traces joined 600/600 frames, but neither exported
the submitting thread's state records. All 480 steady API intervals in each
were therefore explicitly uncovered. Starting an all-process System Trace
before independently launching HEVC replay fixed this limitation:
**600/600 exact joins and 480/480 steady calls with complete, unambiguous
state coverage**.

| Submitting-thread state during VT call | Median per frame | Share of summed call interval |
| --- | ---: | ---: |
| Blocked | 0.650 ms | 75.26% |
| Running | 0.142 ms | 21.03% |
| Runnable | 0.0247 ms | 3.11% |
| Interrupted | 0 ms | 0.12% |
| Preempted | 0 ms | 0.49% |
| Uncovered / ambiguous | 0 ms | 0% |

In this instrumented HEVC 4K SDR run the raw API-call median is 0.832 ms and
VT submit-to-callback median is 2.831 ms. The largest API component is blocked
time, rather than ordinary time runnable but waiting to get a CPU.

The matching syscall export contains one `psynch_cvwait` per steady call:
480 waits, with 0.495 ms median per-frame overlap and 228.647 ms summed
overlap, 57.43% of the API intervals. There are also 1,152 `mach_msg2` rows;
116.545 ms of their overlap has stacks explicitly containing synchronous XPC
send-and-wait-for-reply functions. All 2,463 selected syscall intervals are
wholly inside the matched call intervals.

The [follow-up dependency analysis](vt-wait-dependencies.md) resolves an
important counting distinction: the two XPC-attributed Mach syscall rows per
frame are the send and receive sides of **one synchronous XPC request**, not
two requests. It also identifies the condition-variable signal and separates
the decoder submission acknowledgement from later output delivery.

These syscall findings attribute operations inside the call; they are not a
second additive timing partition. Exported syscall CPU/wait annotations can
exceed the enclosing syscall wall duration, so the thread-state partition is
used for Running/Blocked claims. Several middle stack symbols were missing from
the initial export; the follow-up uses matching installed image UUIDs and
scheduler wake edges to resolve them. Neither analysis establishes a
hardware-only engine duration.

See [profile aggregates and raw-source hashes](evidence/vt-profile-analysis.json)
and [syscall attribution aggregates](evidence/vt-submit-syscalls.json).
Frame records and thread/process identities remain in local ignored results.
Signpost emission slightly changes timer boundaries: the HEVC trace-call minus
raw-call median difference is about −0.0007 ms. Instrumented values never enter
the uninstrumented performance comparison tables.

## Repeated confirmation

`vt-confirmation` completed **48/48 qualified runs and 28,800/28,800 outputs**.
It uses the same binary and source hash as `vt-control-screen` and
`vt-inflight-one`, with ten-second paced runs, three repetitions per setting,
600 offered / 480 steady AUs per run, and two frames in flight. Ordering rotates
four settings over three repetitions; it is still not complete positional
balance. Values are VT p50 / p95 / p99, in milliseconds.

| Stream | Baseline | Native output | RealTime off | Power preference off |
| --- | ---: | ---: | ---: | ---: |
| AV1 SDR | 2.723 / 2.927 / 17.278 | 2.627 / 2.953 / 17.223 | 2.741 / 2.934 / 17.423 | 2.741 / 3.076 / 17.461 |
| AV1 HDR | 2.783 / 2.993 / 17.844 | 2.701 / 2.935 / 17.771 | 2.849 / 3.193 / 17.992 | 2.830 / 3.312 / 18.004 |
| HEVC SDR | 2.648 / 3.037 / 5.702 | 2.585 / 2.978 / 5.815 | 2.678 / 3.021 / 5.848 | 2.693 / 3.134 / 5.821 |
| HEVC HDR | 2.795 / 3.289 / 6.020 | 2.685 / 3.211 / 5.815 | 2.741 / 3.212 / 5.990 | 2.778 / 3.235 / 5.921 |

Native output has the clearest small median benefit, but its tails and repeat
consistency matter. Comparing same-numbered repetitions, the median paired
VT p50 change is −0.096 ms for AV1 SDR, −0.091 ms for AV1 HDR, −0.054 ms for
HEVC SDR, and −0.095 ms for HEVC HDR. All three AV1 SDR and HEVC HDR pairs
improve their median; AV1 HDR and HEVC SDR each regress in one of three pairs.
HEVC SDR p99 worsens in all three pairs. The paired statistic need not equal
the difference of the marginal medians in the table.

This is a modest format-dependent improvement for continued investigation,
not a route from 2.7 ms to 1 ms. RealTime and power controls do not yield a
consistent cross-codec benefit. The earlier HEVC HDR 2.220 ms single-screen
baseline does not reproduce as the baseline median here. No production
output-format change is selected on these short tests alone.

## Pixel correctness and validation

The recorded reference gates comprise:

| Cohort | Passing cases | Displayed / offered | Visible reference samples | Maximum error |
| --- | ---: | ---: | ---: | ---: |
| Archived baseline | 4 / 4 | 480 / 480 | 5,971,968,000 | 0 |
| Output-format probes | 16 / 16 | 1,920 / 1,920 | 23,887,872,000 | 0 |
| Public-control probes | 32 / 32 | 3,840 / 3,840 | 47,775,744,000 | 0 |
| Retained-output probes | 8 / 8 | 960 / 960 | 11,943,936,000 | 0 |
| Final exact-binary gates | 48 / 48 | 5,760 / 5,760 | 71,663,616,000 | 0 |
| ASan/UBSan native HDR + retain three | 2 / 2 | 240 / 240 | 2,985,984,000 | 0 |

All mean sample errors are also zero. Each gate independently verifies hardware
output, IOSurface/Metal compatibility, and retained-buffer validity. Correctness
processing is kept out of timed runs.

Gate provenance stays explicit: archived-baseline, output-probe, and control-
probe binaries have separate saved hashes. The initial retained-output gate
summary does not record a binary hash. Final gates resolve exact-build coverage:
all 12 variants across all four streams pass on binary `bf2856a2…`, source
`a263348b…`, identical to the control screen, one-frame screen, and repeated
confirmation. They cover all ten public-control/retention settings plus native
and native-without-output-attributes. Each gate records its manifest/reference
and output-artifact hashes. Earlier gates remain separately identified.

The final normal Release build with diagnostics off passes all four CTests.
The measured experimental Release build passes all six CTests, and a fresh
Debug ASan/UBSan experimental build passes all six. The 16 runner/trace-
accounting Python tests and nine profile-parser/coverage tests also pass.
Recorded CTest logs are under `results/vt-validation/`; their hashes are
included in the aggregate evidence. These checks verify correctness and
diagnostic gating, not decode performance.

Two additional hardware gates run the ASan/UBSan build on AV1 HDR and HEVC HDR,
with native lossless `&xv0` output and three retained outputs. Both display
120/120 frames, match all visible reference samples exactly, and preserve
IOSurface/Metal compatibility and retained-buffer validity after destruction.
No ASan or UBSan diagnostics occur in these gates or the sanitizer unit logs.
The sanitizer binary is separately identified and is not used for timing claims.

## Interpretation and stopping criteria

The completed uninstrumented cohorts above account for **152/152 runs and
169,920/169,920 offered, submitted, completed, and displayed frames**. The
1,800 instrumented replay outputs and 13,200 pixel-gate outputs are separate
populations. Exploratory initial probes are not mixed into the controlled
tables. All full-run outcomes remain visible even when startup or warmup frames
are excluded from steady timing distributions.

The remaining material limitation is that these are short synthetic fixtures
on one M3, not high-bitrate live game captures, an iOS/tvOS device sweep, a
sustained thermal study, or a live client test. An observed operating-system
wait is not proof that an application can safely bypass it. Disabling a hint,
omitting output attributes, retaining surfaces, or changing queue depth is not
promoted solely because one short run is faster.

For this M3, these fixtures, and the equivalent-quality public controls available
to this implementation, the reasonable supported local options investigated
here are exhausted as credible routes to 1 ms. The goal remains unmet. This
does not establish a universal hardware floor or rule out different hardware,
streams, OS behavior, or future supported APIs.

The [follow-up investigation](vt-wait-dependencies.md) identifies the
condition-variable/XPC dependency more precisely. Further work can test
representative encoder outputs and target hardware, or obtain Apple-supported
guidance for the API wait. Repeating nearby allocation or public-property tweaks without a measured
lead cannot reasonably promise the missing 1.7–1.8 ms. The diagnostic controls
and aligned analyzer are retained for that work; a native future client can
consume CVPixelBuffer/IOSurface/Metal directly while measuring presentation
separately. Native lossless surfaces may preserve the measured small benefit,
but removing Qt wrapping cannot eliminate waits already observed inside VT.

## Reproduction

Build diagnostic tools separately, then complete correctness before timing:

```sh
cmake -S . -B build-vt-experiment -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES=arm64 -DMAV_VT_EXPERIMENTS=ON
cmake --build build-vt-experiment --parallel 4
ctest --test-dir build-vt-experiment --output-on-failure
```

Controls exist only in the diagnostic build and remain outside the C ABI:

| Environment variable | Values / effect |
| --- | --- |
| `MAV_VT_PIXEL_FORMAT` | `native` or a compatible four-character pixel format; preserve 4:2:0, depth, and range |
| `MAV_VT_REALTIME` | `0` / `1`; request the public RealTime property |
| `MAV_VT_POWER_EFFICIENCY` | `0`; disable the preference, with setter/readback diagnostics |
| `MAV_VT_THREAD_COUNT` | Nonnegative integer; inspect support/status before attributing a result to it |
| `MAV_VT_ASYNC` | `0` / `1`; synchronous delivery remains a blocking diagnostic |
| `MAV_VT_METAL`, `MAV_VT_IOSURFACE` | `0` / `1`; omit/include the corresponding output attribute |
| `MAV_VT_ACTIVITY` | `none`, `user-initiated`, `latency-critical`; replay process activity |
| `MAV_VT_RETAIN_OUTPUTS` | `0..8`; retain a bounded number of latest replay outputs |
| `MAV_VT_SIGNPOST` | `0` / `1`; enable timestamp-anchored diagnostic signposts |

For example, after creating the independent reference through the
[fixture workflow](fixtures.md), validate native lossless output separately:

```sh
MAV_VT_PIXEL_FORMAT=native build-vt-experiment/mav-replay \
  --fixture fixtures/generated/av1-hdr10-3840x2160p60-120/manifest.json \
  --mode correctness --loops 1 --inflight 2 --queue-depth 32 \
  --reference-raw results/experiment-preparation/av1-hdr10-3840x2160p60-120-reference.yuv \
  --output results/vt-new-native-correctness
```

A variants JSON object contains explicit environment overrides, for example
`{"baseline": {}, "native": {"MAV_VT_PIXEL_FORMAT": "native"}}`. Capture a new
serial cadence comparison without overwriting existing evidence:

```sh
python3 scripts/investigate-vt.py --binary build-vt-experiment/mav-replay \
  --source-dir . --results-dir results/vt-new-cadence --variants variants.json \
  --modes paced,throughput --seconds 6 --throughput-loops 30 --repetitions 3
python3 scripts/investigate-vt.py --analyze results/vt-new-cadence \
  --output results/vt-new-cadence/reanalysis.json
python3 tests/vt_investigation.py -v
python3 tests/vt_profile_analysis.py -v
```

`--seconds` specifies paced offered duration; throughput uses its explicit
loop count. `--loops` instead gives both modes the same offered AU count.
Use a new results directory for every invocation. Raw profiler captures must
run separately with `MAV_VT_SIGNPOST=1`; export region-of-interest, thread-state,
and TOC XML, then run `scripts/analyze-vt-profile.py` with their common prefix.
Full commands, hashes, failures, and timing populations must remain associated
with the binary that actually produced them.
