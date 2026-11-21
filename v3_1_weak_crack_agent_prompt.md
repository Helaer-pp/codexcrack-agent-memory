# V3.1 裂纹尖端追踪算法（`notch_identity_v3`）弱裂纹修复与普适性升级开发指令（Agent Prompt）

> **使用说明**：请将本文档直接发送给负责代码开发的执行 Agent，并附带完整仓库环境。本指令基于 V3 交接规范 [V3_AGENT_SPEC.md](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/docs/V3_AGENT_SPEC.md)、V3 开发与消融报告 [REPORT.md](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/evidence/v3/REPORT.md) 及核心源码 [terminal.py](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/research/notch_identity_v3/terminal.py)、[detector.py](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/research/notch_identity_v3/detector.py) 编写。

## 1. 任务背景与 V3.1 核心目标

当前 V3 完整版（`s3t`）在 `REG-C` 上将 `Hit@10` 与 `Joint` 从 `6/20` 提升至 `13/20`（中位误差从 `14.52 px` 降至 `5.86 px`），但**未通过生产验收**（[V3_AGENT_SPEC.md](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/docs/V3_AGENT_SPEC.md)）。核心短板集中在**裂纹较弱区域的异常截断与断带**，以及**偏离基准尺度 `scale=288` 时的普适性退化**：

| 评测集 / 探针 | V3 (`s3t`) 当前表现 | 本轮 V3.1 开发与验收目标 |
| :--- | :--- | :--- |
| **DEV-A（可见 19 帧）** | `full`: `14/19`；`raw_only`: `15/19`（`366, 451, 504, 542` 因尖端渐弱被提前截断 `13~22 px`）([REPORT.md](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/evidence/v3/REPORT.md)) | 恢复 `Hit@10 >= 16/19`、`Joint >= 16/19`、`Severe == 0`，且 `full` 不劣于 `raw_only` |
| **DEV-B（可见 15 帧）** | `Hit@10`: `10/15`；`Joint`: `1/15`（第 215 帧下唇在 `x=1505` 因弱对比断带停止，未能走到 `x=1603` 汇合）([V3_AGENT_SPEC.md](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/docs/V3_AGENT_SPEC.md)) | 跨越近缺口局部弱对比断带并完成上下唇消歧，使 `Joint` 大幅提升（目标 `>= 8/15`），`Severe == 0` |
| **REG-C（可见 20 帧，隔离盲测）** | `Hit@10`: `13/20`；`Joint`: `13/20`（中位误差 `5.86 px`）([latest_metrics.json](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/evidence/latest_metrics.json)) | 在不针对 `REG-C` 调参的前提下，保持 `Hit@10 >= 13/20` 与 `Joint >= 13/20`，`Severe == 0` |
| **弱裂纹与跨尺度探针** | `P2_fade`: `7/12`；`P4_ring`: `4/12`；`P4_open`: `5/12`；`0.5x`: 正例 `20/28`（FP `5/16`）；`2.0x`: 正例 `22/28`（FP `4/16`）([REPORT.md](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/evidence/v3/REPORT.md)) | `P2_fade >= 10/12`，提升 `P4_ring` / `P4_open` 通过率；`0.5x` 与 `2.0x` 跨倍率正例与误报率逼近 `1.0x` 水平 |

## 2. 必须严守的工程与隔离纪律

1. **严格的数据隔离与泛化原则**：遵守 [V3_AGENT_SPEC.md](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/docs/V3_AGENT_SPEC.md) 的数据规则，**仅在获准开发组（DEV-A）和独立合成探针上设计规则与调参**；`DEV-B` 仅作阶段对照（不用于拟合参数），`REG-C` 仅在所有逻辑冻结后统一跑一次回归评分。严禁读取样本文件名、组别、帧号或标注坐标。
2. **保留 `raw_only` 对照与可复现接口**：所有修改必须兼容现有接口 `research.notch_identity_v3.terminal.prepare(raw, hint, scale, stage)` 与 `predict(prepared, bonus)`，并通过 `python -m research.notch_identity_v3.check_public` 等公共自检。
3. **无量纲化与光照自适应**：全面清理残留的固定像素常数与固定 8-bit 绝对灰阶阈值，确保算法对不同图像分辨率（`scale`）和不同曝光对比度具备物理普适性。

## 3. 针对 V3 弱裂纹与普适性短板的五大修改任务

请依次在 [terminal.py](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/research/notch_identity_v3/terminal.py)、[detector.py](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/research/notch_identity_v3/detector.py) 与 [topology.py](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/research/notch_identity_v3/topology.py) 中实施以下五个独立可消融的改进（建议通过 `stage` 参数或配置开关支持逐项消融，最终合入 `v3_1` / 新预设）：

