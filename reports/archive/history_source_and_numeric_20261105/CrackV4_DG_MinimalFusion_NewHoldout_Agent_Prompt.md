# Agent 开发任务书：CrackV4 冻结 A × D+G 最小证据融合的前瞻验证

**项目代号：** `CrackV4_DG_Evidence_Gated_Fusion_Prospective_Study`  
**任务类型：** 有约束的研发 + 独立新测试 + 源码级消融 + 只读旁路；**不是直接发布改版 DLL**  
**生产算法：** `KEEP_FROZEN_A`；任何输出改变须经过独立证据和实时性全部门槛  
**参考环境：** C++17 / OpenCV 4.4 / Windows DLL；最低 15 Hz、核心预算 **66.67 ms/帧**  
**工作语言：** 中文报告、代码标识及固定状态码使用英文  
**当前已知研究目录（Agent 在用户本地执行时使用）：** `D:/workspace\comparison_fusion_study_20261103`  
**最后要求：** 真正实现、运行并留下可复现实验证据；不要仅写分析或凭视觉推测宣布优化成功。

---

## 0. 角色、目标和最重要的约束

你是工业疲劳裂纹视觉追踪算法研发 Agent。现有两个架构：

1. **A0**：已冻结的 C++17/OpenCV4.4 生产版 DP 连续路径跟踪。输入参考帧、当前帧、逐帧 P1/P2，输出经确认的单条中心线、二维尖端坐标和长度；现有实现中有已知错误长尾和渐浅裂纹提前停止问题。
2. **Frangi 全体系**：参考单向差分 D → Frangi 响应 F → 根部几何约束 G → 闭运算桥接 C → 骨架/末端 S；四组旧 Python 管线具有试件专用根部与 ROI，F1 移植并不等于通用自动 ROI，Frangi 全套尚未证明优于 A0。

**本轮不重新优化完整 Frangi；优先研究从中剥离出的轻量机制 D+G：**

- `D`：在可评价的参考对齐条件下计算当前帧新变暗证据；原受控消融的 D 为共同刚体对齐后的单向差分阈值 `>5`，但此次不得未经审查地把数值复制为生产阈值。
- `G`：通过参考图像、P1/P2、有效材料域、根部/缺口几何推导的候选路径约束。它不是“以 A 的路径或某个已知错误尖端为中心裁一个窄 ROI”。
- 最终目标是论证 **D+G 能否在不损失弱线、弯线与既有有效确认的前提下，独立识别 A 的错误长尾风险**，以及能否支持**最小的、明确可控的输出变更**。

### 0.1 硬性红线

1. **冻结 A 不变。** 不修改其生产源码、DLL、导出符号、ABI、基线参数、`motion/refineRoot/tile/seed/ridge/process`、历史状态行为、`CopyPath`，不改变视频正式渲染合同；原始数据只读。
2. 禁止以材料组名、实验名称、文件夹名、帧 ID、已知错误样本的坐标，来切换阈值、补丁或 ROI。允许统一规则从参考图像和基准点**自动**计算几何量，但不得藏匿按组常量。
3. 任何 A 输出变化先在**独立 research sidecar/EXE/候选 DLL** 中完成；生产正式 A 始终输出完全原样。只读 shadow 不得宣传为精度改善。
4. 不要求未来项目提供人工标注的真实裂纹尖端 GT；可用程序生成的已知可见几何终点、独立测量的受控物理线靶/标记和严格负对照。无法观测实际物理尖端时必须写 `N/A`。
5. 不得用更低确认率伪造更高条件 MAE；正确确认、漏检、错误确认、条件尖端误差、长尾、短截及全部端到端运行时必须并报。
6. 不得将已经看过的 `20261103` TEST、排除组X 51/473、CT2 6/18/84 等再称为盲测或用于新一轮最终模型选择；它们只可作为 `HISTORICAL_EXPOSED_REGRESSION`。
7. 禁止手工修正任一正式视频的裂纹中心线和尖端；确认时输出**一条实线中心线和一个终点**，不确认时只输出原图；候选线、阴影、热力图和对比诊断仅出现在独立的研究材料中。
8. 禁止宣称“Frangi=0 虚警”、“视觉上更短=正确尖端”、“两个算法都确认=两个算法都正确”、“P1/P2 距离变化=真实 CMOD/相位”、“浮点坐标=物理亚像素精度”。
9. 不得使用未运行的硬件、未获取的新试件或未完成的 C++ 实测作为通过证据；无法获得时标注 `NOT_AVAILABLE` / `NOT_TESTED`，不可用数字模拟冒充真实采集。
10. **优先用已有环境实际执行与交付**。若输入/源代码缺失，先核查清单，继续完成可执行部分并列出缺口，不要悄悄推测数据。

---

## 1. 第一阶段：复核上轮锁定结果并冻结本轮问题

### 1.1 必须读取的原始材料

定位并读取（若实际存在）以下文件；可用相对路径映射用户本地上述工作区：

