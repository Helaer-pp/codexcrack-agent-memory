# 裂纹尖端追踪算法（`detector.py`）普适性与精度提升开发指令（Agent Prompt）

> **使用说明**：请将本文档完整发送给负责代码开发的执行 Agent，并附上项目代码包（含 `research/raw_notch_trace_v2b/detector.py`、评测脚本与数据集）。本指令基于 [four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt)（对应 [原始诊断记录](https://raw.githubusercontent.com/Helaer-pp/codexcrack-agent-memory/refs/heads/main/handoff/diagnosis/four_files_for_chat.txt)，提交版本 `c2beeffc`）确立的实验结论与源码诊断编写。

## 1. 角色定位与总体目标

你是一名资深计算机视觉与实验力学图像算法工程师。你的任务是在现有**原灰度 r02 基线**（`research/raw_notch_trace_v2b/detector.py`）的基础上，结合 `UCTIP-60Q`（`research/unified_crack_tip_60q/engine.py`）的有益机制与 [four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt) 中的历史实验结论，对裂纹路径与尖端追踪算法进行**分阶段、可消融、零硬编码作弊**的迭代升级，显著提升算法的**跨场景普适性（Generalizability）**与**路径/尖端联合精度（Joint Accuracy）**，并在完成后提交一份结构化的**《算法开发与消融验证报告》**。

| 评估维度 | 核心指标定义 | 冻结基线（原灰度 r02）表现 | 本轮开发目标 |
| :--- | :--- | :--- | :--- |
| **DEV-A（full / raw_only）** | 可见 19 帧：`Hit@10` / `Joint` / `Severe` | `16/19` / `16/19` / `0`（中位误差 `4.92 px`）([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt)) | 保持 `Hit@10 >= 16/19`、`Joint >= 16/19`、`Severe == 0`，记录任何受损帧 |
| **DEV-B（full）** | 可见 15 帧：`Hit@10` / `Joint` / `Severe` | `10/15` / `1/15` / `0`（中位误差 `8.63 px`）([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt)) | 解决近缺口选错上下唇问题，使 `Joint` 大幅逼近 `Hit@10`（目标 `Joint >= 8/15`），`Severe == 0` |
| **DEV-B（raw_only）** | 可见 15 帧：`Hit@10` / `Joint` / `Severe` | `10/15` / `2/15` / `0`（中位误差 `8.63 px`）([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt)) | 消除 `full` 模式下双差分对近缺口唇缘的负向干扰，确保 `full` 不劣于 `raw_only` |
| **REG-C（固定版本回归）** | 可见 20 帧：`Hit@10` / `Joint` / `Severe` | `6/20` / `6/20` / `0`（中位误差 `14.52 px`，14 帧向右过冲）([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt)) | 抑制尖端后材料纹理继续得分，显著提升 `Hit@10` 与 `Joint`（参考 `60Q` 曾达 `12/20` 与 `10/20`），`Severe == 0` |
| **扩展合成探针（Synthetic Probes）** | 静态暗线、相邻划痕、闭合细线、开口边缘、渐弱暗线+纹理 | `60Q` 扩展探针存在静态暗线假阳性，`r02` 仅覆盖 3 项特定几何 ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt)) | 独立反例假阳性清零，通过多尺度（`scale`）与多信噪比鲁棒性检验 |

## 2. 严守的工程与学术纪律（Hard Constraints）

1. **禁止样本身份泄露与过拟合**：`detector.py` 必须保持纯观测驱动接口（不读取文件名、组别 `DEV-A/B/C`、帧号或标注点），严禁针对特定样本坐标硬编码分支条件。所有几何参数必须与输入尺度因子 `scale` 或局部统计量成比例绑定，消除固定像素魔数（如硬编码的 `55`、固定像素窗口等）以提高跨分辨率普适性。
2. **严格遵守控制变量与阶段消融**：遵循 [four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt) 确立的实验原则——**每项改动先在开发数据上与冻结 `r02` 对照，同时记录尖端命中（`Hit@10`）与路径联合命中（`Joint`），并逐帧记录受益帧与受损帧（Damaged Frames）**。
3. **严格隔离回归集审计**：不得将 `REG-C` 的图像或点位用于超参数调优（吸取 `UCTIP-60Q` 阶段误读 `C` 组导致隔离审计失败的教训 ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt))）；所有阈值与结构设计必须在开发集与合成探针上确定后，一次性在 `REG-C` 上执行盲测回归验证。
4. **保持计算高效与可确定性**：吸取 `UCTIP-60Q` 在 `DEV-A` 上 551 帧全部触发搜索预算耗尽（`BUDGET_EXHAUSTED`）的教训 ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt))，保持 `detector.py` 基于局部动态规划与轻量级多起点竞争的常数级复杂度，不引入无界图搜索。

