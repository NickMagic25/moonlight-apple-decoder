# Startup scheduling controls

These eight two-second trials use the same C++23 replay binary and saved HEVC streams. Only the initial admission allowance changes. Each trial offers 480 frames at 3440×1440/240 fps, with two in-flight frames, a 16-frame steady arrival-age limit, and 120 statistical warmup frames. The two policies alternate order across repetitions.

| Stream target | Startup allowance | Native passes | Outputs per trial | First output range ms |
|---|---:|---:|---:|---:|
| SDR 100mbps | 0 ms | 0/2 | 420/480, 420/480 | 255.226–256.996 |
| SDR 100mbps | 250 ms | 2/2 | 480/480, 480/480 | 80.762–80.781 |
| HDR10 350mbps | 0 ms | 0/2 | 420/480, 420/480 | 258.115–259.311 |
| HDR10 350mbps | 250 ms | 2/2 | 480/480, 480/480 | 76.058–80.453 |

Every startup-aware trial delivered all frames with no scheduler drops or cancellations. Every strict trial lost frames at startup. First output under the startup policy passed the separate 250 ms limit; every strict trial exceeded it. The setup interval remains measured and is not removed from the first-output time.

The framework independently checked all eight native results against their raw CSVs, fixed arrival timeline, scheduler-event deadlines and fixture hashes. These controls test the replay policy, not a C++17/C++23 speed difference. Requested bitrates are encoder targets; payload identity is retained in the evidence.

[Commands, results and hashes](controls.json) · [Framework analysis](controls-analysis.json). Raw native JSON/CSV/logs remain in the complete local result directory.