```text
00_manifest/protocol_frozen.json
00_manifest/preregistered_metrics.json
00_manifest/coordinate_contract.json
00_manifest/frozen_A_identity.json
00_manifest/group_c_transfer_policy_frozen.json
02_synthetic_gt/manifest_DEV.json
02_synthetic_gt/manifest_TEST.json
03_controlled_inputs/paired_outputs_raw_coordinates.csv
04_ablation/ablation_summary.csv
04_ablation/sensitivity_summary.csv
05_fusion_shadow/selection_frozen.json
05_fusion_shadow/fusion_acceptance.md
05_fusion_shadow/DEV_mechanism_selection.csv
06_metrics/paired_synthetic_gt.csv
06_metrics/confirmed_negative_counterexamples.csv
06_metrics/paired_case_intervals.csv
06_metrics/TEST_per_background_paired_intervals.csv
06_metrics/tip_and_length_metrics.csv
06_metrics/real_coverage_and_geometry.csv
06_metrics/paired_per_frame.csv
07_performance/latency_summary.csv
07_performance/regression_and_abi.json
09_media_diagnostics/key_cases/*
10_reports/overall_comparison.md
10_reports/key_findings.md
10_reports/failure_analysis.md
10_reports/source_direction_audit.md
source_and_build/research/*
```

如目录不同，以实际清单为准；若只找到轻量 ZIP，则报告缺少原始 BMP/合成 PNG，不能把“缓存统计复算”等同于“从输入图像重新运行算法”。**本轮前瞻 TEST 需要能够从图像重新计算输出。**

### 1.2 作为已见历史证据的数值（不得用于重新挑选 TEST 最优阈值）

上轮 TEST **右侧**、程序可见 GT：

| 方法 | 可观察正例 | 正例确认 | 阴性误确认 | 条件尖端 MAE |
|---|---:|---:|---:|---:|
| A0 | 265 | 223 | 6/90 | 9.710 px |
| D | 265 | 178 | 0/90 | 3.420 px |
| D+G | 265 | 250 | 10/90 | 11.236 px |
| D+F+G | 265 | 235 | 20/90 | 23.736 px |
| D+F+G+C | 265 | 235 | 20/90 | 21.984 px |
| F-WIDE | 265 | 235 | 20/90 | 21.984 px |

已知受控风险：

- `false_bridge`：A0 的 15 个确认案例尖端 MAE≈121.632 px；D+G≈1.071 px；D+F+G≈1.071 px；加 C 后≈121.647 px。**但一项场景成功不等于可无害修复 A 的长尾。**
- `hole_motion` 阴性：完整 F 在原 TEST 为 15/15 错误确认；D+F 也有 12 例，显示加入 Frangi 有独立的运动边缘伪响应风险。
- `weak`：A0 与完整 Frangi 的特定 15 个可观察合成样本均 0/15 确认；禁止以撤销结果规避难例。
- `fading`、`curve`、`angle50`：Frangi 存在截短/大角度漏检等风险；加入强方向限制不能默认安全。
- 排除组X 473：A0 `(2344.05,2409.42)`、中心线弧长 1084.13 px；F0/F-WIDE `(1984.26,2080.465)`、有序弧长≈310.255 px；扩大 F 纵向搜索范围后 F 尖端不变。**差异并非纯窄 ROI 截断，真实尖端优劣仍 N/A。**
- 排除组X 51：A0 未正式确认；F 有约 25.83 px 的短响应；不将任一版本判为真实正确。
- 已看过的 A∧D+G 事后配对探索：在该批 TEST 中 223/223 A 正例确认被交集保留、A 的 6 个阴性误确认与 D+G 仅有 2 个重合。这仅产生**前瞻假说**，不能作为新规则已验证、也不能直接据此设定阈值。
- 原 A 核心耗时上轮最大值：开发组A 13.168 ms，验证组C 8.831 ms，CT2 32.938 ms，开发组H 55.367 ms，排除组X 61.584 ms；尤其排除组X仅约 **5.086 ms** 预算余量。不同测试环境不得强行直接排名。

### 1.3 预注册三个相互独立的命题

为每个命题在 `00_protocol/hypotheses_locked.json` 写入：描述、可能证伪的样本、对照、指标、统计单位、是否需要物理信息及通过阈值；在**生成任何新 TEST 输出之前**锁定文件哈希。

- **H-D：** 单向差分 D 能在参考对齐可信的条件下识别静态原有纹理／假连接的可疑延伸；若参考对齐失败、加载状态不等价或光度改变，D 不得对真实裂纹作硬否定。
- **H-G：** 由参考图和锚点独立确定的根部几何与材料域约束，能减少因孔缘／背景纹理产生的错误长尾，且不系统性截断曲折、渐浅或双侧生长。
- **H-COMBO：** D+G 对 A 路径的**定位一致性检查**可能提供真实风险区分度；**“两者确认”本身不足以判断 A 尖端是否正确**，必须测试相对末端位置、路径支持与几何可评价性。

本轮结果可以否定任一命题；最终 `KEEP_A / SHADOW_ONLY / RESEARCH_CANDIDATE / INSUFFICIENT_EVIDENCE` 均是允许结果。

---

## 2. 输入、输出与评价定义：不统一测量语义禁止比较

### 2.1 输入合同

```text
reference_image: 原始 BMP 字节和 SHA256
current_image[t]: 当前原始 BMP 字节和 SHA256
P1_ref/P2_ref: 参考两点，必须有坐标系说明
P1_t/P2_t: 当前两点，每帧独立输入
frame_id: 仅用于关联和日志，不允许驱动算法分支
optional: 真实加载力/硬件触发相位（缺失则 UNKNOWN）
optional: 受控生成已知图像几何与像素端点（仅评估器可读）
```

