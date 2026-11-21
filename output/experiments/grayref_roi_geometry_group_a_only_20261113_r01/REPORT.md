# ROI 单因素实测报告

工程 PASS；输入1633/1633；三模式4899；PROTOCOL_FROZEN/GT_LEAKAGE_CHECK/BASELINE_PARITY=PASS。算法 FAIL；生产 NO。

[全量图册](galleries/index.html) · [数值完整性](run_integrity.json) · [源码快照](source_hashes.json) · [复现](README.md)

| group | mode | visible | outputs | no_public | hit3 | hit5 | hit10 | hit20 | joint | over100 | over500 | any_candidate_path_good | GT_EXCLUDED |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | A_ORIGINAL_ROI | 19 | 0 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| group_a | B_COMPACT_FIXED_BAND | 19 | 1 | 18 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 2 | 0 |
| group_a | C_DYNAMIC_CORRIDOR | 19 | 0 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| group_c | A_ORIGINAL_ROI | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| group_c | B_COMPACT_FIXED_BAND | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 18 | 0 |
| group_c | C_DYNAMIC_CORRIDOR | 20 | 0 | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| three_point_bend | A_ORIGINAL_ROI | 15 | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| three_point_bend | B_COMPACT_FIXED_BAND | 15 | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| three_point_bend | C_DYNAMIC_CORRIDOR | 15 | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

原始A为本轮真实重新运行的冻结C_FUSION_RAW路径引擎，证据缓存经原图/点/SHA核验；A的全部原生结果和节点/边逐帧一致。缓存不是本轮重新提取特征的成绩。旧V1/V2本轮NOT_REPLAYED。

## 几何、竞争、耗时

| group | mode | area_ratio_mean | search_pixels_mean | bandwidth_P50 | nodes_total | capacity_dropped | containment_deleted | path_budget_not_visited | corridor_touch | ROI_LIMITED | inference_P50_ms | inference_P95_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | A_ORIGINAL_ROI | 1.0 | 272770.3067150635 | 285.0 | 5976552 | 16200599 | 2050 | 1020376 | 0 | 0 | 701.0173000016948 | 768.2242000009865 |
| group_a | B_COMPACT_FIXED_BAND | 0.3044791350985781 | 83052.38294010889 | 87.0 | 4557570 | 1000490 | 44893 | 746266 | 1 | 1 | 288.9778000098886 | 322.65609999740263 |
| group_a | C_DYNAMIC_CORRIDOR | 0.5160068552089804 | 140762.52268602542 | 152.0 | 5194947 | 6697542 | 5731 | 956350 | 1 | 1 | 491.66329999570735 | 550.2588500021375 |
| group_c | A_ORIGINAL_ROI | 1.0 | 379105.346975089 | 181.0 | 14032375 | 15392840 | 7386 | 2568057 | 11 | 0 | 1767.4860499973875 | 1838.6201799978153 |
| group_c | B_COMPACT_FIXED_BAND | 0.3061847729055461 | 116076.6797153025 | 56.0 | 8931383 | 2867 | 90118 | 1393328 | 1 | 1 | 580.6817999982741 | 616.8048349878518 |
| group_c | C_DYNAMIC_CORRIDOR | 0.2940356664778843 | 111467.26868327401 | 53.0 | 8509441 | 33161 | 29406 | 1394734 | 50 | 50 | 558.474749996094 | 616.6007600040756 |
| three_point_bend | A_ORIGINAL_ROI | 1.0 | 1025728.9807692308 | 284.0 | 22151293 | 59513847 | 2884 | 3197103 | 0 | 0 | 3624.9045500007924 | 3811.514035001892 |
| three_point_bend | B_COMPACT_FIXED_BAND | 0.3047979283309668 | 312639.4557692308 | 86.0 | 20439580 | 2168148 | 19655 | 3755488 | 0 | 0 | 1967.6313000018126 | 2094.115239995881 |
| three_point_bend | C_DYNAMIC_CORRIDOR | 0.6305257177042436 | 646744.1269230769 | 185.5 | 21805857 | 28576399 | 9386 | 4015740 | 4 | 4 | 3217.7704499990796 | 3395.385240005271 |

计时为缓存证据上的路径引擎；C控制器、缓存加载/哈希、只读路线审计、绘图另外记录在runtime_performance.csv。不得把三模式共用的旧预处理缓存当成ROI带来的全流程加速。worker_peak_rss为每个工作进程截至该帧的峰值，非整个机器峰值；不宣称生产实时。

## 成对差异

| group | mode | visible | hit10_gained | hit10_lost | joint_gained | joint_lost | new_over100 | new_over500 | new_GT_EXCLUDED | pool_good_lost | pool_good_gained |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | B_COMPACT_FIXED_BAND | 19 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 |
| group_a | C_DYNAMIC_CORRIDOR | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| group_c | B_COMPACT_FIXED_BAND | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| group_c | C_DYNAMIC_CORRIDOR | 20 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| three_point_bend | B_COMPACT_FIXED_BAND | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| three_point_bend | C_DYNAMIC_CORRIDOR | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |

逐帧胜负见paired_frame_comparison.csv。GROUP_A仅19个可见标签，一帧影响约5.26个百分点，不作显著性或新盲测声称。未知标签单独记录，未标注不当阴性，FPR=N/A。

## 决策

| mode | decision | GO_NO_GO | production |
| --- | --- | --- | --- |
| B_COMPACT_FIXED_BAND | GEOMETRY_HARMFUL | NO_GO | NO |
| C_DYNAMIC_CORRIDOR | GEOMETRY_HARMFUL | NO_GO | NO |

默认C预先指定，不依据组别选择最佳模式。规则冻结后没有据GROUP_A或验证标签调参。验证仅触发预先规定的退化判定，不用于重新设计参数。CT2/开发组H/CT3/排除组X图像、逐帧结果和标签本轮未进入队列。P中心线/图像缺口假设未获物理认证。仅GROUP_A开发不能证明跨试件通用。

{
  "utc": "2026-11-13T06:23:34.437099+00:00",
  "python": "3.12.7 | packaged by Anaconda, Inc. | (main, Oct  4 2024, 13:17:27) [MSC v.1929 64 bit (AMD64)]",
  "platform": "Windows-11-10.0.26200-SP0",
  "numpy": "1.26.4",
  "opencv": "4.12.0",
  "logical_cpus": 32,
  "memory_bytes": 67768807424,
  "free_disk": 70708916224,
  "workers": 12,
  "git": "NOT_A_GIT_REPOSITORY"
}