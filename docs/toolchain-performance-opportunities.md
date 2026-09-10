# Performance opportunities after the toolchain upgrade

C++23 and Swift 6.3 provide tools for further experiments. Selecting newer
language and toolchain versions does not itself establish a decoding speedup:
the previous C++17 build already used the same Apple Clang 21 compiler, and the production
decoder remains C++/Objective-C++. Swift currently contains only the C API
ownership smoke example.

In the [new resolution/frame-rate matrix](toolchain-matrix.md), per-run parser
medians were 3.5–30.5 microseconds, while VT call-to-callback medians were
1.49–2.85 milliseconds. This bounds the direct latency available from parser
work in these fixtures; representative fragmented live traffic still needs
separate measurement.

The [VT wait analysis](vt-wait-dependencies.md) places the largest unresolved
interval before the AppleAVD decoder/driver notification, approximately
1.46–1.47 ms in the investigated instrumented 4K60 traces. That is not a pure
hardware execution measurement, and application language changes cannot be
assumed to remove it. The candidates below target application CPU work,
allocation pressure, and latency variation. None is implemented by this PR.

## Prioritized experiments

1. **Reduce allocations for bounded pending submissions.**
   [The core](../src/decoder.cpp) and [VT backend](../src/backend_vt.mm) use
   node-based `std::map` containers
   and per-submission ownership allocations. The default in-flight bound is two.
   Compare reserved contiguous storage, including C++23 `std::flat_map`, with
   the existing maps. Reserve the underlying storage; merely replacing an empty
   map can introduce different allocations. Preserve shared ownership, delayed
   callbacks, cancellation, and reset semantics. Measure allocation counts,
   submission/callback CPU, and public p95/p99 latency at both default and maximum
   supported in-flight limits, including AV1 temporal units with multiple child
   samples. Flat-map insertion and erasure move elements and
   can invalidate iterators, so this is a benchmark candidate, not an automatic win.
   [Standard design and tradeoffs](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2022/p0429r9.pdf)

2. **Remove the extra copy for fragmented HEVC access units.**
   The multi-span path in [the bitstream parser](../src/bitstream.cpp) assembles
   the input and then copies
   it again during Annex-B normalization. A scanner that reads across bounded
   spans could write directly into the final owned normalized buffer. C++20
   `std::span`, available under the C++23 baseline, can express those borrowed
   views. The benefit would come from removing a copy, not from the view type
   alone. Preserve `mav_decoder_submit_copy`'s ownership contract. Measure with
   representative fragmented, high-bitrate live input; the current replay's
   single-span fixtures do not exercise this opportunity.

3. **Prototype a bounded word-based bit reader.**
   `Bits::get` and Exp-Golomb parsing in `src/bitstream.cpp` currently consume
   individual bits. C++20 `std::countl_zero` and C++23 `std::byteswap` can support
   word-based reads. Preserve truncation checks, overflow behavior, unaligned
   input support, and reads at the end of an allocation. Compare parser CPU and
   public latency against the existing implementation using both valid and
   malformed inputs. Existing scalar byte swaps may already compile identically;
   changing syntax alone does not establish an improvement.
   [Bit operations](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/p0553r4.html),
   [byteswap](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2021/p1272r4.html)

4. **Use ownership and specialization in a future Swift consumer.**
   Borrowed `Span` views and noncopyable ownership abstractions can help avoid
   intermediate data copies while retaining CVPixelBuffer output for direct
   Metal use. Swift 6.3 adds `@specialize`, `@inline(always)`, and
   `@export(implementation)` for measured generic or library-boundary overhead.
   Apply these only to demonstrated hot paths, accounting for code-size growth.
   Avoid unnecessary per-frame Tasks or actor hops in the eventual native
   consumer. Measure ARC activity, allocations, callback-to-render handoff, and
   actual presentation deadlines. There is no production Swift hot path in this
   library today.
   [Swift 6.2 systems features](https://www.swift.org/blog/swift-6.2-released/),
   [Swift 6.3 optimization controls](https://www.swift.org/blog/swift-6.3-released/)

## Availability and acceptance

Apple's installed Xcode 26.6 SDK implements the C++ APIs above; `flat_map`
requires Xcode 26 according to [Apple's C++ support matrix](https://developer.apple.com/xcode/cpp/).
Using it would need a documented compiler minimum or a fallback. The current
SDK does not implement `std::move_only_function`. Swift `InlineArray` requires
OS 26, while `Synchronization.Atomic` requires macOS 15/iOS 18/tvOS 18; neither
can be used unconditionally with this library's current deployment targets.
Validate each chosen API against those targets when implementing an experiment.

The bounded HEVC scanner and redundant parser-state-copy removal are already
[adopted](main-adoption.md). Thread QoS, synchronous delivery, output-pool hints,
and the investigated private in-process/fence options have not established a
repeatable equivalent-output win; the language upgrade is not a reason to repeat
those controls without new evidence.

For any future implementation, compare the same saved stream bytes and arrival
deadlines on alternating baseline/candidate runs, preserve full frame accounting,
and require equivalent pixels/metadata and improved CPU or public latency
distributions. Lower parser time alone does not establish lower presentation
latency, and no speedup is claimed here for these unimplemented candidates.