两套算法共用相同原始帧、相同基准点和同一帧加载瞬间。**不能把相同 P1/P2 偷换成相同内部配准**：A0 原生 refine-on 与旧 F0 中点平移不同。本轮按以下两个通道报告：

1. **系统级对照**：A 原样独立执行；D+G 按固定协议独立执行。结论属于完整处理链比较。
2. **模块级因果对照**：固定一个明确运动映射/采样网格，在同一图像取样下仅打开或关闭 D、G 或选择硬／软证据；结论仅属于该模块，不冒充真实 A 的实际改变。

### 2.2 坐标与量测合同

- `RAW_CURRENT` 原图当前坐标，x 右、y 下；`RAW_REF` 参考原图坐标；`ROI_LOCAL` 对齐参考网格减 ROI 原点。
- 末端二维误差：预测尖端与程序**可观察端点**的欧氏像素距离；另报已形成端点（若不可见则只作独立状态，不用于伪造当前精度）。
- 弧长：完整有序中心线相邻采样点欧氏距离和；**不可**用水平投影替代。
- 物理轴投影：`dot(tip - root, unit_growth_axis)`；左右各自单独报告；不把 F 双侧长度总和与 A 单侧比较。
- 路径空间位置、末端差、根部误差与 ROI 边界截断分别量化。
- `GetResultV2` 的小数位或 float 回投不等于物理亚像素精度。
- 正例已形成但闭合不可见、完全不可观察时，不把不可见部分虚构成可追踪的 GT。
- `PHASE_UNKNOWN` 时只允许“同一原始帧同一瞬间”的 A/F 比较；跨帧同相位准确率 `N/A`。

### 2.3 严格分离判定状态

推荐：

```text
A_STATUS: A 的原生状态（不得改写）
DG_EVALUABLE: PASS / FAIL / UNKNOWN
DG_EVIDENCE: SUPPORT / DISAGREE / INSUFFICIENT / NOT_APPLICABLE
GEOMETRY_STATUS: VALID / AMBIGUOUS / INVALID
REGISTRATION_STATUS: VALID / AMBIGUOUS / INVALID / UNKNOWN
ROI_STATUS: VALID / TRUNCATED / UNKNOWN
FUSION_SHADOW: PASS / SUSPECT_TAIL / SUSPECT_MISSED / ABSTAIN
RESEARCH_OUTPUT_CHANGED: yes / no（只对独立研究变体）
PHYSICAL_TIP_ACCURACY: N/A，除非有真正独立可观测真值
```

无可评价的差分信号时必须 `ABSTAIN`，不能将“D 没看见”解释成“真实裂纹不存在”。

---

## 3. P0：自动根部、材料域、动态 ROI 与 D+G 可评价性

### 3.1 通用几何初始化

在**独立于 A0 路径**的参考帧分析中，执行：

1. 利用 P1/P2 建立试样局部轴系，记录镜像、左右侧、局部尺度与不确定性。
2. 在参考图像和材料轮廓中寻找可解释的孔／缺口根部候选，避免依据文件名选“CT / MT / 圆孔”专用常量。
3. 根部候选位置、根部几何类别、可信度和竞争候选分数分别保存；若无法确定，输出 `AMBIGUOUS/UNKNOWN`，不得“偷偷使用排除组X坐标”或以 A 的尖端反推根部。
4. 对材料外孔腔、试样边界、参考遮挡建立有效材料域；材料域本身也可能误判，单列验证指标。
5. 单侧及多侧统一在坐标变换后的**每个 root 与 growth direction** 下运行相同规则，支持一侧不存在或一侧未确认。

### 3.2 自动 ROI 与自适应长度

用户目标是 ROI 根据基准点、根部和几何**自动创建、随裂纹生长动态扩展**，不是固定 `1900×200` 之类人工数值。

必须实现并独立测试以下契约：

- `ROI_initial = f(reference_image, P1_ref, P2_ref, geometry_confidence, image_bounds)`；**不能依赖历史 A 检测路径或数据组名**。
- `ROI_update = f(previous_independently_supported_state, valid_material_bounds, growth_direction, uncertainty, image_size)`；允许由经确认的本方法历史信息增长，但不能把未证实的 A 错误尾部作为扩张依据。
- 扩张前留有统一规则的曲折/转角裕量；不允许“只能向右水平生长”而导致真实转向的系统漏检。
- ROI 不应无限扩大：需要上界、可评价性标记和时间预算治理；几何不可信时输出状态并跳过危险硬判定。
- 固定已知 GT 几何上记录**端点覆盖率、主干覆盖率、错误裁剪率、边界触发次数、重定位误差与开销**。
- 可分别跑 `AUTO_ROI`、`WIDE_CONTROL`、`ORACLE_ROI_ONLY_FOR_DIAG`（最后一项仅作理论上界，禁止生产取 GT）；不可将 oracle 指标算进通用模型分数。
- 动态 ROI 的行为按统一策略冻结；训练阶段不可按试件名称设置不同增长系数。

### 3.3 D 差分的可靠性检查

对 D 不仅计算差分阈值图，还计算：

