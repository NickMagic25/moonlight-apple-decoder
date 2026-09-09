# Isolated latency experiments

This is the historical comparison report from `b126a85`. Main subsequently
adopts the scanner, parser-state and optional replay-pacing branches; see
[adoption and combined validation](main-adoption.md). The measurements and
reproduction instructions below still refer to their recorded branch revisions.

The paced **1 ms median objective remains unmet** on this Apple M3. The HEVC
scanner is a measurable, bounded preparation optimization; the scheduling,
dispatch, parser-state, cold-start and encoder experiments are separate branches
so their costs and benefits can be reviewed independently. No experiment changes
the production defaults on `codex/native-apple-video`.

This report extends the [cadence investigation](optimization-investigation.md).
The library remains in this repository. Moonlight Qt remains on its **local-only**
`codex/native-apple-video` branch at `d1279085`; no Qt branch is pushed.

## What to prioritize

1. **Review the HEVC scanner for adoption.** It repeatedly saves 22–28 µs before
   VT, with dedicated malformed-input and sanitizer coverage. This is the
   clearest immediate production gain, although it is far smaller than the gap
   to 1 ms.
2. **Investigate the remaining VT/cadence gap and representative stream tails.**
   Use explicit per-frame profiling alignment and real game-stream captures.
   Existing throughput results demonstrate lower latency under a different
   workload, but QoS, dispatch mode and tile layout did not turn that into a
   paced 1 ms result. The current synthetic 4K AV1 keyframes remain expensive.
3. **Consider parser-state cleanup after the scanner.** Its sub-3-µs preparation
   saving is real but lower priority. Keep the changes separately reviewable.
4. **Keep pacing as an optional harness control.** A short final polling window
   improves arrival precision at a measured CPU cost; it has not been tested as
   a Qt worker optimization.
5. **Retain the other branches as diagnostic evidence.** Do not promote sync
   delivery, a QoS policy, larger pools, a capability-query bypass or a new tile
   default on these mixed/negative results. Startup needs further lifecycle
   work; a single control failure is not proof that bypass fixes it.

## Measured baseline, including 4K60

All values are milliseconds and are the median of three per-run percentiles,
not pooled percentiles. These are the unchanged baseline runs in the main screen.
Public AU latency starts at the scheduled complete-AU availability and ends at
the public callback's `sink_entry_ns`; it includes scheduler lateness and queueing.
VT latency starts immediately before the decode call and ends at the first
instruction of the VT callback. It includes API/driver work and callback delivery,
and does not isolate the hardware engine.

| Stream | VT p50 | VT p95 | VT p99 | Public AU → output p50 |
| --- | ---: | ---: | ---: | ---: |
| AV1 SDR8, 1920×1080 at 120 fps | 1.593 | 1.820 | 5.968 | 1.839 |
| HEVC Main, 1920×1080 at 120 fps | 1.544 | 1.921 | 2.524 | 1.832 |
| AV1 SDR8, 3840×2160 at 60 fps | 2.708 | 2.883 | 17.208 | 2.999 |
| AV1 HDR10, 3840×2160 at 60 fps | 2.868 | 3.044 | 17.997 | 3.120 |
| HEVC Main, 3840×2160 at 60 fps | 2.835 | 3.310 | 5.963 | 3.149 |
| HEVC Main10/HDR, 3840×2160 at 60 fps | 2.763 | 3.287 | 5.944 | 3.081 |

The four new 4K fixtures contain 120 real 8/10-bit 4:2:0 frames each, with
periodic random-access pictures, motion, detail and frame IDs. Each passed native
hardware validation, IOSurface/Metal compatibility and retained-buffer ownership
checks. Independent software decoding of the same compressed pictures matched
all visible native luma/chroma samples exactly: **1,492,992,000 samples per case,
maximum and mean code error zero**. Pixel comparison ran separately from timing.
These are synthetic headless decode tests; display refresh, visible HDR, live
host interoperability and rendered game latency are not established by them.

## Decoder and scheduler controls

### HEVC scanner: useful preparation saving

The isolated change uses bounded `memchr` start-code candidates and reserves the
normalized sample once. It preserves Annex-B payloads, leading/trailing zeros,
split start codes and malformed-input rejection. Median preparation changed:

