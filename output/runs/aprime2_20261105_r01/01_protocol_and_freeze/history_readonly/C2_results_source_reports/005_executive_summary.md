# C2 开发验证结果

结论：**KEEP_A / C2_RESEARCH_ONLY / CPP_C2_NOT_BUILT**。冻结生产A、DLL、ABI、参数和旧媒体未修改。本轮完成独立C2研究实现、源码合同审计、新DEV、锁定后的新受控TEST、已曝光真实六组回归与媒体。M2/M4仍有未解决失败，不能替换生产算法。

## 本轮做了什么

保留A原始double尖端为候选，合并时保留原坐标和来源；从旧C的A路径/根部无关DP种子及延伸中提取当前终点候选。终点审核使用原图1px局部采样，独立于SearchROI。参考模块在固定材料背景候选区域做两点刚体初值、纹理匹配、FIT局部平移、空间独立HOLDOUT验证，再做独立背景仿射光度补偿。归属模块比较新增前缀与参考已有线的延续，保持参考UNKNOWN不否决A。尖端投影相对当前P1/P2基准线；旧弧长另列。无标定不输出mm，无载荷相位，物理精度N/A。

本原型未完成生产级归属校准：候选级完整三态排序、独立DP平行分支覆盖和参考不足时的局部替代验证仍不充分。未以增加UNKNOWN或保留A冒充新精度收益。

## 新受控结果（TEST只执行一次）

DEV 108案例×3帧=324；TEST 162案例×3帧=486，其中378可观察正例、81阴性、27不可观察正例。DEV与TEST使用不同背景生成过程、图像尺寸及长度组合；所有旧合成/真实/截图均只读曝光诊断。TEST生成前锁定检测、生成、GT和评价源；检测前封存图像、点、GT和SHA。

**DEV安全门槛已经失败**（13帧正确A被改错）；因此后续新TEST属于冻结研究方案的一次诊断验证，不提升为正式准入成功。未根据新TEST修改任何检测规则。

| metric | A | C2 |
|---|---|---|
| observable_positive | 378 | 378 |
| confirmed | 360 | 371 |
| correct_le8 | 330 | 357 |
| coverage | 0.9523809523809523 | 0.9814814814814815 |
| correct_rate | 0.873015873015873 | 0.9444444444444444 |
| confirmed_MAE | 19.011019524475874 | 5.738952892352622 |
| confirmed_P95 | 179.42852857040893 | 5.727333131413475 |
| all_positive_loss | 7.702296157218655 | 3.5353292820517486 |
| negative_n | 81 | 81 |
| negative_FP | 27 | 27 |


全正例损失：未确认32px、错误64px封顶。C2−A为-4.1670px，按共享当前图pair/其他case聚类、背景与机制分层bootstrap，95%CI [-5.0715, -3.0542]，2000次；117个可观察正例独立聚类，378帧不能当独立样本。

C2修复强假尾20/27帧，涉及7/9独立pair，6/9 pair三帧全部两端正确；A为0。匹配真长27/27正确，无新增截短。弱渐浅24/27、S弯27/27、75°27/27保持A；55°从27/27降至25/27。**两帧正确A被错误改写**，均为 `TEST_heldout_random_fibers_curve55_2` 的2/3帧，误差161.45/163.08px；触发零误伤硬门槛，正式效果判定失败。

候选上界：372/378可观察正例有≤8px候选，最终选对357/372。剩余21个正例失败分为6个没有准确候选、15个已有准确候选但决策失败。候选保留改善了流转，但没有解决全部选择问题。

## 真实六组（全部已曝光，无物理GT）

| group | frames | A_tip_valid | C2_tip_valid | A_C2_changed | registration_valid | photometry_valid | ownership_supported |
|---|---|---|---|---|---|---|---|
| group_a | 551 | 497 | 497 | 0 | 0 | 0 | 0 |
| group_c | 562 | 543 | 543 | 0 | 0 | 0 | 0 |
| ct2 | 468 | 404 | 404 | 0 | 1 | 1 | 0 |
| group_h | 410 | 345 | 345 | 0 | 0 | 0 | 0 |
| group_x | 524 | 269 | 269 | 0 | 0 | 0 | 0 |
| three_point_bend | 520 | 445 | 445 | 0 | 1 | 1 | 0 |


3035帧含6个参考帧，C2尖端/投影输出与A均未改变。几何/光度仅2/3035通过，归属SUPPORTED为0；所有帧归属UNKNOWN。此结果是保底行为回归，不是现实精度改进。排除组X为退役历史诊断，三点弯仍为已曝光不调参数据，不称新holdout。

## 不发布的原因

1. DEV和新TEST均出现正确A改错；55°弱背景纤维会产生假参考归属边界。
2. 真实参考有效性覆盖极低；参考有效域布局/匹配观测不足，不能用不可信差分改写尖端。
3. 没有新真实材料holdout、物理尖端标注、加载相位或本组标定。
4. 按任务书效果不过就不开发C2原生核心；没有C2 DLL，没有C2完整C++15Hz结论。

## 交付

- [全部视频与逐帧原图/A/C2对照](../07_media/index.html)：真实6组3035 PNG、新DEV324 PNG、新TEST486 PNG；含所有失败，不只选成功图。合成视频串接独立案例，每段3帧，非单件真实扩展全过程。
- [TEST逐帧结果](../04_results/TEST_frame_predictions.csv)、[逐候选结果](../04_results/TEST_all_candidates.csv)、[证据有效性](../04_results/TEST_evidence_and_validity.csv)、[全配对结果](../04_results/TEST_matched_pair_results.csv)、[失败阶段](../04_results/TEST_candidate_selection_failures.csv)。GT字段带EVAL_ONLY，候选oracle仅OFFLINE_ONLY，运行时不接收GT。
- [六组逐帧回归](../05_regression/all_six_groups_per_frame_A_C2.csv)、[全部不一致帧索引](../05_regression/A_C2_all_inconsistent_frame_index.csv)（本轮为空，仅表头说明另附）、[历史157/19回归](../05_regression/exposed_cases_diagnostics.csv)。
- [12问逐项答复](ownership_identifiability_results.md)、[失败根因](candidate_selection_failure_analysis.md)、[源码合同](../01_audit/source_contract.md)、[构建复现](../README_build_and_run.md)。

不可观察正例另列：27帧中A确认0帧、C2确认1帧。该额外确认不能算正确可见尖端，也未计入81个阴性的分母；它是额外的可观察性风险，不因主指标排除就隐藏。详见TEST_unobservable_positive_subset.csv。

## 耗时（范围分开）

冻结A原生完整核心的本次实测：

| group | n | P95_ms | P99_ms | Max_ms | over66_67 |
|---|---|---|---|---|---|
| group_a | 550 | 9.80933 | 10.108478999999999 | 10.5992 | 0 |
| group_c | 561 | 6.3489 | 6.716559999999999 | 6.8896 | 0 |
| ct2 | 467 | 22.41346 | 23.059627999999996 | 23.3027 | 0 |
| group_h | 409 | 40.47106 | 42.269200000000005 | 43.1627 | 0 |
| group_x | 523 | 39.46216999999999 | 42.396938 | 50.3625 | 0 |
| three_point_bend | 519 | 9.503529999999998 | 10.180154 | 11.3477 | 0 |

C2仅Python研究实现，附加全流程Max约49–173ms；未开发C2完整原生核心，不能宣称15Hz。A这次全部当前帧Max≤66.67ms，不代表采集/解码/队列端到端保证，亦不代表C2可直接追加在66.67ms预算内。