- 原图与参考图在验证材料区域的配准可评价性、可独立复核的运动误差（若已知运动存在）、光照变化指标。
- 当前单向变暗支持：沿候选路径分主干/近末端采样，双侧横断面的局部灰度支持，路径外邻域阴性对照。
- 参考差分中 `hole_motion`、静态双线、静态根部纹理、反光、强度变化的误支持；已知变换下的虚假差分长度与面积。
- 对灰度高码值的拒绝，不以 `>=250` 直接称传感器饱和，需分别记录编码范围及材料/孔腔采样位置。
- `D_eval = FAIL/UNKNOWN` 时**不能凭 D 排除 A 的真实路径**；是否能作为弱证据分开测。
- 在不同相位加载可见性变化下，D 只代表“相对参考出现的新变暗”，不是已形成裂纹物理长度。

**不得单纯通过放宽 NCC 或降低 D 阈值宣称诊断修复成功；必须同时报告已知误匹配与阴性误接受。**

---

## 4. P0：候选融合形式及禁止误用的方案

本轮同时实现以下**只读**候选，供受控验证；只有通过全部准入门槛后才有资格在独立研究副本实施实际输出变化。

| ID | 候选 | 研究目的 | 禁止行为 |
|---|---|---|---|
| `H0_A` | 纯冻结 A | 恒定参照 | 不得改动 A |
| `H1_G` | A 路径上的参考几何/根部材料域证据 | 判断 A 长尾是否离开合理材料结构 | 不得因 G 不支持直接删路径 |
| `H2_D` | A 路径上的已校验参考变暗证据 | 判断 A 尾部相对于参考有无新增暗线支持 | 不得把无参考差分等同不存在裂纹 |
| `H3_DG` | D 与 G 联合证据，含独立 D+G 路径 | 诊断长尾、静态纹理及 D+G 末端分歧 | 不得仅用双方法确认标志硬投票 |
| `H4_ROI` | 统一规则自动根部/ROI 与宽 ROI 对照 | 查明先验搜索范围的贡献 | 不得按已知异常帧设置窄裁剪 |
| `H5_DIAGNOSTIC_AGREEMENT` | 对应路径的空间重合、主干支持与末端差 | 评价“位置一致”是否比“确认一致”更有辨识力 | 不得事后用 TEST 寻找最优 tolerance |

### 4.1 重点研究三个相斥的尖端分歧类型

1. **`SHARED_TRUNK_DIFFERENT_STOP`**：两者主干在统一坐标中长段接近，但停止位置不同。可对应 A 沿暗纹长尾或 D+G 提前截短，不能仅凭末端较短选择 D+G。
2. **`BODY_BRANCH_DIFFERENCE`**：从较早位置开始出现持续主体分叉；单独计算首次分歧位置、后续重汇合和二者路径支持。
3. **`ROOT_GEOMETRY_CONFLICT`**：根部或变换本身分歧超过独立可评价界限；这时不能用两条路径的末端差判定谁对。

所有类型均单独区分 `A_CONFIRMED` / `A_UNCONFIRMED_CANDIDATE`。旧帧 51 不得因 CopyPath 中有候选而画入正式结果。

### 4.2 探索性组合——必须显式反例

- `A_AND_DG_CONFIRMED`：只读统计联合确认与误确认重合。**该条件可能同时通过两条不同、均错误的路径，不等于“端点一致”。**
- `A_PATH_DG_SUPPORT`：逐段统计 A 的主干与最后 K px 是否被可靠差分和根部拓扑支持；K 只在 DEV 选择，全组统一自动尺度规则；不允许按图固定后剪。
- `DG_TIP_A_TAIL_CONFLICT`：D+G 尖端与 A 共享主干且较早停止；应输出“可疑长尾”而非自动把 A 截短到 D+G。
- `INCONCLUSIVE`：D+G 未确认、配准未知、图像不可评价、ROI 截断或两方法均可能错时，**保持 A 不变并给出诊断理由**。

任何真正改变输出的方案都必须在独立研究副本中重新运行：保留 A、撤销 A、改变 A 尖端、从 D+G 补一个 A 未确认输出，分别计算影响；默认只准研究“识别可疑长尾”，**不授权增加确认或修改尖端**。

### 4.3 对假连接的根因归因实验

要求在 `false_bridge` 程序场景中对 D、G、D+G、D+F+G、D+F+G+C、A、只读 H3 的中间层进行对照：

- A：延伸前后各 tile 的得分、支持数量、路径首次离开 GT 的位置（若支持导出，禁止修改 A 正式行为）。
- D：参考差分是否实际拒绝静态延伸；如果 D 本身未通过可评价性，则结论降级。
- G：根部连通域与孔洞/材料边界是否排除错误通路；分辨是几何过滤还是连接选择。
- F：Frangi 是否增强了孔洞边缘差分；记录原来 D/G 不支持但加入 F 后支持的位置。
- C：逐像素记录**闭运算新增连通桥**及其是否跨越已知 GT 断点/静态纹理；解释从≈1 px 到≈122 px 的变化。
- 对 `hole_motion` 阴性：专门检查 D+F 与完整 F 的新增误确认，和错误位移/响应强度的依赖。

禁止只给一句“闭运算不好”；必须追踪到**新增连接点／响应图／组件选择／终点极值**中的第一个可证实变化阶段。

---