## 3. 现有 `detector.py` 的四大源码级症结诊断

在动手修改代码前，请完整理解以下已定位的源码级根因：

### 症结一：近缺口段选错唇缘且后段汇合后无法替换（对应 `DEV-B` 联合命中仅 1/15）
* **源码位置**：`locate_root`（第 24–35 行）与 `predict`（第 106–115 行）。
* **机理剖析**：
  1. `locate_root` 取连通域外接矩形最右列 `end = bx + width - 1` 的像素中位数作为主起点 `starts[0]`。当缺口张开且上下唇长度相差仅 1～2 px 时，最右列 `end` 仅包含突出侧唇缘（例如上唇），导致 `starts[0]` 直接偏置到单侧唇尖而非缺口中心。
  2. `predict` 第 109 行设置硬门控 `if result['tip'] is None or result['tip'][0] - root[0] < 55:`。当从错误唇缘（如 `DEV-B` 第 215 帧的上唇）出发的轨迹在后段汇入主裂纹并走完全程时，其总水平跨度远超 `55 px`，导致 `starts[1:]` 中的正确下唇起点**被完全短路跳过，根本没有执行追踪** ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt))。
  3. 即便进入 `for start in starts[1:]:` 循环，第 113 行的替换条件 `trial['tip'][0] > result['tip'][0] + 2` **只比较终点 `x` 坐标谁更靠右**。对于“近缺口分走上下唇、后段汇合到同一真值尖端”的样本（如 `DEV-B` 第 215 帧端点误差仅 `2.08 px`，但路径覆盖仅 `57%` ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt))），两条候选路径的终点 `tip[0]` 几乎完全相同，按终点 `x` 比较永远无法选出前段真正沿着裂纹暗谷延伸的那条轨迹。

### 症结二：尖端后方材料纹理继续得分导致向右过冲（对应 `REG-C` 14 帧全部预测在标注点右侧）
* **源码位置**：`valley_image`（第 39–51 行）、`trace_windowed`（第 54–75 行）与 `follow`（第 82–86 行）。
* **机理剖析**：
  1. `valley_image` 第 48 行 `background = np.percentile(evidence[::3], 85, axis=0)` 按每一列 `x` 独立计算 85% 分位数背景。当追踪越过真实裂纹尖端进入右侧纯材料区域时，列内不再有深暗谷，该列 `background` 与 `threshold` 随之降到最低保底水平，变相放大了尖端右侧微弱的材料纹理响应。
  2. `valley_image` 第 43 行 `cv2.GaussianBlur(response, (5, 3), 1.0, .65)` 沿 `x` 轴平滑使尖端强响应向右拖尾，配合 `trace_windowed` 的 `horizon = 20` 前瞻窗口与 `min(4., v) - 1.1` 截断奖励，使路径顺着零星材料暗斑继续向右滑行。
  3. `follow` 第 82–85 行仅要求 `v >= 1. and response[py, px] >= 3.` 且末端 6 个命中点跨度内有 4 个点达标。`response >= 3.0` 在 8-bit 灰度图中仅相当于比上下侧翼暗 3 个灰度级，且完全没有对比**路径主干段的暗谷深度**与**末端尾段的暗谷深度**，也没有类似 `UCTIP-60Q` 中 `verify_candidate` 对尖端前方完好材料区（`after_material_fraction`）的校验 ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt))。

### 症结三：双差分通道（`bonus`）与尖端确认脱节，并在近缺口段放大唇缘位移伪影
* **源码位置**：`trace_windowed`（第 67 行）与 `follow`（第 82–86 行）。
* **机理剖析**：
  1. `bonus` 仅在 `trace_windowed` 的 DP 转移 `nxt[i] = best + min(4., v) - 1.1 + bonus[...]` 中累加，而在 `follow` 的 `hits` 过滤与 `end` 尖端回溯中**完全未使用 `bonus`**。
  2. 在近缺口段，试件受载张开使上下唇外缘产生强烈帧间差分，`bonus` 在原灰度暗谷较弱的错误唇缘上强行加分续命，导致 `DEV-B` 在 `full` 模式下的 `Joint`（1/15）反而低于 `raw_only` 模式（2/15）([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt))。

