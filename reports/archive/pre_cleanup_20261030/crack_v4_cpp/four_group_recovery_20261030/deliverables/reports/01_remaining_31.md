# 剩余25帧与额外6帧的定位清单

这31帧均是原发布算法曾给出完整长度、本轮候选仍拒绝的帧。`frame_id`从0开始，对比图的图序为frame_id+1。
16帧因为当前跟踪末端前方仍存在连续暗线支撑；15帧因为路径支撑丢失而截断。全部纳入逐帧对照，没有以“保护”一词替代真实准确性结论。

前一类需要后续考虑重新搜索末端前方的真实路径，而不是直接放松末端验证；后一类需要人工标注区分真实弱段和噪声误追。当前版本已锁定，没有为了这些帧继续增大阈值/间隙预算。实测长度允许回落，没有使用单调先验。

| 组 | frame_id | 文件名 | 集合 | 直接拒绝原因 | 末端无支撑间距px | 前向连续支撑px | 对比图 |
|---|---|---|---|---|---|---|---|
| 开发组A测试-1 | 51 | 20240328171332313-512.bmp | 原336剩余 | current_trace_continues | 0 | 8 | [原图/结果](<../review/per_frame/group_a/0051_20240328171332313-512.png>) |
| 开发组A测试-1 | 55 | 20240328171342556-552.bmp | 原336剩余 | current_trace_continues | 0 | 10 | [原图/结果](<../review/per_frame/group_a/0055_20240328171342556-552.png>) |
| 开发组A测试-1 | 59 | 20240328171352562-592.bmp | 额外回退 | current_trace_continues | 0 | 12 | [原图/结果](<../review/per_frame/group_a/0059_20240328171352562-592.png>) |
| 开发组A测试-1 | 101 | 20240328171537562-1012.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/group_a/0101_20240328171537562-1012.png>) |
| 开发组A测试-1 | 105 | 20240328171547568-1052.bmp | 额外回退 | current_trace_continues | 0 | 11 | [原图/结果](<../review/per_frame/group_a/0105_20240328171547568-1052.png>) |
| 开发组A测试-1 | 107 | 20240328171552314-1072.bmp | 额外回退 | current_trace_continues | 0 | 11 | [原图/结果](<../review/per_frame/group_a/0107_20240328171552314-1072.png>) |
| 开发组A测试-1 | 109 | 20240328171557565-1092.bmp | 额外回退 | current_trace_continues | 0 | 12 | [原图/结果](<../review/per_frame/group_a/0109_20240328171557565-1092.png>) |
| 验证组C | 20 | 1 (21).bmp | 原336剩余 | current_trace_continues | 0 | 11 | [原图/结果](<../review/per_frame/group_c/0020_1 (21).png>) |
| 验证组C | 290 | 3 (229).bmp | 额外回退 | current_trace_continues | 0 | 12 | [原图/结果](<../review/per_frame/group_c/0290_3 (229).png>) |
| 验证组C | 294 | 3 (233).bmp | 额外回退 | current_trace_continues | 0 | 13 | [原图/结果](<../review/per_frame/group_c/0294_3 (233).png>) |
| CT2 | 108 | 20241101163428241-2836.bmp | 原336剩余 | current_trace_continues | 0 | 8 | [原图/结果](<../review/per_frame/ct2/0108_20241101163428241-2836.png>) |
| CT2 | 111 | 20241101163437242-2863.bmp | 原336剩余 | current_trace_continues | 0 | 10 | [原图/结果](<../review/per_frame/ct2/0111_20241101163437242-2863.png>) |
| CT2 | 114 | 20241101163446242-2890.bmp | 原336剩余 | current_trace_continues | 0 | 10 | [原图/结果](<../review/per_frame/ct2/0114_20241101163446242-2890.png>) |
| CT2 | 135 | 20241101163549239-3079.bmp | 原336剩余 | current_trace_continues | 0 | 10 | [原图/结果](<../review/per_frame/ct2/0135_20241101163549239-3079.png>) |
| CT2 | 150 | 20241101163634238-3214.bmp | 原336剩余 | current_trace_continues | 1.0090225546553369 | 9 | [原图/结果](<../review/per_frame/ct2/0150_20241101163634238-3214.png>) |
| CT2 | 351 | 20241101165006883-649.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/ct2/0351_20241101165006883-649.png>) |
| CT2 | 380 | 20241101165128547-894.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/ct2/0380_20241101165128547-894.png>) |
| CT2 | 384 | 20241101165145879-946.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/ct2/0384_20241101165145879-946.png>) |
| CT2 | 386 | 20241101165146545-948.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/ct2/0386_20241101165146545-948.png>) |
| CT2 | 392 | 20241101165204546-1002.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/ct2/0392_20241101165204546-1002.png>) |
| CT2 | 399 | 20241101165230879-1081.bmp | 原336剩余 | current_trace_continues | 0 | 10 | [原图/结果](<../review/per_frame/ct2/0399_20241101165230879-1081.png>) |
| CT2 | 407 | 20241101165249544-1137.bmp | 原336剩余 | trace_support_lost | 1.0021997271409093 | 0 | [原图/结果](<../review/per_frame/ct2/0407_20241101165249544-1137.png>) |
| CT2 | 417 | 20241101165324876-1243.bmp | 原336剩余 | current_trace_continues | 0 | 14 | [原图/结果](<../review/per_frame/ct2/0417_20241101165324876-1243.png>) |
| CT2 | 429 | 20241101165400876-1351.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/ct2/0429_20241101165400876-1351.png>) |
| CT2 | 438 | 20241101165427875-1432.bmp | 原336剩余 | trace_support_lost | 0 | 12 | [原图/结果](<../review/per_frame/ct2/0438_20241101165427875-1432.png>) |
| 开发组HMT | 49 | 20250314144145112-43.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/group_h/0049_20250314144145112-43.png>) |
| 开发组HMT | 56 | 20250314144152111-50.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/group_h/0056_20250314144152111-50.png>) |
| 开发组HMT | 296 | 20250314155345787-369.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/group_h/0296_20250314155345787-369.png>) |
| 开发组HMT | 351 | 20250314161738299-185.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/group_h/0351_20250314161738299-185.png>) |
| 开发组HMT | 387 | 20250314165856688-166.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/group_h/0387_20250314165856688-166.png>) |
| 开发组HMT | 401 | 20250314165900888-250.bmp | 原336剩余 | trace_support_lost | 0 | 0 | [原图/结果](<../review/per_frame/group_h/0401_20250314165900888-250.png>) |
