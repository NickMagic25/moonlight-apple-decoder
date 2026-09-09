# YAML decoder tests and paired comparisons

`scripts/compare-decoders.py` runs the same encoded access units and replay
settings through one or two decoder builds. It prepares all fixtures before
timing, checks correctness, then alternates baseline/candidate order for each
repetition. The output includes raw frame CSVs, native JSON, commands, fixture
bytes and hashes, build/environment provenance, a Markdown report, aggregate
JSON, and JUnit XML. Explicit-bitrate noise fixtures also require an independent
software reference for full-frame correctness checks. The same command runs
locally and on a physical CI runner.

The [96-case Mbps validation](bitrate-matrix-validation.md) includes the
generated Markdown and JSON reports, measured bitrate coverage, full-frame
correctness evidence, and preserved delivery failures.

This is a headless decoder test. It measures hardware decoding and delivery to
the replay client's callback. Display refresh, render/presentation latency,
network transport, audio, input latency, and a live Sunshine session require
separate client integration tests. A configured 240 fps stream does not prove
240 Hz presentation on a monitor.

## Configuration

Install the pinned YAML dependency into a local virtual environment:

```sh
python3 -m venv .local/benchmark-venv
.local/benchmark-venv/bin/python -m pip install -r scripts/requirements-benchmarks.txt
```

The supplied configurations are:

| File | Coverage |
| --- | --- |
| [`benchmarks/bitrate-matrix.yaml`](../benchmarks/bitrate-matrix.yaml) | All six resolution/frame-rate modes, AV1/HEVC, SDR/HDR10, and 50/100/250/350 Mbps encoder targets; 96 cases |
| [`benchmarks/full-matrix.yaml`](../benchmarks/full-matrix.yaml) | 1080p60/120, 3440×1440p120/240, and 4K60/120; AV1/HEVC and SDR/HDR10; 24 cases |
| [`benchmarks/full-matrix-q32.yaml`](../benchmarks/full-matrix-q32.yaml) | The two AV1 3440×1440p240 cases with additional startup arrival-age headroom |
| [`benchmarks/smoke.yaml`](../benchmarks/smoke.yaml) | Small AV1/HEVC streams that exercise an explicit encoder bitrate target |
| [`benchmarks/toolchain-confirmation.yaml`](../benchmarks/toolchain-confirmation.yaml) | Six balanced 20-second pairs for the three latency flags from the initial toolchain comparison |

For example, this creates the six requested resolution/rate combinations with
both codecs, both dynamic ranges, and each requested bitrate target: 96 cases.
Bitrates use decimal megabits per second (Mbps).

```yaml
schema_version: 1
defaults:
  codec: [av1, hevc]
  dynamic_range: [sdr, hdr10]
  bitrate_mbps: [50, 100, 250, 350]
  gop: 60
  decoder:
    inflight: 2
    queue_depth: 16
    power: -1
    consumer_delay_ms: 0
    jitter_us: 0
    seed: 7
run:
  seconds: 10
  repetitions: 3
  warmup_frames: 120
  timeout_seconds: 180
thresholds:
  decoded_fps_ratio: 0.99
  bitrate_tolerance_pct: 20
  latency_relative_pct: 5.0
  latency_absolute_ms: 0.1
cases:
  - name: 1080p
    resolution: 1920x1080
    fps: [60, 120]
  - name: ultrawide
    resolution: 3440x1440
    fps: [120, 240]
  - name: 4k
    resolution: 3840x2160
    fps: [60, 120]
```

Lists expand into a Cartesian product within each case. A case overrides
defaults; nested `decoder` settings preserve other defaults. Width and height
may be written separately instead of `resolution`. Omitted fixture frame count
is `max(120, fps)`; `frames` sets an explicit count. The runner continuously
loops that sequence long enough to cover the requested duration, rounding up
to whole fixture loops. `run.seconds` is therefore a minimum scheduled duration;
the per-run timeout must also cover that rounded duration and decoder drain.
Longer pattern-compatible fixtures can exercise more of the generated sequence.
Content-sensitive changes need additional representative-content validation.

