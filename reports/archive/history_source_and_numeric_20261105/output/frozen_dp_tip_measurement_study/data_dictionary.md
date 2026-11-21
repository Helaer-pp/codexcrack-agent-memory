# 数据和帧号约定

`03_experiments/per_frame_results.csv` 为规范化全消融导出，包含任务书要求的最少列，10981条当前帧记录；`final_research_measurements.csv` 只选已冻结的 AE 分支，共2510条当前帧。没有人工GT的误差字段为空，未执行采样的质量字段为空，不用0冒充已测量值。

- 原图坐标：左上角原点，x右、y下，单位px；弧长是原图折线弧长。没有新增通用标定文件，不自行换算mm。
- `frame_id=0` 是参考；当前帧从1开始。原视频零基帧下标=`frame_id-1`。不同组分别编号。
- `image_filename` 是原始文件名，不用视频帧下标替代图像编号。源图与逐帧基准点对应关系见各输入manifest。
- `baseline_confirmed`、`candidate_confirmed` 都是尖端确认且完整长度有效。独立的尖端/完整长度有效位另列；tip-only不画正式完整路径。
- tip x/y为空表示未确认该尖端；length为空表示没有完整长度。不要自行把上一帧填入当前帧。
- `tip_delta_px` 是两个均有效输出间的位移，不是尖端真值误差；`length_delta_px` 是版本差异，不是实际长度误差。
- `path_file` 定位完整JSONL，`path_jsonl_row` 为**零基记录下标**，文本物理行号需加1。每条JSON含原始A、实际变换、原路径、研究输出、剖面及明确原因。
- samples列依次为`s,x,y,mx,my,contrast,reference_contrast,reference_change,local_background,noise,support,quality,new_growth,static_texture,temporal_support`。s为原图弧长，m为参考/材料坐标，灰度量用0～255灰度单位；support/quality为判据位，其余分数为定义内的比例，不是准确率或真实概率。
- 原API尖端和长度保留0.01px舍入；CopyPath保留双精度。正式绘制使用CopyPath实际末端，量化差详见M审计，不改变A数值。
- `process_core_ms` 是预解码输入上的完整调用wall测量；A原生Process、旁路及细分模块耗时另列。样本导出、读写盘、渲染、视频编码不在core内。
- 通用stats函数在像素分布中也保留`over_budget`键，它只有在毫秒计时数组中才有预算意义；像素误差只解释P50/P95/P99/Max，不能把像素值当66.67ms超时。

冻结后只作列名映射、数组展开、目录索引及报告文字整理，不修改检测、评测门槛、研究参数、统计或视频脚本。原始冻结统计CSV/JSONL同时保留；规范化导出记录见`delivery_formatting_receipt.json`。