### 任务 1：解决下唇候选在局部弱对比断带处的提前终止（攻克 `DEV-B` 第 215 帧）
* **现有病灶（[terminal.py](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/research/notch_identity_v3/terminal.py) 第 41–85 行）**：
  1. `_dp` 使用 `- off_lam * abs(j - half)` 将路径强行拉向水平线，丢失了沿裂纹切向弯曲进入主干的斜率记忆；
  2. `trace_windowed` 遇到连续 `max_gap = px(scale, .021)`（在 `scale=288` 下仅 6 px）的 `signal < 0.8` 区间即永久退出循环，导致 `DEV-B` 第 215 帧下唇在 `x=1505` 断轨而无法与 `x=1603` 汇合。
* **改进要求**：
  1. **恢复切向斜率引导**：在 `trace_windowed` 与 `_dp` 中引入轻量级动态斜率记忆（平滑更新的局部切向偏移 `slope`），替换生硬的水平中心偏移惩罚 `off_lam * abs(j - half)`，允许路径顺着上下唇合流趋势平稳转向。
  2. **近缺口合流区的“条件式跨断带重连”**：在近缺口合流段（例如距起点水平距离 `< px(scale, 0.35)`）将最大容忍弱对比断带宽度放宽至 `px(scale, 0.045)`（并同时支持在合成双唇探针上注入可控弱对比断带进行验证）；但必须配合**“跨带后重获强支持检验”**——只有当跨过弱区后，后续 `px(scale, 0.05)` 窗口内能够重新稳定达到强暗谷均值（如平均 `signal >= 1.05`）时，才保留该跨断带连接；否则回退至断带起点截断，避免在真尖端后方误连纹理。

### 任务 2：修复 `follow` 终止门对“渐弱真尖端”的误砍（找回 `DEV-A` 丢失 4 帧与 `P2_fade`）
* **现有病灶（[terminal.py](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/research/notch_identity_v3/terminal.py) 第 93–112 行）**：
  `base` 由路径前 60%（深裂纹主干）决定，而 `while last > 8:` 强制要求末端窗口同时满足 `tail > 0.55 * base` 与 `tail_sig > 1.05`。当真实裂纹从深主干向尖端自然渐弱时，合法的微裂纹尖端因低于主干深度的 55% 被一刀砍掉（导致 `DEV-A` 的 `366, 451, 504, 542` 偏左 `13~22 px`）。
* **改进要求**：
  1. **引入“双通道渐弱尖端门控（Tapered-Tip Dual Gate）”**：保留现有强尖端通道的同时，新增渐弱真尖端通道——当尾窗相对于**尖端正前方基底材料（`front`）**及**局部行噪声（`mad_row`）**依然具备清晰可辨的暗谷对比度（例如 `tail > max(1.6 * front, 2.5 * mad_row)` 且局部斜率连续、无剧烈折返）时，将对前段主干的相对比例门槛从 `0.55 * base` 放宽至 **`0.25 * base` ~ `0.30 * base`**（同时保持尾窗 `tail_sig` 下限略低于 1.05 的软边界，由前方材料对比度 `front` 把关防过冲）。
  2. **消除 `valley_image` 单侧高背景扩散（第 23–26 行）**：审视 `background = np.maximum.reduce([col, local, np.full_like(col, np.median(col))])` 对弱裂纹段信号值的过度压低，评估将 `local` 替换为更稳健的局部中位平滑或截尾背景，使弱裂纹区不至于被相邻强缺口列抬高分母而跌破 `0.8` 断带线。

### 任务 3：重构双差分通道（`bonus`）的作用区间与主干基线隔离
* **现有病灶（[terminal.py](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/research/notch_identity_v3/terminal.py) 第 141 行）**：
  `b = np.where(sig >= 1., b, 0.)` 在原灰度已经足够强（`sig >= 1.0`）的地方锦上添花，却在最需要帧间张开信息辅助的**弱裂纹断带与渐弱尖端（`0.55 <= sig < 1.0`）**将 `bonus` 彻底清零；同时叠加了 `bonus` 的 `signal` 进入 `follow` 后，反而在 `DEV-A` 第 451 帧改变了截断行为，导致 `full`（14/19）不如 `raw_only`（15/19）。
* **改进要求**：
  1. **将双差分门控下探至弱谷辅助区间**：允许在 `sig >= 0.55`（已有初步暗谷趋势，而非纯噪声平地）的区域保留受限的 `bonus` 增益（抑制 `hint_xy[0] + px(scale, 0.2)` 之前的近缺口张开边缘伪影仍保留），真正用于修补局部弱对比断带与辅助确认渐弱尖端。
  2. **分离“追踪信号”与“终止门验证信号”**：在 `follow` 中计算主干基准 `base` 与截断门控时，严格使用纯原灰度 `resp` 与纯原灰度归一化信号 `sig` 作为主导判据，`bonus` 仅作为弱区的辅助置信加权，确保任何情况下 `full` 模式在 `DEV-A` 与 `DEV-B` 上均**不劣于** `raw_only` 模式。

