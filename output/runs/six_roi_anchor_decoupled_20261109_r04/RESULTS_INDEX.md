# 六组基准点解耦媒体结果

本目录包含六组实验的逐帧对比图、15 FPS 对比视频和逐帧 CSV。每个视频面板包括：原图、旧 A 对照、原始 P1/P2、右移/左移/上移、间距缩放等 8 种当前基准点输入。

| 实验组 | 对比视频 | 逐帧 PNG | 逐帧压缩包 | 数值结果 |
|---|---|---|---|---|
| 开发组A | [comparison.mp4](group_a/comparison.mp4) | [frames/](group_a/frames/) | [frames.zip](group_a/frames.zip) | [per_case.csv](group_a/per_case.csv) |
| 验证组C | [comparison.mp4](group_c/comparison.mp4) | [frames/](group_c/frames/) | [frames.zip](group_c/frames.zip) | [per_case.csv](group_c/per_case.csv) |
| CT2 | [comparison.mp4](ct2/comparison.mp4) | [frames/](ct2/frames/) | [frames.zip](ct2/frames.zip) | [per_case.csv](ct2/per_case.csv) |
| 开发组H MT | [comparison.mp4](group_h/comparison.mp4) | [frames/](group_h/frames/) | [frames.zip](group_h/frames.zip) | [per_case.csv](group_h/per_case.csv) |
| 三点弯 | [comparison.mp4](three_point_bend/comparison.mp4) | [frames/](three_point_bend/frames/) | [frames.zip](three_point_bend/frames.zip) | [per_case.csv](three_point_bend/per_case.csv) |
| 排除组X白板 | [comparison.mp4](group_x/comparison.mp4) | [frames/](group_x/frames/) | [frames.zip](group_x/frames.zip) | [per_case.csv](group_x/per_case.csv) |

每组目录还包含：

- `frames.csv`：逐帧共同覆盖、确认数、组间最大坐标差；
- `per_case.csv`：每帧每种 P1/P2 输入的尖端坐标、确认状态和原因；
- `common_pairs.csv`：八种输入两两坐标差；
- `media.json`：视频分辨率、帧率和帧数；
- `summary.json`：该组汇总统计。

本批媒体均已验证为 1920×1080、15 FPS，PNG 数量与视频帧数一致。
