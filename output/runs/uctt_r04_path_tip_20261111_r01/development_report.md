# R04 路径归属实验：保留诊断，不替换生产算法

1. **R04_RESULT=PARTIAL；替换 R02 生产算法=NO。** 实际完成冻结、R03原16项注入重现、B0/B1回放、两种E1原生候选验证、真实对照与性能。生产源码/DLL未覆盖。E2、E3、B3–B5因E1证据/覆盖门槛未通过而阻断，不宣称全任务验收通过。用户另要求的结果视频无论成败均交付为 R04_results.mp4。

2. **Q1 首锁根因：** roi_tip.inc:68的局部DP可在任意列起始；:224将非空局部路径同时置为tip/path_valid/terminal，缺少独立主裂纹归属验证。R03原16项结果完全复现，其中自洽错首锁仍写历史。R04 D1用原图横断面复核，D2增加独立主路径/root代理连接。构造标签不送入审计算法，真实人工标签数为0。D2代理仍不是物理归属证明，不能把“有前缀”宣称为真实裂纹。**Q2 停止位置：** 已导出原算法实际检查过的至多5个端点分支和前后截面诊断；E3新停止候选/融合未启用，改善提前停止或过识别=NOT_PROVEN。**Q3 初始化敏感性：** 不同初始化的首分歧可复现，ROI/mask/配准具体因果贡献=NOT_PROVEN。中间数组已导出；F1–F5未执行，不能用“先变ROI”替代因果结论。

3. **结果数字：** 本轮642个初始化/帧案例、472个组帧，235个预选审核案例；B0/B1输出差异0/642，与R03存档差异0/642。B0视觉确认268/642；D1=159/642；D2=21/642，D2总覆盖变化-38.474个百分点（预警线-5）。所有“距离”仅是共同确认输出差，非物理误差。完整R03窗口覆盖44.96%，完整R02 15808案例覆盖4.06%；仅11/112个初始化且窗口截短。GROUP_A确认不足，不能以多数未确认计0像素。实验阶段失败后未扩大矩阵。

| method | N | constructed_visible_positives | true_candidate_retained | constructed_negatives | false_candidate_admission | wrong_first_lock | contract_failures |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 30 | 11 | 11 | 8 | 6 | 0 | 6 |
| 2 | 30 | 11 | 10 | 8 | 1 | 0 | 2 |

注入来源：24种场景，前16种映射R03合同语义；与旧fixture是不同图像构造，旧fixture另行原样复现。表内正负标签仅是synthetic construction，不是实际试件人工GT。完整逐例见lock_injection_results.csv。额外使用同一GROUP_A原图、同一R03路径及(-30,-30)平移做了新方法复核：D1/D2均保留原候选、拒绝平移干扰，后者原图支持率为0；见original_fixture_r04.csv与provenance。这个结果证明新增像素复核能拦住该具体候选注入，并不证明原候选是物理真裂纹。真实可标注样本清单已由frame_manifest和视频提供，但没有伪造双人标注。无独立HOLDOUT，无真实T2-B轨迹；原算法仍主要支持暗线，D1/D2能采样两极性不等于整条算法已支持亮裂纹。

4. **保留/回滚：** 保留旁路候选、原图截面、独立前缀和map hash导出，帮助后续真正隔离G/M/T/P；保留可复跑的失败反例。D1不能单独证明路径身份；D2若大幅降低覆盖或接受相连伪影，均不能推广为生产确认门槛。B2只存在sidecar，不写回原Detector，不控制ROI。未上线步进ROI，未修改长度、ABI或生产DLL。没有用旧尖端附近约束制造稳定。

5. **下一轮最少任务：** (a) 对视频中的首分歧和独立前缀失败制作双人复核标签，真/假/不可辨至少分开，作为归属验证的阻断输入；(b) 改进前缀的证据可用性和歧义处理，在同一构造反例上既保真又拒假，并以真实覆盖下降≤5pp作为预警，未通过则继续阻断E3；(c) E1过关后，用已导出的统一原图域数组逐项交换G/M/T，先定位直接因果再产生新的终止候选。当前不进行无根因参数扫描或B5降采样提速。

## 逐组覆盖（完整执行前缀）