| Setting | Applied behavior |
| --- | --- |
| `resolution`, or `width` and `height` | Actual encoded dimensions; positive, supported even dimensions |
| `fps` | Encoder timing and paced replay arrival rate |
| `codec` | Native `av1` or `hevc` hardware path |
| `dynamic_range` | `sdr` is 8-bit BT.709; `hdr10` is 10-bit BT.2020/PQ with HDR metadata |
| `bitrate_mbps` | Encoder target in decimal megabits/second, from `0.001` to `1000` inclusive in `0.001` Mbps increments; `null` retains the existing fixture generator's defaults |
| `gop` | Encoded random-access/keyframe interval in frames |
| `frames` | Number of encoded access units in the fixture before looping |
| `decoder.inflight` | Maximum admitted, unresolved access units |
| `decoder.queue_depth` | Maximum scheduled-arrival age, expressed in frame intervals; it is not a render queue |
| `decoder.power` | VideoToolbox power-efficiency hint: `-1` leaves the system default, `0` requests the non-power-efficient preference |
| `decoder.consumer_delay_ms` | Retention delay in the correctness sink; paced timing does not simulate a delayed renderer |
| `decoder.jitter_us` and `seed` | Reproducible synthetic arrival jitter and its seed |

Use numeric YAML values, for example `bitrate_mbps: 50` or
`bitrate_mbps: 50.125`; values with unit suffixes are not accepted. One Mbps is
1,000,000 bits/second. The native fixture generator uses `--bitrate-mbps` with
the same units and precision. The old `bitrate_kbps` YAML key is rejected so an
old value cannot silently become a target 1,000 times larger.
Previously captured kbps fixture manifests and `plan.json` archives remain
readable. Analysis converts their explicitly labeled units in memory and leaves
the archived inputs unchanged.

Requested bitrate and measured payload bitrate are separate evidence fields,
both expressed in Mbps. AV1 CBR and capped HEVC average-bitrate control target a
stream rate; neither guarantees that a short synthetic fixture achieves
the requested bitrate. A case labeled 350 Mbps means the encoder was asked for
350 Mbps, and its measured rate must be checked before claiming that the
decoder sustained that input rate. Changing bitrate regenerates the stream;
baseline and candidate always receive the same saved bytes. The historical
full toolchain matrix keeps `bitrate_mbps: null` to retain the earlier test's
encoding policy. Fixtures with an explicit bitrate use deterministic textured
luma and a frame-ID strip. The framework requires independent full-frame
software reference validation for this noise profile: lossy encoding of this
content cannot be validated by assuming that its decoded pixels still match
the original marker pattern. Both builds receive the same compressed bytes and
the same software-decoded reference. This is still synthetic content and does
not establish behavior for every game.
The [fixture documentation](fixtures.md) records the encoder buffers, caps,
content profile, and unchanged legacy encoder policy.

`thresholds.bitrate_tolerance_pct` sets the allowed deviation of measured payload
bitrate from the requested target. It accepts `0` through `100` and defaults to
`20`, meaning the rate must be within ±20% of the target. A 350 Mbps case must
therefore measure between 280 and 420 Mbps to establish bitrate coverage under
the default gate. A case whose decode checks pass but whose encoded rate falls
outside that range is `INCONCLUSIVE`, and the overall comparison cannot pass.
The reports preserve the successful decode measurements separately from the
failed bitrate-coverage gate. A `null` bitrate target skips this gate because no
specific encoded rate was requested.

An optional `fixture` path names an existing manifest relative to the YAML file.
Its metadata must match the declared stream settings; it is validated and copied
into the evidence directory. An externally prepared fixture must use a supported
harness content profile, sequential frame IDs, one displayed output per access
unit, the requested exact GOP, and the supported frame-rate timebase. Legacy
fixtures use the synthetic marker checks; the framework's archived noise
fixtures require a software reference instead. Arbitrary recorded Sunshine or
game streams are not supported by this comparison path. Such captures need a
separate content-validation strategy. Fixture identity includes
the validated manifest and payload hashes; a bitrate label alone does not
establish content or encoding equivalence.

Unknown keys, duplicate keys, invalid types/ranges, and unsupported options fail
configuration validation. Client options that the harness cannot apply are not
silently accepted. In particular, H.264, 4:4:4, Dolby Vision, display/HDR output
mode switching, VSync, audio, and network bitrate negotiation are outside this
runner's current coverage.

## Local execution

Build Release tools with the same compiler, SDK, deployment target, optimization
flags, and experimental settings for both revisions. Build and encode before
running timed work; do not run another benchmark or a compiler on the device
at the same time. Keep the Mac on AC power with a stable thermal state.

For an explicit-bitrate comparison, first provide an existing FFmpeg development
prefix containing `include/` and `lib/`, with software decoders for both AV1 and
HEVC. `MAV_FFMPEG_ROOT` builds the optional `mav-reference-decode` helper; it adds
no FFmpeg dependency to the production decoder. For the candidate:

