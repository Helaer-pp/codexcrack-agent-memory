# 异常帧根因与证据边界

本轮定位的是可复现计算机制。没有人工/物理端点GT，不能把第一处失支持、A/Frangi分歧点或较短路径直接当正确尖端。

## ct2 / num=6

A确认=True，停止=evidence_ended，末端审计=terminal_supported，路径块数=10。全路径原图暗谷支持比例=0.963963963963964；首次持续弱段=；最长弱段=。原生内部累计插值列=11，最长连续空档=8。

旁路材料检验=REGISTRATION_UNKNOWN/NO_INDEPENDENT_CORRESPONDENCE，原生与两点映射中心差=5.322132632729518px；法向±3px可恢复暗谷的中心弱样本=2/222。因此中心线无支持可能包含偏线与弱线，不能一刀截断。

[整路径证据](../07_diagnostics/key_cases/ct2_6_whole_path_evidence.png) · [原生逐块追踪](../07_diagnostics/key_cases/ct2_6_native_trace.json) · [原图/路径对照](../07_diagnostics/ct2/frames/000006.png)

## ct2 / num=18

A确认=True，停止=evidence_ended，末端审计=terminal_supported，路径块数=10。全路径原图暗谷支持比例=0.972972972972973；首次持续弱段=；最长弱段=。原生内部累计插值列=10，最长连续空档=8。

旁路材料检验=REGISTRATION_UNKNOWN/NO_INDEPENDENT_CORRESPONDENCE，原生与两点映射中心差=4.580982029706457px；法向±3px可恢复暗谷的中心弱样本=2/222。因此中心线无支持可能包含偏线与弱线，不能一刀截断。

[整路径证据](../07_diagnostics/key_cases/ct2_18_whole_path_evidence.png) · [原生逐块追踪](../07_diagnostics/key_cases/ct2_18_native_trace.json) · [原图/路径对照](../07_diagnostics/ct2/frames/000018.png)

## ct2 / num=84

A确认=True，停止=evidence_ended，末端审计=possible_forward_continuation，路径块数=10。全路径原图暗谷支持比例=0.972972972972973；首次持续弱段=；最长弱段=。原生内部累计插值列=11，最长连续空档=10。

旁路材料检验=REGISTRATION_UNKNOWN/NO_INDEPENDENT_CORRESPONDENCE，原生与两点映射中心差=4.704035970874065px；法向±3px可恢复暗谷的中心弱样本=2/222。因此中心线无支持可能包含偏线与弱线，不能一刀截断。

[整路径证据](../07_diagnostics/key_cases/ct2_84_whole_path_evidence.png) · [原生逐块追踪](../07_diagnostics/key_cases/ct2_84_native_trace.json) · [原图/路径对照](../07_diagnostics/ct2/frames/000084.png)

## group_x / num=51

A确认=False，停止=direction_ambiguous，末端审计=direction_ambiguous，路径块数=18。全路径原图暗谷支持比例=0.6034858387799564；首次持续弱段=；最长弱段=。原生内部累计插值列=353，最长连续空档=9。

旁路材料检验=REGISTRATION_UNKNOWN/NO_INDEPENDENT_CORRESPONDENCE，原生与两点映射中心差=0.0px；法向±3px可恢复暗谷的中心弱样本=57/357。因此中心线无支持可能包含偏线与弱线，不能一刀截断。

[整路径证据](../07_diagnostics/key_cases/group_x_51_whole_path_evidence.png) · [原生逐块追踪](../07_diagnostics/key_cases/group_x_51_native_trace.json) · [原图/路径对照](../07_diagnostics/group_x/frames/000051.png)

## group_x / num=473

A确认=True，停止=evidence_ended，末端审计=terminal_supported，路径块数=22。全路径原图暗谷支持比例=0.6488970588235294；首次持续弱段={"state": "RAW_VALLEY_WEAK_OR_ABSENT", "start_arc_px": 158.0, "end_arc_px": 190.0, "length_px": 32.0, "start_index": 79, "end_index": 95}；最长弱段={"state": "RAW_VALLEY_WEAK_OR_ABSENT", "start_arc_px": 158.0, "end_arc_px": 190.0, "length_px": 32.0, "start_index": 79, "end_index": 95}。原生内部累计插值列=265，最长连续空档=10。

旁路材料检验=REGISTRATION_UNKNOWN/NO_INDEPENDENT_CORRESPONDENCE，原生与两点映射中心差=0.0px；法向±3px可恢复暗谷的中心弱样本=58/431。因此中心线无支持可能包含偏线与弱线，不能一刀截断。

[整路径证据](../07_diagnostics/key_cases/group_x_473_whole_path_evidence.png) · [原生逐块追踪](../07_diagnostics/key_cases/group_x_473_native_trace.json) · [原图/路径对照](../07_diagnostics/group_x/frames/000473.png)

## 源码层可确认的机制

1. 每个tile仅保留一条ridge DP最优路径，没有次优支路得分与路径间裕量。沿已选路径支持点>=3且gain>=4即可继续，每次最多向前48像素；局部连续空档超过10才阻断。多个短间隙的总量可能很大，累计265列不等于存在265像素单一断口。

2. 继续方向来自末尾约14个点，故局部纹理若持续得分，方向可逐块转弯。真实弯裂纹也依赖此能力，增加普遍转角限制可能同时误伤真裂纹。

3. t.score是参考变化与形态线响应组合，再按噪声自适应阈值归一；它不是物理裂纹概率。参考已有裂纹允许区又采用当前形态响应，静态线与真实裂纹可能无法仅由图像区分。

4. 当前生产决策policy=1为SHADOW：末端audit记录并不普遍取代legacy正式确认。代码只有policy=VERIFIED_EXPERIMENTAL才用shadow_tip覆盖正式tip。因此橙色候选未确认、最终帧被legacy确认，需要分别查原始stop、temporal和audit，而不能仅看图上是否有线。

5. terminalAudit主要检查最终16样本及向前三条±15°短射线；不能替代整路径物理验证。B2首次弱段只定位可疑位置，未证明在那里发生真正错误分叉。

## 几何敏感性

新cold_start_geometry_sensitivity.csv明确为空历史条件，比较相同空历史的refine/点扰动，不能冒称时序A误差。CT2历史同历史干预链原样保留并附SHA，指出首个tile采样/阈值/路径事件分歧；这些是配置差异，不是物理真值。

## 本轮无法单独确认的原因

没有竞争支路得分，不能把第一失支持定位为第一错误分叉；材料匹配UNKNOWN不能区分错位与低纹理；没有同步载荷不能证明长度回落由闭合引起。真实正确尖端、真实总裂纹长度均N/A。

详细确认链、累计间隙与时序前缀机制见 [异常帧最终追因](abnormal_frames_final_causes.md)。
