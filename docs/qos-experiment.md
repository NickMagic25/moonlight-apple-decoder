# Replay submitting-thread QoS experiment

This branch changes the standalone replay harness only. Production decoder policy,
the public ABI, Qt integration, decode flags, pacing deadlines, input bytes and
output accounting are unchanged.

`mav-replay --qos unchanged|user-initiated|user-interactive` selects the experiment.
The default is `unchanged`, which does not call a QoS setter. The other modes call
`pthread_set_qos_class_self_np(class, 0)` on the submitting thread immediately
before `mav_decoder_create`; the actual VT session is subsequently created by
submission on that same thread. Invalid modes or failed setter/readback operations
fail explicitly. These pthread APIs are available from macOS 10.10; this build
retains the existing macOS 11 deployment target.

The result JSON adds `qos`, containing selected mode, requested class, whether the
setter was attempted, setter status (null when untouched), before/start/end
readbacks and a histogram of completion-thread observations. Setter status is the
result of the single pre-creation call; there is no setter at the end. Readbacks
report **requested QoS**, not effective scheduler priority or temporary overrides.
`qos_stable` checks that the submitting thread's start/end readbacks agree; a
change makes the result fail without filtering recorded output/accounting.

Every public completion callback, in every mode, reads its own requested QoS
exactly once after the existing sink-entry timestamp and before the record lock.
No callback-thread QoS is changed, no callback logging or histogram allocation is
added, and no pixel checks enter timed modes. The reserved CSV record stores
`completion_qos_class`, `completion_qos_relative_priority` and
`completion_qos_get_status`. Histograms are computed after drain, distinguishing
records that do/don't contain a VT callback timestamp. Observations are at the
public library completion boundary, so synchronous/no-display/cancelled records
must not be mislabeled as measurements of an Apple-owned callback thread.

The getter occurs after both existing latency endpoints. It can still perturb
later scheduling; comparisons must use this same instrumented binary with
`--qos unchanged` as the control. Do not compare its results as an isolated QoS
effect against an older uninstrumented executable.

Example comparison settings (performance runs are coordinated separately):

```sh
./build/mav-replay --fixture /absolute/path/to/manifest.json \
  --mode paced --fps 120 --loops 10 --loop-mode continuous --warmup 120 \
  --inflight 2 --queue-depth 32 --qos unchanged --output results/qos/unchanged
```

Repeat with the other QoS values while retaining the same rate and all remaining
settings. Preserve the true offered cadence, dropped-frame accounting and the
original submit-to-callback interval. Higher priority does not establish a media
engine clock policy or guarantee lower decode latency. No busy-spin pacing option
is added; timer/power behavior should be tested as a separate controlled variable.

`ctest --test-dir build --output-on-failure` includes `replay-qos`, which checks
all modes on fresh owned threads without invoking VideoToolbox, and rejects an
invalid mode. Hardware correctness replay remains separate from timed benchmarks.
