# VT dispatch diagnostic

This isolated experiment compares the existing asynchronous flag with synchronous
decode, keeping temporal processing off and the C ABI unchanged. It is disabled
by default. Build with `-DMAV_EXPERIMENT_VT_DISPATCH=ON`, then use replay
`--vt-mode asynchronous` or `--vt-mode synchronous` on the same binary.

The synchronous case blocks the submitting thread through callback delivery.
It is a diagnostic, not a production nonblocking policy. No per-frame drain was
added. Both modes retain the same submit-to-callback timestamp boundaries.

A preallocated, submission-thread recorder retains exact VT submit and return
timestamps. Inline callbacks naturally occur before return, so after the run the
replay tool enriches missing return timestamps from that recorder. The CSV
`public_trace_valid` column preserves the original callback snapshot validity;
the separate `-vt-calls.csv` contains the actual calls. Recorder overflow or a
mismatch against the internal-sample count fails the run. These returned-call
records must not be interpreted as timestamps available to an inline callback.

Validation: Release arm64/macOS 11 build, four portable CTests, and both dispatch
modes on 1080p AV1/HEVC SDR plus 4K60 AV1/HEVC SDR/HDR hardware correctness gates.
The comparison branch holds the centrally scheduled performance evidence.
