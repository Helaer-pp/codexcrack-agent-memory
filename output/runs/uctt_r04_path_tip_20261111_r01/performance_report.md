# Full native API performance

631 non-reference calls per version; cached GetBaseline excluded, initialization separate. B0 wall includes full original C API. B1 wall includes same detector plus map copies, both E1 methods, branch audits, state/JSON packing, in one R04Process call. B2 methods are jointly evaluated within B1; no fabricated standalone B2/B3/B4/B5 timings. B1 is a diagnostic upper-cost implementation, not optimized deployment. Threads=4 native, AMD Ryzen 9 7950X; OpenCV4.4/MSVC v142 /O2 /fp:precise. Same decoded frame fed in fixed B0 then B1 order; OS/file cache warms during sequential replay, no forced cache flush. Order/cache bias not isolated. Disk decode/hash/map compression/video generation are outside API timers. Video render runs later. SIMD uses the installed OpenCV dispatch; runtime feature toggles unchanged, exact dispatched instruction set NOT_INSTRUMENTED.

Counters reset each frame; direct values read. Only the listed disjoint scope components are summed; old nested timers are not. Residual includes serialization/API overhead and clock measurement error. No 50 ms guarantee. State breakdown groups B1 timings by D2 source, not a newly implemented recovery search.

| kind | name | version | N | P50 | P95 | P99 | max | timeout_50ms_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dataset | group_a | B0_R02_A0 | 245 | 88.993 | 104.153 | 119.659 | 124.673 | 1.000 |
| dataset | group_a | B1_DIAGNOSTIC | 245 | 91.551 | 107.432 | 123.599 | 134.334 | 1.000 |
| resolution | 1856x2072 | B0_R02_A0 | 245 | 88.993 | 104.153 | 119.659 | 124.673 | 1.000 |
| resolution | 1856x2072 | B1_DIAGNOSTIC | 245 | 91.551 | 107.432 | 123.599 | 134.334 | 1.000 |
| D2_source | fallback | B0_R02_A0 | 593 | 89.085 | 167.953 | 188.909 | 210.701 | 0.916 |
| D2_source | fallback | B1_DIAGNOSTIC | 593 | 91.583 | 173.313 | 194.208 | 224.619 | 0.948 |
| D2_source | observed | B0_R02_A0 | 19 | 136.582 | 196.569 | 221.380 | 227.583 | 1.000 |
| D2_source | observed | B1_DIAGNOSTIC | 19 | 142.350 | 175.462 | 178.617 | 179.405 | 1.000 |
| D2_source | predicted | B0_R02_A0 | 19 | 139.062 | 209.789 | 214.210 | 215.315 | 1.000 |
| D2_source | predicted | B1_DIAGNOSTIC | 19 | 143.681 | 178.557 | 182.310 | 183.249 | 1.000 |
| dataset | group_c | B0_R02_A0 | 142 | 52.261 | 55.420 | 70.617 | 76.270 | 0.866 |
| dataset | group_c | B1_DIAGNOSTIC | 142 | 53.653 | 57.408 | 67.745 | 74.259 | 1.000 |
| resolution | 5120x5120 | B0_R02_A0 | 187 | 53.126 | 137.694 | 145.950 | 193.123 | 0.898 |
| resolution | 5120x5120 | B1_DIAGNOSTIC | 187 | 54.491 | 142.836 | 151.665 | 167.458 | 1.000 |
| dataset | ct2 | B0_R02_A0 | 22 | 137.437 | 173.642 | 189.391 | 193.123 | 1.000 |
| dataset | ct2 | B1_DIAGNOSTIC | 22 | 142.244 | 155.191 | 164.928 | 167.458 | 1.000 |
| dataset | group_h | B0_R02_A0 | 162 | 164.966 | 192.666 | 212.500 | 227.583 | 1.000 |
| dataset | group_h | B1_DIAGNOSTIC | 162 | 169.774 | 188.712 | 203.905 | 206.247 | 1.000 |
| resolution | 5112x1406 | B0_R02_A0 | 162 | 164.966 | 192.666 | 212.500 | 227.583 | 1.000 |
| resolution | 5112x1406 | B1_DIAGNOSTIC | 162 | 169.774 | 188.712 | 203.905 | 206.247 | 1.000 |
| dataset | group_x | B0_R02_A0 | 6 | 160.177 | 175.399 | 176.516 | 176.795 | 1.000 |
| dataset | group_x | B1_DIAGNOSTIC | 6 | 167.529 | 214.739 | 222.643 | 224.619 | 1.000 |
| resolution | 3036x4024 | B0_R02_A0 | 6 | 160.177 | 175.399 | 176.516 | 176.795 | 1.000 |
| resolution | 3036x4024 | B1_DIAGNOSTIC | 6 | 167.529 | 214.739 | 222.643 | 224.619 | 1.000 |
| dataset | three_point_bend | B0_R02_A0 | 23 | 111.056 | 127.752 | 133.339 | 134.498 | 1.000 |
| dataset | three_point_bend | B1_DIAGNOSTIC | 23 | 114.392 | 120.944 | 129.639 | 132.080 | 1.000 |
| dataset | ct3 | B0_R02_A0 | 31 | 11.212 | 15.846 | 15.899 | 15.912 | 0.000 |
| dataset | ct3 | B1_DIAGNOSTIC | 31 | 11.380 | 16.546 | 16.589 | 16.594 | 0.000 |
| resolution | 2024x1032 | B0_R02_A0 | 31 | 11.212 | 15.846 | 15.899 | 15.912 | 0.000 |
| resolution | 2024x1032 | B1_DIAGNOSTIC | 31 | 11.380 | 16.546 | 16.589 | 16.594 | 0.000 |

| scope | mean_ms | share |
| --- | --- | --- |
| main_motion_ms | 0.824 | 0.008 |
| tip_motion_ms | 0.680 | 0.007 |
| main_other_ms | 13.218 | 0.128 |
| local_reference_ms | 65.316 | 0.634 |
| distal_path_ms | 9.995 | 0.097 |
| tip_other_and_trace_ms | 12.802 | 0.124 |
| new_audit_ms | 0.059 | 0.001 |
| json_and_api_residual_ms | 0.173 | 0.002 |