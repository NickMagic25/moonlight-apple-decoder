# Bounded timer-wakeup diagnostic

Replay accepts `--spin-us 0..1000` (default zero). At the original absolute
arrival deadline it submits the same AU. With a nonzero value, it sleeps until
the final requested window and polls the monotonic clock during that bounded
window. It does not move arrival deadlines or change the offered rate.

Compare zero, 250 and 1000 microseconds on the same Release binary. This changes
CPU activity as well as wakeup behavior, so a latency gain would need a measured
CPU/energy tradeoff and would not identify a hardware-clock mechanism.

`experiment_busy_wait_wall_ns` measures elapsed wall time in the polling loops,
including descheduling. Actual process user+system CPU comes from `getrusage`;
its corresponding wall window and percentage of one CPU core are reported
separately. The library, Qt integration and production scheduling are unchanged.

Validation: Release arm64/macOS 11 build, four portable CTests, and hardware
correctness on 1080p AV1/HEVC SDR and 4K60 AV1/HEVC SDR/HDR. Paced runs must also
check full accounting and original deadline timestamps because correctness mode
does not use the paced wait loop. Central measurements live on the comparison
branch.
