# CrackV4-C2 下一轮 Agent 开发任务书

## 高召回候选保留 × 可信参考归属证据 × 独立尖端决策

> **请直接执行本任务，而非仅给出方案。** 你是可访问用户 Windows 本地 CrackV4 工程及既有研究数据的研发 Agent。需要完成：源码合同审计 → 独立研究分支实现 → 新 DEV 机制实验 → 冻结方案 → 一次性新 TEST → 已曝光真实组只读回归 → 统计、关键帧可视化、性能可行性与发布决策。允许且鼓励最终得到 `KEEP_A / C2_RESEARCH_ONLY`；严禁为了宣布成功而削弱验证标准。
>
> **本轮唯一核心目标：准确定位单侧向右生长裂纹的当前可见尖端 `(x,y)`。** 路径继续保留作候选/辅助输出，根部可选，不要求精确根部或完整中心线才能确认尖端。长度只以 P1/P2 基准线投影为新版主要长度语义。
>
> **不变前提：冻结生产 A 的源码、DLL、参数、ABI、历史输出与正式媒体；新算法只能在独立 C2 研究目录开发。** 未通过预注册的新 TEST 与 C++ 完整原生核心性能门槛之前，禁止替换 A 或发布新 DLL。

---

## 0. 为什么这次必须收缩研究范围

上一轮 C_FULL 虽然实现了动态 ROI、三尺度响应、鲁棒噪声、光度与局部尖端审核，但新 TEST 未通过效果门槛。以下是**历史报告／补充原始 CSV 已曝光的诊断事实，仅用于定位问题、不能再次用来选择参数后作为独立 TEST 胜利证据**：

| 已曝光结果 | 证据与研发含义 |
|---|---|
| 1107 个可观察正例，A 确认 1065（96.21%），C_FULL 确认 833（75.25%） | C 的主要风险是大规模拒绝准确结果，而非简单缺少候选。 |
| A 正确（2D 端点误差 ≤8px）却被 C 撤销 157 帧，另有 19 帧被 C 改到 >8px | **157/157 在 C 原始候选中有距已知端点 ≤8px 的候选**；这是离线 GT oracle 诊断，不是在线可用选点条件。 |
| 上述 157 帧被撤销原因：`NO_SUPPORTED_CURRENT_ENDPOINT` 120；`ROI_LIMITED_OR_FORWARD_AUDIT_UNAVAILABLE` 13；`H_CONTINUE_COMPETES_WITH_STOP` 12；`MULTIPLE_SUPPORTED_TRANSITIONS` 12 | 优先核查候选保留和判决逻辑；不得只调一个 `after_snr` 阈值。 |
| 在 9 对、54 对帧的 `strong_serial_false_tail` 与 `true_long_matched` 中，配对的**当前图像和 P1/P2 相同**，参考图不同，定义的可见端点不同 | 任何只读取当前图像（加 P1/P2）、忽略参考/历史信息的确定性算法，对同一对输入必须给同一结果，因而不可能同时正确；研究应验证**可信参考增量信息**。 |
| 强假尾 54 帧 C 达到 ≤8px 的结果为 0；配对真长 54 帧 C 达到 ≤8px 为 27 | C 的“前强后弱”局部停止判据不能承担裂纹归属判别。 |
| 受支持候选的 `reference_ratio` 中位数：强假尾约 0.256，真长约 0.016 | **仅是已曝光数据中的相关线索**；先审计字段定义、方向与计算条件，不能照抄固定阈值。 |
| C_FULL 新 TEST 1404 帧中 0 帧有 `VALIDATED_AFFINE_HELDOUT`；真实 3035 帧中约 66 帧有相应有效状态 | 当时参考证据的几何/光度可信合同覆盖不足；不能把 `UNKNOWN` 当作“参考差分为零”。 |
| 234 个末帧 ROI 放大 1.5 倍，10 条原确认结果消失或移动 >2px；配对测试记录候选路径相同、计算 cap 相同，但采样步长可能变化 | 先解除“搜索 ROI 范围、审核窗口、采样密度、候选竞争”之间的非必要耦合。 |
| C_SCALE 单模块的 TEST 正例覆盖仅 28.09%，C_ROI 约 90.61%，C_BASE 约 45.71% | 保留尺度估计供诊断，不能将单一估计尺度变成新硬门槛；ROI 有潜在价值但需要稳定性验证。 |
| 真实六组无独立物理尖端 GT；排除组X 473 的 C 端点视觉上可能更合理、三点弯 53 的 C 不予确认 | 都是已曝光诊断个例，**不是精度证明**。 |

**本轮研究必须分离两个问题**：

1. **候选定位**：可靠的尖端是否在候选集合内？候选在哪里因什么原因被丢弃？
2. **裂纹归属与确认**：候选是否属于新形成/新显露的裂纹末端，而非原有静态线、假桥接或参考配准残影？如果证据不足，能否明确输出不确定，且不会大规模毁掉 A 已正确结果？

本轮不再同时重写全部 DP、ROI、尺度、噪声、光度和尖端算法。只对上述因果链采取最小可分辨的改动。**不以“减少确认数”“增加 UNKNOWN”“视频看着更短”代替精度提升。**

---

## 1. 研发边界与工程输入

### 1.1 输入、方向、目标与坐标