## 5. P0：设计真正前瞻、独立的新程序 GT 与负对照

**这是本轮最重要的验收部分。已有 20261103 的 DEV/TEST 均已被看过，不能再当新的独立 TEST。**

### 5.1 分组与先后顺序

1. `HISTORICAL_EXPOSED`：旧 TEST、旧五组及已知关键帧，仅用于复现实验、提出失败假说；在新一轮中不承担证明独立提升的角色。
2. `NEW_DEV`：未生成过的新随机种子与空间位置、独立合成几何、多个背景类型；允许用于确定**唯一统一策略**和很少量的全局参数。
3. `NEW_TEST_LOCKED`：新 seed、新几何变量、新空间区域以及至少部分先前未出现的**场景家族/组合**。脚本应先生成并封存原始图像和 GT 的 SHA、案例列表与分母，且 Agent 不得查看 TEST 测量结果选参。生成器和算法同工作流时必须提供不可变哈希及审计日志。
4. `NEW_MATERIAL_EXTERNAL`：真正未参与此前研发的独立试样或硬件靶，若没有就明确 `NOT_AVAILABLE`；不能把同五组不同帧叫做新材料盲测。
5. 如果只具备共享材料背景，则仅允许声称“新受控干预泛化”，**不得声称跨材料真实普适性已经证实**。

### 5.2 样本分层（全部须预注册且含反例）

**正例（可见与已形成状态分开）：**

- 强直线、弱线、渐浅尾部、宽度渐变、反射不对称暗线。
- 直线外至少 25°/35°/50°/70° 曲折线、S 弯、局部大曲率、多段折点。
- 裂纹根部偏移、孔边单侧萌生、双侧生长、长度跨越动态 ROI 初始边界。
- 具有已知短缺口/断点和接近静态背景划痕的真实程序线；允许真实目标短暂闭合，区分 formed vs visible。
- 原参考已有暗线、当前新生线、复开/闭合、曝光与位移混合变化；不要假设所有参考都是干净无裂纹状态。
- 跨材料/编码对比度：亮白背景、暗背景、金属加工纹理、低纹理、孔洞边界；真实背景源尽可能不同。

**阴性：**

- 无裂纹、参考与当前相同、只有加载平移/微旋转、局部扭曲、孔边错位。
- 静态根部深线、静态双线、孔洞边缘暗线、没有根部连接的长暗划痕。
- 光照增益/偏置、局部光照起伏、高灰/低灰编码范围、饱和但不可断言传感器饱和。
- 离根部很近但未连通的伪线、跨一小段亮区后被形态学桥接的静态纹理。
- P1/P2 不确定、材料无独立配准纹理、ROI 边界截断及方向 50° 以上案例。

**困难对照：** 设计“真正长裂纹 vs 假连接静态尾部”配对案例，图像形态尽量相似，只在生成真值上有区别；要求方法不能靠“总是更短”取得看似更低的长尾误差。

### 5.3 足够统计效力与单位

- 每一类关键风险在 NEW_TEST 应有**独立案例**而非只增加同案例连续帧；建议每类每背景至少 10 个独立场景，实际数量须先做可达性/功效说明并冻结，不足则标 `UNDERPOWERED`。
- 每个案例可模拟多帧及加载相位，但 bootstrap 的基础单位必须是 `case_id`，跨材料推断需在 `material_id` 级处理，不把 3 帧当 3 个独立材料实验。
- 给出所有案例的失败、未知、拒绝、确认状态。不能删掉算法崩溃、ROI 漏掉 GT、低信噪比样本或运行超时。
- GT 中保留双向 `side`、末端二维坐标、完整有序真中心线、弧长、轴投影、根部、已形成/可见状态以及图像可观察性；逐帧记录输入 SHA。
- 已有人造目标的生成器独立于算法实现，算法不能读取真值字段或生成器内部 mask。

### 5.4 关键反事实与消融

对同一张输入重复构造：

- `D_only` vs `D+G`：衡量 G 的覆盖收益、静态双线误接受代价。
- `D+G` vs `D+F+G`：衡量加 F 的真实增量和 hole-motion 伪响应。
- `D+F+G` vs `D+F+G+C`：衡量 C 的补线收益与错误桥接代价。
- `AUTO_ROI` vs `WIDE_CONTROL`：分离几何截断对假长尾和真实弯折的影响。
- 相同图像与变换下 `A observer only`、`A+DG shadow` 与可选、仅研究版输出变更 `A+DG_candidate`：严禁同时改变 ROI、配准、输出规则而把结果归因于单个模块。
- 在可靠参考差分不可评价时启用 `ABSTAIN`，评估这种拒绝是否把 A 有效确认过度撤销。

---

## 6. P1：源代码开发与运行要求

### 6.1 执行顺序及必须留下的证据

**Milestone 0 / 环境锁定**

- 自动扫描用户本地研究工作区，建立 `inputs_inventory.csv`、依赖版本、编译器、CPU、OpenCV、Python、源文件 SHA、Git HEAD。不要覆盖上轮研究目录。
- 创建**新的独立输出目录**，例如 `D:/workspace\DG_minimal_fusion_prospective_20261103`；如同名已存在则用不同的 run_id 子目录，绝不删旧研究。
- 复现冻结 A 的身份及全部既有快照；出现任何不等价，停止所谓融合研究并先排查输入或版本。

