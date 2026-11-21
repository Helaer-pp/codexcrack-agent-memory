# P1/P2-GrayRef V1.0 冻结版：跨试件批量回放

**状态：研究用候选算法已冻结；仅有一对真实 BMP 已证明可产生接近人工尖端的暂定结果；尚未证明跨组普适性，也未成为生产版本。**

## 目录与冻结身份

- `paired_p1p2_roi_V1_FROZEN.py`：**检测器原样冻结，不允许修改其任意一行。** SHA-256：
  `2e2e5ebef80ab33e486c561b6dec09ee15d23033020cc1886a7de24c7ce2baf6`
- `batch_validate_V1.py`：可编辑的外部批量执行/离线评分器；它仅通过子进程调用冻结算法，不能改变阈值或源代码。
- `baseline/expected_summary_results.csv`：首次真实图像对的六组既有输出。
- `examples/manifest_example.csv`：每帧输入的约定示例；这里假设参考 BMP 和变形 BMP 位于冻结包所在文件夹的**父目录**，换到你的电脑后必须修改成真实路径。
- `examples/labels_example.csv`：**仅用于推理完成后**统计误差的离线标签示例。
- `baseline/smoke_result_overlay.png`：本次原样冻结代码的回归结果图。
- `baseline/smoke_group_summary.csv`：参考联合/仅当前，8/10/12 各档结果。
- `Agent_Development_Prompt.md`：Agent 全开发与验证规格。

**请勿在冻结脚本顶部修改阈值，即使那里有「用户设置区」。** 此冻结版只允许通过 `--reference`、`--current`、`--p1-ref`、`--p2-ref`、`--p1-cur`、`--p2-cur`、`--output-dir` 替换每帧输入。实验标签不通过 `--gt-tip` 传入推理程序，由外部评分器独立读取。

## 1. 输入 manifest（UTF-8 CSV）

一行一张变形帧，列名为：

```
group,frame_id,split,reference,current,p1_ref_x,p1_ref_y,p2_ref_x,p2_ref_y,p1_cur_x,p1_cur_y,p2_cur_x,p2_cur_y
```

- `group`：组名，只用于报告分组，不允许用于检测器选择不同参数。
- `frame_id`：组内唯一帧号；可以是 `000175`，连续运行器不改变组内时序，但冻结算法本身目前**逐帧独立、没有历史状态**。
- `split`：`DEVELOPMENT` 或 `VALIDATION_ONLY`。验证组C/三点弯在开发完成及冻结前，**不得拿来反调参数**。
- `reference`：该帧对应的参考图路径；`current`：变形帧路径。绝对路径或相对于 **manifest 文件目录** 的相对路径。
- `p1_ref_x...p2_ref_y`：该参考图的上/下预制缺口标记点原始像素坐标 `(x,y)`。
- `p1_cur_x...p2_cur_y`：该帧当前 P1/P2；四项一起填写最可靠。四项全空则检测器使用自己的 NCC 模板搜索，其最大搜索位移固定 ±25 px。
- 如果你的基准点由单独 CSV/TXT 存储，请让 Agent 编写**仅格式转换**工具把数据映射到这个 manifest；不得根据试件调整检测参数或用尖端标注重置基准点。

同一参考图下改变帧号，仅需改变 `current` 及相应 `p1_cur/p2_cur`；新试件必须更换 `reference` 和相应参考 P1/P2。初始方向在冻结算法中默认**向右**，其他方向会失败，这是 V1 的适用边界，不得隐瞒。

## 2. 单独的人工真值（可选）

`labels.csv`：

```
group,frame_id,visibility,tip_x,tip_y
example,175,VISIBLE,2423,2344
```

`visibility` 可设 `VISIBLE`、`UNCERTAIN`、`NO_VISIBLE_CRACK`、`UNLABELED`。仅 `VISIBLE` 且坐标齐全的样本进行尖端误差统计，所有其他状态单独计数；无负例时不声称 FPR。

**GT 只在全部图像完成推理之后载入**，不允许用于起点选择、ROI 改动、调阈值或修复单帧结果。

## 3. 运行

安装：

```bash
pip install opencv-python numpy pandas scipy matplotlib
```

先检查输入清单（不启动检测器）：

```bash
python batch_validate_V1.py --manifest examples/manifest_example.csv --output runs/test --dry-run
```

批量运行并离线评分：

```bash
python batch_validate_V1.py --manifest examples/manifest_example.csv --labels examples/labels_example.csv --output runs/test
```

如果没有 GT：

```bash
python batch_validate_V1.py --manifest your_manifest.csv --output runs/test_no_gt
```

请更换输出路径以避免覆盖旧结果。执行器会检查冻结检测器 SHA，不一致则拒绝运行。一个图像对大约产生六种结果（`joint`/`current` × T=8/10/12），同时保存逐列轨迹和叠加图。

## 4. 输出与评估口径

- `runs/xxx/cases/<group>/<frame>/`：每张图的原生 `result_overlay.png`、`summary_results.csv`、`trace_*.csv`、`metadata.json`、stdout/stderr。
- `all_frames.csv`：全部输入帧的成功/失败（包括 P1/P2 NCC 失败、ROI 无效等）。
- `all_results.csv`：六种模式逐帧暂定尖端、误差、GT 是否位于 P1/P2 ROI 内。
- `group_summary.csv`：各组全部标注可见帧为分母的 ≤3/5/10px、>100/500px、未得输出数量以及只在有输出子集上的 P50/P95。
- `run_identity.json`：脚本 SHA、manifest SHA 和本次配置身份。

**注意：** 此脚本没有对“裂纹是否真实存在”建立独立身份确认，凡是 `tip_x/tip_y` 均为暂定端点，不得称为正式 `observed`。

## 5. 初始烟雾测试（已实际执行）

在 `1 (1).bmp` 对 `3 (175).bmp`，估计的参考 P1=(2243.75,2247.50)、P2=(2260.00,2431.25)，由当前帧 NCC 追踪，联合模式得到：

| T | 暂定端点 |
|---:|---|
| 8 | (2424,2344) |
| 10 | (2423,2344) |
| 12 | (2418,2345) |

`current` 单独的 T=10 为 (2285,2307)。这些是**同一图像已多次探索的回归锚点**，不能算外部验证或超参数无偏验证。

## 6. 必须面对的外推风险

1. 现有位移补偿只是**P1/P2 两点上下线性插值**，不是已验证的材料变形场；存在开裂和上下两侧非均匀移动时可能失真。
2. 绝对灰度 `MIN_MATERIAL_GRAY=135` 和 `T=10` 可能对其他亮度、喷漆条件不适用，V1 不做自适应改动。
3. P1/P2 之间的 y 范围可能不足以容纳偏离/弯曲裂纹；`group_summary` 离线输出 GT 是否落在 ROI 之外。
4. 目前起点是 x=max(P1x,P2x)+6 的**单列贪心初始化**，错首次锁定仍可能传导；停止靠连续20列无共同证据，不是独立终止证明。
5. 初始/后续裂纹可能已存在参考图内，`newdark` 不一定提供正信号；V1 不自动修复参考可用性问题。
6. 源码假定输入相同像素尺寸、裂纹向右延伸；没有针对 CT3/其他组的独立成功证据。

因此本轮目标是**完整收集统一规则跨组成功和失败的证据**，而不是换个名字就把 V1 当成最终通用模型。
