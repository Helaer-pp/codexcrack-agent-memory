# 计时口径与结果

Release / C++17 / v142 / OpenCV 4.4 / 4 threads。完整 C++ 核心包括 Process、GetResultV2、CopyPath 与必要路径分配；输入预解码，JSON/文件日志另计，媒体编码和诊断不进入生产计时。Python 核心另含 JSON/geometry 转换，不能混用。

|组|调用|N|P50|P95|P99|Max|>66.67ms|
|---|---|---:|---:|---:|---:|---:|---:|
|group_a|A_native|550|8.766|10.741|11.468|13.898|0|
|group_a|Python_A|550|9.217|11.762|13.526|14.753|0|
|group_a|offline_diagnostic|550|45.110|67.832|68.812|130.570|72|
|group_c|A_native|561|5.507|6.677|7.340|7.910|0|
|group_c|Python_A|561|5.729|7.651|9.117|40.736|0|
|group_c|offline_diagnostic|561|148.862|157.491|161.898|204.530|561|
|ct2|A_native|467|17.925|23.433|27.279|31.782|0|
|ct2|refine_off|467|16.517|22.024|24.189|26.781|0|
|ct2|Python_A|467|19.607|26.828|33.061|107.125|2|
|ct2|offline_diagnostic|467|161.337|183.967|193.411|307.679|467|
|group_h|A_native|409|36.972|44.953|49.589|53.609|0|
|group_h|automatic|409|37.079|45.577|51.244|55.726|0|
|group_h|Python_A|409|38.361|47.037|49.386|52.881|0|
|group_h|offline_diagnostic|409|62.840|81.220|87.100|113.505|90|
|group_x|Python_A|523|31.885|44.249|51.511|93.474|1|
|group_x|offline_diagnostic|523|70.777|95.091|106.278|155.389|324|

所有超预算帧见 all_over_budget.csv；同一帧 Python/C++ 独立全序列重复对照见 python_cpp_same_frame_comparison.csv。未采集线程等待、分配栈或 OS 调度 trace，不能将峰值归因为 DP 或包装环境中的某一个模块。RSS/调度等待为 UNKNOWN；原生 DLL 自报 detector_ms 也包含内部等待，不等于纯算术耗时。

第五组如果仅有 Python 口径，不冒充额外的 C++ 全组重跑；该组按照冻结协议只评测一次。离线诊断无需达到15Hz。