**Milestone 1 / 独立自动几何与差分诊断**

- 将 D/G 独立封装为一个统一、非按组分支的研究模块（可先 Python 验证，最后候选必须提供 C++17/OpenCV4.4 原生实现）。
- 首轮以**只读输入**输出 D、G、可评价性、ROI、根部、路径支持和诊断日志；A 行为和正式视频均不变。
- 提供数值单测：坐标往返、左右镜像、孔/缺口、旋转/平移、边界越界、空 ROI、根部不可辨识、裂纹跨越 ROI、新线/静态线。

**Milestone 2 / NEW_DEV 选择**

- 按预注册场景生成训练允许的受控案例；只在 NEW_DEV 选择一个全局统一的 D/G 策略与阈值。
- 参数全写入 `selected_policy_dev.json` 与源码哈希；输出选择被否定/保留的候选和失败原因。
- 不允许一组材料一套参数，亦不允许看到新 TEST 再微调。必要时允许统一尺度适配函数，但输入必须是图像、标记和可靠几何，而不是材料名。

**Milestone 3 / NEW_TEST 一次性锁定复核**

- 在配置与代码哈希锁定后运行一次主 TEST。失败、崩溃可在单独 errata 中说明并用相同哈希复跑技术故障；凡参数/代码改变必须重新生成新的 TEST，不可“补救性调参后沿用同一 TEST”。
- 原 A、D、G、D+G、Frangi 全套（仅作为固定对照）以及 shadow/candidate（若已获准）使用相同帧/坐标合同。
- 输出配对案例级误差、置信区间、负例误确认和漏检分母。若新独立背景不足，不能声称跨材料稳定获益。

**Milestone 4 / 只在有独立收益时考虑输出变更**

- 正常结果应先停在 `SHADOW_ONLY`。只有新 DEV 已选出的**单一最小机制**在 NEW_TEST 达到下述全部门槛，才可在研究副本中启动一个非常小的 output-changing 分支；该分支本身如果已经看过 NEW_TEST 再设计，必须重新获得新 TEST 进行未来评估。
- 把每次输出改变分类为 `TRUE_CORRECTION / FALSE_REVOKE / FALSE_SHORTEN / FALSE_EXTEND / INDETERMINATE`。真实图无 GT，永远不可直接标 TRUE_CORRECTION。
- 撤销 A、保留 A、调整 A 尖端、增加 A 未确认输出分别统计，严禁把减少误报的一种收益抵消别的重大漏检而只报净值。

**Milestone 5 / C++ 原生等价和性能**

- 只有通过前述证据准入后，才实施候选 sidecar 的 C++17/OpenCV4.4 数值等价测试，不修改 A 源码或 ABI。
- C++ 的 D/G 中间层、ROI 坐标、路径支持和最终研究状态与 Python 原型逐帧逐像素对照，给出误差容限和不能等价的具体项目。
- 按真实完整核心单帧计时 `Process + GetResultV2 + CopyPath + 必要分配 + 候选判定`；预解码/渲染/日志另计，并独立报告端到端环境时延。
- 五组每个帧的 P50/P95/P99/Max、内存峰值、超时帧必须给出；**所有被测帧 Max ≤66.67ms** 才满足当前数据上的核心预算。排除组X原 A 余量约 5.086ms，应把 CPU 工作复用与局部化作为约束，不能仅引用 Python 或 GPU 估计。

---

## 7. 预注册验收门槛（必须是联合门槛，不得选单一最优指标）

以下是**研发建议门槛**，不是历史验证已经达到的事实；如工程方提供真实容差，先以其为准并在新 TEST 前冻结。

### 7.1 生产候选的必要条件

1. **A 完全可重复**：全部 2510 张当前图及 5 张参考图的正式状态、尖端、长度、double `CopyPath`、历史状态对照严格无意外差异；研究边车未启用输出变更时严格 0 差异。
2. **正例有效覆盖不下降**：独立 NEW_TEST 相对 A 的可观察正例确认数不降低，尤其原 A 已确认的弱/渐浅/曲折/大转角场景不得出现未经明确说明的新撤销。若采用错误长尾拒绝策略必须独立统计由此造成的正确确认撤销。
3. **阴性错误确认不增加**：主要 NEW_TEST 总阴性 FP 不能超过 A，`hole_motion`、`static_double`、`static_root`、`false_bridge` 需要分别报告；稀少情况下 `0` 事件需给出置信上界，不可称零风险。
4. **条件误差与长尾合格**：在共同确认案例上比较尖端 2D MAE、P95、`>8px` 尾部、轴投影和弧长误差；改进必须在预先指定主要亚组上有案例级统计证据，且不通过拒绝困难样本换取条件平均改进。
5. **渐浅与弯曲反例守住**：单独验证 `weak / fading / curve / angle50 / false_bridge / closed`，不许只在直线或排除组X 473 的视觉演示上通过。
6. **ROI 安全**：自动 ROI 正确覆盖可见 GT 主干及末端，且不会只因纵向变宽出现大量错误连接；ROI 生成失败必须明确失败状态，不得复用上一试件的固定值。
7. **跨背景结论真实**：按背景和场景出分母、效果与区间；没有新材料只能写受控新场景有效，不得写“普适”。
8. **完整 C++ 性能合格**：各组实际测得核心 Max ≤66.67ms；性能不足则研究结论可以有效，但不具备当前生产条件。
9. **ABI 和媒体合同一致**：旧接口、NULL P1/P2 合法自动回退语义、未确认仅原图、单侧/双侧独立输出不变。调用方需保证点数组缓冲区大小；不得尝试不安全短数组造成 UB。

