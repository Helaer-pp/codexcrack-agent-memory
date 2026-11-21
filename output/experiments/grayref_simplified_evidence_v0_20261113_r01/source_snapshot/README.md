# 简化灰度 / 差分 / 断续路径研究

运行：在项目根目录执行 `research/grayref_simplified_evidence_v0/reproduce.ps1 -RunId <全新名称>`。
安装环境：D:/ProgramData/anaconda3/python.exe，NumPy / SciPy / OpenCV / Matplotlib / Pillow；无需另安装依赖。
脚本自动执行合成测试、输入身份核对、配置与源码冻结、1565 帧开发推理和独立评分、1082 帧固定曝光验证与评分、2647 帧图册核验、报告。
默认 C_FUSION_RAW，九种证据/滤波模式全量执行。TEMPORAL_OFF。排除组X排除。标签只作冻结后比较。
每帧完整分辨率数组与九模式候选保留。3D 曲面仅在渲染时规则采样，Z 为原灰度0–255；完整2D图和数组避免丢失细线。
原型只有暂定路径/尖端，物理主裂纹身份未认证。参考可信是材料窗纹理代理。不得替换冻结 A/V1/V2。
CT3 原始 TXT 缺失，保留已审计历史 CSV 出处。旧基线用完整逐帧结果/trace 校验回放。
结果仅写 output/experiments/<RunId>/，约需数十GB，建议80GB可用。已存在 run 只有源码/配置一致才允许恢复；只补缺失文件，损坏工件报错。
复现包括输入和既有冻结基线，可读外部原图，不修改原图、点、标签或旧输出。
