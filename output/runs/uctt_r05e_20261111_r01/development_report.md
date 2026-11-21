# R05E 证据解耦与候选安全排查

本轮交付为隔离 C++17 原生 B0/B1/B2 研究。**生产替换 NO。B1=PASS；B2=FAIL。** 新旁路没有 observed 输出或可信历史，生产结果原样保留。候选出现不能视为尖端修复。

## 实现与阶段门

- B0：从当前生产源码独立构建；1565开发帧和冻结A/R05D逐帧非计时hash一致，四个指定案例也在完整序列中复现。
- B1：`research/uctt_r05e/evidence.hpp` 独立当前暗谷、参考暗谷/变化、空间有效性及原因位；参考不可用为NaN+UNKNOWN，参考已有裂纹零差分不删除当前证据。仅暗线方案，没有宣称亮线支持。保留全部旧score算法。
- B2：当前DP局部峰与旧DP峰求并集；方向/空间3px合并；4×4空间桶，每桶强累计、强当前响应、最远停止和弱响应4种代表；K64、原始存储8192、短追踪16点。规则在看本轮GT对比前固定，没有搜索阈值。实际逐帧lineage共1128770条。
- B3/B4：前置门未通过，未实施新归属/终止或可信历史策略；原R03 16例保持15通过/错误首锁1失败。B5完整生产替换验收BLOCKED。
- B1/B2调试选帧与全帧输出等价；诊断采样不进入决定输出的分支。默认trace未访问字段不能视为已审计。

|Gate|状态|分母|
|---|---|---|
|B0_BASELINE_EQUIVALENT|PASS|1565 development frames; all non-timing fields|
|EVIDENCE_DECOUPLED|PASS|1565 chronological frames / 76 visible development selections|
|TRUE_TIP_CANDIDATE_RECALL|FAIL|76 visible development selections|
|CANDIDATE_BUDGET_SAFE|FAIL|76 visible selections + 1565 development full frames|
|ATTRIBUTION_LOCK_SAFE|BLOCKED|0 new B3 cases; unchanged original R03 16 cases|
|TERMINAL_AUDIT_SAFE|BLOCKED|0 B4 cases|
|VISIBLE_GT_ACCURACY|FAIL|76 development VISIBLE, 35 validation VISIBLE|
|OBSERVED_COVERAGE|PASS|2647 chronological shadow replay frames|
|STATE_CAUSAL_REPLAY|PASS|1565 development + 1082 validation frames|
|INITIAL_ANCHOR_STABILITY|NOT_VERIFIED|0 new perturbed-initialization experiments|
|CPU_50MS|NOT_VERIFIED|AMD Ryzen9 7950X; target i7 not tested|
|VALIDATION_ONLY_FROZEN_RESULT|PASS|1082 frames / 40 selected / 35 VISIBLE / 5 UNCERTAIN|
|PRODUCTION_REPLACEMENT_ELIGIBLE|FAIL|stage gates B0-B5|

## 六组结果

|组|全帧|可见/不确定|原A observed|原A ≤5px|current10|raw10|retained10|预算误删10|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|group_a (DEVELOPMENT)|551|19/1|4|2|19|19|18|1|
|ct2 (DEVELOPMENT)|468|20/0|14|0|18|15|8|7|
|group_h (DEVELOPMENT)|410|18/2|16|0|18|14|10|4|
|ct3 (DEVELOPMENT)|136|19/1|18|9|19|19|19|0|
|group_c (VALIDATION_ONLY)|562|20/0|18|6|19|19|16|3|
|three_point_bend (VALIDATION_ONLY)|520|15/5|3|0|15|10|6|4|

current10表示半径10原图像素内存在分数≥3的像素。raw/retained表示候选端点≤10px，未代表归属或终止正确。所有候选距离/误差只在快照完成后由独立比较器读取标注计算。没有人工无裂纹负例，因此真实误报率NOT_VERIFIED；距离GT较远的候选不直接叫误报。UNCERTAIN不填0误差、不进入可见分母。

## 指定反例

- ct2/395: current10=True; raw nearest=8.312289711836618 px; retained nearest=8.312289711836618 px; original A error=928.9363675792426 px. `traces/B2_ct2__000395.json` 与图册同帧可复核。
- group_h/78: current10=True; raw nearest=12.147304905860315 px; retained nearest=12.147304905860315 px; original A error=900.7066836598076 px. `traces/B2_group_h__000078.json` 与图册同帧可复核。
- group_a/504: current10=True; raw nearest=7.118098585681481 px; retained nearest=7.118098585681481 px; original A error=N/A px. `traces/B2_group_a__000504.json` 与图册同帧可复核。
- ct3/65: current10=True; raw nearest=1.6415242838213608 px; retained nearest=1.6415242838213608 px; original A error=8.408008204942192 px. `traces/B2_ct3__000065.json` 与图册同帧可复核。

## 新增退化与停止原因

开发可见76例：current10=74，raw10=67，retained10=55；预算丢失12例。逐帧反例见first_regression.csv，所有帧预算计数见evidence_channels_per_frame.csv，实际代表坐标见candidate_lineage.csv。若方向合并代表偏移跨越10px边界，也计为损失；没有把重复节点原坐标冒充保留代表。

