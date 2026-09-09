# YAML decoder tests and paired comparisons

`scripts/compare-decoders.py` runs the same encoded access units and replay
settings through one or two decoder builds. It prepares all fixtures before
timing, checks correctness, then alternates baseline/candidate order for each
repetition. The output includes raw frame CSVs, native JSON, commands, fixture
bytes and hashes, build/environment provenance, a Markdown report, aggregate
JSON, and JUnit XML. The same command runs locally and on a physical CI runner.

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
| [`benchmarks/full-matrix.yaml`](../benchmarks/full-matrix.yaml) | 1080p60/120, 3440×1440p120/240, and 4K60/120; AV1/HEVC and SDR/HDR10; 24 cases |
| [`benchmarks/full-matrix-q32.yaml`](../benchmarks/full-matrix-q32.yaml) | The two AV1 3440×1440p240 cases with additional startup arrival-age headroom |
| [`benchmarks/smoke.yaml`](../benchmarks/smoke.yaml) | Small AV1/HEVC streams that exercise an explicit encoder bitrate target |
| [`benchmarks/toolchain-confirmation.yaml`](../benchmarks/toolchain-confirmation.yaml) | Six balanced 20-second pairs for the three latency flags from the initial toolchain comparison |

For example, this creates the six requested resolution/rate combinations with
both codecs and dynamic ranges, using explicit stream bitrate targets:

```yaml
schema_version: 1
defaults:
  codec: [av1, hevc]
  dynamic_range: [sdr, hdr10]
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
  latency_relative_pct: 5.0
  latency_absolute_ms: 0.1
cases:
  - name: 1080p
    resolution: 1920x1080
    fps: [60, 120]
    bitrate_kbps: 20000
  - name: ultrawide
    resolution: 3440x1440
    fps: [120, 240]
    bitrate_kbps: 60000
  - name: 4k
    resolution: 3840x2160
    fps: [60, 120]
    bitrate_kbps: 80000
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
| `bitrate_kbps` | Encoder target in decimal kilobits/second; `null` retains the existing fixture generator's defaults |
| `gop` | Encoded random-access/keyframe interval in frames |
| `frames` | Number of encoded access units in the fixture before looping |
| `decoder.inflight` | Maximum admitted, unresolved access units |
| `decoder.queue_depth` | Maximum scheduled-arrival age, expressed in frame intervals; it is not a render queue |
| `decoder.power` | VideoToolbox power-efficiency hint: `-1` leaves the system default, `0` requests the non-power-efficient preference |
| `decoder.consumer_delay_ms` | Retention delay in the correctness sink; paced timing does not simulate a delayed renderer |
| `decoder.jitter_us` and `seed` | Reproducible synthetic arrival jitter and its seed |

Requested bitrate and measured payload bitrate are separate evidence fields.
Rate control targets a long-term average and does not guarantee an exact rate
for every short synthetic fixture. Changing bitrate regenerates the stream;
baseline and candidate always receive the same saved bytes. The full toolchain
matrix keeps `bitrate_kbps: null` to retain the earlier test's encoding policy.

An optional `fixture` path names an existing manifest relative to the YAML file.
Its metadata must match the declared stream settings; it is validated and copied
into the evidence directory. An externally prepared fixture must retain the
harness's visible frame-ID pattern, sequential frame IDs, one displayed output
per access unit, the requested exact GOP, and the supported frame-rate timebase.
The correctness sink checks that synthetic pattern, so arbitrary recorded
Sunshine or game streams are not supported by this comparison path. Such
captures need a separate content-validation strategy. Fixture identity includes
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

For the candidate:

```sh
cmake -S . -B build-candidate -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DBUILD_TESTING=ON -DMAV_BUILD_TOOLS=ON \
  -DMAV_VT_EXPERIMENTS=OFF -DMAV_SANITIZE=OFF
cmake --build build-candidate --parallel 3
ctest --test-dir build-candidate --output-on-failure
./scripts/bootstrap-aom.sh
```

Configure an independent baseline source checkout with the same options, using
its own build directory. Do not change the baseline's language standard: the
source revision supplies that setting. A toolchain migration comparison should
use the same installed compiler for both language modes. A change of compiler
version or SDK is a different experiment and must be identified as such.

Validate YAML without requiring binaries or hardware:

```sh
.local/benchmark-venv/bin/python scripts/compare-decoders.py \
  --config benchmarks/full-matrix.yaml --dry-run
```

Run a paired comparison, substituting the independent baseline build path:

```sh
.local/benchmark-venv/bin/python scripts/compare-decoders.py \
  --config benchmarks/full-matrix.yaml \
  --candidate-build build-candidate \
  --baseline-build /path/to/baseline-build \
  --fixture-build build-candidate \
  --aomenc .local/aom-build/aomenc \
  --results-dir results/comparison-001
```

Omit `--baseline-build` for a candidate-only correctness/performance run. That
run cannot establish regression against an earlier revision. Optional
`--candidate-revision` and `--baseline-revision` labels are preserved alongside
the detected source revision, source hash, executable hash, and build settings;
a label is not proof that a binary was built from that commit.

Each new run uses a fresh results directory so previous evidence survives.
`--prepare-only` validates and prepares fixtures without timed replay; its output
is not resumable run state, so use another results directory for a timed run.
`--analyze-only --results-dir results/comparison-001` rebuilds reports from an
existing results directory. The normal command handles preparation and
measurement in one invocation. The entire
24-case comparison with three 10-second repetitions per build spends about
24 minutes in paced replay, in addition to preparation and correctness checks.

## Reading the evidence

`results.json`, `report.md`, and `junit.xml` summarize the same recorded runs.
`plan.json` records the expanded settings and fixture identity; per-build
environment records capture compiler/SDK, build configuration, source and
executable identity, model, OS, and power/thermal observations. Raw native JSON,
frame CSV, command logs, and fixture bytes remain available for review and
reanalysis. Archive the whole results directory to preserve these relationships.

The report separates these questions:

* Did correctness and hardware validation pass, with complete output accounting
  and no rejected frames, scheduler drops, resets, or failed output?
* Did decoded throughput meet the configured fraction of the requested rate?
* How did steady-state VT submit-to-callback and caller-visible
  arrival-to-output latency change between the two builds?

Warmup excludes early frames from steady-state latency statistics. It does not
erase startup loss, change total output accounting, or make a failed run pass.
Cold-start timing and sustained decode latency answer different questions.

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
evidence cannot produce a pass; non-nominal or unavailable thermal state makes
otherwise successful timed results inconclusive. The overall result passes
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
calls the local runner. All encoding finishes before timed comparison. A
workflow-wide concurrency group prevents overlapping jobs from this workflow;
keep unrelated workloads off the same device as well. Results, fixture bytes,
JUnit output, build logs, CMake caches, and compile commands upload even when
the comparison fails. The Markdown report is also copied into the job summary.
Artifacts are retained for 30 days; download or archive evidence that must last
longer. A missing runner or unsupported hardware leaves this job unable to
establish performance; portable checks cannot substitute for it.
