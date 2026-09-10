# Isolated ultrawide HEVC HDR startup-loss audit

Both cases use 3440×1440 at 240 fps, queue depth 16 and 120 offered warmup frames (about 500 ms). The original measurements remain unchanged.

| Case / affected run | Outputs / offered | Scheduler drops | Failed completion | Missing public output IDs | Recovery output | Post-warmup outputs |
|---|---:|---:|---|---|---:|---:|
| 50.0 Mbps / baseline 1 | 2341/2400 | 58 | ID 1, status 4, terminal 76.088 ms | 1–59 | ID 60 at 261.091 ms | 2280/2280 |
| 250.0 Mbps / candidate 3 | 2345/2400 | 54 | ID 5, status 4, terminal 96.076 ms | 5–59 | ID 60 at 265.041 ms | 2280/2280 |

The 50 Mbps baseline event lacks scheduler records for IDs 2–59 (scheduled about 8.333–245.833 ms); ID 1 completed without output. The 250 Mbps candidate event lacks IDs 6–59 (about 25.000–245.833 ms); ID 5 completed without output. Both recover at the next keyframe, ID 60 (scheduled about 250 ms), and output every ID from 60 through 2399. Their frame losses are confined to startup, before warmup.

| Case | Other five trials | Decoded FPS range | VT median range, ms | VT p95 range, ms | VT p99 range, ms |
|---|---|---:|---:|---:|---:|
| 50.0 Mbps | All 2400/2400; zero drops/failures | 240.042420–240.048081 | 1.963500–2.020062 | 2.837021–2.957039 | 6.262894–6.432191 |
| 250.0 Mbps | All 2400/2400; zero drops/failures | 240.030994–240.035660 | 2.489917–2.587270 | 3.340559–3.492504 | 13.489033–13.751177 |

74 cases have all six native timed trials PASS, including 24 outside bitrate coverage. None of those cases has a VT or public median/p95/p99 paired latency threshold breach.

Both isolated frame-loss events are confined to startup before warmup; this identifies where loss occurred and does not establish its root cause or eliminate recurrence.

Exact native/public metrics, inferred missing-ID schedules, absolute timestamps, and verified JSON/CSV/log hashes are retained in [summary.json](summary.json).

## Balanced confirmation

The separate confirmation ran six 20-second pairs per case, preserving the full-run payload bytes (verified from both archives), decoder settings and warmup of 120 offered frames. All four correctness checks passed. Timed trials: 13 passed and 11 failed; all had nominal thermal state.

| Target Mbps | Failed run | Outputs / 4800 | Scheduler-missing IDs | Cancelled IDs (status 4) | Recovery ID 60 output, ms | Post-warmup outputs |
|---:|---|---:|---|---|---:|---:|
| 50.0 | candidate 3 | 4740 | 1–59 | 0 | 264.278 | 4680/4680 |
| 250.0 | baseline 1 | 4742 | 4–59 | 2, 3 | 261.950 | 4680/4680 |
| 250.0 | baseline 2 | 4745 | 6–59 | 5 | 262.572 | 4680/4680 |
| 250.0 | candidate 2 | 4745 | 6–59 | 5 | 261.863 | 4680/4680 |
| 250.0 | candidate 3 | 4744 | 5–59 | 4 | 264.144 | 4680/4680 |
| 250.0 | baseline 3 | 4744 | 5–59 | 4 | 262.619 | 4680/4680 |
| 250.0 | baseline 4 | 4745 | 6–59 | 5 | 261.845 | 4680/4680 |
| 250.0 | candidate 5 | 4744 | 5–59 | 4 | 263.478 | 4680/4680 |
| 250.0 | baseline 5 | 4744 | 6–59 | 4, 5 | 262.317 | 4680/4680 |
| 250.0 | baseline 6 | 4743 | 5–59 | 3, 4 | 260.910 | 4680/4680 |
| 250.0 | candidate 6 | 4744 | 6–59 | 4, 5 | 263.177 | 4680/4680 |

Every failed confirmation run lost only public IDs below 60, recovered at ID 60 (scheduled about 250 ms), and delivered all IDs 60–4799. All 4,680 post-warmup IDs 120–4799 were delivered in every trial. The earlier full-run losses were also confined to this startup interval. No paired VT/public median/p95/p99 latency gate was flagged in either confirmation case; frame accounting failures still prevent a passing result.

| Target Mbps | Build | Full-run failures / trials | Confirmation failures / trials | Combined descriptive count |
|---:|---|---:|---:|---:|
| 50.0 | baseline | 1/3 | 0/6 | 1/9 |
| 50.0 | candidate | 0/3 | 1/6 | 1/9 |
| 250.0 | baseline | 0/3 | 6/6 | 6/9 |
| 250.0 | candidate | 1/3 | 4/6 | 5/9 |

Frame losses recurred in both builds and were confined to startup before warmup. These descriptive counts do not establish a statistically supported toolchain regression or its absence.

The original full-run audit fields remain unchanged in summary.json; the appended `confirmation` object contains exact cancellation timestamps, inferred missing-ID schedules, per-run metrics and verified evidence hashes.