旧A输出、observed覆盖、ROI、长度、历史及非计时ABI数据均未变化；这只证明旁路隔离。新模块没有确认输出，故“新增错锁=0”不能被当成安全性成功。原始coherent_wrong_first_lock仍会错误写入历史。

## 冻结后验证

规则、生成源码、DLL及比较器hash在validation_freeze.json中冻结。之后仅对验证组C/三点弯1082帧回放，40选帧对比，未据验证结果改规则。冻结状态最终再次逐文件核验。排除组X图像/标注读取0；六组均历史曝光，不称独立未见TEST。人工标注从未用于训练、拟合、阈值扫描或运行时选择。

## 性能与限制

见performance_report.md。正常与失败状态均计入；参考帧GetBaseline是缓存查询，单独列出、不冒充推理。阶段计时互斥，other包含旧主路径和未单列开销。初始化扰动本轮NOT_VERIFIED，不能以R05D历史四例替代B2稳定性证明。目标i7未测试，本机Ryzen结果不能推断i7达标。

## 下一步（仅开发组，最多三项）

1. 优先处理已有raw候选被固定桶预算删除的逐帧反例：下一轮研究结构链的多停止位置保留，先证明候选可达性，再允许归属；不从验证组调规则。
2. 对current响应存在但没有近端峰的G2_RAW案例，检查真实停止位置与DP局部极值定义；继续区分像素恢复和端点可达性。
3. 前两项通过后再实现可信首锁归属和独立终止；必须先通过原R03错误首锁反例，禁止用大幅降低observed覆盖换取安全性表象。

## 对候选未生成的直接定位

76个有图像地图的选帧，用同一个原生distalLine递推重算currentEvidence；current-source峰坐标/增益与B1快照集合完全一致，之后才离线查询GT邻域。74个VISIBLE有图可查，2个G0没有证据地图。

|组/帧|当前达标像素10|同时gain≥12|再通过纵向极值|再通过向前停止极值|首先丢失条件|
|---|---:|---:|---:|---:|---|
|ct2/196|61|61|20|0|not_forward_stopping_maximum|
|ct2/338|57|55|18|0|not_forward_stopping_maximum|
|ct2/431|59|59|20|0|not_forward_stopping_maximum|
|group_h/41|6|0|0|0|gain_below12_at_supported_pixels|
|group_h/78|10|0|0|0|gain_below12_at_supported_pixels|
|group_h/115|4|0|0|0|gain_below12_at_supported_pixels|
|group_h/304|49|49|20|0|not_forward_stopping_maximum|

这定位的是固定提取器中的实际过滤步骤，不是物理裂纹终止真相；未据此下降阈值或更换容差。控制表current_dp_control.csv、查询表current_peak_filter_diagnosis.csv、实际gain图maps/*__current_dp.npz可复核。

## 预算误删归因

全部误删的近端raw_id、合并代表、桶内保留节点、分数及裁剪原因见budget_loss_lineage.csv。B1/B2原始候选集合逐帧精确对照；只发生压缩变化，因此不能用“原本没有候选”解释这些退化。

- group_a/398 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 1749 → retained 62；原A hit5=False, hit10=False。
- ct2/1 (dev): ["BUCKET_CAPACITY"]；近端raw 4；全帧raw 149 → retained 48；原A hit5=False, hit10=False。
- ct2/43 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 137 → retained 47；原A hit5=False, hit10=False。
- ct2/76 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 130 → retained 45；原A hit5=False, hit10=False。
- ct2/131 (dev): ["BUCKET_CAPACITY"]；近端raw 2；全帧raw 118 → retained 46；原A hit5=False, hit10=False。
- ct2/157 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 133 → retained 50；原A hit5=False, hit10=False。
- ct2/251 (dev): ["BUCKET_CAPACITY"]；近端raw 2；全帧raw 120 → retained 47；原A hit5=False, hit10=False。
- ct2/271 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 155 → retained 47；原A hit5=False, hit10=False。
- group_h/141 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 73 → retained 46；原A hit5=False, hit10=False。
- group_h/216 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 70 → retained 45；原A hit5=False, hit10=False。
- group_h/252 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 92 → retained 47；原A hit5=False, hit10=False。
- group_h/401 (dev): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 81 → retained 50；原A hit5=False, hit10=False。
- group_c/221 (val): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 122 → retained 31；原A hit5=False, hit10=True。
- group_c/456 (val): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 132 → retained 32；原A hit5=False, hit10=False。
- group_c/528 (val): ["BUCKET_CAPACITY"]；近端raw 3；全帧raw 127 → retained 31；原A hit5=False, hit10=False。
- three_point_bend/1 (val): ["BUCKET_CAPACITY"]；近端raw 3；全帧raw 130 → retained 28；原A hit5=False, hit10=False。
- three_point_bend/178 (val): ["BUCKET_CAPACITY"]；近端raw 1；全帧raw 123 → retained 27；原A hit5=False, hit10=False。
- three_point_bend/306 (val): ["BUCKET_CAPACITY"]；近端raw 2；全帧raw 117 → retained 26；原A hit5=False, hit10=False。
- three_point_bend/407 (val): ["MERGE_REPRESENTATIVE_OUTSIDE10"]；近端raw 1；全帧raw 134 → retained 30；原A hit5=False, hit10=False。
