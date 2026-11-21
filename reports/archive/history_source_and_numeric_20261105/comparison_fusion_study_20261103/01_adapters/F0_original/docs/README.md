# 工业级疲劳裂纹亚像素追踪系统与多试样验证套件
# Industrial Fatigue Crack Tracking & Multi-Specimen Verification Suite

本软件套件包含针对金属疲劳试验开发的高精度、亚像素级自动化裂纹追踪与断裂力学相容性表征代码，严格冻结了基于 **Route A 差分 + 可分离 2D Frangi 脊线滤波 + 引伸计基准点亚像素刚体位姿补偿 + 拓扑几何针定 + 细化骨架提取** 的统一鲁棒算法架构。

---

## 目录结构 (Directory Structure)

```
crack_tracking_system_release/
├── docs/                               # 算法架构规范与技术文档
│   ├── ALGORITHM_ARCHITECTURE.md       # 完整算法技术文档（含 Mermaid 流程图、数学物理公式、性能剖析）
│   └── README.md                       # 本说明文档
├── pipelines/                          # 自动化全流程批处理脚本
│   ├── group_a_crack_tracking_pipeline.py      # 开发组A CT 紧凑拉伸试样流水线 (551帧)
│   ├── group_x_crack_tracking_pipeline.py # 排除组X白板圆孔双向开裂试样流水线 (524帧)
│   ├── group_h_crack_tracking_pipeline.py  # 开发组H M(T) 中心贯穿裂纹试样流水线 (410帧)
│   ├── ct2_crack_tracking_pipeline.py      # CT2 大视场紧凑拉伸疲劳试样流水线 (468帧)
│   ├── crack_tracking_pipeline.py          # 通用模块化基础流水线
│   ├── analyze_group_x_results.py         # 排除组X试验数据统计与力学相容性分析脚本
│   └── analyze_group_h_results.py          # 开发组H试验数据统计与双侧对称性分析脚本
├── datum_points/                       # 规范化引伸计基准点坐标文件 (UTF-8)
│   ├── group_a_datum_points.txt                # 551 组基准点
│   ├── group_x_datum_points.txt           # 524 组基准点
│   ├── group_h_datum_points.txt            # 410 组基准点
│   └── ct2_datum_points.txt                # 468 组基准点
├── results_csv/                        # 全量逐帧量化测量结果
│   ├── group_a_verification_results.csv        # 开发组A试样全量结果
│   ├── group_x_verification_results.csv   # 排除组X试样全量结果
│   ├── group_h_verification_results.csv    # 开发组H试样全量结果
│   └── ct2_verification_results.csv        # CT2 试样全量结果
└── scientific_plots/                   # 出版级高清科学分析图表 (300 DPI)
    ├── group_a_crack_growth_curve.png          # 开发组A扩展曲线与柔量力学校验图
    ├── group_x_crack_growth_curve.png     # 排除组X双侧扩展包络与左右对称性相关性图
    ├── group_h_crack_growth_curve.png      # 开发组H M(T) 双侧裂纹演化图 (r = 0.9962)
    └── ct2_crack_growth_curve.png          # CT2 疲劳开闭呼吸与扩展路径三联图
```

---

## 运行环境依赖 (Prerequisites)

```bash
pip install numpy opencv-python scikit-image matplotlib pillow
```

如需生成 H.264 编码的 1080P 超清四视窗演示视频，请确保系统已安装 `ffmpeg` 并加入环境变量 PATH。

---

## 快速复现指南 (Quick Start)

运行任意试样的全量自动化处理流水线（自动执行图像对齐、差分、滤波、骨架提取、CSV 写入、科学绘图与 1080P 视频压制）：

```bash
# 1. 运行 CT2 试样流水线 (468帧)
python pipelines/ct2_crack_tracking_pipeline.py

# 2. 运行 开发组H M(T) 试样流水线 (410帧)
python pipelines/group_h_crack_tracking_pipeline.py

# 3. 运行 排除组X白板圆孔试样流水线 (524帧)
python pipelines/group_x_crack_tracking_pipeline.py

# 4. 运行 开发组A CT 试样流水线 (551帧)
python pipelines/group_a_crack_tracking_pipeline.py
```

---

## 算法核心性能指标 (Key Performance Highlights)

1. **虚警抑制率：** 全数据集未开裂参考基准态识别长度均为 $0\text{ px}$（**0 虚警**），彻底消除机械机加工刀纹和反光噪点干扰。
2. **物理力学相容性：** 
   - 开发组H M(T) 试样双向对称扩展 Pearson 相关系数高达 **$r = 0.9962$**；
   - CT2 试样峰值裂纹与引伸计 CMOD 张开位移决定系数达到 **$R^2 = 0.6177$**；
   - 排除组X圆孔试样力学柔量决定系数 **$R^2 = 0.6980$**。
3. **计算效率：** 纯算法核心在单 CPU 核心下耗时仅 **$12 \sim 52\text{ ms/帧}$**，完全满足在线工业原位闭环监测（$20 \sim 80\text{ FPS}$）要求。
