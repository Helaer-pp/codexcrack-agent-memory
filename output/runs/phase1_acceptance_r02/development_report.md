# R02 验收报告

1. R02 证据补全：**COMPLETED**。T1 重跑和最终项目 check 已完成。
2. Phase 1 基准点稳定解耦行为：**BLOCKED / PARTIAL_FAIL**。
3. Phase 1 CPU 50 ms 性能：**FAIL**。
4. 是否可以进入 Phase 2：**NO**（当前不能把 Phase 1 行为和性能称为完整验收通过；仅允许保留诊断结果和后续最小修复评审）。

## R01 冻结与可复现性

R01 输出目录、源码、输入清单和候选 DLL 均实际存在。当前目录没有 Git 元数据，因此 Git commit 和 dirty 状态无法取得；R02 用 `frozen_manifest.json` 记录源码树、DLL、配置和输入清单 hash，并保留 AB-before/after 源码副本。R01 目录未被改写。真实物理 GT 和多初始点对应的外部追踪轨迹不存在。

R01 复核显示严格矩阵共有 12,908 条记录，其中有效输入 12,874、执行 12,874；视觉确认 4,785、未确认 8,089；paired distance 非空分母只有 4,785。R01 的 0 px 结论只覆盖共同确认样本，不能代替 T2。详见 `r01_evidence_reconciliation.md`。

## T2-A 初始点重新初始化

每组 16 个初始变体独立创建检测器，使用相同当前点轨迹；总窗口为 988 帧变体回放。变体包括 ±2%/±10% 共同 x/y 偏移、0.95/1.05 间距、±2°旋转、P1/P2 单点偏移和组合扰动。所有 112 个变体通过输入有效性检查。

- GROUP_A：252 帧，控制组仅 1 个确认帧，`INSUFFICIENT_OBSERVED_SUPPORT`，不能判定 PASS。
- 验证组C：80 帧，50 个控制确认；最坏 max 6.08 px，82 个状态差异，FAIL。
- CT2：120 帧，110 个控制确认；最坏 P95 190.92 px、max 257.64 px，FAIL。
- 开发组H：120 帧，114 个控制确认；最坏 P95 1194.06 px、max 1400.83 px，确认覆盖下降，FAIL。
- 排除组X：120 帧，120 个控制确认；部分 10% y 偏移出现约 296 px 坐标差异，FAIL；该组仍是曝光历史，不能作为调参依据。
- 三点弯：160 帧，160 个控制确认；坐标相同但状态差异 500，FAIL。
- CT3：136 帧，124 个控制确认；P95/max 0 px，PASS（仅本窗口）。

因此 T2-A 总体不是 PASS。差异首帧和 ROI/状态证据在 `first_divergence.csv` 与 `failure_gallery.html`。R02 观察到初始点变化首先能改变初始化阶段的端点 ROI 几何；这属于 T2 要验证的初始化敏感性，尚不足以证明需要生产修补。

T2-B-real：**BLOCKED**。没有每个初始物理选点对应的真实上游追踪轨迹。R02 没有把统一仿射/平移轨迹冒充真实端到端数据，也没有宣称 T2-B-synthetic PASS。

## 同源码 A/B

AB-before 与 AB-after 使用同一当前源码树和配置；before 仅逆向 R01 输入隔离补丁，未使用历史发布 DLL。A/B-valid 共 988 帧，状态、尖端、长度、路径逐帧完全一致。A/B-invalid 18 个 NaN/越界/退化案例中，before 全部返回错误，after 全部返回成功并继续到端点分支；这证明接口隔离修复行为，但不证明视觉精度提升。详见 `ab_regression_report.md` 和 `ab_build_manifest.json`。

## 首个分歧与诊断覆盖

`first_divergence.csv` 记录每个变体相对 `measured` 的首个可观察差异。当前接口能提供 ROI 原图坐标、registration state/quality、状态和确认坐标；无法提供端点专用 rotation/translation，也没有独立 `predicted/fallback` 枚举，因此相应字段明确为 null/`not_confirmed`，没有伪造证据。详见 `diagnostic_coverage.md`。

## 性能

候选生产 DLL 的控制窗口中，多数组 P95 超过 50 ms：GROUP_A 100.93、排除组X 169.51、CT2 155.61、开发组H 171.73、三点弯 112.02、验证组C 63.08 ms；CT3 13.80 ms。profile 诊断构建观测到的前三个已插桩 scope 是 seed、tile、median，但三者累计时间远小于端到端时间，主要成本仍在未归因的 OpenCV/采样/配准路径。AB-before/after 有效输出一致；18 帧小样本时序耗时差异不能归因于 R01 补丁。T5=FAIL，R02 未做性能重构。

## 生产代码变更

`NO_PRODUCTION_CODE_CHANGE`。R02 只新增测试脚本、独立 AB/profile 构建副本和报告；没有修改 `src/cpp/a/`。

## 下一步边界

Phase 1 仍需先解决或明确初始化选点敏感性，并补齐真实对应的多初始点追踪轨迹；没有 GT 时继续只能报告解耦稳定性，不能宣称物理尖端准确。裂纹证据、路径连通性、闭合机理和尖端终止误判继续留在 Phase 2 研究范围，R02 不改阈值或核心检测器。

详见 `acceptance_matrix.csv`、`performance_report.md`、`t2_reinit_report.md` 和 `reproduction_commands.md`。

