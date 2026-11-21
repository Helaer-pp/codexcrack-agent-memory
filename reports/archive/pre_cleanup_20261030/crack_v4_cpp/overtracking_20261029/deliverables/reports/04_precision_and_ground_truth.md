> 用户最新约束：第五组排除组X是独立实验，禁止参与算法调优。v1/v2/v3在澄清前已观察51/473，现全部退出正式候选；其第五组输出仅作排查记录，不能称独立验证。正式独立实验只采用见第五组之前已冻结的旧发布算法。新版本选择仅可依据原四组+合成测试，本轮四组回归未通过，因此不发布算法变更。

# 精度与真值边界

tip_ground_truth_available=false。五组均无独立根部/尖端/中心线/可见性标签。真实MAE/P50/P95/Max、有符号偏差、过长尾误差、真实召回/无裂纹误确认率均N/A；有效率是算法输出覆盖，非准确率。未确认不算0误差。人工复核模板所有GT字段为N/A，review_status=PENDING，不以冻结结果当标签。

排除组X全部帧禁止用于当前与未来版本选择。本轮旧发布算法是第五组独立外部实验，实验v1-v3因已看案例而撤回；其余排除组X帧也不包装成盲测。原四组仅作为选型回归集，不是独立精度GT。复核集覆盖第五组全序列及四组所有重大输出分歧和固定四分位帧。标注人应先看原图再独立标root/tip/centerline/遮挡；无中心线不能填写长度GT。

## 独立生成的合成真值

| 合成场景 | 配置 | 尖端确认 | 观察 | 已确认尖端MAEpx | 尖端Maxpx | 已确认长度MAEpx |
|---|---|---|---|---|---|---|
| clean | baseline | 0 | 5 | N/A | N/A | N/A |
| clean | candidate | 0 | 5 | N/A | N/A | N/A |
| defocus_restore | baseline | 5 | 5 | 3.42 | 4.63 | 8.37 |
| defocus_restore | candidate | 5 | 5 | 3.42 | 4.63 | 8.37 |
| disconnected_background_line | baseline | 0 | 5 | N/A | N/A | N/A |
| disconnected_background_line | candidate | 0 | 5 | N/A | N/A | N/A |
| fast_growth_and_visible_reduction | baseline | 5 | 5 | 2.94 | 3.35 | 6.20 |
| fast_growth_and_visible_reduction | candidate | 5 | 5 | 2.94 | 3.35 | 6.20 |
| independent_sensor_noise | baseline | 0 | 5 | N/A | N/A | N/A |
| independent_sensor_noise | candidate | 0 | 5 | N/A | N/A | N/A |
| large_turn | baseline | 0 | 5 | N/A | N/A | N/A |
| large_turn | candidate | 0 | 5 | N/A | N/A | N/A |
| long_curved | baseline | 5 | 5 | 2.90 | 2.90 | 6.09 |
| long_curved | candidate | 5 | 5 | 2.90 | 2.90 | 6.09 |
| occlusion_restore | baseline | 3 | 5 | 2.61 | 2.61 | 6.13 |
| occlusion_restore | candidate | 3 | 5 | 2.61 | 2.61 | 6.13 |
| overexposure | baseline | 5 | 5 | 3.34 | 3.34 | 6.69 |
| overexposure | candidate | 5 | 5 | 3.34 | 3.34 | 6.69 |
| precracked_reference | baseline | 5 | 5 | 3.48 | 3.48 | 6.93 |
| precracked_reference | candidate | 5 | 5 | 3.48 | 3.48 | 6.93 |
| short | baseline | 5 | 5 | 3.75 | 3.75 | 6.15 |
| short | candidate | 5 | 5 | 3.75 | 3.75 | 6.15 |
| strong | baseline | 5 | 5 | 2.61 | 2.61 | 6.13 |
| strong | candidate | 5 | 5 | 2.61 | 2.61 | 6.13 |
| weak | baseline | 5 | 5 | 1.88 | 1.88 | 4.33 |
| weak | candidate | 5 | 5 | 1.88 | 1.88 | 4.33 |

通过断言402 / 404，失败2。这些断言包括短/长弯曲保留、遮挡不造端点、恢复、可见长度回落、独立背景线不造长尾、只读查询与Reset。large_turn等场景若表中确认为0，应明确为仍未支持，不能仅凭断言通过宣称成功。完整生成/物理与可见GT/逐次误差见tests/overtracking_synthetic.json。
