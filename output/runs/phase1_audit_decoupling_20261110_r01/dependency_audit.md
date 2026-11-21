# 依赖审计

## 已证实调用链

1. `CrackV4CreateExtended`/`CrackV4Create` 构造 `Detector`，参考图和初始化 P1/P2 在 `src/cpp/a/CrackV4.cpp:509-604` 建立固定 `origin/forward/spacing`、参考 ROI 和固定参考纹理块。
2. `CrackV4Process`（`src/cpp/a/CrackV4.cpp:2245`）读取当前图像，验证当前点；有效点只进入 `Detector::process -> motion`（`911-1120`）作为粗刚体定位先验。
3. 端点 motion 独立链路是 `estimateTipMotion`（`748`）：只读取固定参考 `patches/tip_patches` 与当前图像，不读取当前 P1/P2。
4. 端点几何由 `tipCenter/tipDirection`（`626-627`）和 `tip_rotation/tip_translation` 变换得到，随后 `measureTip`（`src/cpp/a/roi_tip.inc:146`）在固定参考几何后的 ROI 内独立找末端。
5. `GetBaseline`（`2306`）是只读缓存查询，不推进状态；`CrackV4Process` 后才推进帧状态和输出。

## 当前点耦合结论

- 原有有效点路径中，当前 P1/P2 仍会影响主路径 `rotation/translation`，这是允许的粗定位先验。
- 端点专用 ROI、方向、候选和视觉确认使用 `tip_*` 独立变换；严格扰动与既有锚点不变性检查显示有效扰动下端点状态/坐标保持不变。
- 修补前唯一已证实的缺口是：当前点 NaN、越界或退化时，`motion` 的 `validatePoints` 会抛错，入口将整个 `CrackV4Process` 返回为错误，端点分支没有机会运行。这属于 `current_anchor_gate`。

## 首个分歧

无效当前点的首个分歧在 `CrackV4Process` 的当前点门控（现行实现 `2268-2271`），而不是端点 ROI 或终止审计。修补后无效点被标记为 `current_anchor_invalid`，不再传给粗定位先验；若自动主路径配准因此异常，仅在该条件下捕获异常并继续端点独立配准（`process:1758-1776`）。

## 未发现/未声称

- 未发现当前点直接重定义端点 ROI 的代码路径。
- 未声称存在人工物理 GT、真实尖端像素误差或完整原生 15 Hz 证明。
- 发布目录 2026-11-06 DLL 与 2026-11-09 当前源码不是同一构建；其全组对照出现真实差异，不能当作“无修改基线”。