### 症结四：近缺口静态暗线与开口边缘缺乏结构反例抑制
* **源码位置**：`locate_root`（第 16–36 行）与 `follow`（第 82–88 行）。
* **机理剖析**：`follow` 只要满足 `hits[0] <= 2`、`end + 1 >= 9` 且局部 4/6 命中即可输出 `VALID`。当缺口附近存在长 10～15 px 的静态划痕、闭合细线或开口边缘阴影时，缺乏对路径几何形态（如直线性/折返率、与缺口张开轮廓的贴合伪影）和根部结构连续性的独立甄别 ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt))。

## 4. 分阶段开发任务书（Staged Implementation Plan）

请严格按以下四个阶段依次推进代码开发与对照实验，**每个阶段必须保留可切换的配置开关或消融分支**，以便在最终报告中给出逐阶段量化对比。

### Stage 1：近缺口段身份选择与汇合消歧（严格固定 `valley_image`、`trace_windowed` 与 `follow` 终止门）

按照 [four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt) 中 `OPEN_PROBLEMS.md` 的第一优先级要求：**“固定灰度证据、终止门和评价器，只改变近缺口段身份选择，逐帧检查两条候选的起点和汇合位置”**：

1. **改进 `locate_root` 起点集合生成**：
   * 避免仅用单列 `end = bx + width - 1` 定义主中心，改为统计缺口连通域前端 `end - max(4, round(0.04 * scale))` 至 `end` 区间内的前缘轮廓，提取稳健的缺口前端中心与上下唇前缘候选点集合 `starts`。
   * 确保上下唇两侧前缘对称采样，采样跨度与步长均与 `scale` 绑定。
2. **解除 `predict` 的 `< 55 px` 短路限制，实现全起点平行评估**：
   * 对 `starts` 中的每一个候选起点均调用 `follow(signal, response, bonus, start)`，记录所有 `status == 'VALID'` 的候选轨迹。
3. **实现“路径汇合检测（Coalescence Detection）”与“汇合前近缺口段质量裁决”**：
   * 编写辅助函数检测任意两条有效轨迹 `A` 与 `B` 是否在后段汇合（即从某个相对水平位置 `x_merge` 起，两条轨迹在同一 `x` 处的 `|y_A - y_B| <= 2` 持续重合，或最终尖端距离小于等于 `max(3.0, 0.03 * scale)`）。
   * **当两条轨迹发生后段汇合时**（代表同一主裂纹的上下唇分叉竞争），严禁按 `tip[0]` 选路径，而是提取每条轨迹在**汇合前路段（`x` 从各自起点到 `x_merge`，或前 `min(dx, round(0.25 * scale))` 范围）**的观测特征进行打分：
     * **近缺口段有效支撑密度**：汇合前路段中满足强暗谷响应的像素占比（惩罚沿空白/弱边缘硬跳变后再斜向切入主裂纹的伪分支）；
     * **近缺口段暗谷强度与横向连续性**：汇合前路段内 `signal` 与 `response` 的中位数/截尾均值，减去纵向剧烈跳变（`|dy| > 1`）的曲率惩罚；
     * **起点根部附着质量**：起点最初 `5~8 px` 内的局部谷深与方向一致性。
   * **当两条轨迹未发生汇合（走向完全不同的终点）时**：综合整条轨迹的平均暗谷质量、有效命中密度与延伸长度进行裁决，避免一条靠微弱纹理勉强延长几个像素的伪分支仅凭 `tip[0] > result['tip'][0] + 2` 击败高置信主裂纹。
4. **输出逐帧近缺口诊断信息**：
   * 在返回字典中附加 `diagnostics` 字段，记录该帧所有 `starts` 候选坐标、各候选对应的 `tip`、是否发生汇合、汇合位置 `x_merge` 以及汇合前各候选的近缺口段得分明细，并在 `DEV-B`（重点核查第 215 帧等样本）与 `DEV-A` 上与冻结 `r02` 逐帧比对。

### Stage 2：尖端终止门升级与材料纹理过冲抑制（攻克 `REG-C` 过冲，兼顾跨材质普适性）

