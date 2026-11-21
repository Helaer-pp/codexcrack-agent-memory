# 当前裂纹识别程序

1. 打开 [run_crack_tip.py](../run_crack_tip.py)，修改文件开头的 **手动设置区**。脚本使用手动设置区里当前保存的路径和基准点。
2. 双击 [CrackTipRunner.exe](../output/releases/CrackTipRunner/CrackTipRunner.exe)，或在项目根目录运行下方命令。程序在控制台打印本次结果目录。
3. 打开该目录的 `results.mp4` 查看全程，或在 `comparisons` 和 `differences` 查看单帧。每次运行都会新建子目录，旧结果保留。

```powershell
& 'D:/ProgramData/anaconda3/python.exe' -B ./run_crack_tip.py
& './output/releases/CrackTipRunner/CrackTipRunner.exe' --config 'E:/实验/本次参数.json'
& './output/releases/CrackTipRunner/CrackTipRunner.exe' --version
```

EXE 是 Windows 控制台启动器，需要保留在项目目录树内，调用本机已安装依赖的 Python 环境。解释器路径来自 [config/project.json](../config/project.json) 的 `python_executable`，也可用环境变量 `CRACKTIP_PYTHON` 覆盖。直接运行 [run_crack_tip.py](../run_crack_tip.py) 使用相同的检测和渲染入口。

## 运行 V6.3 验证候选

在脚本顶部将 `use_validation_candidate` 设为 `True`，再双击原来的 EXE，即可使用 **V6.3 S2** 检测并生成同版视频、参考差分和局部图。默认值 `False` 使用 **V5.15 S2**。两种模式共用你的输入路径、基准点和保存设置，`run.json`、结果表和图中均标明实际版本。

也可临时从命令行指定候选。已有的 JSON 配置文件同样可用。

```powershell
& './output/releases/CrackTipRunner/CrackTipRunner.exe' --candidate --version
& './output/releases/CrackTipRunner/CrackTipRunner.exe' --candidate --config './crack_tip_settings.json'
```

## 更换自己的图像

先填 `reference_image`、`image_input`、`output_dir` 和 `reference_points`。脚本顶部的相对路径以脚本目录为起点。命令行显式传入 `--config` 时，整套设置取自指定的 JSON，相对路径以该 JSON 所在目录为起点。可复制 [JSON 示例](../crack_tip_settings.json) 单独保存多套参数。Python 设置区用 `None`、`True`、`False`，对应 JSON 中的 `null`、`true`、`false`。Windows 路径推荐写成 `E:/试验/参考.bmp`。输入为相同分辨率的 8 位图像，彩色图会转换为灰度。

`reference_points` 格式为 `[[P1x,P1y],[P2x,P2y]]`。所有坐标均为原图像素，左上角为原点，P1 在上、P2 在下，点间距离至少 20 px。按照当前点的来源选用一种模式。

| 你的输入 | point_mode | 需要填写 |
|---|---|---|
| 只有参考图的两个点 | `ncc` | `current_points` 填空值。每张图相对固定参考图做模板匹配，可修改 `ncc_radius`、`ncc_search`（px）和 `ncc_min`。低于门槛的帧记录为输入异常 |
| 有一对已知当前点，或整个序列使用相同点位 | `fixed` | `current_points` 填两点。填空值 时全程沿用参考点。单帧与批量均可使用 |
| 每张当前图各有两点 | `table` | `points_file` 填坐标表，`current_points` 填空值。优先使用按文件名匹配的 CSV |

CSV 使用以下表头，`image` 是含扩展名的文件名。

```csv
image,x0,y0,x1,y1
sample_001.bmp,863.185,996.521,874.065,1281.66
sample_002.bmp,863.665,998.043,874.158,1283.76
```

也支持项目现有的 `num: N 基准点: x0 y0 x1 y1` TXT。TXT 按文件夹内自然排序后的**全序列序号**匹配，`table_first_index` 表示第一张图对应的 num，默认 0。筛选帧范围后沿用原序号。若把 `image_input` 改成单个文件，使用 CSV、手填点，或将 `table_first_index` 改成该帧真实的 num。