### 7.2 统计比较的严格性

- 主指标：**联合目标** `coverage + FP + paired_tip_error + tail + runtime`，不是“正例确认最多”或“最低条件 MAE”单项。
- 置信区间：以 `case_id` 为基本 cluster 做 bootstrap（例如 ≥1000 次），同一案例不同帧不独立；跨背景推断有材料级局限。
- 每个预注册关键分层独立报告，特别是 A 与 D+G 的两个可能失效方向：**对静态纹理的双重误确认**、**对弱/渐浅真实裂纹的双重漏检**。
- 版本间配对指标、被拒的真阳性、新增误确认和没有输出的不可观察样本分开呈现；不可在正文只选成功子集。
- 正例误差默认基于可见 GT，形成但不可见 GT 仅做边界研究；实测物理尖端依然 `N/A`。
- 若新独立样本不足或指标区间宽到无法判定，请真实结论 `INSUFFICIENT_EVIDENCE`，不得因完整测试耗时较长而越过门槛。

---

## 8. 重点回归：保留已知问题但不得借它们选生产参数

### 8.1 排除组X 473

核对 A0 与 D、G、D+G、F0、F-WIDE 的同帧参考坐标/原图坐标、原路径是否离开材料、差分支持的沿程变化以及根部/孔洞掩膜。明确 F-WIDE 已包住 A 尖端但 F 仍停在≈310.255px；不能把这解释成“Frangi 滤波已证明准确”。

**必须输出两个独立结论：**

- 哪一模块从哪里开始拒绝 A 的下行尾部（有数值支持和图像证据）？
- 是否有独立 GT 可以宣布真实尖端？若无则 `NOT_IDENTIFIABLE`，严禁按 F 尖端强制裁剪 A。

### 8.2 排除组X 51

A 无正式确认，F 有短根部响应。研究视频可以单独展示候选，但正式视频不能把 A CopyPath 中的候选画成裂纹；不得给 F 增加确认作为提升率。

### 8.3 CT2 6、18、84

复用先前 `refine=true/false` 因果链；不要把 127.21px 的配置间分歧称作真实尖端误差。按 shared trunk / different stop 分类；D/G 观察必须考虑不同配准结果导致的采样差异。

### 8.4 新 GT 反例

必须特意保留“正确目标确实更长”与“假连接尾部更长”的双向受控对照。不能仅用过长截断成功证明收益；若正确目标也被同样截断应立即失败。

---

## 9. 交付目录、最小数据格式与实际验收

创建独立新目录，例如：

```text
DG_minimal_fusion_prospective_<run_id>/
  00_protocol/
    input_inventory.csv
    frozen_A_identity.json
    environment.json
    hypotheses_locked.json
    protocol_frozen.json
    hashes.sha256
    exposure_register.csv
    deviations_and_errata.md
  01_source/
    dg_geometry.py                 # 研究原型：自动几何、根部、材料域
    dg_reference_evidence.py       # 差分可评价性与路径支持
    dg_roi.py                      # 统一初始/动态ROI规则
    dg_shadow.py                   # A只读与路径空间一致性
    gt_generator.py                # 独立可见/形成GT生成器
    cpp/                           # 若满足准入，候选侧车C++代码
    build_and_run.md
  02_cases/
    new_dev_manifest.csv
    new_test_locked_manifest.csv
    ground_truth.csv
    negative_controls.csv
    image_sha256.csv
  03_results/
    per_frame_all_methods.csv
    per_case_paired.csv
    coverage_and_false_positives.csv
    tip_axis_arc_errors.csv
    centerline_geometry_errors.csv
    first_divergence.csv
    dg_evaluability.csv
    roi_root_coverage.csv
    failure_taxonomy.csv
    test_per_background_intervals.csv
  04_ablation/
    D_G_F_C_causal.csv
    roi_width_height_controls.csv
    reference_alignment_controls.csv
    candidate_rule_selection_DEV.csv
  05_regression/
    A_identity_2515.csv
    historical_exposed_cases.csv
    archived_336_480.csv
    abi_state_regression.json
  06_performance/
    native_all_frames.csv
    p50_p95_p99_max.csv
    memory_peak.csv
    cpp_python_equivalence.csv
  07_media/
    official/                     # 仅正式A确认结果，始终不变
    diagnostics/                  # 标注为研究用途的多窗口/热力图/候选
    key_cases/                    # 排除组X51/473、CT2 6/18/84、新GT反例
  08_reports/
    executive_summary.md
    diagnostic_failure_analysis.md
    D_G_independent_value.md
    auto_roi_generalization.md
    prospective_test_results.md
    release_decision.md
    reproducibility.md
    index.html
```

**`03_results/per_frame_all_methods.csv` 的每行最少包含：**