```sh
cmake -S . -B build-candidate -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DBUILD_TESTING=ON -DMAV_BUILD_TOOLS=ON \
  -DMAV_VT_EXPERIMENTS=OFF -DMAV_SANITIZE=OFF \
  -DMAV_FFMPEG_ROOT=/path/to/ffmpeg-development-prefix
cmake --build build-candidate --parallel 3
ctest --test-dir build-candidate --output-on-failure
./scripts/bootstrap-aom.sh
```

Configure an independent baseline source checkout with the same options, using
its own build directory. Do not change the baseline's language standard: the
source revision supplies that setting. A toolchain migration comparison should
use the same installed compiler for both language modes. A change of compiler
version or SDK is a different experiment and must be identified as such. Only
one reference helper is needed; the candidate helper can supply the reference
for both decoder builds. The FFmpeg option can be omitted when testing only
legacy marker fixtures with null bitrate targets.

Validate YAML without requiring binaries or hardware:

```sh
.local/benchmark-venv/bin/python scripts/compare-decoders.py \
  --config benchmarks/bitrate-matrix.yaml --dry-run
```

Run a paired comparison, substituting the independent baseline build path:

```sh
.local/benchmark-venv/bin/python scripts/compare-decoders.py \
  --config benchmarks/bitrate-matrix.yaml \
  --candidate-build build-candidate \
  --baseline-build /path/to/baseline-build \
  --fixture-build build-candidate \
  --reference-tool build-candidate/mav-reference-decode \
  --aomenc .local/aom-build/aomenc \
  --results-dir results/comparison-001
```

Omit `--baseline-build` for a candidate-only correctness/performance run. That
run cannot establish regression against an earlier revision. Optional
`--candidate-revision` and `--baseline-revision` labels are preserved alongside
the detected source revision, source hash, executable hash, and build settings;
a label is not proof that a binary was built from that commit.

`--reference-tool` defaults to `mav-reference-decode` in `--fixture-build`.
The runner uses the helper's CMake cache to locate the FFmpeg runtime libraries
when `DYLD_LIBRARY_PATH` is not already set. If the helper cannot supply the
required software decoder, reference validation fails before timed comparison;
it cannot substitute another VideoToolbox decode for an independent reference.

For each noise fixture, the runner generates one raw planar YUV reference and
checks every visible Y, U, and V sample from both builds against it. Maximum
allowed differences are 2 code values for 8-bit and 8 for 10-bit output; exact
expected sample counts are also required. After both correctness checks, the
large raw reference is deleted before preparing the next case. Reserve at
least 6 GB of scratch space for one reference with the supplied modes, plus
space for compressed fixtures and reports; larger custom fixtures may need
more. All reference generation and validation finish before serial timed
replay starts, so software decoding does not contend with the performance run.

Each new run uses a fresh results directory so previous evidence survives.
`--prepare-only` validates and prepares fixtures without timed replay; its output
is not resumable run state, so use another results directory for a timed run.
`--analyze-only --results-dir results/comparison-001` rebuilds reports from an
existing results directory. The normal command handles preparation and
measurement in one invocation. The 96-case bitrate matrix uses three 10-second
repetitions per build: 576 timed trials and about 96 minutes of paced replay,
in addition to preparation and correctness checks. The historical 24-case
matrix takes about 24 minutes of paced replay with the same settings.

## Reading the evidence

Every normal comparison writes both human-readable `report.md` and
machine-readable `results.json` into the selected `--results-dir`, including
comparisons that complete with failed or incomplete cases. `junit.xml` provides
CI test results from the same recorded runs. The Markdown report includes each
case's requested and measured bitrate, bitrate-coverage result, status, and
decode-latency comparison; the JSON retains the structured settings,
measurements, and comparison gates, including bitrate deviation and the applied
tolerance.

The report also includes Moonlight decode-time means, per trial and per case.
`moonlight-decode-times.json` supplies their sums, sample counts, stream settings,
and baseline/candidate values; new runs also retain per-trial means under
`cases[].runs[].derived.moonlight_decode_time` in `results.json`.

`--dry-run` only validates and expands configuration, and `--prepare-only`
prepares fixtures; neither produces a timed comparison report. Invalid command
arguments or configuration fail before a comparison starts.

`plan.json` records the expanded settings and fixture identity; per-build
environment records capture compiler/SDK, build configuration, source and
executable identity, model, OS, and power/thermal observations. Raw native JSON,
frame CSV, command logs, and fixture bytes remain available for review and
reanalysis. For noise fixtures, the framework preserves the original manifest
and a derived validation manifest that identifies reference-based correctness,
records the original manifest hash, and points to the identical compressed
bytes. A reference sidecar preserves the software decoder command, executable
identity, library version/provenance, selected runtime library path, and raw
reference hash. Full-frame comparison counts and errors remain in the native
results. The temporary raw reference is not retained; it can be regenerated
from the preserved fixture with the recorded software toolchain. Archive the
whole results directory to preserve these relationships.

