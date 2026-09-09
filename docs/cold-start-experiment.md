# Private cold-start diagnostic experiment

This isolated branch adds opt-in stage tracing and a documented output-pool
minimum-count experiment. No public C ABI, default session property, decode flag,
timing endpoint, packet accounting or Qt policy is changed.

```sh
./build/mav-replay --fixture /absolute/path/manifest.json --mode correctness \
  --cold-trace results/cold/default.jsonl --pool-minimum 0 --output results/cold/default
```

`--cold-trace PATH` enables tracing and starts a new JSONL file. Each configured
session, including a failed configuration attempt, produces one record when it
is invalidated. In the replay tool the final record is serialized after the timed
drain/end timestamp, during reset/destroy. A real mid-run reconfiguration emits
the previous session's record on the serialized control thread; its I/O can affect
that transition and must not be treated as uninstrumented recovery performance.
Callbacks never log or collect these stage timings. Steady frames take only a
disabled/first-attempt branch. Abrupt process death can lose an unflushed record.

Raw timestamps use `mav_monotonic_time_ns` (Apple CLOCK_UPTIME_RAW). Stages are
capability query, format creation, VT session creation, hardware readback,
supported-property query, ordinary property hints, the optional pool experiment,
and first sample creation. The first VT submit/return timestamps are copied from
the existing trace. They can join the main replay CSV exactly. Configure totals
include gaps between stages, but exclude prior-session invalidation and parser
work preceding backend configuration. Compare that total with the main CSV's
admission/preparation/first-VT timestamps to account for the whole cold path.
Capability status uses `mav_result`; other stage API statuses use OSStatus. The
property-hints interval retains the supported-dictionary status; individual
RealTime/power statuses and readbacks are separate. Missing intervals are null.

`--pool-minimum 0|3|6` requires `--cold-trace`. The default 0 performs no setter;
3/6 request `kVTDecompressionPropertyKey_OutputPoolRequestedMinimumBufferCount`
before any decode, only when listed as supported. Unsupported or failed requests
fail configuration explicitly. The record includes support, setter attempt/status,
readback status/value, and `PixelBufferPoolIsShared` status/value. A readback of -1
means unavailable, not zero. Setter success with unavailable readback is recorded
without claiming the requested count was verified. Positive pool requests use
more retained memory; no preallocation or latency improvement is assumed.

Both public pool keys are available within the project's minimum deployment
targets (minimum-count: macOS 10.9/iOS 8/tvOS 10.2). These are not private VT keys.
The diagnostic controls themselves are private environment variables consumed at
backend construction: `MAV_EXPERIMENT_COLD_TRACE`, `MAV_EXPERIMENT_POOL_MIN`, and
`MAV_EXPERIMENT_SKIP_CAPABILITY`.
Direct environment use appends instead of truncating and requires an existing
parent directory. Pool settings without a trace path are rejected. No settings
are added to the public library configuration structure.

Tracing adds first-session clock reads and two pool readbacks even for pool 0;
the latter are timed separately. Compare pool 0/3/6 with the same instrumented
binary. Verify trace records exist: serialization failures report stderr and do
not alter production teardown semantics. Cold diagnostics are separate from
steady decoding performance; no busy-spin, dummy decoding or session prewarming
is performed by this branch.

The direct-session experiment adds `--skip-capability 0|1`, default 0. An explicit
option requires `--cold-trace`. The replay CLI always overrides the private skip
environment setting with its requested value, including the default 0, so an
inherited setting cannot silently change the baseline. Direct library environment
use accepts only 0/1 and requires a trace path for 1.

With 1, configure bypasses `VTIsHardwareDecodeSupported` only for
`MAV_HARDWARE_REQUIRED`. AV1 availability remains macOS 14/iOS 17/tvOS 17. Session
creation still requires hardware; actual-session hardware readback and decoded
output validation remain mandatory. Preferred-policy sessions retain the query.
The public `mav_query_capability` API always queries normally and is unaffected by
the private setting. There is no capability cache or public ABI change.

Each session trace adds `skip_capability_requested`, `skip_capability_applied`,
`hardware_policy`, `capability_query_attempted`, and `hardware_candidate`. The
candidate is -1 when no hardware-support query ran. Applied is true only after
the API availability guard succeeds and the required-policy configure query is
bypassed. The existing `hardware` field is the actual-session readback. The
`capability` stage times the availability guard and optional query, so bypassed
records still contain a small interval rather than pretending that no code ran.
Session reset clears all observed fields but preserves the requested control.

Use fresh-process alternating 0/1 runs with this same binary and equivalent
fixtures, pool settings, and tracing. Compare total admission-to-first-public
output alongside stage timings and full frame accounting. Decoder creation does
not itself query capability. The first query may pay shared VideoToolbox startup
costs that move into session creation when bypassed; no additive 13 ms saving or
age-budget improvement is assumed. Apple's required-hardware session option
provides the enforcement needed for this experiment:
[RequireHardwareAcceleratedVideoDecoder](https://developer.apple.com/documentation/VideoToolbox/kVTVideoDecoderSpecification_RequireHardwareAcceleratedVideoDecoder).
