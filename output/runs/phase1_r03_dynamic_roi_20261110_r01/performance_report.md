# CPU performance: FAIL against 50 ms

981 current-image calls (7 cached reference queries excluded), flags3572/policy1/terminal1/refine=true/4 native threads, OpenCV4.4. Timer-only copy is recorded in profile_instrumentation.diff; original production untouched. Profile raw-output differences: 0. It runs serially after the behavior replay, excluding disk decode, JSON, drawing, hashing, and report generation. It includes native C API call/packing and image processing; DLL initialization is separately listed in initialization_timings.csv. CPU is AMD Ryzen 9 7950X, 32 logical processors; registry frequency value 4491 MHz is not a measured dynamic clock. This is NOT the requested i7-12700K target machine; target-hardware performance remains NOT_VERIFIED. CPU/platform/compiler are in frozen_manifest_r03.json. These are this machine's measurements, not a real-time guarantee.

Fresh counters are read after each process; no after-minus-before of reset counters. main_total and tip_total are top-level disjoint scopes. Within them localReference and distalLine are nested. The attribution table uses disjoint components only. Tip residual includes score/pre/post operations not separately timed; outer residual includes C API plumbing and measurement overhead. Remaining residual is explicitly unassigned, not attributed to seed search. Nested old seed/response/follow columns are diagnostics only and must NOT be summed.

State breakdown labels the A0 call using the corresponding A2 shadow state; it is NOT A3 recovery performance. A2 processing_ms is A1 native call plus native state cost, an estimate for a future integration. diagnostic_overhead_ms in frame CSV contains TWO observer calls and JSON parsing, not production algorithm time. A1/A2 pilot timings overlap a short profile build; authoritative native timings below are isolated profile replay. SEARCHING/ACQUIRING/OCCLUDED/RECOVERING states with no calls are NOT_MEASURED rather than zero.

| kind | name | N | P50 | P95 | P99 | max | over_50_ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dataset | group_a | 251 | 74.8649 | 76.9099 | 78.8077 | 107.6925 | 1.0000 |
| state | SEARCHING | 262 | 74.6413 | 76.8285 | 78.2685 | 107.6925 | 0.9122 |
| resolution | 1856x2072 | 251 | 74.8649 | 76.9099 | 78.8077 | 107.6925 | 1.0000 |
| state | TRACKING | 484 | 94.6517 | 139.6867 | 144.5446 | 147.3071 | 0.7562 |
| state | OCCLUDED | 6 | 75.8872 | 132.6244 | 137.0150 | 138.1126 | 0.6667 |
| state | RECOVERING | 229 | 115.7052 | 141.0036 | 141.9599 | 143.5819 | 0.6900 |
| dataset | group_c | 79 | 45.1610 | 46.3550 | 47.4024 | 49.6171 | 0.0000 |
| resolution | 5120x5120 | 357 | 94.3170 | 118.6654 | 120.1313 | 122.4082 | 0.7787 |
| dataset | ct2 | 119 | 116.6346 | 119.5412 | 121.2128 | 122.4082 | 1.0000 |
| dataset | group_h | 119 | 139.1204 | 142.7541 | 144.4818 | 144.5511 | 1.0000 |
| resolution | 5112x1406 | 119 | 139.1204 | 142.7541 | 144.4818 | 144.5511 | 1.0000 |
| dataset | group_x | 119 | 135.0771 | 140.0375 | 146.2879 | 147.3071 | 1.0000 |
| resolution | 3036x4024 | 119 | 135.0771 | 140.0375 | 146.2879 | 147.3071 | 1.0000 |
| dataset | three_point_bend | 159 | 94.1126 | 95.6376 | 101.8400 | 103.6994 | 1.0000 |
| dataset | ct3 | 135 | 9.3089 | 10.5097 | 10.9918 | 11.0922 | 0.0000 |
| resolution | 2024x1032 | 135 | 9.3089 | 10.5097 | 10.9918 | 11.0922 | 0.0000 |

Disjoint attribution:

| scope | mean_ms | share |
| --- | --- | --- |
| main_motion_ms | 0.6055 | 0.0070 |
| tip_motion_ms | 0.7738 | 0.0089 |
| main_other_ms | 10.4161 | 0.1198 |
| local_reference_ms | 58.2421 | 0.6700 |
| terminal_path_ms | 9.2013 | 0.1059 |
| tip_response_prepost_residual_ms | 7.6616 | 0.0881 |
| outer_residual_ms | 0.0225 | 0.0003 |