The report separates these questions:

* Did the encoded payload rate meet the requested bitrate within the configured
  tolerance?
* Did correctness and hardware validation pass, with complete output accounting
  and no rejected frames, scheduler drops, resets, or failed output?
* For noise fixtures, did both builds match the independent software reference
  across every expected sample within the allowed reconstruction difference?
* Did decoded throughput meet the configured fraction of the requested rate?
* How did steady-state VT submit-to-callback and caller-visible
  arrival-to-output latency change between the two builds?

Warmup excludes early frames from steady-state latency statistics. It does not
erase startup loss, change total output accounting, or make a failed run pass.
Cold-start timing and sustained decode latency answer different questions.

The [native Apple adapter](../integration/moonlight-qt/apple_video.cpp) displays
**Frame-ready mean (VT submit -> callback)**, rounded to three decimal milliseconds. It
accumulates `callback_ns - vt_submit_ns` for successful new, single-sample
outputs with both trace timestamps. The report uses that same arithmetic mean,
including cold/startup, warmup, and recovery outputs. A case mean pools integer
duration sums and eligible output counts across its trials; every trial includes
its own startup, so this is not one continuous client session. Dropped or
cancelled frames contribute no decode sample and remain failures in the delivery
accounting. This supplemental mean does not replace the steady-state latency
gates.

**VT submission mean (submit -> return)** separately averages
`vt_return_ns - vt_submit_ns` for successful new, single-sample outputs with valid
ordered submission/return timestamps. This measures time inside the API call;
it does not establish that decoding has completed. Both intervals start at VT
submission, so they overlap and must not be added together. Their difference
is not a hardware execution measurement. A callback can occur before the API
returns, leaving that completion without a captured return timestamp. Those
outputs retain their frame-ready samples but supply no submission sample.
Each metric therefore has its own sample count and pooled duration sum; missing
timestamps never become zeros or inferred callback values. Both counts appear
in the overlay and reports.

The existing JSON key `native_vt` retains its frame-ready meaning and values;
`native_submission` is an additional field under `moonlight_decode_time` and
the companion's per-build/per-run means. The final adapter log retains
`VT-submit-to-callback-mean-us` and adds `VT-submit-to-return-mean-us` plus both
sample counts. No completion, output ownership, admission, or decode scheduling
behavior changes with this reporting addition.

The regular Qt/FFmpeg overlay's **Average decoding time** has a broader boundary
and uses recent statistics windows. The report's separately labeled
**queue-inclusive proxy** averages recorded complete-frame scheduled arrival to
the harness output callback, including startup. It approximates that boundary
but does not measure the app's queue, output wrapping, or live statistics window.
Some FFmpeg GPU paths return an output surface before later rendering-side
synchronization confirms GPU completion. The proxy therefore does not establish
an identical readiness boundary for Intel and Apple. None of these replay
values establishes actual network or presentation latency.

To add these columns to an existing native comparison **without rerunning any
tests, builds, fixture generation, or decoding**, use the offline report command:

```sh
.local/benchmark-venv/bin/python scripts/refresh-decode-report.py \
  --results-dir results/comparison-001
```

The source directory must retain its original `results.json`, `report.md`, and
raw timed JSON/CSV files. The command verifies recorded hashes and native
results before deriving means. It preserves `results.json`, existing verdicts,
correctness evidence, and raw files byte for byte; it saves `report-original.md`
and writes an enhanced `report.md` plus `moonlight-decode-times.json`. The
companion records source/report hashes and derivation provenance. Optional
`--report-dir docs/evidence/comparison-001` writes the reports separately while
leaving the source directory untouched. Archived summaries without raw traces
cannot be refreshed this way. Unlike `--analyze-only`, this command does not
reapply comparison gates or replace the original analysis.

For VT submit-to-callback and caller-visible arrival-to-output latency, the
runner compares median, p95, and p99 separately. Each repetition supplies one
value for each statistic; samples from different repetitions are not pooled.
The gate flags a regression when the median paired increase exceeds
`max(latency_absolute_ms, baseline_median_ms * latency_relative_pct / 100)`.
The relative allowance uses the median of the baseline repetitions for that
statistic. The example therefore requires an increase greater than both 0.1 ms
and 5% of baseline before its latency gate trips.