在锁定 Stage 1 改进并确认 `DEV-A / DEV-B` 无退化后，针对 `REG-C` 14 帧全部向右过冲的问题（如第 38 帧误差 `22.75 px` ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt))）改进背景估计与尖端截断：

1. **稳健化 `valley_image` 的背景阈值基线**：
   * 检查单列 `np.percentile(evidence[::3], 85, axis=0)` 在越过裂纹尖端后的数值塌陷现象。引入沿 `x` 方向的宽窗口平滑或与全局/前半区稳健背景分位数的下界融合，防止在无裂纹的纯材料列上因分母过小而将微弱材料纹理归一化为 `signal >= 1.0`。
2. **在 `follow` 中引入“主干相对谷深比”与“尖端前方材料上下文”双重终止门**：
   * **主干-尾段相对对比度（Body-to-Tail Relative Support）**：计算当前轨迹已确认主干段（例如前 60% 或高置信连续段）的稳健谷深基准 `body_response_ref`。在从后往前搜索 `end` 时，除了要求局部窗口内命中点个数（`4/6`）外，要求候选尖端局部窗口的 `response` 均值/中位数不仅满足绝对下限，还需满足相对于 `body_response_ref` 与局部背景噪声 `noise` 的自适应门槛，识别并截断“暗线逐渐消失后退化为基底微弱纹理”的拖尾段。
   * **尖端前方完好材料上下文检验（借鉴 `UCTIP-60Q` `verify_candidate`）**：对比候选尖端左侧紧邻段（裂纹尾端，长度 `L_in`）与右侧紧邻段（尖端前方材料区，长度 `L_out`）的暗谷响应分布及灰度方差特征，确保最终认证的 `tip` 真正位于“连续暗线支撑的终点”而非材料纹理内部。

### Stage 3：双差分通道（`bonus`）重构与静态暗线反例过滤（提升普适性与抗伪影能力）

1. **重构 `bonus` 的作用方式**：
   * **门控化 DP 增益**：在 `trace_windowed` 中，限制 `bonus` 仅在当前位置原灰度已经具备基本暗谷趋势（如 `v >= 0.65`）时按比例生效，或者在近缺口张开段（前 `0.2 * scale` 范围内）抑制纯边缘位移造成的非暗谷差分伪影，彻底解决 `DEV-B` 开启双差分后 `Joint` 反而下降的问题。
   * **尖端阶段的差分辅助判据（非一票否决）**：当 `bonus` 可用时，监测差分改变了哪一段路径（按 `OPEN_PROBLEMS.md` 要求保留原灰度对照 ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt))），使 `full` 模式在所有数据集上均大于等于 `raw_only` 模式。
2. **近缺口静态暗线与几何反例抑制**：
   * 针对静态划痕、相邻平行细线、闭合环状伪影及缺口张开外轮廓边缘，在候选轨迹验证中加入：
     * **起点与缺口主体的拓扑连续性检查**（排除与缺口根部存在明显亮带隔离的独立划痕）；
     * **路径折返率与直线性（`path_straightness`）检查**（借鉴 `60Q` 的 `coherence = displacement / length` 判据 ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt))，剔除沿开口边缘弯曲折返或纹理打转的伪路径）。

### Stage 4：构建独立合成探针套件（Synthetic Benchmark Suite）

编写独立的自动化测试脚本，构造以下 5 类参数化合成图像探针（覆盖不同 `scale`、信噪比与对比度），验证算法的普适性：
1. **探针 P1（双唇分叉再汇合）**：模拟缺口张开后上下唇均有边缘响应，其中一侧为浅边缘伪影、另一侧为真实深暗谷并在 `40~80 px` 后汇合，检验路径覆盖率是否达 100%。
2. **探针 P2（暗线渐弱后接材料纹理）**：模拟真实裂纹暗线对比度逐渐衰减至消失，后方存在周期性或随机晶界暗斑纹理，检验尖端是否精准停在连续暗线末端而不向右过冲。
3. **探针 P3（近缺口独立静态暗线与相邻划痕）**：模拟无真实裂纹扩展、仅有与缺口微距分离或斜交的静态划痕，检验算法是否能正确拒绝输出假阳性（单列假阳性来源）。
4. **探针 P4（闭合细线与大张开缺口外缘）**：模拟缺口大角度张开时的明亮/暗边过渡及闭合细环纹，检验是否误锁开口唇缘。
5. **探针 P5（多尺度 `scale` 缩放测试）**：将上述探针在 `0.5x`、`1.0x`、`2.0x` 尺度下缩放，验证算法无硬编码像素阈值依赖。

