# 实现范围

生产源码/DLL未改。research/uctt_r05e 为当前研究代码；生成副本在output/build/uctt_r05e_source，B0/B1/B2目标在output/build/uctt_r05e/Release。generate.py复用只读R05D源生成逻辑并把所有输出根明确重定向到R05E；不执行旧sealed输出中的源码。B0是原源码重建；B1/B2同一生成源，B2仅定义R05E_BUDGET。旧Trace计时/局部参考元数据为旁路；旧DP峰只读导出并与current峰合并。R05E exports均研究专用，不改变原ABI。research_source_patch含构建所需研究源码/生成源；完整差异见research_source_patch/production_instrumentation.diff。

早期B1运行首帧遇到Python汇总字典mode重复键，修复报表字段后从第1帧重跑；日志保留logs/B1_writer_fix.log。该修复未改C++或候选规则。