| Stream | Baseline, µs | Scanner, µs | Saving, µs |
| --- | ---: | ---: | ---: |
| 1080p120 SDR | 43.230 | 15.209 | 28.021 |
| 4K60 SDR | 46.688 | 18.355 | 28.333 |
| 4K60 HDR | 40.875 | 18.709 | 22.166 |

This work precedes the VT timer. It cannot directly eliminate the much larger
paced VT interval. Changes in VT medians across separate binaries also include
run variation; attribute the reliable saving to preparation. Release and
ASan/UBSan parser/lifecycle tests passed, including 19,753 bitstream checks.

### Parser state: small follow-up

Preparing the already-detached parser candidate removes one redundant clone
without weakening transactional admission. Preparation saves approximately
0.3–0.5 µs for AV1 and 1.4–2.3 µs for HEVC in this screen. There is no consistent
VT benefit. Keep this below the scanner in priority. Public rollback behavior,
configuration-only inputs and backend configuration equality remain intact;
Release and ASan/UBSan checks passed.

### QoS and synchronous delivery: no reliable path to 1 ms

The unchanged replay submitting thread already reports requested
`QOS_CLASS_USER_INTERACTIVE` in this launch environment. Explicit user-initiated
or user-interactive QoS produced mixed results across cases. Callback threads
report requested QoS as unspecified; that getter does not establish their
effective QoS overrides or CPU placement. This does not measure the live Qt
worker's scheduling policy.

Synchronous delivery did not improve the objective. At 1080p, asynchronous versus
synchronous VT medians were 1.580/1.671 ms for AV1 and 1.573/1.617 ms for HEVC.
The synchronous call blocks the submitting thread. It remains a diagnostic,
with no per-frame waits added to the normal asynchronous path. Its return
timestamps are recovered after timing when callbacks occurred inline; callback
before return is counted explicitly instead of subtracting unsigned timestamps.
The bounded recorder's count and overflow checks passed.

### Pacing: arrival precision has a CPU cost

The replay scheduler's final bounded polling window reduces wake-up lateness,
while preserving the original absolute arrival deadlines. At 4K60, a 250 µs
window reduced median scheduler lateness from roughly 238–258 µs to 0.15–0.18 µs.
This improves caller-visible arrival latency; it does not establish faster VT
decoding. A 1,000 µs window costs more CPU without a consistent decode benefit.

| 4K60 stream | Sleep CPU, % of one core | 250 µs window | 1,000 µs window |
| --- | ---: | ---: | ---: |
| AV1 SDR | 4.30 | 4.52 | 8.34 |
| AV1 HDR | 4.12 | 4.73 | 8.01 |
| HEVC SDR | 4.92 | 5.14 | 9.02 |
| HEVC HDR | 4.76 | 5.19 | 9.31 |

CPU comes from process CPU time over the timed window. Busy-wait wall time
includes descheduling and must not be presented as CPU utilization. Qt receives
network AUs through its input worker rather than this periodic fixture timer, so
this result supports an optional harness control, not a live-client speed claim.

## AV1 tile layout and keyframe tails

All nine layouts passed hardware correctness, and the independent libaom
`AOMD_GET_TILE_INFO` probe verified the actual 1/2/4-column, one-row geometry of
every frame. Twenty-seven ten-second paced runs completed **21,600/21,600 frames**.
The same decoder binary was used throughout. Values below are VT p50/p95/p99
in milliseconds, each a median of three per-run percentiles.

| Stream | 1 column | 2 columns, existing default | 4 columns |
| --- | ---: | ---: | ---: |
| 1080p120 SDR | 1.592 / 1.838 / 5.959 | 1.562 / 1.826 / 5.944 | 1.575 / 1.811 / 5.843 |
| 4K60 SDR | 2.791 / 3.091 / 17.430 | 2.775 / 3.057 / 17.334 | 2.741 / 2.914 / 17.217 |
| 4K60 HDR | 2.869 / 3.105 / 18.010 | 2.880 / 3.042 / 18.032 | 2.942 / 3.268 / 18.277 |

