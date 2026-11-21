# UCTIP-60Q 独立研究实现

本目录仅实现本轮 1633 帧协议。DEV=GROUP_A551+三点弯520；LOCKED=验证组C562（历史已曝光，非新盲测）。其他试验不进入队列。此角色覆盖仅限本轮，未修改全局数据政策。标注只用于封存后的独立比较，不训练，不按 GT 搜索参数。输出当前已验证分支的最右原图 x 观测端点；无可靠结果、平局歧义或预算不完整则 null。无裂纹长度输出。

**本轮执行偏差**：通用 `run.ps1 check` 在预验证冻结前执行了旧 A 的验证组C图像/P点回放，并包含CT2/开发组H旧检查。新算法未使用这些结果改规则，四模块hash未变，但严格数据隔离审计不通过。详见run内 `reports/PROTOCOL_DEVIATION.md`。后续验证组C结果只能作为注明偏差的固定曝光回归，不能声称隔离流程完全合格；不批准生产。不再运行通用旧数据检查。

## 源码与入口

- `features.py`：原始 uint8、缺口图像假设、安全区、RAW 多尺度法向暗谷、结构化观测段、两路独立材料纹理配准。
- `graph.py`：观测段端点连接；小 gap 与有额外 RAW 支持的大 gap 分开；每条测试边保留接受/拒绝码。
- `engine.py`：动态工作掩膜、前探/回退、词典序有界图搜索、候选验证、多轨迹、异常重查和当前最右有效尖端。
- `pipeline.py`：按数据角色校验原图 SHA/尺寸/位深/原始 TXT，公共无历史证据缓存；每组每 arm 按原始顺序串行推进状态。
- `offline_evaluate.py`：单独进程、推理封存后才读标签；正式、preferred uncertain、Oracle 分列。
- `render.py`：全部帧分层 PNG、RAW 数值 NPZ、灰度表面、按需加载本地 HTML。
- `audit.py`、`tests.py`：合成、无 GT 接口、源图重算、顺序重放、冻结文件核对。
- `delivery.py`：最终汇总、三组全序列视频、独立 GT 对比、验收和交付索引。

运行环境：Python 3.12、NumPy、SciPy、OpenCV、scikit-image、Numba、Pillow、Matplotlib。仅 Python 实现，未实现 C++；不声称跨语言 parity 或实时性能。所有缓存/中间文件仅落在 output 下。

## 复现命令

在项目根目录 PowerShell：

```powershell
$env:PYTHONPATH="$PWD/research"
$env:PYTHONPYCACHEPREFIX="$PWD/output/pycache"
$env:PYTHONIOENCODING='utf-8'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$py='D:/ProgramData/anaconda3/python.exe'
$run='output/experiments/unified_crack_tip_60q_20261113_r01'
# 新实验需新的唯一目录；inventory 不覆盖已有目录。
& $py -m unified_crack_tip_60q.inventory --run $run
& $py -m unified_crack_tip_60q.audit engineering --run $run
& $py -m unified_crack_tip_60q.pipeline prepare --run $run --split DEV --workers 6
& $py -m unified_crack_tip_60q.pipeline infer --run $run --split DEV --workers 6
& $py -m unified_crack_tip_60q.render --run $run --split DEV --workers 4
& $py -m unified_crack_tip_60q.viewer_audit --run $run --split DEV --workers 4
& $py -m unified_crack_tip_60q.audit backend --run $run
& $py -m unified_crack_tip_60q.offline_evaluate --run $run --split DEV
& $py -m unified_crack_tip_60q.audit replay --run $run --split DEV
& $py -m unified_crack_tip_60q.delivery --run $run --phase DEV
& $py -m unified_crack_tip_60q.pipeline freeze --run $run
& $py -m unified_crack_tip_60q.pipeline prepare --run $run --split LOCKED --workers 6
& $py -m unified_crack_tip_60q.pipeline infer --run $run --split LOCKED --workers 1
& $py -m unified_crack_tip_60q.offline_evaluate --run $run --split LOCKED
& $py -m unified_crack_tip_60q.render --run $run --split ALL --workers 4
& $py -m unified_crack_tip_60q.viewer_audit --run $run --split ALL --workers 4
& $py -m unified_crack_tip_60q.audit replay --run $run --split LOCKED
& $py -m unified_crack_tip_60q.audit integrity --run $run
& $py -m unified_crack_tip_60q.delivery --run $run --phase FINAL
```