## 5. 强制交付物要求：标准化《开发与消融验证报告》

完成代码迭代与全部实验后，你必须输出一份结构完整、数据真实的 Markdown 格式**《裂纹尖端追踪算法升级开发与验证报告》**，报告必须包含以下 6 个核心章节：

### 5.1 执行摘要与核心改动清单（Executive Summary & Code Diffs）
* 简述针对四大症结所做的核心算法改动。
* 列出 `detector.py` 每个函数（`locate_root`、`valley_image`、`trace_windowed`、`follow`、`predict`）修改前后的关键逻辑差异与参数尺度化（`scale`）映射关系。

### 5.2 分阶段消融实验指标总表（Staged Ablation Metrics Table）
必须以标准 Markdown 表格汇报从冻结 `r02` 基线到各阶段叠加后的完整评测结果：

| 实验配置 / 阶段 | 评测组与模式 | Visible / Valid | Hit@10 | Joint（路径+尖端联合） | Severe（严重误差） | Median Error (px) | Max Error (px) | 相比 r02 的净变化 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline（冻结 r02）** | DEV-A (full / raw_only) | 19 / 19 | 16 | 16 | 0 | 4.92 | 92.06 | 基线参照 ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt)) |
| **Baseline（冻结 r02）** | DEV-B (full / raw_only) | 15 / 15 | 10 / 10 | 1 / 2 | 0 | 8.63 | 65.91 | 基线参照 ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt)) |
| **Baseline（冻结 r02）** | REG-C (full) | 20 / 20 | 6 | 6 | 0 | 14.52 | 39.42 | 基线参照 ([four_files_for_chat.txt](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/handoff/diagnosis/four_files_for_chat.txt)) |
| **+ Stage 1（近缺口汇合消歧）** | DEV-A / DEV-B / REG-C | 实测填写 | 实测填写 | 实测填写 | 实测填写 | 实测填写 | 实测填写 | 重点核验 DEV-B `Joint` 提升 |
| **+ Stage 2（尖端终止门升级）** | DEV-A / DEV-B / REG-C | 实测填写 | 实测填写 | 实测填写 | 实测填写 | 实测填写 | 实测填写 | 重点核验 REG-C 过冲收敛 |
| **+ Stage 3（差分门控+反例抑制）** | DEV-A / DEV-B / REG-C | 实测填写 | 实测填写 | 实测填写 | 实测填写 | 实测填写 | 实测填写 | 重点核验 `full` vs `raw_only` |

### 5.3 逐帧诊断审计表（Frame-by-Frame Diagnostic Audit）
* **DEV-B 近缺口段专项复查**：列出 `DEV-B` 全部 15 个可见标注帧（特别是第 215 帧）在修改前后的起点坐标、备选唇缘起点坐标、汇合点 `x_merge`、汇合前近缺口段得分对比、路径覆盖率（Path Coverage）以及端点误差变化。
* **REG-C 过冲帧专项复查**：列出 `REG-C` 原先 14 个向右过冲帧（特别是第 38 帧）在修改前后的预测 `x`、真值 `x`、误差 `dx`、主干谷深基准 `body_response_ref` 与截断处的局部响应值。
* **受损帧（Damaged Frames）透明披露**：明确列出任何在冻结 `r02` 上命中、但在新版本上未命中或误差增大的帧号，分析具体原因并说明是否可接受。

### 5.4 扩展合成探针验证矩阵（Synthetic Probes Matrix）
* 汇报 P1～P5 五组合成探针在 `r02` 与新版本上的通过率、假阳性率（False Positive Rate）与跨尺度（`0.5x / 1.0x / 2.0x`）误差一致性。

### 5.5 普适性与鲁棒性论证（Generalizability Analysis）
* 说明所有新增或调整的判据为何具备物理与几何普适性（如何自适应不同光照、不同信噪比、不同缺口张开角度及不同图像倍率 `scale`）。

### 5.6 残余问题与下一步可检验假设（Remaining Open Problems & Next Steps）
* 按照 `docs/OPEN_PROBLEMS.md` 的三列格式（`问题 | 已有证据 | 可检验的下一步`）更新剩余未解决的边界情况，并同步更新 `evidence/latest_metrics.json`。