Four columns reduce the 4K SDR median by a paired 0.032 ms (1.15%), but one of
three pairs regressed. The HDR results do not reproduce that benefit. Random-access
VT medians at 4K remain roughly 17.5 ms for SDR and 18.1–18.6 ms for HDR across
layouts. Increasing tiles does not remove the keyframe tail in these fixtures.

Fixed CQ 12, GOP 60, source pattern, dimensions, depth, AOM version and other
encoder options are held constant. Fixed CQ does not guarantee equal bitrate or
quality; these are changes relative to two columns:

| Stream | 1-column bitrate / luma PSNR change | 4-column bitrate / luma PSNR change |
| --- | ---: | ---: |
| 1080p120 SDR | +2.593% / +0.127 dB | −1.966% / +0.140 dB |
| 4K60 SDR | −0.025% / −0.320 dB | −2.955% / +0.640 dB |
| 4K60 HDR | +0.691% / +0.032 dB | +2.952% / −0.443 dB |

The default encoded payload rates are about 2.236, 2.229 and 2.397 Mbps,
respectively. These simple patterns are not representative high-bitrate game
captures. PSNR is the encoder reconstruction versus source in encoded sample
values, not a perceptual HDR score or an independent decoder correctness test.
Keep the existing layout default; a more representative stream-complexity study
has greater value than promoting a small mixed result from this tile sweep.

The local public SDK exposes no HEVC slice/tile setter for this experiment, and
three hardware compression-session property queries were preserved. HEVC layout
tuning is **unavailable through the public control tested**; no private key,
H.264 slice option or replacement software encoder was used to manufacture a
comparable result. The ordinary 4K HEVC tests still passed.

## Output-pool minimum

The supported public pool minimum was tested at default/no setter, 3 and 6
buffers. Both codecs read back 3/6 correctly and reported a shared pixel-buffer
pool. All six 4K HDR correctness gates and eighteen paced runs passed, with
**6,480/6,480 frames** displayed. VT p50/p95/p99 in milliseconds:

| 4K60 HDR codec | Default | Minimum 3 | Minimum 6 |
| --- | ---: | ---: | ---: |
| AV1 | 2.996 / 3.402 / 17.821 | 3.061 / 3.414 / 18.093 | 2.894 / 3.162 / 18.094 |
| HEVC | 2.649 / 3.124 / 5.828 | 2.737 / 3.246 / 5.772 | 2.766 / 3.204 / 6.004 |

AV1 minimum 6 has a paired median improvement of 0.102 ms, but one of three
pairs regresses and p99 does not improve. HEVC does not reproduce the median
benefit. Baseline medians themselves vary substantially across repetitions
(AV1 2.751–3.010 ms; HEVC 2.631–2.858 ms). This is insufficient to select a
larger pool as the default. The setting is applied after session creation and
therefore cannot remove the earlier session-creation interval. Memory overhead
was not measured; the timing sink does not retain output buffers like a renderer.

## Cold initialization

Stage tracing across 21 fresh processes places 98.9–99.6% of the elapsed time before
the first VT submission in the capability query plus `VTDecompressionSessionCreate`.
The capability query costs roughly 10–15 ms and session creation roughly
38–49 ms. Format creation, property handling and sample creation are much smaller.
This identifies initialization, but does not prove either stage can be removed.

A separate branch bypasses only the preliminary capability query for
hardware-required creation. It preserves OS availability guards, the required
hardware session option and actual hardware/output validation. In **56 fresh
processes, four balanced pairs per case**, the apparent query saving moves into
session creation: capability reductions of 10.1–14.4 ms accompany creation
increases of 9.5–15.5 ms. All 7,680 offered frames completed and displayed.

| Stream | First public output, baseline → bypass, ms | Median paired change, ms |
| --- | ---: | ---: |
| 1080p AV1 SDR | 56.176 → 56.118 | −0.462 |
| 1080p HEVC SDR | 52.888 → 53.155 | +0.353 |
| 4K AV1 SDR | 83.123 → 82.936 | +0.253 |
| 4K AV1 HDR | 84.721 → 86.356 | +2.118 |
| 4K HEVC SDR | 70.909 → 71.991 | +0.850 |
| 4K HEVC HDR | 70.739 → 72.838 | +1.142 |
| 3440×1440 AV1 HDR | 76.059 → 76.216 | −0.452 |

