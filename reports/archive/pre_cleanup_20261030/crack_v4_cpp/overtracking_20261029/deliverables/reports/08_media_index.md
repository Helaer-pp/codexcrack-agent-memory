# 视频与报告实际清单

第五组独立实验使用冻结原版；其余优化命名视频是任务书要求的已撤回诊断版，不用于算法选择。

[第五组独立原版完整视频](../videos/group_x_independent_frozen_full.mp4) — 524帧，15FPS演示，已全帧解码。

|组|原图与诊断版|原版与诊断版|关键片段|帧数（前两项/预览）|
|---|---|---|---|---|
|开发组A|[完整](../videos/group_a_optimized_full.mp4)|[对照](../videos/group_a_before_after.mp4)|[预览](../videos/group_a_keyframes_preview.mp4)|551/551/60|
|验证组C|[完整](../videos/group_c_optimized_full.mp4)|[对照](../videos/group_c_before_after.mp4)|[预览](../videos/group_c_keyframes_preview.mp4)|562/562/60|
|CT2|[完整](../videos/ct2_optimized_full.mp4)|[对照](../videos/ct2_before_after.mp4)|[预览](../videos/ct2_keyframes_preview.mp4)|468/468/60|
|开发组H|[完整](../videos/group_h_optimized_full.mp4)|[对照](../videos/group_h_before_after.mp4)|[预览](../videos/group_h_keyframes_preview.mp4)|410/410/60|
|排除组X|[完整](../videos/group_x_optimized_full.mp4)|[对照](../videos/group_x_before_after.mp4)|[预览](../videos/group_x_keyframes_preview.mp4)|524/524/142|

全部16文件H264、1920×1080、15FPS，完整解码成功；ffprobe_all_videos.json及*_videos.json保存实际帧数。随机61画面同源重绘核对通过，最低PSNR37.87dB（编码压缩下不应逐字节相等）。

[人工复核图索引（876帧）](../review/index.html)

[开发主报告](00_executive_summary.md) · [根因证据](01_root_cause_case_51_473.md) · [回归](03_five_group_regression.md) · [精度边界](04_precision_and_ground_truth.md) · [性能](05_performance_15hz.md) · [发布决策](06_integration_and_release_decision.md)