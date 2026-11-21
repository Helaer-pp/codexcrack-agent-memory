# 验证组C同一 BMP 冻结 V1 故障审计

本目录仅为用户指定的已曝光验证组C案例复盘。原生 Python 源码 SHA256 必须为 `2e2e5ebef80ab33e486c561b6dec09ee15d23033020cc1886a7de24c7ce2baf6`。不修改 V1、生产算法、阈值或默认模式；不开发 V2。

在项目根目录用 PowerShell 执行，新输出路径必须位于项目 output 内且未存在：

```powershell
& ./research/group_c_same_bmp_v1/reproduce.ps1 -Output './output/diagnostics/group_c_same_bmp_replay_01'
```

依赖 config/project.json 指定的 Python、项目冻结源、原始 F: BMP、原始追踪 TXT、已封存 V1 回放数据（只读比较）、既有标签快照（推理后离线比较），以及项目第三方 FFmpeg。Node 用于逐列查看器逻辑检查。旧封存脚本不会作为活动代码执行。脚本不写外部原图或覆盖旧运行。

执行顺序：身份与预注册输入 → 原生 CLI 和只读观察器 ABCD → 几何/位移场 2×2 诊断控制 → 101 个固定扰动 → 4 个既有可见标注帧 → 离线证据分析 → 观察器一致性及 C++ 辅助对照 → PNG/HTML/54 秒视频 → 中文报告 → 完整性检查和快照。

原生 Python main 共114次，诊断反事实4次，每次6模式；辅助原生 DLL 4次。不把重复执行当独立样本。反事实只在诊断副本替换位移场；AA/DD输出与13个数组分别逐位核验。

默认结果：`output/diagnostics/group_c_same_bmp_root_cause_v1_20261112_r01/ROOT_CAUSE_REPORT.md`。同 BMP、同源码成立；A复现(2423,2344)，D复现(2255,2282)，错误初始化与参考差分/采样几何耦合已复现。物理配准真值与原始选点语义仍未解决。第237帧不在20张标注帧内，其(2423,2344)只作事后近似锚点；不得冒称真实精确GT。

验证组C仍为VALIDATION_ONLY，本次仅用户授权的故障审计，不选参、不训练；标签只作推理后比较。排除组X完全排除。源目录的 Python、JS 与 PowerShell 脚本随结果复制到 scripts，原检测源码diff为空。
