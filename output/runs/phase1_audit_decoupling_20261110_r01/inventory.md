# 工程盘点

- 项目根目录：`CodexCrack/`
- 生产算法：A，源码 `src/cpp/a/`，C++17/OpenCV 4.4，动态库导出 `CrackV4.dll`。
- 当前构建产物：`output/build/src/cpp/a/Release/CrackV4.dll`、`CrackV4Example.exe`、`output/build/Release/CrackReadOnlyBench.exe`。
- 上一发布包：`output/releases/A_Win64_OpenCV440/`（2026-11-06，作为历史发布对照，不覆盖）。
- Python/回放桥：`src/python/crackv4/` 与 `research/gate_adapt/`。
- 冒烟输入：`data/smoke/manifest.csv`，六组各 3 帧；真实组清单由 `data/inputs/six_groups_manifest.csv` 与 `data/anchors/` 提供，原图只读。
- 既有验证：`tests/check_project.py`、`tests/check_anchor_invariance.py`、`tests/check_roi_terminal.py`、`tests/strict_anchor_invariance.py`。
- 运行约束：正式 flags=3572，SHADOW policy=1，terminal validation=1，refine=true，4 个 native threads；GetBaseline 为缓存查询。
- 研究代码 `research/aprime*` 保持研究用途，不作为本轮生产运行依赖。

## 当前可访问性

G0 工程可构建，项目检查可执行。真实 F 盘图像可通过清单读取，但完整逐帧对照成本高；本轮先执行既有冒烟/回放和可复现的端点解耦审计，再记录真实全量对照的结果与限制。