The paired statistic is bypass minus baseline within each repetition; it need
not equal the difference between the two marginal medians. These measurements
start at first admission and end at the public callback, in fresh-process
throughput mode. They are not steady paced or renderer latency. No additive
startup saving is established. All ultrawide first-output measurements remain
above the reference 16-frame/240 fps age budget of 66.667 ms. The initial
42-run pilot had an unbalanced order and is excluded from these conclusions.
[Balanced cold evidence](evidence/experiment-direct-cold.json) preserves stages,
all pairs, exact CSV joins and the pilot distinction.

A separate paced 3440×1440 HDR/240 fps follow-up used the original queue depth
16, six seconds and four alternating pairs. Bypass passed 4/4 runs; baseline
passed 3/4. The failed baseline run displayed 1,381/1,440 AUs, with 58 scheduler
drops, one failed/cancelled/dropped completion and one reset. All 1,382 accepted
AUs received terminal completions. Across the eight runs, 11,461/11,520 offered
AUs displayed. These failures remain in the evidence; the failed pair is
excluded only from the qualified timing comparison. The three passing pairs
show a **0.027 ms median VT regression** for bypass. Four small trials and the
larger cold experiment do not establish a reliable startup fix.

The remaining startup lead is earlier initialization when valid stream
configuration becomes available. That requires a separate session-lifecycle
design and explicit measurement of where the cost moves. A generic capability
cache or a larger queue is not demonstrated here as a latency fix.

## Qt handoff inspection

The native adapter performs AVFrame wrapping and HDR metadata allocation on the
handoff worker, then passes frames to the existing Pacer/renderer. Its input and
handoff workers are distinct. All of this occurs after the VT callback timestamp.
Consequently, wrapper allocation or renderer
work cannot directly explain time already measured before VT callback entry.
They can affect caller/presentation latency, which needs a separate measurement.

The current offline application probe exercises ownership and renderer input;
it returns before the real input/handoff workers start. Those workers depend on
common-c and the active `Session`, so simply disabling test-only mode would not
be a valid server-free worker benchmark. A fixture input seam with an isolated
session/overlay dependency, or a real host session, is needed to measure the
full path. No live worker, renderer or presentation improvement is claimed, and
no Qt optimization is promoted on the basis of the headless tests.

## Separate System Trace diagnostic

System Trace captured the unchanged 1080p AV1 paced path and a throughput
control outside all performance comparisons. Paced samples show XPC/VideoToolbox
pixel-buffer, IOSurface and attachment work. The receive worker's observed
runnable intervals have median 10.959 µs and p95 14.875 µs; aggregate blocked
time also includes waiting between frames and cannot be called decode delay.
The main submitting API stack was not available in these samples, and no
calibrated anchor aligns Instruments timestamps with per-frame `CLOCK_UPTIME_RAW`
timestamps. This trace does not separate execution/wait/descheduling within an
individual VT call.

The throughput trace exported zero target CPU samples and only 37 target state
records near exit, so it is **insufficient as a profiling comparison**. Both
traces report windowed five-second recording; actual exported coverage is retained
in [profile evidence](evidence/experiment-profile.json). Their 1,200/18,000
replay outputs passed accounting, but instrumented latency is diagnostic only
and is excluded from the performance tables. A future per-frame signpost/clock
alignment experiment would be needed before assigning the cadence gap to a
specific scheduler or driver mechanism.

## Branches and reproduction

All decoder branches are independently reviewable against
`codex/native-apple-video` (`d0bd4a1`). The direct-session branch includes the
cold-start diagnostics as a dependency. The comparison branch contains runners
and evidence, without merging experimental production changes.