The case statuses are `PASS`, `REGRESSION`, `BASELINE_FAILURE`, `INCONCLUSIVE`,
`INCOMPLETE`, and candidate-only `FAIL`. A baseline failure prevents a clean
regression conclusion even when the candidate passes. Missing or changed raw
evidence cannot produce a pass; non-nominal or unavailable thermal state, or
encoded bitrate outside the configured target tolerance, makes otherwise
successful timed results inconclusive. The overall result passes
only when every case passes. Any non-pass result exits with status 1;
configuration/argument errors exit with status 2, so CI does not silently ignore
an existing baseline failure or incomplete comparison.

These latency limits are explicit tolerances for this experiment. Three paired
repetitions help expose order-dependent drift but do not establish statistical
equivalence or guarantee that smaller regressions are absent. Inspect the
individual repetitions, tails, and hardware/environment records before treating
a difference near the limit as a product improvement or regression. Increase
duration, repetitions, and content variety for a release-level performance claim.

The prior AV1 3440×1440p240 experiment hit the 16-frame startup arrival-age budget
in both C++17 and C++23 builds. Reproducing that failure in both versions is an
existing limitation, not evidence that the workload passed. Run the separate
32-frame configuration to compare uninterrupted output with more startup
headroom; it does not increase the speed of the hardware decoder or change a
client default. See [the original matrix report](toolchain-matrix.md).

## CI

[Decoder tests](../.github/workflows/decoder-tests.yml) runs on pull requests,
pushes to `main`, and manual dispatch. It validates every YAML example, tests the
configuration/comparison code with Python `unittest`, builds Debug CMake tests
with assertions enabled on Linux and macOS, and runs the Swift package smoke
on macOS. The macOS job also compiles the native tools and checks encoder-process
timeout cleanup through `mav-fixture` using a sleeping fake encoder; these checks
require no VideoToolbox or Metal decode device. It selects Xcode 26.6 from the
[official `macos-26` runner image](https://github.com/actions/runner-images/blob/main/images/macos/macos-26-arm64-Readme.md).
Hosted and mock tests do not claim hardware decode performance.

[Decoder hardware comparison](../.github/workflows/decoder-benchmarks.yml) is a
manual `workflow_dispatch` job. It requires a provisioned physical Apple Silicon
Mac with the labels `self-hosted`, `macOS`, `ARM64`, and `moonlight-video`, actual
AV1 and HEVC hardware support, an accessible Metal device, a supported GitHub
Actions runner, CMake 3.23+, and the validated Xcode/Swift toolchain. Installing
the workflow does not register or provision that machine.

Preinstall `aomenc` with high-bit-depth support outside the Actions checkout,
which the checkout action cleans between jobs. Set repository Actions variable
`MAV_AOMENC` to its executable path, or make it available on the runner's `PATH`.
Optional `MAV_DEVELOPER_DIR` selects the Xcode Developer directory.
For the default bitrate matrix, set repository Actions variable
`MAV_FFMPEG_ROOT` to an existing FFmpeg development prefix outside the checkout,
including the headers, libraries, and software AV1/HEVC decoders. The workflow
fails early if an explicit-bitrate configuration is selected without this
prefix. This provisioned dependency is used only by the reference helper.
Provision dependencies and confirm hardware access before benchmarking; an SSH
or service session without the needed device access is not a successful decode
test environment.

After the workflow is available on the default branch, dispatch it with a
reviewed candidate branch, a full 40-character baseline commit SHA from this
repository, and the reviewed YAML path. Both revisions execute native build
and Python code on the physical machine: review them before dispatching. The
workflow deliberately has no PR event and does not use `pull_request_target`.
Repository runner access and any required reviewer policy should restrict this
machine to trusted code.

The workflow validates all YAML examples and runs the Python framework tests,
checks out the two exact commits, builds and tests them sequentially with the
same Release options, verifies tiny SDR/HDR fixture
generation with explicit bitrate targets and preserved import metadata, then
calls the local runner. The default configuration is the 96-case bitrate matrix;
the job allows up to six hours for builds, fixture generation, independent
reference generation, correctness checks, and the 96 minutes of paired timed
replay. All encoding and software reference work finish before timed comparison. A
workflow-wide concurrency group prevents overlapping jobs from this workflow;
keep unrelated workloads off the same device as well. Results, fixture bytes,
JUnit output, build logs, CMake caches, and compile commands upload even when
the comparison fails. Reference provenance sidecars are retained; temporary raw
references are removed after correctness validation. `report.md`, `results.json`,
and `moonlight-decode-times.json` are included in the
artifact, and the Markdown report is also copied into the job summary.
Artifacts are retained for 30 days; download or archive evidence that must last
longer. A missing runner or unsupported hardware leaves this job unable to
establish performance; portable checks cannot substitute for it.