### 任务 4：消除跨尺度打分偏置与固定灰阶魔数（补齐 `0.5x` / `2.0x` 与跨材质普适性）
* **现有病灶（[terminal.py](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/research/notch_identity_v3/terminal.py) 第 16、117、121、151 行及 [detector.py](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/research/notch_identity_v3/detector.py) 第 129 行）**：
  1. 候选打分 `score` 中的长度奖励 `0.02 * min(feat['length'], px(scale, .25))` 未除以 `scale`，导致 `2.0x` 分辨率下长度权重比 `0.5x` 放大了整整 4 倍；
  2. `flanks > 40`、`mean(raw) > 130`（`bright_root`）以及 `max(abs(diff(raw))) < 8.`（`straight_edge`）均为写死的 8-bit 绝对灰度值，无法自适应低照度或高曝光图像。
* **改进要求**：
  1. **无量纲化候选打分**：将长度项归一化为 `w_len * min(feat['length'] / max(1.0, float(scale)), 0.25)`，确保 `0.5x`、`1.0x`、`2.0x` 下的打分尺度完全一致。
  2. **相对分位数替代绝对灰阶阈值**：将 `flanks > 40`、`bright_root` 的 `130` 及 `straight_edge` 的 `8.0` 全部替换为基于当前 ROI 图像块灰度分位数（如 `np.percentile(raw, 50)`、`IQR` 或 `noise`）的相对阈值。
  3. **改进近缺口闭环与开口边缘过滤（[topology.py](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/research/notch_identity_v3/topology.py)）**：分析 `P4_ring`（4/12）与 `P4_open`（5/12）在 `0.5x` 与 `2.0x` 下失败或误报的原因，确保形态学与轮廓面积门槛严格保持尺度不变性。

### 任务 5：扩充“可控弱对比断带”合成探针并完成全量回归验证
* 按照 [V3_AGENT_SPEC.md](https://github.com/Helaer-pp/codexcrack-agent-memory/blob/main/docs/V3_AGENT_SPEC.md) 的下一步指引，在合成测试套件中新增**“双唇可控弱对比断带探针（`P1_weak_gap`）”**（在下唇路径中段注入不同长度与对比度衰减的局部弱带），固定评价器，统计首次失去支持的位置与错误重接率。
* 重新在 `0.5x`、`1.0x`、`2.0x` 三个尺度上运行全部合成探针，验证跨尺度一致性。

## 4. 强制交付物要求：标准化《V3.1 开发与消融验证报告》

开发完成后，请更新代码与指标文件，并输出一份 Markdown 格式的**《V3.1 裂纹尖端追踪算法弱裂纹修复与普适性验证报告》**（建议保存至 `evidence/v3_1/REPORT.md`），报告必须包含以下 6 个核心章节：

1. **执行摘要与核心改动对照表**：逐函数列出相对于 V3（`s3t`）的具体修改、无量纲化/自适应阈值改造清单及各参数物理含义。
2. **分阶段消融实验总表（含 `r02`、`V3-s3t` 与 `V3.1` 逐项叠加对比）**：
   * 必须同时汇报 `DEV-A`、`DEV-B`、`REG-C`（冻结后一次性回归）在 `full` 与 `raw_only` 两种模式下的 `Visible / Valid`、`Hit@10`、`Joint`、`Severe`、`Median Error (px)` 与 `Max Error (px)`。
   * 明确检验 `full` 是否已全面追平或优于 `raw_only`。
3. **关键反例逐帧复查（Frame-by-Frame Diagnostic Audit）**：
   * **DEV-B 第 215 帧专项**：给出下唇候选是否成功跨越 `x=1505` 弱对比断带、是否与上唇汇合以及最终 `Joint` 路径覆盖率与端点误差（对比 V3 的 `57.4%` 与 `2.08 px`）。
   * **DEV-A 四帧回归反例专项（`366, 451, 504, 542`）**：给出修改前后的预测 `tip` 坐标、误差变化以及双通道渐弱尖端门控的实际触发情况。
   * **受损帧清单**：透明披露所有相比 `r02` 或 `V3-s3t` 出现指标回退的帧号与原因。
4. **弱裂纹与跨尺度合成探针验证矩阵**：
   * 汇报 `P1_upper`、`P1_lower`、新增 `P1_weak_gap`、`P2_fade`、`P3` 负例、`P4_ring`、`P4_open` 在 `0.5x / 1.0x / 2.0x` 下的通过率与误报率（FP/N）对比表。
5. **普适性与运行效率评估**：
   * 评估不同光照偏移（亮度/对比度扰动）下的稳定性，以及单帧平均耗时（FPS）与最坏耗时，确认无预算爆炸风险。
6. **生产验收结论与遗留边界**：
   * 明确给出是否满足生产验收的结论；若仍有未解决的边界情况，按 `OPEN_PROBLEMS.md` 格式列出 `问题 | 已有证据 | 可检验的下一步`。
