# 复算

Python D:/ProgramData/anaconda3/python.exe；源代码均在本目录，common_b.py将输出绑定此run01。冻结A为原C++17/OpenCV4.4 DLL，不重编译。

严格顺序：p0.py → unit_tests.py → contracts.py → controlled.py DEV → summarize.py DEV → freeze.py → controlled.py TEST → summarize.py TEST → history.py → trace_native.py → sensitivity.py → regression.py → media.py history → media.py controlled → root_causes.py → report.py。

每步非0必须停止。TEST输入生成拒绝覆盖；若要重新试验，复制到新run_id，修改种子/OUT，重新冻结，不能覆盖既有TEST。已封存结果使用CSV/JSONL/PNG逐项审阅；复查冻结A可新建运行目录重放native TSV。

history.py与media.py history支持可选group参数，独立组可在原生计时结束后并行执行。研究计时不与A完整原生计时混用。视频15FPS为演示；正式原A视频可在上轮总览查看，本轮生成的是标注研究状态的新诊断视频，包含完整原图及局部原图。

trace_native.py只开启DLL已存在的DIAGNOSTICS/DEBUG_IMAGES配置3575；生产仍3572。每个追踪帧与本轮正式3572的状态/尖端/长度/double路径强制相等。它不导出第二名DP分支分数，所以没有编造H_ALT。冷启动敏感性实验历史为空，与时序结果不可混称同一实验。


## 最终实际复算顺序与勘误

冻结的trace_native.py保留了空路径shape比较错误，最终请使用trace_native_corrected_posttest.py。其flags仍3575，比较使用reshape(-1,2)，并将支持阈值计数纠正为实际2.5；不改检测器。图片/视频最终使用media_final_posttest.py，增加P1/P2虚线和尖端/长度文字，纯显示改动。

成功TEST后执行：history.py（历史）→ trace_native_corrected_posttest.py → regression.py → sensitivity.py → posttest_native_reconstruction.py → root_causes.py → media_final_posttest.py history [可选group] → media_final_posttest.py controlled → report.py → posttest_deep_audit.py → posttest_descriptive_metrics.py → posttest_duration_diagnostic.py → posttest_engineering.py → finalize.py。

posttest_audit.py只用于保留/校正本次DEV期间先行运行的历史H_SHORT导出；从冻结后history.py重新开始复算则无需此步骤。所有posttest_*均是只读分析/工程验证/显示修正，不修改选定政策或新TEST预测，不是新的独立测试。原始TEST拒绝覆盖；相同seed复现只能称复现，不能称新的盲测。

关键DP重建只对65个延伸tile验证native终止列一致。seed使用另套重启/边界/历史惩罚，NOT_RECONSTRUCTED，不能混用延伸递推。权威数据为key_native_tile_reconstructed.csv和key_native_selected_point_scores.csv；旧key_native_tile_audit.csv为简化导出，重建表优先。
