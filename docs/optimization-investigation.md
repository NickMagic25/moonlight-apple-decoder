# Investigation toward 1 ms decode latency

The strongest measured lead is **submission cadence and scheduling around VideoToolbox**, followed by stream complexity for keyframe tails. On this M3, the unchanged library decodes the same 1080p SDR streams with a median VT call-to-callback interval of about **0.67 ms under saturation**, versus **1.56–1.60 ms at 120 fps**. This demonstrates a substantial mode-dependent gap; it does **not** meet the paced 1 ms objective or identify a hardware-clock, CPU-placement or driver cause.

The implementation was saved on `codex/native-apple-video`: decoder commit `8c94197f56dd4d9a0c218c8a2d3ddaaac8b66cf5` was pushed; Qt integration commit `d1279085` is on a **local-only** branch. The diagnostic below used that decoder revision and its existing Release binary. No production decoder or Qt behavior changed during this investigation.

## Controlled cadence comparison

All 18 runs completed **108,000 / 108,000** offered, accepted, completed and displayed AUs. There were no scheduler drops, rejected frames, failed/cancelled completions, resets, display-count mismatches or trace overflows. Hardware selection was verified. This is headless decode accounting; pixel correctness and IOSurface/Metal verification were performed separately in the [earlier validation](offline-correctness-results.md), not inside these timings.

Environment: Apple M3 / Mac15,3, macOS 26.6.2, SDK 26.5, Release arm64, AC power, observed nominal thermal state. No builds, encoders, software reference decoding or profilers ran alongside timing. Both modes used the same binary, saved compressed bytes, output format, continuous session, in-flight limit two, queue depth 32 and 120 warmup AUs. There were three repetitions per case and mode, alternating mode order. Paced runs used ten fixture loops (about ten seconds); saturation used 100 loops at 1080p and 30 ultrawide (about 4.5–7.2 seconds). Different duration, occupancy and CPU activity remain limitations of this diagnostic.

Values below are milliseconds, each the median of the three per-run percentiles. They are not pooled distributions. Full distributions, counts, commands, binary/fixture/CSV hashes and environment are in [portable evidence](evidence/optimization-cadence.json).

| Stream | Mode | VT p50 | VT p95 | VT p99 | Actual decoded fps | Displayed / offered |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| AV1 SDR8, 1920×1080 | Saturation | 0.665 | 0.752 | 4.969 | 2404.12 | 36,000 / 36,000 |
| AV1 SDR8, 1920×1080 | Paced 120 fps | 1.561 | 1.940 | 5.916 | 120.08 | 3,600 / 3,600 |
| HEVC Main, 1920×1080 | Saturation | 0.668 | 1.084 | 2.434 | 2646.56 | 36,000 / 36,000 |
| HEVC Main, 1920×1080 | Paced 120 fps | 1.597 | 1.967 | 2.725 | 120.08 | 3,600 / 3,600 |
| AV1 HDR10, 3440×1440 | Saturation | 1.576 | 1.742 | 11.951 | 1011.93 | 21,600 / 21,600 |
| AV1 HDR10, 3440×1440 | Paced 240 fps | 2.082 | 2.419 | 12.682 | 240.04 | 7,200 / 7,200 |

The three paced 1080p AV1 medians were 1.538, 1.561 and 1.701 ms; HEVC was 1.618, 1.597 and 1.538 ms. All three saturation medians remained approximately 0.665 ms for AV1 and 0.668 ms for HEVC. The gap is much larger than repetition variation. Ultrawide AV1 remains above 1 ms even with a continuously busy decoder. HDR10 at 1080p and ultrawide HEVC were not included in this new cadence experiment.

Saturation offers each next AU as quickly as capacity allows; its nominal `--fps` does not impose real-time arrivals. Its caller-visible arrival timestamp therefore has different semantics from the paced run. Keep these modes separate when assessing the streaming objective. Queue depth 32 was used in both modes to accommodate the already-characterized cold-start delay; this did not change the library default or erase any warmup losses from accounting.

