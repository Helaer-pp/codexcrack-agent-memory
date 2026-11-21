# Frozen DP / MTE 研究

正式默认保留A，研究AE未证明真实精度提升。

- 09_reports/development_report.md：十项结论和消融表
- 07_videos/final：五组完整视频/对比/问题片段
- 08_frames_final：每个当前帧原图与研究结果PNG，参考帧不计入
- 03_experiments/dev4、05_holdout：逐帧CSV及完整JSONL
- 04_freeze：源码/参数/门槛/脚本/二进制冻结及第五组一次访问记录

视频15FPS是演示速度。选定AE本次五组完整调用Max62.10ms、0超时；全消融的其他配置存在超过66.67ms的长停顿，不能忽略这些最坏值。新的纯C++全串联性能尚未直接测试。所有真实精度均N/A，合成精度未过关，故不启用研究模块。

优先打开[index.html](index.html)与[正式十项报告](09_reports/ordered_results_report.md)。36个MP4已完整解码，2510张当前帧PNG齐全；每组frame0参考帧不进视频。