| dataset_id | variant_id | N_total | N_observed_base | N_observed_new | coverage_delta_pp |
| --- | --- | --- | --- | --- | --- |
| group_a | measured | 246 | 1 | 1 | 0.000 |
| group_c | measured | 72 | 42 | 0 | -58.333 |
| group_c | p1_plus_5pct_x | 72 | 42 | 0 | -58.333 |
| ct2 | measured | 12 | 11 | 8 | -25.000 |
| ct2 | shift_x_plus_2pct | 12 | 12 | 8 | -33.333 |
| group_h | measured | 82 | 77 | 4 | -89.024 |
| group_h | shift_y_plus_10pct | 82 | 31 | 0 | -37.805 |
| group_x | measured | 4 | 4 | 0 | -100.000 |
| group_x | shift_y_plus_10pct | 4 | 4 | 0 | -100.000 |
| three_point_bend | measured | 24 | 24 | 0 | -100.000 |
| ct3 | measured | 32 | 20 | 0 | -62.500 |

## 初始化扰动（共同确认，非GT误差）

| dataset_id | variant_id | version | N | C0 | Cv | Cpair | P95 | max | worst_frame_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_c | p1_plus_5pct_x | B0_R02_A0 | 72 | 42 | 42 | 42 | 0.000 | 6.083 | 69 |
| group_c | p1_plus_5pct_x | B1_DIAGNOSTIC | 72 | 42 | 42 | 42 | 0.000 | 6.083 | 69 |
| group_c | p1_plus_5pct_x | B2_D1_STRUCTURE | 72 | 0 | 0 | 0 | N/A | N/A | N/A |
| group_c | p1_plus_5pct_x | B2_D2_PREFIX | 72 | 0 | 0 | 0 | N/A | N/A | N/A |
| ct2 | shift_x_plus_2pct | B0_R02_A0 | 12 | 11 | 12 | 11 | 95.459 | 190.919 | 8 |
| ct2 | shift_x_plus_2pct | B1_DIAGNOSTIC | 12 | 11 | 12 | 11 | 95.459 | 190.919 | 8 |
| ct2 | shift_x_plus_2pct | B2_D1_STRUCTURE | 12 | 11 | 12 | 11 | 95.459 | 190.919 | 8 |
| ct2 | shift_x_plus_2pct | B2_D2_PREFIX | 12 | 8 | 8 | 8 | 0.000 | 0.000 | 1 |
| group_h | shift_y_plus_10pct | B0_R02_A0 | 82 | 77 | 31 | 27 | 1166.901 | 1347.094 | 78 |
| group_h | shift_y_plus_10pct | B1_DIAGNOSTIC | 82 | 77 | 31 | 27 | 1166.901 | 1347.094 | 78 |
| group_h | shift_y_plus_10pct | B2_D1_STRUCTURE | 82 | 77 | 19 | 17 | 1203.142 | 1347.094 | 78 |
| group_h | shift_y_plus_10pct | B2_D2_PREFIX | 82 | 4 | 0 | 0 | N/A | N/A | N/A |
| group_x | shift_y_plus_10pct | B0_R02_A0 | 4 | 4 | 4 | 4 | 298.311 | 298.719 | 1 |
| group_x | shift_y_plus_10pct | B1_DIAGNOSTIC | 4 | 4 | 4 | 4 | 298.311 | 298.719 | 1 |
| group_x | shift_y_plus_10pct | B2_D1_STRUCTURE | 4 | 4 | 4 | 4 | 298.311 | 298.719 | 1 |
| group_x | shift_y_plus_10pct | B2_D2_PREFIX | 4 | 0 | 0 | 0 | N/A | N/A | N/A |

## Gate结论

| gate | status | denominator | reason |
| --- | --- | --- | --- |
| Gate0_reproduction | PASS | 642 | Raw JSON and all original 16 injection outcomes reproduced |
| B1_output_equivalence | PASS | 642 | Timing excluded; paths/status/coordinates equal |
| Gate_A_attribution | FAIL | 30 | Wrong-first detached candidate blocked in constructed component test; broader source identity not certified. Real manually labeled positives=0. |
| Gate_B_coverage | FAIL | 642 | D2 coverage delta -38.474 pp; allowed regression warning is -5 pp |
| Gate_C_termination | BLOCKED | 0 | E1 not passed; no independently labeled real terminal GT, E3 not enabled |
| Gate_D_initialization | FAIL | 642 | Baseline sensitivities reproduced; low B2 Cpair is not a stability pass; E2 not run |
| Gate_E_CPU | FAIL | 631 | Full native API timings, not video playback; no B5 claim |
| T2_B_REAL | BLOCKED | 0 | No real multi-initial external tracker trajectories |
| NO_PRODUCTION_CHANGE | PASS | 462 | Frozen hashes reverified during final validation |