## Where the time goes

[`src/backend_vt.mm`](../src/backend_vt.mm) stamps immediately before `VTDecompressionSessionDecodeFrame`, immediately after it returns, and at callback entry before our callback locks, metadata processing or ownership work. The VT interval contains API/driver work, decoding and callback delivery. It is not an isolated hardware-engine duration.

| Stream / mode | Inside VT submission call, p50 | Return → callback, p50 | Parser preparation, p50 |
| --- | ---: | ---: | ---: |
| AV1 1080p saturation | 0.079 | 0.587 | 0.0005 |
| AV1 1080p paced | 0.648 | 0.909 | 0.0045 |
| HEVC 1080p saturation | 0.074 | 0.593 | 0.0088 |
| HEVC 1080p paced | 0.665 | 0.925 | 0.0426 |
| AV1 ultrawide saturation | 0.306 | 1.274 | 0.0027 |
| AV1 ultrawide paced | 0.671 | 1.403 | 0.0050 |

The split uses only valid, ordered return timestamps. One paced 1080p AV1 row and two paced ultrawide rows lacked an eligible return timestamp and are excluded from this split, while their original outcomes and VT intervals remain in the evidence. Per-phase percentiles are not additive. Much of the 1080p gap appears inside the submission call itself, despite asynchronous decoding being enabled. Apple's asynchronous flag permits a callback after return; it does not promise a zero-cost or immediately returning submission. [Apple decode API](https://developer.apple.com/documentation/videotoolbox/vtdecompressionsessiondecodeframe(_:samplebuffer:flags:framerefcon:infoflagsout:))

Steady paced post-parser work before VT submission is approximately 7–8 µs; callback entry to our public callback is approximately 13–18 µs. Eliminating all that work cannot directly remove the roughly 0.9 ms difference inside the VT interval. Parser and handoff timings also improve under saturation, consistent with a broader cadence-dependent execution effect; this does not isolate its cause.

## Prioritized experiments and changes

1. **Test submitting-thread QoS at the real arrival rate.** Neither the native replay submitting path nor the Qt native input worker explicitly sets QoS. Compare unchanged, `QOS_CLASS_USER_INITIATED` and `QOS_CLASS_USER_INTERACTIVE`, applied before session creation. Record setter status and requested thread QoS; observe callback-thread QoS without changing Apple-owned threads. Use equal run durations, alternate settings, retain identical stream bytes and all latency/count endpoints, and follow with a saturated control. Apple documents effects on scheduling, CPU/I/O resources and timer latency, so this is a relevant hypothesis, not a demonstrated fix. Avoid mixing this with SDL/pthread scheduling-policy changes: the SDK warns that incompatible `pthread_setschedparam` use can permanently opt the thread out of QoS. A separate Instruments/System Trace run should distinguish time executing inside VT from time descheduled or waiting; rerun uninstrumented for the performance claim. [Apple QoS guide](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/EnergyGuide-iOS/PrioritizeWorkWithQoS.html)

