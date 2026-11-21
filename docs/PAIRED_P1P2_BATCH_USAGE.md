# P1/P2 文件夹批量计算

入口为项目根目录的 `paired_p1p2_roi_easy_edit.py`。原检测公式保留；新增文件夹遍历、自动P点跟踪、逐帧独立保存和浏览页面。它不替换生产算法，也不是上一轮ROI实验的B/C模式。

## 最少设置

修改文件顶部四项；P1/P2都是**参考帧**原图上的像素坐标，P1在上、P2在下：

```python
REFERENCE_IMAGE = r"F:\你的图像目录\参考.bmp"
IMAGE_FOLDER = r"F:\你的图像目录"
P1_REFERENCE = (1529, 2563)
P2_REFERENCE = (1529, 2858)
CURRENT_IMAGE = None
```

保持 `P1_CURRENT`、`P2_CURRENT`、`GROUND_TRUTH_TIP` 为 `None`。运行：

```powershell
& D:\ProgramData\anaconda3\python.exe .\paired_p1p2_roi_easy_edit.py
```

当前已保留原脚本的三点弯参考图46.bmp、原P1/P2，并把文件夹设为该参考图所在目录。换试件时同步修改参考图和两点，不要套用上一试件坐标。

## 批量行为

- 读取文件夹本层的BMP/PNG/JPG/JPEG/TIF/TIFF，不递归子目录。自然排序，例如1、2、10；参考图若在此目录，也作为一帧正常处理。
- 差分参考图始终固定。默认 `POINT_TRACKING_MODE='previous'`：以上一张处理成功的图像及P点作为NCC模板；局部位移累积成当前P点，再相对初始参考P点计算原算法位移。单次搜索半径默认25px。匹配失败不强行输出，不更新跟踪状态，下一帧仍以上一成功帧为模板。
- `POINT_TRACKING_MODE='reference'` 改为每帧匹配初始参考模板，允许位移范围就是相对初始帧的搜索半径。两种点跟踪方式不保证整段不漂移，相关性及匹配来源都记录在每帧metadata.json中。
- 当前图与参考图必须同尺寸；坏图、尺寸不符、P点匹配失败均记录ERROR并继续。配置错误和参考图无法读取会在批量开始前报错。Ctrl+C保留已完成帧和部分图册。
- 每次生成新的 `output/paired_p1p2_roi_easy_edit/run_日期时间/`，不覆盖旧结果，不写原图目录。中文路径可用。排除组X路径被排除；验证组仅固定规则推理，不使用标签选参。

## 结果显示

结束后自动打开本次 `index.html`，下拉框或左右箭头切换帧；点击图片查看原尺寸PNG。设置 `OPEN_RESULTS=False` 或命令行 `--no-open` 可以只保存。

每张成功帧的图有三栏：**整幅原图+完整搜索ROI；局部ROI原图；相同局部区域的裂纹结果**。青色是搜索ROI，黄色是展示裁剪框；红/蓝加号为P1/P2；绿色为观测轨迹，橙色为缺失段预测，红叉为原算法暂定端点。没有检测端点就显示NO_TIP；ERROR帧有可读原图时展示原图，不伪造ROI或路径。

`DISPLAY_MODE='joint'` 默认显示当前暗谷+参考变暗；`'current'` 显示仅当前暗谷对照。`MAIN_DISPLAY_THRESHOLD=10` 控制显示阈值。无论显示哪一种，原有joint/current及8/10/12共六组结果都保存；显示选择不改变检测计算。

| 文件 | 内容 |
|---|---|
| index.html | 可翻页的全部帧，包括失败帧 |
| batch_summary.csv | 每帧主显示模式的端点、P点、状态、错误 |
| all_mode_results.csv | 成功处理帧的所有模式与阈值结果 |
| run_config.json / script_snapshot.py | 本次输入清单、配置、代码SHA和源码副本 |
| run_status.json | 完成/中断状态、帧数、失败数和耗时 |
| frames/000001/result_overlay.png | 三栏对比图 |
| frames/000001/trace_*.csv | 原分辨率逐列轨迹和证据 |
| frames/000001/metadata.json | 文件映射、当前点、NCC、ROI与参数；失败时为错误详情 |

原脚本的stop_reason原来在到达ROI右边时也写gap_limit，现只纠正日志为roi_right_boundary；端点与轨迹数值未因此改变。右边界处的最后观测点仍属暂定端点，不代表已确认物理裂纹停止。

单对图像兼容：`--current "当前图路径"`；可配 `--p1-cur x,y --p2-cur x,y`，会忽略文件夹设置。命令行 `--reference`、`--image-folder`、`--p1-ref`、`--p2-ref`、`--point-tracking`、`--display-mode` 和 `--output-dir` 可覆盖顶部配置。

此次检查包括：自然排序、中文路径、坏图后继续、累计位移超出初始搜索半径、低纹理模板拒绝、排除排除组X；修改前后六份逐列轨迹数值完全一致。使用原配置的7695.bmp完成真实单帧显示检查；这不是全文件夹精度验收。项目run.ps1 check通过。没有读取人工标签。
