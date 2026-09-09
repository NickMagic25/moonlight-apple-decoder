# Beneficial optimizations adopted into main

The selected branches were merged with their history intact. The implementation
and comparison evidence from `codex/experiment-comparison` provide the foundation;
the following changes are adopted on top:

| Branch | Adopted behavior | Prior measured benefit |
| --- | --- | --- |
| `codex/experiment-hevc-scan` | Bounded HEVC Annex-B scanning and one reserved normalization allocation | Approximately 22–28 µs less preparation |
| `codex/experiment-parser-state` | Prepare the already-detached parser candidate without cloning it again | Approximately 0.3–2.3 µs less preparation |
| `codex/experiment-pacing` | Optional `mav-replay --spin-us 0..1000`, with CPU accounting | More precise fixture arrival scheduling at a measured CPU cost |

The replay polling window remains **zero by default**. This is a harness option,
not a Qt worker or production decoder scheduling policy. The normal decoder
remains asynchronous, and its C ABI and hardware/output requirements are
unchanged. The other experiments remain on their separate branches: QoS,
synchronous delivery, output pools, capability-query bypass and encoder layout
did not establish sufficient repeatable benefit for adoption.

The scanner and parser branches both appended bitstream tests. Their only merge
conflict was resolved by retaining both test functions and invoking both from
the test entry point. The combined core otherwise contains exactly the selected
scanner and parser changes. The real backend, format/sample construction,
public headers and fixture encoder are unchanged from `d0bd4a1`.

## Combined validation

The tested merge revision is `183b830` (followed only by this documentation and
evidence commit). Validation used a fresh Release arm64/macOS 11 deployment build
and a separate ASan/UBSan build on Apple M3, macOS 26.6.2, SDK 26.5.

- All four Release CTests and all four ASan/UBSan CTests passed. Both builds
  executed **19,769 bitstream checks**, including both merged test additions,
  plus the lifecycle, C ABI and adapter-timing tests.
- All 36 runner regression scenarios and 19 analyzer cohorts passed.
- Hardware correctness passed **1,920/1,920 outputs**: AV1 and HEVC, SDR8 and
  HDR10, at 1080p120 and 4K60, with two fixture loops/reset handling per case.
  IOSurface/Metal and retained-output ownership checks passed. Every 4K case
  compared **2,985,984,000 visible samples** against the independent software
  reference, with maximum and mean sample error zero.
- Real reconfiguration passed for both codecs: 26 hardware outputs, six implicit
  format changes and six pending transition retries per codec, with retained
  pixels stable.
- Real AV1 8/10-bit accounting passed using the existing saved reference streams:
  48 grouped and 71 split submissions, 23 no-display completions and 20 existing
  frame displays per depth. Software-reference maximum and mean error were zero.
- Eight paced 4K60 checks passed **1,920/1,920 outputs**, covering both codecs and
  SDR/HDR with the omitted/default polling option and explicit 250 µs polling.
  Every original frame deadline remained spaced by 16,666,666–16,666,667 ns.
  Default runs recorded zero polling time; optional runs exercised polling.

The [combined validation evidence](evidence/main-adoption.json) records exact
commands, source and binary identity, full outcomes and paced default/optional
polling checks. These are combined-build regression checks; they do not establish
an additive performance improvement or a new latency record. The **paced 1 ms
objective remains unmet** in the prior controlled comparisons. Qt remains on
its existing local-only branch and was not modified or pushed by this merge.

## Historical comparisons and reproduction

[Experiment results](experiment-results.md) and their recorded hashes and timing
distributions remain historical evidence. For those original controls, check out
`codex/experiment-comparison` at `b126a85` as its reproduction instructions specify.
A new build of main includes the adopted optimizations and must not be labeled
the unchanged historical baseline. Do not overwrite old result directories.

Build and validate current main normally:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0
cmake --build build --parallel 4
ctest --test-dir build --output-on-failure
./scripts/validate.sh --suite offline-hardware --skip-build --require-hardware --require-codecs av1,hevc --require-variants sdr8,hdr10
```

The combined validation reused the saved 4K fixtures and independent references
from the experiment preparation, without re-encoding during replay. Their
generation and reference workflow remains documented in the fixture and
experiment reports. The optional arrival-control syntax is:

```sh
build/mav-replay --fixture fixtures/generated/av1-hdr10-3840x2160p60-120/manifest.json \
  --mode paced --fps 60 --loops 2 --loop-mode continuous --warmup 120 \
  --inflight 2 --queue-depth 32 --spin-us 250 --output results/paced-250
```

Omit `--spin-us` to use the unchanged sleep-based default. Live Qt latency,
presentation, physical iOS/tvOS performance and longer thermal confirmation of
the combined optimizations remain separate validation work.
