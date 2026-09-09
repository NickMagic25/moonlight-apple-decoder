# Reproducible headless measurements

Run correctness first, then use Release tools with no simultaneous encoding, builds, software reference decoding, or sanitizer run:

```sh
./scripts/benchmark.sh --preset 1080p120-av1 --inflight 1,2,3
./scripts/benchmark.sh --preset 1080p120-hevc --inflight 1,2,3
./scripts/benchmark.sh --preset 3440x1440p240-av1-10bit-hdr
./scripts/benchmark.sh --preset 3440x1440p240-hevc-main10-hdr
```

The preset set includes AV1/HEVC SDR8 and HDR10 at 1080p120, 1440p120/240, 3440x1440p240, and 4k60/120. `--seconds` defaults to 10 and `--repetitions` to 3; `--warmup` excludes the first 120 submissions from steady-state distributions. `--power -1` selects the system default and `--power 0` requests disabled power efficiency. `--inflight 1,2,3` changes one variable at a time. `--chroma 444` explicitly reports BLOCKED because the mandatory renderer-compatible path is 4:2:0; it does not substitute another format. Long overload/thermal runs can use `--seconds 120` after short correctness and performance gates.

Each requested configuration is hardware-decoded and validated before timed runs. Results go to `results/benchmarks/PRESET/` with one CSV and JSON per repetition/in-flight/power setting, plus `summary.json`. Failures retain requested preset and reasons; overrun/drop measurements are never silently promoted to a successful high-rate result. Saved fixture hashes identify exact compressed bytes. The benchmark script selects `--loop-mode continuous` for both native and FFmpeg runs. Repeated fixtures keep one warmed decoder session: each loop begins with the same genuine random-access access unit, media timestamps and IDs are rebased, and absolute arrival deadlines continue across loops. No drain/reset is inserted at an ordinary continuous-loop boundary. Explicit fixture discontinuities and real decode recovery still reset state. The standalone replay default remains `--loop-mode reset`, which drains/resets at each loop boundary for lifecycle correctness tests; `loop_mode` is recorded in results.

`mav-replay --mode paced` uses absolute `CLOCK_UPTIME_RAW` arrival deadlines, preserving each deadline through backpressure. Both native and FFmpeg paced tools use the same absolute-deadline scheduler, with each sleep capped at 1 ms. Deadlines do not move to the current time when decoding is slow. Matching the scheduler avoids comparing a full-frame-interval sleep in one backend against shorter waits in the other. The maximum pending arrival backlog is bounded by `--queue-depth` (default sixteen frame intervals); excess lag causes explicit loss, decoder reset, and dependency-safe recovery at a genuine random-access point. `--mode throughput` submits whenever capacity is available and is saturation evidence, not real-time arrival latency. `--mode correctness` maps pixels and creates Metal textures and must not be used for performance comparisons.

The timed callback records a cheap completion record and timestamp, retaining no pixel buffer and performing no image checks. Statistics are computed after drain. `vt_submit_to_callback_ns` is measured immediately before `VTDecompressionSessionDecodeFrame` to output callback entry, including work within the call. It is API-visible VideoToolbox latency, not isolated hardware-engine time. Only newly decoded single-sample displayed outputs contribute to that distribution; no-display completions, existing-frame displays, and multi-sample submissions remain separately counted. All steady frame-latency distributions consistently exclude warmup and the first displayed output in each decoder generation, including preparation, queue wait, submission duration, complete-AU-to-output and client handoff. Native cold VT intervals remain in their separate cold-generation distribution, and both tools retain cold records in CSV. Continuous runs normally have one startup generation; reset runs have a cold generation for every loop. Offered/admitted/displayed totals include all frames, and scheduler-lateness explicitly covers all offered arrivals, including warmup, cold starts and losses. CSV includes raw timestamps and validity bits. JSON reports count, mean, median, p95, p99, min/max, preparation, submission-call duration, queue wait, complete-AU-to-output, callback-to-client handoff, scheduler lateness, counts, copy accounting, peak outstanding depth, settings/status/readback, hardware validation, codec/depth/chroma, fixture hash, OS/model, thermal state, warmup, and duration. Renderer/presentation and unavailable power-state measurements are `null`.

The headless harness does not establish display refresh or presentation rate. The 1 ms median objective is measured per configuration; it is not a universal hardware guarantee. Count offered, admitted, and output frames and check sustained rate and backlog before evaluating latency percentiles.

## Optional FFmpeg VideoToolbox comparison

Build the isolated FFmpeg tool using a suitable local FFmpeg development tree. It never links into the production core:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DMAV_FFMPEG_ROOT="$MOONLIGHT_QT_DIR/libs/mac"
cmake --build build --parallel 4
DYLD_LIBRARY_PATH="$MOONLIGHT_QT_DIR/libs/mac/lib" build/mav-ffmpeg-baseline --fixture fixtures/generated/example/manifest.json --mode paced --fps 120 --loops 10 --loop-mode continuous --warmup 120 --output results/ffmpeg-example
```

`--ffmpeg-baseline` on the benchmark script runs the optional executable with the same saved fixture, paced rate, continuous-loop duration, warmup and repetition count when built; set the required library search path for that FFmpeg distribution. Both backends must consume the same manifest and preserve output depth/chroma, and both must prove actual hardware selection. FFmpeg's send/receive API boundaries differ from the native VT callback boundaries. Compare the derived `public_complete_au_to_output_ns` from `scripts/summarize-benchmarks.py`; exact FFmpeg VT submission/callback values remain unavailable. An unavailable FFmpeg AV1 hardware backend is BLOCKED for that comparison, never relabeled software decoding.

The runtime Moonlight environment variables select native or FFmpeg for live A/B. Standalone headless timings exclude the application's decoder handoff, pacer, renderer, GPU, and presentation and must be reported separately.

The native scheduler's `--queue-depth` is a bounded maximum arrival age expressed
in frame intervals (default 16). It is separate from `--inflight`, which bounds
unresolved decoder submissions. A larger limit can preserve input during session
startup while allowing more initial backlog; it does not change the offered rate.
The optional FFmpeg baseline drains every scheduled AU without the native
age-based drop/reset policy. Compare actual backlog and full accounting, especially
at cold start. Use `--results-dir` to preserve controlled experiments separately.

For the equivalent caller-visible comparison, run:

```sh
python3 scripts/summarize-benchmarks.py
python3 scripts/summarize-benchmarks.py --input results/thermal --output docs/evidence/thermal.json
```

The resulting JSON adds `public_complete_au_to_output_ns`: native public completion
callback entry in the harness versus FFmpeg `avcodec_receive_frame` return. The
native per-run `complete_au_to_output_ns` ends earlier at the internal VT callback;
it remains available as a separate interval and is not substituted for caller
availability. Both endpoints come from the saved CSV, with identical warmup and
cold-generation exclusions. Cold caller-visible latency and total submit-entry to
VT-submit preparation are also derived. Parser preparation alone excludes later
sample/session construction; queue wait includes scheduler lateness and capacity
wait. Original accounting totals and raw traces remain unchanged.