## 其余配置

| 键 | 用途 |
|---|---|
| `image_input`、`extensions` | 输入单张文件或目录。目录只枚举当前层，按文件名中的数字自然排序，支持扩展名列表筛选 |
| `first_frame`、`last_frame` | 从 1 开始，含首末两帧，末帧填空值 表示处理到最后 |
| `roi` | 默认空值，由点位计算。手动值为原图 `[左,上,右,下]`，右、下边界不含。启用亮区约束时取交集 |
| `feature_scale_px` | 默认空值，跟随当前版本。V5.15 S2 的冻结值为 288 px，改值属于自定义实验 |
| `bright_profile` | `"auto"` 对登记的验证组C目录启用[配套亮区配置](../config/crack_tip_group_c_bright.json)，其他目录用普通点位。处理迁移后的验证组C图像时显式填该配置路径。验证组C做亮区敏感性测试时保持该约束。若专门复核原点结果，填空值 |
| `title` | 对比图和视频中的试验名称，建议简短 |
| `save_comparisons`、`save_differences`、`save_video` | 分别开关四联对比 JPG、独立有符号差分 PNG、MP4。仅存视频时编码完成即清理临时帧 |
| `video_fps`、`ffmpeg` | 视频播放帧率和编码器路径。默认使用项目内的 FFmpeg |
| `output_dir` | 每次运行的结果保存根目录，选择可写位置。项目登记的原始图像目录保持只读 |

亮区模式使用输入的参考点和当前点估计试件移动，再在参考、当前两张图上检查测量邻域。若要改变亮区内请求的点位，可复制亮区 JSON，修改 `reference_virtual_points` 并将 `bright_profile` 指向副本。该文件还记录参考框、有效亮带、亮度下限和绑定的参考文件 SHA256。更换参考帧时应提供与新参考帧对应的几何和亮度设置。逐帧结果同时保存输入点、实际使用点和实际 ROI。

## 结果文件

- `results.csv` 给出每帧文件名、状态、终止原因、尖端原图坐标、根点至尖端的折线弧长，以及相对两基准点中点的法向投影长度。长度单位为 px。有效图像未找到裂纹时，尖端和长度留空。
- `paths.jsonl` 每行对应一帧，`points` 是从根点到尖端的全部原图坐标。`run.json` 保存版本、输入配置和参考文件校验值。
- 四联图与视频使用同一个渲染器，显示固定参考原图对应位置、当前灰度图、裂纹路径与尖端、固定参考减当前的配准差分。亮红为当前变暗，蓝为当前变亮。无有效对应的位置用灰色表示。无尖端时图中明确标注定位窗口中心。
- 图像无法读取或当前点不可用时，程序记录 `INPUT_ERROR`，继续下一帧，并在视频保留该帧位置。退出码 0 表示批次完成，2 表示批次完成且有输入异常。

## 小版本更新

[research/current_crack_tip.py](../research/current_crack_tip.py) 绑定当前选定的算法阶段、特征尺度和配套渲染器。项目的 [AGENTS.md](../AGENTS.md) 已将日常入口同步和真实帧回放列为小版本交付步骤。用户可继续使用同一个 EXE 和个人配置。

可用 [check_crack_tip_run.py](../tools/check_crack_tip_run.py) 复核有相同输入点的回放。以下为本次开发组A全序列在项目根目录复核的命令。验证组C亮区使用 `--placement bright`，从单张文件运行时用 `--first-baseline-frame` 指定其对应的完整序列帧号。

```powershell
& 'D:/ProgramData/anaconda3/python.exe' -B tools/check_crack_tip_run.py output/crack_tip_runs/20261120_175710_3a3fc185 output/experiments/v515_clean_fast_r02/group_a.jsonl
```

本次开发组A 551 帧的状态、尖端、完整路径、弧长及投影长度与冻结结果逐帧一致，551 张对比图、551 张差分图和视频均完成校验。[示例视频](../output/crack_tip_runs/20261120_175710_3a3fc185/results.mp4) · [三组抽帧核对记录](../output/verification/current_runner_r01/checks.json)。