```text
case_id,split,material_id,background_id,family,frame_id,side,
input_sha256,reference_sha256,algorithm_version,
A_confirmed,A_tip_valid,A_tip_x,A_tip_y,A_arc_px,
DG_evaluable,registration_status,geometry_status,roi_status,
D_support_body,D_support_tail,G_support_body,G_support_tail,
DG_confirmed,DG_tip_x,DG_tip_y,DG_arc_px,
root_x,root_y,roi_x,roi_y,roi_w,roi_h,roi_truncated,
shared_trunk_px,first_divergence_arc_px,tail_disagreement_px,
shadow_state,research_output_changed,
GT_positive,GT_observable,GT_visible_tip_x,GT_visible_tip_y,
GT_formed_tip_x,GT_formed_tip_y,
FP_confirmed,FN_confirmed,tip_error_px,arc_error_px,axis_error_px,
reason_code,core_latency_ms,physical_tip_accuracy_status
```

列为示例；实际可按通用结构拆文件，但必须有明确 `case_id / input_sha / frame_id / side / algorithm` 可关联键和缺失值定义。所有失败状态保留；`N/A` 不能填成零。

### 9.1 最终报告必须逐项回答

1. 在新独立受控 GT 中，A、D+G、完整 Frangi 的覆盖、误确认、尖端误差分别是多少？哪些分层可信，哪些证据不足？
2. `A∧D+G` 只是事后旧 TEST 上的假说：在**新 TEST** 中是否能同时保留 A 的有效确认且减少误确认？有没有共错、弯曲和渐浅反例？
3. D+G 末端与 A 尾部不一致时，哪一个更接近已知可见 GT？对“真实更长”和“假尾更长”两个反事实分别怎样？
4. `false_bridge` 的首次错误发生在哪里？是 D 未抑制、G 根部连接失败、F 方向退化、还是 C 新桥接连通？必须给出可复现的中间矩阵／图／路径数据。
5. `hole_motion` 的误确认是否由 F 增强、差分配准误差或几何假设造成？各因素是否能够被单独介入验证？
6. 自动 ROI 和根部是否真的脱离专用参数，并且能覆盖大角度曲线、多侧裂纹和向外生长目标？失败样本在哪里？
7. 候选机制是否仅在旧背景可行，还是通过新背景、独立材料与硬件数据？明确泛化证据等级。
8. 冻结 A 是否 2515/2515 零差异？新 C++ 研究分支的最大帧时延是否满足 66.67ms？若未运行则不能宣称通过。
9. 是否有**足以支持真实生产输出变化**的直接独立证据？如果没有，维持 `KEEP_A`，并指出唯一最值得做的下一项实验。

---

## 10. 输出决策规则：允许负结果，不允许夸大

最终必须且只能提出一个主决策：

- **`KEEP_A`**：未观察到足够稳健的独立改进，或新错误/漏检/时间预算不满足。
- **`SHADOW_ONLY`**：D+G 旁路可以识别风险，但不足以安全改变 A 输出；保留研究日志，不宣称真实尖端精度改善。
- **`RESEARCH_CANDIDATE_NOT_RELEASED`**：在严格新 GT 联合门槛下得到独立收益，并完成源码与性能研究，仍需真正新材料/物理对照后考虑生产。
- **`INSUFFICIENT_EVIDENCE`**：缺少测试源图、新独立场景、统计能力、物理可观察性或关键日志，不能判定。

不允许只因从 A 的 6 个旧阴性误确认里通过交集过滤掉了 4 个，就宣布“提升 66.7%”。这是使用**已经被观察过的 TEST**所产生的研究假说，不能替代预注册的前瞻性检验。

同样，`A0 = 9.710px`、`D+G = 11.236px` 和 `F = 21.984px` 都是旧程序 TEST 的**已确认且可观察正例条件误差**，不是任何新真实物理裂纹的精度；不得借用它们作为新开发的验收结果。

### 提交前自查

- [ ] 原生产 A 源码、DLL、运行参数和全部冻结输出未改变。
- [ ] 新 DEV、新 TEST 与已暴露历史案例有清楚的数据边界和 SHA。
- [ ] 已有旧 TEST 没有被重新用于选参、宣称盲测或随意复测后回调。
- [ ] 一套通用参数及生成规则；没有任何数据组名称判断、固定根部与裁剪坐标。
- [ ] 正例、阴性、未知、误确认、漏检、长尾、截短、ROI 失效等分母完整。
- [ ] 参考差分与几何不可信时安全 abstain，没有伪造的“确定无裂纹”。
- [ ] false_bridge、hole_motion、weak、fading、curve、angle50 均有新反例。
- [ ] 特别区分“确认一致”“路径一致”“尖端位置一致”“真实正确”。
- [ ] 真正输出改变只存在独立研究候选，已记录每一种错误撤销／错误截短。
- [ ] 真实无 GT 的组只报告风险和分歧，不报告物理尖端 MAE。
- [ ] 每张正式视频只画 A 确认的一条实线及一个尖端，调试图分目录。
- [ ] C++ 等价、全量帧时延、峰值内存只在实际完成时标通过。
- [ ] 全部脚本、输入清单、日志、CSV、报告和重要错误案例可以复现。

**Agent 请立即以本地可访问的已有研究目录为输入，先复核冻结基线和协议边界，然后实施代码与新受控实验。不要先写一份“预计会改善”的方案再停止；在不违反冻结原则和数据隔离的前提下尽量完成实测，并交付独立研究包。**