- 输入仅包括：**参考灰度图、当前灰度图、对应的参考与当前 P1/P2、可合法获得的先前历史状态**；如已有接口的 `flags`、refine 配置和参考判定等，必须记录并按冻结合同复现。
- 当前只支持 CT、三点弯等**单侧向画面右侧**裂纹；允许局部弯曲、大角度和 S 形，不开发左侧、双向、多裂纹根源的生产版本。
- 每帧主要输出：`tip_valid`、原图坐标 `tip_x/y`、尖端状态/原因、相对 P1/P2 基准线投影长度、审计信息。
- 路径继续输出（可以是 A 原路径、研究路径或可信局部段，必须标明角色），根部继续输出（可空）；**不以完整路径、root_valid、旧弧长是否为 0 作为有效尖端的前置条件**。
- 没有标定不输出 mm，没有加载相位不声称已形成物理裂纹尖端准确。状态 `PHASE_UNKNOWN`；真实物理尖端精度 `N/A`。

以当前图像 P1、P2 为准，定义

\[
O=(P_1+P_2)/2,\quad v=P_2-P_1,\quad u=(v_y,-v_x)/\|v\|,\quad
L_{\mathrm{horizontal,px}}=(T-O)\cdot u.
\]

输入 P1 位于 P2 上方时 `u` 指向图像右侧；如果点身份、顺序或退化标距异常，返回 `INVALID_INPUT`，**不得根据 GT 或当前预测方向调整右法向**。旧 root-to-tip 弧长留在 `legacy_arc_length_px`，绝不能与投影长度混写。无尖端时研究 CSV 使用空值 + validity，展示界面如需显示 0，必须明确标志未确认。

### 1.2 自动 ROI 与统一规则

- 一套公共代码、相同的规则与常数，不允许 `if specimen_name == ...`、路径关键字、帧号分支、手工截断位置、根据历史物理尖端/GT 定 ROI。
- P1/P2 可作为宏观几何尺度；细线宽度与局部背景噪声必须通过统一规则从图像估计，不可假设所有试件线宽与基准标距成固定比例。
- 所有用于在线决策的数值只能来自已准许的输入和 DEV 冻结策略，**GT 只能在评估器中出现**，不得进入检测函数、候选排序、门控或 ROI 选择。
- 旧 A 的完整核心仍须保有原有 15Hz 目标：66.67ms/当前帧为 C++ 核心**最大**预算，不是平均或 Python 演示播放速度。

### 1.3 本机资料定位（先查找，不要凭空假设存在）

优先核对用户本地工作区与附件：