| Branch | Purpose | Recorded implementation revision |
| --- | --- | --- |
| [codex/experiment-comparison](https://github.com/NickMagic25/moonlight-apple-decoder/tree/codex/experiment-comparison) | Shared runners, results and priorities | This report |
| [codex/experiment-qos](https://github.com/NickMagic25/moonlight-apple-decoder/tree/codex/experiment-qos) | Requested submitting-thread QoS | `58373d4` |
| [codex/experiment-vt-sync](https://github.com/NickMagic25/moonlight-apple-decoder/tree/codex/experiment-vt-sync) | Async/sync diagnostic and exact call tracing | `c8b660a` |
| [codex/experiment-pacing](https://github.com/NickMagic25/moonlight-apple-decoder/tree/codex/experiment-pacing) | Bounded scheduler polling and CPU accounting | `d3aa3e5` |
| [codex/experiment-hevc-scan](https://github.com/NickMagic25/moonlight-apple-decoder/tree/codex/experiment-hevc-scan) | Bounded scanner and normalized allocation | `36ef094` |
| [codex/experiment-parser-state](https://github.com/NickMagic25/moonlight-apple-decoder/tree/codex/experiment-parser-state) | Remove redundant isolated-state clone | `f1c59a2` |
| [codex/experiment-encoder-layout](https://github.com/NickMagic25/moonlight-apple-decoder/tree/codex/experiment-encoder-layout) | Tile fixtures, quality and geometry verification | `d72fd14`, then docs-only `8766b74` |
| [codex/experiment-cold-start](https://github.com/NickMagic25/moonlight-apple-decoder/tree/codex/experiment-cold-start) | Session stages and pool minimum 0/3/6 | `51017be` |
| [codex/experiment-direct-session](https://github.com/NickMagic25/moonlight-apple-decoder/tree/codex/experiment-direct-session) | Isolated preliminary-query bypass | `345d4a8` |

Use a fresh checkout of the comparison branch. Build the unchanged baseline as
described in the README. The matrix expects each experiment in
`build-experiments/wt-<suffix>` with its Release binary at `build/mav-replay`:

```sh
git fetch origin
for suffix in qos vt-sync pacing hevc-scan parser-state encoder-layout cold-start direct-session; do
  git worktree add --detach "build-experiments/wt-$suffix" "origin/codex/experiment-$suffix"
  cmake -S "build-experiments/wt-$suffix" -B "build-experiments/wt-$suffix/build" \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0
done
# The synchronous diagnostic is disabled at build time unless explicitly enabled.
cmake -S build-experiments/wt-vt-sync -B build-experiments/wt-vt-sync/build -DMAV_EXPERIMENT_VT_DISPATCH=ON
for suffix in qos vt-sync pacing hevc-scan parser-state encoder-layout cold-start direct-session; do
  cmake --build "build-experiments/wt-$suffix/build" --parallel 4
  ctest --test-dir "build-experiments/wt-$suffix/build" --output-on-failure
done
```

Generate fixtures and run correctness before any performance comparison. Existing
1080p and ultrawide fixture commands are in [fixtures](fixtures.md) and
[benchmarks](benchmarks.md). The added 4K60 cases are reproducible with:

```sh
./scripts/bootstrap-aom.sh
for codec in av1 hevc; do
  for variant in sdr8 hdr10; do
    build/mav-fixture --codec "$codec" --variant "$variant" \
      --width 3840 --height 2160 --fps 60 --frames 120 --gop 60 \
      --aomenc "$PWD/.local/aom-build/aomenc" \
      --output "fixtures/generated/$codec-$variant-3840x2160p60-120"
  done
done
python3 scripts/experiment-matrix.py --phase correctness --results-dir results/repeat-gates
python3 scripts/experiment-matrix.py --phase timed --seconds 6 --repetitions 3 --results-dir results/repeat-screen
```

For AV1 layouts, use the encoder-layout branch's documented plan, generation,
PSNR and `--require-geometry` workflow first; store its plan at
`results/experiment-preparation/encoder-plan.json`, or pass `--plan` explicitly.
The replay script only decodes those saved fixtures:

```sh
python3 scripts/experiment-encoder.py --phase correctness --results-dir results/repeat-encoder-gates
python3 scripts/experiment-encoder.py --phase timed --seconds 10 --repetitions 3 --results-dir results/repeat-encoder
python3 scripts/experiment-matrix.py --phase cold --repetitions 4 \
  --cases 1080-av1-sdr,1080-hevc-sdr,4k-av1-sdr,4k-av1-hdr,4k-hevc-sdr,4k-hevc-hdr,ultrawide-av1-hdr \
  --settings direct-0,direct-1 --results-dir results/repeat-direct-cold
python3 scripts/experiment-matrix.py --phase correctness \
  --cases 4k-av1-hdr,4k-hevc-hdr --settings pool-0,pool-3,pool-6 --results-dir results/repeat-pool-gates
python3 scripts/experiment-matrix.py --phase timed --seconds 6 --repetitions 3 \
  --cases 4k-av1-hdr,4k-hevc-hdr --settings pool-0,pool-3,pool-6 --results-dir results/repeat-pool
python3 scripts/experiment-matrix.py --phase timed --seconds 6 --repetitions 4 \
  --cases ultrawide-av1-hdr --settings direct-0,direct-1 --queue-depth 16 --results-dir results/repeat-direct-startup
```

Runners refuse a nonempty result directory, preserve exact commands and return
failure for failed or malformed outcomes. They do not install, build or encode
during replay. The comparison analyzer independently reconstructs steady VT
counts/p50/p95/p99 from CSV before deriving public-callback and picture-type
timings. The separate cold evidence retains first-frame stage joins; empty
steady distributions from a short cold run are not zero-latency results.

The runner/analyzer regression checks use synthetic results, not mock performance:

```sh
python3 tests/experiment_runners.py -v
python3 tests/experiment_analysis.py -v
python3 scripts/summarize-experiments.py \
  --input results/experiment-screen results/experiment-encoder-screen results/experiment-pool results/experiment-direct-startup \
  --output docs/evidence/experiment-comparison.json
```

Thirty-six runner scenarios and nineteen analyzer cohorts verify invalid-output
preservation, failed accounting, known versus unknown totals, ordering and
qualification of passing pairs. A `FAIL` JSON result cannot pass the runner
merely because its process exited zero. Malformed raw files are preserved rather
than replaced with fabricated counts.

## Method and evidence

All experiments use Apple M3 / Mac15,3, macOS 26.6.2, SDK 26.5, Release arm64,
hardware-required session creation and verified hardware output. Runs are serial;
builds, encoding, pixel comparison and profiling occur outside performance runs.
The main screen uses three repetitions of six seconds, two frames in flight,
queue depth 32, one continuous session and 120 warmup AUs. The first successful
output of each generation is also excluded from steady timing distributions.
All frames, including warmup and startup, remain in outcome accounting.

The main screen completed **189 runs and 90,720/90,720 frames**. Its saved order
rotates settings and reverses alternate repetitions; this is a screening order,
not complete positional balance across its 10/11 settings. Subsequent two-setting
comparisons alternate order and three-setting comparisons use three rotations.
Collections and their ordering are preserved separately in the evidence.
Short screens contain few random-access frames in their p99 population; treat
tails as observations on these saved streams rather than universal estimates.
Per-phase percentiles are not additive. Nominal thermal-state snapshots cannot
establish hardware clock behavior during a call.

| Paced collection | Passed / total runs | Displayed / offered AUs |
| --- | ---: | ---: |
| Broad screen, six cases | 189 / 189 | 90,720 / 90,720 |
| Encoder layout, three cases | 27 / 27 | 21,600 / 21,600 |
| Output pool, two HDR cases | 18 / 18 | 6,480 / 6,480 |
| Original startup queue, ultrawide HDR | 7 / 8 | 11,461 / 11,520 |
| Total | **241 / 242** | **130,261 / 130,320** |

Cold-process studies, 102 branch hardware correctness gates, four full 4K
reference comparisons and instrumented traces are separate from this paced
table. None of the paced experiments achieved a 1 ms VT median. Findings are
specific to this machine, these short runs and these streams; physical iOS/tvOS
performance, longer thermal confirmation of candidate changes, and live Qt
presentation remain unmeasured in this experiment set.

[Full comparison evidence](evidence/experiment-comparison.json) retains commands,
source/binary/fixture hashes, all outcomes, per-run distributions, paired changes,
CPU observations and trace reconstruction. [Preparation evidence](evidence/experiment-preparation.json)
retains correctness gates, independent 4K references, actual tile geometry,
encoder settings/quality and supported HEVC property queries.
[Cold-stage evidence](evidence/experiment-cold.json) preserves the separate
21-process stage measurement. Raw CSV/JSON and generated fixtures remain locally
under ignored `results/` and `fixtures/generated/`; large pixel data is not
committed. Missing values remain unavailable, and failed runs cannot qualify
for a passing paired improvement.