2. **Isolate asynchronous delivery overhead as a diagnostic.** Compare the asynchronous flag on/off with temporal processing still off, preserving submit-to-callback and submit-call duration. Apple documents that clearing both flags completes decoding/callback delivery before the call returns. This changes blocking behavior and needs a separate experiment; it is not an automatic production change to the asynchronous library. Do not introduce per-frame `WaitForAsynchronousFrames` into the normal path. [Apple decode API](https://developer.apple.com/documentation/videotoolbox/vtdecompressionsessiondecodeframe(_:samplebuffer:flags:framerefcon:infoflagsout:))

3. **Treat keyframe tails as a stream-shape problem to test independently.** In the new paced runs, random-access versus inter-frame VT medians were 5.978 / 1.560 ms for 1080p AV1, 3.154 / 1.595 ms for 1080p HEVC, and 12.706 / 2.080 ms for ultrawide AV1. These are classifications from the saved manifests, not discarded samples. Sweep supported encoder tile/slice layouts and decoding complexity with fixed resolution, frame rate, bit depth and controlled quality/bitrate; validate each new bitstream and use identical saved bytes for each backend comparison. The current AV1 fixture uses `--tile-columns=1` in [`tools/fixture.mm`](../tools/fixture.mm). More parallel coding structure is a hypothesis to measure, with possible bitrate/quality tradeoffs. Merely lengthening the GOP changes the mix of expensive frames and recovery behavior without proving a lower inter-frame median.

4. **Optimize HEVC preparation for caller-visible latency.** The byte-at-a-time Annex-B scanner in [`src/bitstream.cpp`](../src/bitstream.cpp) traverses every compressed byte. The existing paced matrix measured approximately 42–46 µs preparation medians at 1080p and 88 µs ultrawide; keyframe preparation was approximately 283–770 µs. Investigate bounded `memchr` candidate scans and one reserved normalization allocation. Preserve leading/trailing zeros, three/four-byte start codes, malformed-input rejection and exact NAL payloads. This is a bounded CPU improvement, but preparation occurs before the VT timer and its full cost is an upper bound, not an expected saving.

5. **Remove redundant parser-state copying while preserving transactional admission.** [`src/decoder.cpp`](../src/decoder.cpp) copies `d->parser` into an outer candidate; `Bitstream::prepare` then copies its state again. An internal preparation operation on the already-isolated candidate could remove one clone. Keep the public parser's rollback behavior and commit only after successful admission, including WOULD_BLOCK, recovery and configuration-change cases. Track the backend's applied configuration explicitly: replacing equality checks with `p.config_changed` alone is incorrect when a configuration-only AU advances the parser before the next picture. Canonicalizing invalid color fields before comparison can also prevent spurious session recreation; the zero-initialized benchmark fixtures do not demonstrate a current penalty from that case.

6. **Measure cold session construction and live Qt handoff separately.** Earlier AV1 ultrawide startup traces put 63–71 ms between parser completion and the first VT submission. Add separate cold-stage spans around format creation, session creation, property queries and sample creation before choosing a prewarm strategy. In Qt, inspect native input and handoff scheduling at [`integration/moonlight-qt/apple_video.cpp`](../integration/moonlight-qt/apple_video.cpp). AVFrame wrapping/HDR allocation and Metal rendering happen after VT callback entry; optimize them against caller/presentation measurements. Headless replay does not establish live-client latency or pacing behavior.

The SDK review found no additional dedicated decoder low-latency switch. `RealTime` is already enabled. Disabling the power-efficiency preference and changing in-flight depth have [already been measured](performance-results.md) without establishing a reliable path to 1 ms. Optional `ThreadCount` and output-pool minimum counts are lower-priority controls that need support/status/readback checks; neither documents a hardware-clock lock. `1xRealTimePlayback`, reduced-output quality tiers and frame suppression do not belong in an equivalent-quality latency comparison. [Apple decompression properties](https://developer.apple.com/documentation/videotoolbox/decompression-properties)

## Reproduce

Use the existing verified Release `build/mav-replay` and generated fixtures. This script does not rebuild or encode during timing:

```sh
python3 scripts/investigate-cadence.py --results-dir results/optimization-cadence-repeat
```

It preserves commands, logs, JSON and raw CSV, then writes the portable evidence. Choose a new results directory to retain previous runs. To recompute the committed evidence from the original local raw artifacts:

```sh
python3 scripts/investigate-cadence.py --analyze-only
```

The analyzer independently reproduces the harness's VT count, p50, p95 and p99 before deriving return-to-callback and random-access/inter distributions. The first successful output of each generation and the first 120 offered IDs are excluded only from steady timing distributions; full run accounting remains intact. Further performance acceptance still requires a loss-free paced run at the requested rate, equivalent decoded output, and improved p50/p95/p99 on the target device.