- `D:/workspace\`、`D:/workspace\crack_v4_cpp\` 及其冻结 A、C 研究、对照研究目录；研究目录名称以实际磁盘扫描和 manifest 为准。
- 本轮最近补充包 `CrackV4_C_截图数据_轻量版.zip`，以及 `C_research_source_reports.zip`（如实际在本机可访问），找出对应冻结协议、研究源码、TEST 和关键图。
- 补充包内需要优先读取的相对文件：
  - `00_protocol/freeze_manifest.json`、`preregistered_gates.json`、`post_TEST_errata.md`、`coordinate_and_measurement_contract.md`；
  - `03_new_gt/matched_pair_audit.csv`；
  - `04_results/TEST_frame_predictions.csv`、`TEST_candidate_tips.csv`、`A_correct_rejection_conditions.csv`、`TEST_paired_frames.csv`、`TEST_mechanism_by_family.csv`；
  - `04_results/TEST_roi_counterfactual.csv`、`TEST_adaptive_params_per_frame.csv`、`REAL_adaptive_params_per_frame.csv`、`case_bootstrap_ci.csv`；
  - `05_regression/*frame_predictions.csv`、`known_historical_cases.csv`、`real_state_and_coordinate_changes.csv`；
  - `07_media/key_cases/controlled/`、`07_media/key_cases/historical/` 及真实试件变化截图；
  - `08_reports/failure_root_causes.md`、`release_decision.md`、`physical_accuracy_limits.md`。
- 如果某文件或原始 BMP/P1/P2 不可访问，先报告 `MISSING_SOURCE` 并列出缺件；使用现有数据完成可验证工作，**不得伪造路径、截图、端点或统计**。

历史已冻结生产 A DLL SHA-256 记录为 `c23498fcc660469927f63244b8e98e39b1eb86d542ec9a7b069d61fcf813654b`。Agent 必须读取实际 DLL、ABI、源码和运行 manifest 并比对，而不是直接假设匹配。既有关键 `flags=3572`、`policy=1`、`terminal_validation=1`、`refine=true` 只作为核对线索；**不得为了新算法表现擅自改变 A 参考模式/参数/时序调用次序**。

### 1.4 分隔输入与输出、分隔各轮数据角色

建立新的独立研究目录，例如 `CrackV4_C2_ReferenceOwnership_Research_<run_id>`；要求：

- 原目录和已封存 DEV/TEST、旧 DLL、原视频、旧指标**只读**。
- 首先写 `data_role_manifest.csv`：标明 `EXPOSED_DIAGNOSTIC` / `DEV_NEW` / `TEST_LOCKED_NEW` / `REAL_HOLDOUT_IF_AVAILABLE`。同一底图、参考图、随机过程参数和近重复纹理不得跨 DEV/TEST；不能靠只换种子就宣称背景独立。
- 现有 **六组真实图、三点弯、排除组X异常、历史所有合成 DEV/TEST 和补充截图均已曝光**；只能做回归、查错与产生机制假设，**不能再把它们作为新优化的独立效果证明**。
- 第五组/排除组X历史用途沿用既有标记，不因本轮研究而假装重新成为独立 holdout。
- TEST 一次性执行；任何 TEST 后针对它重新选阈值/规则都须标为 `POST_TEST_EXPLORATORY`，不得继续沿用原 TEST 名称声称独立有效。

---

## 2. 必须先完成“冻结 A 与旧 C”的源码合同审计

**在任何实现之前**，实际定位源文件、函数、行号、配置与数值路径，提交 `01_audit/source_contract.md`：

1. A 的 Path/Tip、`evidence_ended`、前缀时序验证、参考配准、原图/材料坐标的具体关系；`Process`/`GetResultV2`/`CopyPath` 的输出及运行时合同。
2. C 的候选生成、默认 A 路径复用和路径回退逻辑；C_BASE 与 C_FULL 的准确差异。
3. C `tip_localization`/`tip_validation` 对 `after_snr`、`before_snr`、held-out 采样、forward-ray、margin、`MULTIPLE_SUPPORTED_TRANSITIONS` 的每条**真实判决条件**及其上下游依赖。
4. `reference_ratio` 的**数学定义、取样区、分母归一化、阈值含义、参照帧如何几何对齐**；它的数值大/小究竟表征什么，必须从代码和可控例子中证实。不要仅根据 0.256 对 0.016 推断物理含义。
5. `VALIDATED_AFFINE_HELDOUT` 的完整通过条件、有效像素掩膜、空间覆盖、最常失败分支；明确 0/1404 的阻塞位置。
6. ROI 扩展是否改变采样步长、候选排序、前方审核范围、边界 policy、可用配准/光度数据；不能仅用总计变化推断原因。
7. 各算法版本在 TEST 实际共用的图像、配准、候选路径、GT/domain 及报告的聚合样本范围；配对 Bootstrap 的 case 单位而非逐帧独立。
8. 对已有算法中的材料根部与 P1/P2 零基线的角色作记录；不能因为本轮根部非重点，就偷改 A 根部位置或旧输出。

**核实用户最近补充数据的核心算术**：上述 157/19、54 对匹配图、1404/66 光度状态及 ROI 10/234 均需脚本重新统计；发现差异应给出分母、过滤字段和缺失列说明，而非迎合摘要数字。

**冻结 A 等价性必做**：在可用真实输入与既有生成输入上按原顺序重放；逐帧检查状态、尖端坐标、长度、double 路径和哈希。任何无关变化先停工排查。研究版不能修改冻结生产结果。

---

## 3. 研发里程碑 M1：高召回候选保留（首要）

### 3.1 核心结构

把搜索和最终确认拆成两个**可独立评价**的接口：

```text
Frozen A (immutable) ──> A_tip_candidate (if valid)
         │
         └──────────────> A_path / legacy stop info

C candidate search ────> local terminal hypotheses
                        > shortened-path hypotheses
                        > genuine forward-continuation hypotheses
                        > candidate-unavailable reason

CandidateUnion ────────> de-duplicate with origin preserved
                        > score each hypothesis, without GT
                        > keep all valid contenders within fixed budget

OwnershipEvidence ─────> SUPPORTED / CONTRADICTED / UNKNOWN
EndpointDecision ──────> CONFIRMED / AMBIGUOUS / NOT_OBSERVABLE
```

必须保留：

- 原 A 已确认尖端为研究候选之一；`A_confirmed=false` 时不能凭空伪造 A 尖端。
- C 的本地精修、向前延伸、向前较短停止和 DP 另分支候选；限制 top-K 和局部窗，**候选多不等于自动拒绝**。
- 相近候选合并时保持来源、原像素坐标及对应评分，不得静默用平均坐标替换 A 正确尖端。
- 如候选不完整、存在边界或参考未知，应该记录**哪一项证据不可评价**，而不是一律 `NO_SUPPORTED_CURRENT_ENDPOINT`。
- 显式输出“候选生成召回”与“最终确认覆盖”两种指标；前者只能在有 GT 的评估器里以 `oracle_min_candidate_error` 统计，**在线模块不允许读取这项指标**。

### 3.2 不允许的捷径

以下做法禁止作为 C2 的核心：

```python
# 禁止用缺失的参考证据一票否决 A
if not reference_support: return INVALID

# 禁止所有局部条件必须通过，导致已存在的可信候选被粗暴删掉
if not (before_ok and after_ok and heldout_ok and forward_ok): return INVALID

# 禁止在线查看 oracle 正确性后选择 A 或 C
if oracle_error_A < oracle_error_C: return A_tip
```

可以将局部检测输出为**多维可校准证据**，如 `before_strength`、`after_strength`、`forward_competition`、`tip_transition_stability`、`candidate_origin`。哪些条件构成 `CONTRADICTED` 必须在新 DEV 中经过对照验证，不能仅凭一条前后灰度关系硬编码。

### 3.3 必须完成的 M1 单元/回归测试

- A 正确且 C 局部高置信失败：候选必须保留，决策器可选择 A 或谨慎 UNKNOWN，**不可因候选不存在而拒绝**。
- A 过长、C 提出较短真端点：必须保留两者以供进一步证据比较；不能把 A 锁为永远优先。
- A 漏检但 C 有独立定位：允许 C 单独产生候选，仍要正常审计。
- 多候选接近、多个候选分歧、局部尺度不确定、参考未知、根部缺失、路径缺失、候选位于 ROI 附近：分别测试。
- 旧 157 帧曝光集合用作**故障回归**，记录 `candidate_recall`、`reason_before/after`；不允许根据其 oracle GT 在线选候选或调参后再当 TEST。

**M1 阶段门槛**：不得宣称“成功提高准确率”，除非有新的独立 GT 样本。M1 即使解决 157 个旧拒绝，也只是修复候选流转的机制，不自动证明候选选得对。

---

## 4. 研发里程碑 M2：参考图驱动的裂纹归属证据（最重要的创新验证）

### 4.1 先确认“不可辨识性”反例

对已曝光配对数据验证 `same current SHA + same P1/P2 + different ref SHA + different GT visible endpoints`。写可执行单元测试，说明：

- 任何只接收 `(current, P1, P2)` 的确定性尖端函数对同一对必返回相同结果；
- 若同一对真值不同，它不可能同时符合两端点；
- **必须获得可信的参考、历史或其他独立可用观测信息**，不能仅继续调整当前帧形态阈值。

不得把配对构造的程序 GT 等同真实金相尖端；不得假设真实材料必定存在相同信息结构。这里检验的是算法信息利用能力。

### 4.2 实现“独立于尖端路径”的局部配准与光度有效性

必须先完成原理和范围可审计的验证链，才允许用参考图证据影响尖端确认：

1. **刚体初值**：由两帧 P1/P2 推导参考→当前的刚体映射，保留冻结 A 自己的原生 refine 不变。
2. **参考材料对应点/区域**：在*不依赖 C 当前候选尖端及其后段*的材料背景区域选择多处稳定特征；排除孔洞、缺口、明显动态裂纹带、饱和/反光、边界和明显运动残影，按固定规则限制局部视场和计算开销。
3. **可检测性先行**：检查有效背景像素比例、空间分布、纹理可匹配性、几何残差、交叉验证一致性；对局部非刚体情况记录模型不足。不可信则 `REGISTRATION_UNKNOWN`；不能自动说“裂纹不存在”。
4. **光度补偿**：仅在独立稳定背景上拟合低维鲁棒亮度模型（可从仿射开始），使用空间独立 hold-out 区评估残差、饱和、边缘误差和拟合条件数；避免同一像素既拟合又验证。
5. **分层降级**：独立纹理不足时尝试固定规则下可审计的局部替代证据（若确有可靠性），否则 `PHOTOMETRY_UNKNOWN`、`OWNERSHIP_UNKNOWN`。不得为追求覆盖率虚报 `VALIDATED`。
6. **数据泄漏防护**：必须证明有效性判据不依赖 GT、参考类型标签、背景名称、当前候选好坏的 oracle 信息；验证 matched pair 的参考身份不能通过标签、文件名、输入排序等捷径进入模型。

对 `VALIDATED_AFFINE_HELDOUT` 过去低覆盖，先统计**失败原因分层**。如果新 DEV 仍无法验证参考，则及时记录**无信息可用**；禁止用一个无法验证的 `reference_ratio` 值直接做决策。

### 4.3 参考归属证据定义

在配准和光度可信时，对**候选路径的整体及分段**计算：

- `current_line_support`：当前帧局部线状响应；
- `reference_line_overlap`：对齐参考图在同材料位置是否已有相似连续暗线；
- `registered_change_support`：在校验有效的亮度补偿下，候选前段和远段是否存在新增暗线/变化；
- `false_bridge_risk`：候选是否从新出现的短裂纹跨接到了已存在的长静态暗纹；
- `tip_ownership_evidence`：目标候选为新生/可见裂纹末端的支持、矛盾或未知（注明来源、作用范围和置信条件）。

**重点审核旧 `reference_ratio` 的语义**：在旧配对中强假尾参考比约 0.256、真长约 0.016，仅用于提出机制假说。新实现需基于新 DEV 的可解释、尺度/光度归一化证据，而非直接照抄 0.1、0.15 等阈值。

所有参考证据必须**三态**：

| 状态 | 含义 | 合法行为 |
|---|---|---|
| `SUPPORTED` | 可验证的新裂纹变化或归属支持 | 提高候选证据，仍需结合端点定位 |
| `CONTRADICTED` | 在有充分可观察性时明确支持静态线/假桥风险 | 参与候选排序与不确定性，不能凭单项直接删掉 A |
| `UNKNOWN` | 配准/光度/参考已有裂纹/相位或参考有效域不足 | 不得作负证据；保留候选与显式不确定性 |

**必要保底**：C2 在 `UNKNOWN` 上的行为应能不依赖参考证据保持 A 基线输出的研究候选，防止重现 D+G 的大规模硬门控。它可以选择保守状态，但必须在新 TEST 中付出真实拒绝代价并受覆盖率门槛约束。

### 4.4 匹配真假尾的“必要性 + 充分性”验证

新 DEV / 新 TEST 必须提供**同一当前帧、同一 P1/P2、不同参考帧和不同可见端点**的匹配对，并同时有以下对照：

- `CURRENT_ONLY`：禁止读取参考有效内容，验证只能对一对给出相同当前帧输出；
- `REF_UNVALIDATED`：有参考但故意令对齐/光度不可信，期望记录 UNKNOWN、不得假装有确定归属；
- `REF_VALIDATED`：允许经过验证的参考特征，测试能否在两种不同参考条件下做出正确的不同判断；
- `REF_SHUFFLED`：打乱参考帧配对的负控，**不得比正确参考对照表现得更好**；
- `REF_MASKED`：屏蔽假尾关键参考区域，观察信息缺失后性能和不确定性是否相应变化；
- `TRUTH_LONG` / `FALSE_TAIL`：两种解释对等评估；不能通过一律截短赢得假尾场景，同时毁掉真长场景。

对测试对数、有效参考覆盖、配对同图一致、改变参考后的尖端变化、两端误差、UNKNOWN 比率分别报告**独立案例级**数据。不可以只报当前帧均值或成功截图。

**M2 的提前停止条件**：如果新 DEV 显示参考信息在大多数背景不可验证、无法区分配对真伪或对配准扰动高度敏感，则保持 `OWNERSHIP_UNKNOWN` 和 `RESEARCH_ONLY`，不要继续叠加更复杂模块并宣称已经解决强假尾。

---

## 5. 研发里程碑 M3：将搜索 ROI 与终点审核 ROI 完全解耦

本轮只对 ROI 中**影响尖端证据准确性**的结构进行重构，不把根部精确性、材料轮廓分割、全图新路径扫描作为目标。

1. **SearchROI**：根据 P1/P2、有限当前证据与既有路径自动延伸，仅负责产生/保留候选，记录边界、方向、降采样、动态扩展次数。
2. **TipAuditWindow**：围绕每个候选的实际原图坐标，在相同像素/自适应线宽尺度下进行独立局部高分辨率采样，且具有固定的*物理意义*的前方/后方审核范围，不随着整张 SearchROI 扩大而变粗。
3. **当审核窗口触边**：若可在图像有效材料范围且预算允许，应只扩展**局部审核窗**再试一次；否则返回 `AUDIT_NOT_OBSERVABLE`，不得当作“尖端不存在”。
4. **候选一致性**：只读反事实中固定完全相同的候选列表、采样尺度/步长、审计区域，测试将 SearchROI 放大 1.5 倍是否影响相同候选的分数与坐标；如果影响，必须定位具体耦合节点。
5. **输入变化语义**：若 ROI 扩大确实找到新的有效图像证据和新候选，输出改变不自动算 bug；应区分“新证据导致合理变化”和“仅内存预算/降采样变化导致非局部扰动”。
6. **细裂纹保真**：不同分辨率、基准标距、线宽、曲率下，统计最小采样精度及线型保留率；不可通过全域稀采样掩盖弱线。
7. **计算约束**：优先采用局部缓存、有限数目候选、固定上界和惰性取窗，不引入随全图尺寸线性爆炸的高分辨率操作。

**不得**为了排除组X 473 把 SearchROI 人为裁到 C 历史尖端；也不得以 ROI 边界作为尖端确认的充分条件。

---

## 6. 研发里程碑 M4：校准尖端决策，不允许“候选在但一票否决”

M4 的候选决策必须明确分离两个不同证据：

- **Terminality（是否形态上到达一条线的末端）**：局部前后对比、沿线延伸、法向小范围重定位、候选位置稳定性。
- **Ownership（这条线是否属于需要测量的裂纹）**：参考图新增变化、参考已有纹理重合、独立配准/光度可信性、与可信主体的关系。

**不可把 Terminality 高等同 Ownership 高。** 两者可能互相冲突或处于 UNKNOWN。C2 的规则应能够在新 DEV 中对两者进行独立消融，不采用简单的所有条件逻辑与。

### 6.1 候选决策结构

推荐（可根据审计后实际代码改进，但要说明）如下：

```text
candidate_pool = {valid A-tip, C-local-tip, C-short-stop, C-forward-tip, ...}
  ↓
per-candidate: current image terminality features
  ↓
per-candidate: reference ownership {SUPPORTED / CONTRADICTED / UNKNOWN}
  ↓
rank hypotheses under one frozen global rule (no GT, no dataset IDs)
  ↓
result: CONFIRMED(candidate) | AMBIGUOUS | NOT_OBSERVABLE
  ↓
optional: path and root; projected length from confirmed tip & P1/P2
```

如果旧 A 在参考证据不足时仍可用，允许研究决策输出 `A_PRESERVED`（对应研究证据状态另存），但**不得将回退 A 的覆盖率当成 C2 新模块的正确率增益**。必须单列 `A_UNCHANGED`、`A_RELOCATED`、`C_NEW_WHEN_A_INVALID`、`C_REVOKED_A`、`AMBIGUOUS`。

**若两个尖端候选相互间隔很大、证据又不能区分，必须允许 `AMBIGUOUS`**；但拒绝计入正例失败损失，不能用 UNKNOWN 掩盖工程损害。

### 6.2 禁止事后阈值选择与伪概率

- 所有候选得分/置信规则，必须只在新 DEV 通过机制验证之后固定。若使用概率/排序模型，必须有独立校准与可靠性检查；未经校准不得声称 `confidence=0.95` 对应 95% 正确率。
- 噪声、尺度、光度模块仅作为辅助证据；**单独尺度估计不得控制所有候选的一票生死**，保留多尺度响应和原因记录。
- 不能使用旧 157 帧中已知 oracle 最优候选的坐标或 GT 来训练新的在线 ranker，再宣称旧案例为测试。
- 不允许强制逐帧投影长度单调、不允许用加载相位未知时的“增长趋势”覆盖当前帧检测。
- 如果审计显示没有新的独立归属证据，只能谨慎保留 A 基线或报告歧义；不得借复杂评分重新包装当前帧暗线启发式并声称解决假尾。

---

## 7. 新 DEV/TEST：本轮最重要的实验设计

### 7.1 先在 DEV 证明目标失败机制确实发生

**新生成器必须先跑冻结 A**，确认挑战不是“纸面上的假尾”。DEV 至少覆盖：

| 对照族 | 应检验的行为 |
|---|---|
| 强纹理连续假尾 | A 被多块高响应假纹理诱导并产生超过 8px 的尾部过长误差，而非仅出现一次低增益 |
| 匹配真长裂纹 | 当前图像与假尾一模一样，但参考图不同、可见端点不同；不能通过一律截短得到伪收益 |
| 真实弱渐浅 / 间歇裂纹 | 防止把低 after_snr 或前方纹理竞争当成必须拒绝的证据 |
| S 形、55° / 75° 弯曲 | 不能因固定水平 ROI 或单尺度线型限制而丢失正确尖端 |
| 静态暗线、加工划痕、孔缘运动 | 防止把参考错位的线状残差识别为新裂纹 |
| 参考已有裂纹、裂纹闭合、曝光/反射 | 参考无变化不能硬否决，前后光度可辨识性应分层 |
| 独立局部材料运动、点坐标误差 | 验证配准和三态参考证据的失效方式 |
| ROI 边界/缩放/宽度变化 | 审核精度不应被全局 ROI 放大和采样预算间接改变 |
| 阴性与稀疏真裂纹早期 | 评价误确认，以及 A 无效时 C 新检出的可信性 |

每个新案例保存原始参考/当前图、P1/P2、显式渲染可见端点 GT、可见范围、背景过程与随机 seed。**GT 定义必须对应真正渲染可观察的末端，不能把形成但不可见的尖端拿来算图像定位误差。** 不可观察子集单独报告。

DEV 的强假尾必须来自多个独立背景、案例种子和纹理过程；若 A 实际没有被诱导过长，本轮测试机制不达标，**先修 DEV 场景设计而非宣称算法防长尾成功**。

### 7.2 严格留出全新 TEST（比旧轮次更高的独立性要求）

- 新 TEST 与 DEV 不只是 RNG 不同；在背景生成机制、纹理参数分布、几何与长度组合上做**预先定义**的独立切分，并留出部分未出现过的背景过程。
- 生成器/GT/评价器/候选规则/门槛在 TEST 生成之前完成哈希冻结。
- TEST 原始参考/当前、P1/P2、GT、input SHA 在第一次检测之前封存。TEST 检测一次性执行；失败不得以新 seed 重跑到成功。
- 要保留真假尾**匹配对**，并在 manifest 中断言：当前图 SHA 和 P1/P2 精确一致、reference SHA 不同、GT 端点不同；配对样本必须作为一个独立统计案例/聚类，不得把两条图像和相邻帧当独立重复。
- 不可通过文件名、`family`、`background_id`、参考种类标签向检测器泄漏真假尾条件；另做重命名与打乱元数据不变性检查。
- 按独立 case 聚类，并对共享当前渲染 pair 做成对 / 分层 bootstrap，避免按 6 个相邻帧独立计算窄 CI。
- TEST 后补充的故障分析必须保留只读状态，不得据此调整 C2 后再拿同一 TEST 声称正式通过。

### 7.3 必做消融（每次只问一个因果问题）

至少输出以下**相同输入、同 GT 口径、同候选池或明确注明候选池变化**的版本：

| 版本 | 作用 |
|---|---|
| `A0_FROZEN` | 生产基线，精确重放 |
| `C2_POOL_ONLY` | 只保留候选池，检查 oracle 上界，不进行候选改写 |
| `C2_CURRENT_TERMINALITY` | 使用当前帧尖端局部形态，参考归属强制 UNKNOWN |
| `C2_OWNERSHIP_VALIDATED` | 加入校验合格的参考归属证据 |
| `C2_OWNERSHIP_UNVALIDATED` | 故意屏蔽校验，验证降级行为 |
| `C2_SEARCH_AUDIT_SPLIT` | 固定候选比较 ROI 审核解耦的效果 |
| `C2_FULL_SHADOW` | 实际候选/确认全量输出，**仅研究，不改变生产 A** |
| `REF_SHUFFLED / REF_MASKED` | 参考负控和信息缺失测试 |

不能拿 `C_ROI` 与 `A0` 的指标差当成“只改 A 内部 ROI”造成的因果收益；要报告版本之间哪些代码、候选、配准和审核真正共用。

---

## 8. 指标、保护边界与是否允许进入 C++

### 8.1 必报主指标（统一 TEST scope）

在**可观察正例**上分别统计：

1. 端点二维误差：`MAE`、`median`、`P95`，以及条件于确认的样本范围；
2. 尖端二维误差 ≤8px 的**总可观察正例正确数/正确率**（未确认算未达到，不能只看已确认 MAE）；
3. A/C2 配对：双方正确、A-only 正确、C2-only 正确、双方错误，及每种改写/撤销的 GT 影响；
4. 全正例拒绝惩罚损失（历史版本 32px 拒绝成本、64px 误差封顶作为可比基准；新门槛需在 DEV 前锁定，不得 TEST 后修改）；
5. 假长尾过长（按水平投影与二维分别定义）、真长错误截短、弱渐浅漏检、弯曲漏检；
6. 阴性误确认的例数与比率（相同阴性分母），并按孔缘运动/静态纹理等机制分层；
7. 归属三态的有效范围、参考验证通过率、错误支持/错误矛盾、UNKNOWN；
8. 候选池的 `oracle_min_candidate_error`（**离线仅作诊断上界**）、最终正确选择率、正确候选被拒绝数；
9. ROI 反事实同候选、同采样下的坐标差、候选数变化、引起差异的具体模块；
10. bootstrap 置信区间、按背景/家族/独立 case 统计，报告配对共同确认和全体覆盖的两个不同样本集。

**所有结果必须显示样本分母、参考/当前区别、无效状态及版号，不能把 N/A 填零算精度。**

### 8.2 建议的正式准入规则（冻结后才可使用 TEST）

为防止再出现 C 的 157 次正确结果被撤销，建议延续**不降低 A 的正确端点数和覆盖率**为硬性工程方向，具体数值应在新 DEV 结束/TEST 前作为独立准入协议冻结。建议以下严格标准：

- 全体可观察正例：**正确尖端（≤8px）的绝对数量不得低于 A**，并要求全正例惩罚损失相对 A 改善；
- 正例确认覆盖非劣效：**最多下降 0.5 个百分点**，或者若有事前批准的成本权衡，应提供独立非劣效区间而不是口头解释；
- 已知原本正确的 A 结果被撤销/改错：**以 0 为目标准入线**；若新 TEST 有违反则原则上 `RESEARCH_ONLY`，不可事后用被修复案例数冲抵；
- 阴性误确认：不得高于 A，配对错误差异和置信区间同时报告；
- 假尾必须有**独立案例级的实际修复**，且匹配真长**不得出现系统性截短**；不能只挑单帧成功；
- paired case bootstrap 的全正例损失差必须有支持“C2 优于 A”的统计证据，不允许仅用条件 MAE 或只看阴性 FP；
- 搜索 ROI 扩大不会无端改变固定候选的局部审核证据：如变更 >2px，需有可审计的**新增证据或特定模型变化**，否则视为稳定性失败；
- 所有版本/参数、合成器、冻结 DLL、最终评估代码和测试输入均 SHA-256 锁定；元数据不变性测试通过；
- 未获得全新未曝光真实材料或物理真值：只能通过**程序已知端点的研究准入**，真实物理精度仍 N/A，生产发布条件 `REAL_HOLDOUT_NOT_AVAILABLE`。

如果实际新 DEV 显示 0 次正确 A 撤销无法同时达到假尾修复，必须在**TEST 前**明确提交权衡方案并冻结更合理的非劣效/风险标准；不能在看过 TEST 后临时更改。历史固定标准应保留用于对照。

### 8.3 原生 C++ / 15Hz gate

- **只有当新 TEST 通过效果与安全门槛**时，才开发隔离的 C++17/OpenCV4.4 C2 候选核心；否则只交付 Python/研究实现并明确 `CPP_C2_NOT_BUILT`。
- 原始 A 最大既有部分试件接近 66.67ms，不可按平均时间预算追加整套复杂搜索。优先有限候选 + 局部审核 + 缓存；真实最大耗时必须在全组完整原生核心上测量。
- 计时至少覆盖 `Process`、`GetResultV2`、`CopyPath`、新增局部审核及必要分配，记录 worst-case、P95、P99、各模块耗时与峰值内存；输入预解码、I/O 与视频渲染是否计入要明确。
- `Max ≤66.67ms` 是原生完整核心初始硬边界；若系统要求持续 15Hz，应另外验证采集、解码、队列与系统端到端时延。
- 不允许用 Python 旁路时间、视频 15FPS 或仅 512×512 合成图表现代替 5120×5120 真实场景实时性证明。

---

## 9. 开发执行顺序与阶段性停止条件（严格按顺序）

**M0 — 冻结身份与证据复算**：校验旧 A、C/ZIP 输入，复算 157/19、54 对、reference ratio、光度状态和 ROI 反事实；源码定位、数据角色表、现有测试脚本回放。缺件明确说明。

**M1 — 仅候选保留**：使 A 原尖端和 C 局部候选都不被无谓删除；分离 oracle 候选上界与实际在线决策；修复候选流转和原因记录。输出开发回归，不宣称独立提升。

**M2 — 可信参考归属**：审计现有光度失败条件，开发分离配准/光度/参考归属的三态模块，完成已曝光匹配对的机制检查，并用全新 DEV 验证“加参考确有额外可辨识信息”。无通过证据则停止复杂融合。

**M3 — ROI 搜索/审核解耦**：实现固定局部采样与可解释的边界扩展；验证同候选 SearchROI 扩大反事实。若解决不了稳定性，不可扩大 C2 使用范围。

**M4 — 融合候选决策**：只在新 DEV 上定规则，保持 A candidate 与多种 C candidate 并列；对 `terminality` 与 `ownership` 单独消融；严禁依据已看 TEST 临时回调。

**M5 — 预注册 + 新 TEST 一次性验证**：冻结输入生成器、参数、脚本、指标与门槛；统计 2D tip 及全正例总风险；失败即 `KEEP_A`，不可回填解释成“已修复”。

**M6 — 已曝光真实六组只读回归 + 性能**：只生成 A/C2 差异表和关键图；无物理 GT 则不判定谁更准确；效果 gate 通过之后才做 C++ 候选和核心时延。

**M7 — 决策与交付**：即使未通过，也要交付全部开发代码、失败证据、复现命令、逐帧/逐候选 CSV、指标、图像和明确下一步最小瓶颈。

> **不得跳过某个失败 gate 继续宣布后续阶段通过。** 允许为诊断继续运行，但报告必须将其标为 `EXPLORATORY_ONLY`，正式发布决策仍为 `KEEP_A`。

---

## 10. 完整交付结构与可复现要求

建议建立（实际根目录可不同，但要求语义一致）：

```text
CrackV4_C2_ReferenceOwnership_Research_<run_id>/
├── 00_protocol/
│   ├── data_role_manifest.csv
│   ├── baseline_identity.json
│   ├── DEV_TEST_isolation.json
│   ├── preregistered_gates.json
│   ├── freeze_manifest.json
│   └── deviations_and_errata.md
├── 01_audit/
│   ├── source_contract.md
│   ├── reproduced_prior_metrics.csv
│   ├── known_mechanism_failures.md
│   └── baseline_replay_comparison.csv
├── 02_source/
│   ├── candidate_union.py
│   ├── reference_registration_validation.py
│   ├── reference_photometry_validation.py
│   ├── path_ownership_evidence.py
│   ├── search_roi_and_tip_audit.py
│   ├── endpoint_decision.py
│   ├── replay_and_evaluate.py
│   └── tests/
├── 03_new_gt/
│   ├── DEV_manifest.csv
│   ├── TEST_LOCKED_manifest.csv
│   ├── paired_reference_invariance_audit.csv
│   └── input_gt_hashes.csv
├── 04_results/
│   ├── TEST_frame_predictions.csv
│   ├── TEST_all_candidates.csv
│   ├── TEST_evidence_and_validity.csv
│   ├── TEST_matched_pair_results.csv
│   ├── TEST_roi_same_candidate_counterfactual.csv
│   ├── TEST_ablation_metrics.csv
│   ├── TEST_per_family_and_background.csv
│   ├── TEST_A_correct_protection.csv
│   ├── TEST_bootstrap_CI.csv
│   └── DEV_mechanism_and_gate_results.csv
├── 05_regression/
│   ├── all_six_groups_per_frame_A_C2.csv
│   ├── exposed_cases_diagnostics.csv
│   └── known_cases_and_unresolved.csv
├── 06_performance/
│   ├── A_native_replay.csv
│   ├── C2_native_full_if_eligible.csv
│   └── profiling_notes.md
├── 07_media/
│   ├── historical_key_cases/
│   ├── new_DEV_key_cases/
│   ├── new_TEST_key_cases/
│   ├── per_group_galleries/
│   └── index.html
├── 08_reports/
│   ├── executive_summary.md
│   ├── source_and_contract_findings.md
│   ├── ownership_identifiability_results.md
│   ├── candidate_selection_failure_analysis.md
│   ├── generalization_and_physical_limits.md
│   └── release_decision.md
├── all_files.sha256
└── README_build_and_run.md
```

**逐帧输出列至少包括**：

`case_id, frame_id, side, input_sha256, ref_sha256, algorithm_version, code_hash, tip_valid, tip_x, tip_y, tip_status, tip_reason, tip_origin, A_tip_x, A_tip_y, A_valid, candidate_count, candidate_min_oracle_error_OFFLINE_ONLY, terminality_evidence, ownership_evidence, ownership_status, registration_status, photometry_status, roi_status, SearchROI_bounds, TipAuditWindow_bounds, sampling_step, reference_line_overlap, registered_change_support, path_valid, path_role, root_valid, horizontal_length_px, projection_valid, gt_observable_EVAL_ONLY, gt_tip_x_EVAL_ONLY, gt_tip_y_EVAL_ONLY, tip_error_2d_EVAL_ONLY, runtime_ms`。

研究输出必须能让第三方明确区分**在线检测可用列**与**离线 GT 评价列**，禁止将评价列传入运行时模块。

视频/图库的最低要求：

- **原图、A、C2 候选与最终尖端并排**；显示各自有效位和单位、参考归属三态、ROI/审核范围，不能通过缩放和颜色遮掩错误；
- 真实六组至少提供所有 A/C2 不一致帧索引和精选局部无损 PNG；已曝光历史排除组X 51/473、CT2 6/18/84、三点弯 53 仍须回归，但明确“非 GT”；
- 新 TEST 的假尾/真长**成对同图不同参考**要有并列审计图，展示参考图和当前图以及 GT、候选、决策，不允许只出成功图；
- 15FPS 视频仅为播放速率，不是算法实时性证明。

**复现**：说明 Python/C++/OpenCV 版本、环境依赖、命令执行顺序、每步输入输出、SHA 验证和内存需求；无法重新运行的依赖必须列为 `NOT_REPRODUCIBLE`，不能冒充完整复现。

---

## 11. 最终报告必须直接回答的 12 个问题

1. 历史 157 个 A 正确但 C 拒绝的案例，是否确实都含正确候选？确认失败到底发生在哪一个代码条件？
2. 新 DEV/TEST 的准确候选召回是否足够高？候选已存在时，决策器准确选中的比例是多少？
3. 加入参考归属之前和之后，**相同当前图、不同参考**的假尾/真长配对辨别是否实际改善？有多少独立案例成功？
4. `reference_ratio` 的真正代码语义是什么？它的旧分布差别是否可以经配准/光度与背景变化验证？
5. 新 reference validation 覆盖率为何变化？哪些情况必须 UNKNOWN？有没有错把不可评估当负证据？
6. 当前图局部终点证据相当但归属不同的场景，C2 是否能区分；如果不能，缺的是哪种独立观测？
7. C2 是否仍会将原 A 正确尖端撤销或改错？哪类候选与审核规则导致？
8. 假尾修复是否伴随匹配真长截短？弱渐浅及大曲率场景是否回退？
9. SearchROI 放大时，相同候选/审核像素是否保持稳定？ROI 扩大后结果变动是新证据还是采样伪影？
10. 根部或完整路径无效时，C2 是否仍能正确输出尖端与投影长度？有没有混淆旧弧长？
11. 新 TEST 是否在冻结前就有足够 A 假尾失败案例？用何种 case 聚类统计与置信区间证明净收益？
12. 本轮结论应是 `KEEP_A`、`C2_SHADOW_ONLY`、`C2_RESEARCH_CANDIDATE_NOT_RELEASED` 还是可进一步进入独立物理验证？**不得跳过未通过的效果和 C++ 门槛**。

---

## 12. 给 Agent 的最终执行指令

**现在开始实际执行。** 首先扫描现有源代码与研究目录，验证冻结 A 和补充 ZIP，复算关键数字并查清代码层面拒绝准确候选、参考验证失效与 ROI 采样耦合的原因；然后在完全隔离的新 C2 研究分支中逐模块开发 M1–M4，按照 M5 的新预注册 TEST 给出真实效果判决。要求输出实际运行后的逐帧 CSV、候选级 CSV、配对误差、反例 PNG、性能记录与清晰的发布结论，而不是只有设计文档。

**优先保留 A 的正确结果，但不得神化 A：** 如果参考归属在有充分独立证据时证明 A 延伸到了旧纹理，C2 应有能力提出更短尖端；如果真实裂纹继续延伸，C2 也应有能力保留或提出更远尖端。**核心成败标准是：新独立样本中的已知端点实际更准确、正确尖端总数不下降、真假尾可辨识性得到改善，而不是算法变复杂或者确认率变低。**

如果物理和图像输入的信息量不足以可靠区分两种末端，就应坦诚输出不可辨识和所需新增观测条件；**不得通过针对试件名称调参、追随旧 TEST 真值、硬截断或改写生产 A 来制造成功结果。**