上述是入口说明，实际完成状态以 run 内 seal / 报告为准，不凭 README 认定已执行。过程崩溃时可从已完整写入的帧恢复；不能覆盖已封存 LOCKED 结果。原四模块与配置保持注册字节不变；独立engine_fast.py批量执行副本经133例原生一致性与15项合成测试后用于剩余开发计算和验证组C。每帧核对其实际四文件或五文件来源hash；已完成旧结果保留原字节。预验证冻结包含本目录所有源码、配置和文档。冻结后任何算法或评价修复均不能冒称同一锁定实验。

`galleries/index.html` 可直接打开；浏览器禁止 file:// 像素读取时，在项目根执行：

```powershell
& $py -m http.server 8765 --bind 127.0.0.1 --directory $run
```

然后访问 `http://127.0.0.1:8765/galleries/index.html`。无需网络 CDN。图册中的原始 ROI PNG 和数值 NPZ 保持原始灰度；全图缩略图、视频和 3D 曲面只为展示进行采样。标签只出现在 `offline_evaluation/overlays/`，不进入原始图层。

## 本实现的实际限制

“验证”为规则验证，不是裂纹物理身份的独立认证。根部仅图像假设，注释的最右端语义也未独立复标。工作 ROI 使用完整安全区 RAW scout，不能把工作掩膜面积减少解释为整个特征计算减少。方向估计用 Gaussian Hessian，但深度从 RAW 采样；结构筛选与图路径仍可能丢失弯曲/纹理混杂的细线。图搜索每个有向段只保留词典序最优前驱，并保留其他前驱及理由，不能宣称枚举所有路线。参考有效性仅局部材料纹理质量，不等于真实变形场已获认证。开口量是固定 P 轴投影，仅为 preferred uncertain 弱平局信息，不直接提升正式输出。坐标均为原图整数像素，几何/注册中间量保留浮点。

正式验收分别使用全部可见 GT 分母 19/15/20；GROUP_A 至少14命中10px、16有效、0严重；三点弯11/12/0；验证组C14/16/最多1严重。任何组失败或工程不完整则 PRODUCTION_NO_GO，不替换旧 A。

## 展示与预标注诊断补充

`presentation.py` 在原始图层之外生成 `comparison_clean.jpg`、`local_result_clean.png` 和独立 `official.png`。视频采用清晰对比图：相同坐标的原图/当前验证片段/正式端点，不覆盖密集轨迹文字。完整轨迹、推断gap与拒绝路径保留在交互图层。`viewer_audit` 为每帧生成清晰展示及血缘摘要，再写 reviewed_index；最终 index 同样使用这些资源。查看器支持不确定首选端点筛选；该端点不算正式结果。

三点弯全序列无标注消融的预算定位见run内 `reports/PRELABEL_TRACK_BUDGET_FINDING.md`：FULL的93次预算失败均由轨迹上限触发，NO_GAP有509次轨迹上限触发。该条件差异含历史反馈，不证明gap的物理真实性，也不授权改用单轨默认或删除不同终止位置。最终精度以全DEV封存后的独立评价为准。

执行后端：engine.py为未改动的原始实现，engine_fast.py仅将历史支持中同一批整数采样点的独立KDTree查询/布尔均值比较批量计算。原始点、阈值、候选、轨迹关联和端点判定均相同。DEV_execution_backend_registration.json记录切换前检查；原始版与批量版性能分别统计。新目录复现时默认全部采用批量版；audit backend会在标注读取前用原始版对133个固定检查点做完整结果/状态/掩膜/血缘核对，再允许freeze。r01已存在的注册只核验哈希，不覆盖旧审计数据。
