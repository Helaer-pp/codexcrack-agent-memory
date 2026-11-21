# 阶段开发报告

本轮完成了 UCTT 第一阶段的最小输入隔离补丁，并保留了生产 A 的端点独立链路。源码、构建和输出均在 `CodexCrack/` 内。当前候选 DLL SHA-256：`55a0e7a79162da79e691ede9ff58229e59a56fdd1e0b1e3f609dc51128860402`。

## 实际发现

- 生产检测器在 `src/cpp/a/CrackV4.cpp` 的 `Detector`；端点测量在 `src/cpp/a/roi_tip.inc:146`。
- 当前 P1/P2 进入 `motion` 只用于主路径粗刚体定位；端点使用 `estimateTipMotion:748` 的固定参考纹理和 `tipCenter/tipDirection:626-627`。
- 修补前真实缺口是当前点 NaN、越界、退化时入口 `validatePoints` 直接抛错，导致端点链路未运行；不是端点 ROI 被当前点重定义。

## 修改

- `validCurrentPoints`（`src/cpp/a/CrackV4.cpp:2189`）显式区分无效当前点。
- `CrackV4Process:2268-2271` 将无效当前点从粗定位先验移除，保留 `current_anchor_invalid` 诊断。
- `Detector::process:1758-1776` 仅在该输入条件下隔离主路径自动配准异常，让端点独立注册有机会完成。
- `CrackV4LastDebugJson` 与 `CrackV4LastGeometryJson` 增加只读 `current_anchor_invalid` 字段。
- 未修改 DLL 导出签名、旧结构尺寸、主路径搜索、终止审计、长度定义或研究 A′。

## 验证

- G0/G1/G2/G3：PASS。构建与既有 `run.ps1 check` 通过；冻结 A 回放和研究合同保持通过。
- T1：PASS（有效输入）。严格矩阵覆盖 7 组、25 个当前点变体；有效执行 12874 次，状态差异 0，坐标差异 0，P95/max 偏差均为 0 px。34 个输入因超出图像范围被正确记为无效输入，不计入有效扰动通过率。
- T3：PASS（接口级）。NaN/越界/退化当前点共 18 个案例均返回成功并报告 `current_anchor_invalid=true`；无 GT，未声称视觉精度。
- T2：BLOCKED/未完成。当前矩阵固定初始化点，尚未形成独立的初始 P1/P2 重初始化 P95 统计。
- T4：BLOCKED。没有人工物理真值，也没有新的未见试件留出集。
- T5：FAIL/未达目标。全组端到端历史对照显示存在 >50 ms 帧；例如旧发布对照中开发组A P95 105.88 ms、CT2 P95 161.99 ms、开发组H P95 202.59 ms。该对照 DLL 与当前源码构建时间不同，不能用来宣称本补丁造成这些耗时。
- T6：PASS（冒烟/结构级）。旧调用方式、结构尺寸、多实例冒烟均通过；完整部署级兼容仍需外部宿主验证。

## 证据

- `baseline_results.csv` / `candidate_results.csv`：18 帧冻结 A 与当前候选构建的冒烟逐帧记录。
- `perturbation_results.csv` / `perturbation_summary.csv`：严格当前点反事实逐帧记录。
- `failure_stages.csv`：已证实输入门控根因。
- `timings.csv`：冒烟端到端与检测器计时。
- `strict_report.md`：完整严格矩阵报告。

结论：**当前点解耦通过；初始化点稳定性和视觉尖端精度仍未验收。**


