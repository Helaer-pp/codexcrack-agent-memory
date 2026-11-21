# 耗时与兼容

全部当前帧内存预载，计时含原生Process和FFI边界，不含图像解码、JSON查询、JSON解析、绘图、编码。API查询和Python解析分别保存。detector_ms也单独保存。初始化和参考帧不混入当前帧分位数。VS2022 / v142 x64 Release /O2 /fp:precise /MD，OpenCV4.4.0，4线程。本机测量不是通用硬实时保证。

| group | mode | p50 | p95 | p99 | max | over66 |
| --- | --- | --- | --- | --- | --- | --- |
| group_a | OFF | 8.295 | 11.157 | 12.205 | 12.836 | 0 |
| group_a | FULL_LOCAL | 10.362 | 13.969 | 15.693 | 16.406 | 0 |
| group_a | FULL_PRODUCTION | 10.32 | 14.102 | 15.389 | 15.924 | 0 |
| group_c | OFF | 5.3 | 7.138 | 8.09 | 9.346 | 0 |
| group_c | FULL_LOCAL | 6.282 | 8.592 | 9.278 | 10.599 | 0 |
| group_c | FULL_PRODUCTION | 6.328 | 8.697 | 9.544 | 10.831 | 0 |
| ct2 | OFF | 19.067 | 26.569 | 29.24 | 30.48 | 0 |
| ct2 | FULL_LOCAL | 23.818 | 33.44 | 37.277 | 38.209 | 0 |
| ct2 | FULL_PRODUCTION | 23.599 | 32.659 | 36.885 | 40.532 | 0 |
| group_h | OFF | 39.227 | 47.472 | 52.828 | 55.943 | 0 |
| group_h | FULL_LOCAL | 40.052 | 50.099 | 57.172 | 61.239 | 0 |
| group_h | FULL_PRODUCTION | 40.271 | 50.206 | 58.618 | 62.369 | 0 |

最慢帧和未确认/重定位分支P50/P95/P99/Max见../tests/dev4_aggregate.json。新模块默认关闭，样本诊断数组只在524288标志启用时收集。生产与诊断开启原生结果全帧一致，见diagnostic_production_equality.json。旧ABI、V2、stride、ResetTemporal、多实例、查询无副作用、内存增长及历史失效测试见tests。

第五组只回放冻结声明的BASE和FULL_LOCAL（含诊断），没有为了性能再运行FULL_PRODUCTION。FULL_LOCAL最慢73.0256ms，1帧超预算；不能根据四组诊断关闭结果推断第五组生产关闭的速度一定达标。完整序列的计时、API查询和Python解析见final5逐帧记录。

测试机：{"os": "Windows-11-10.0.26200-SP0", "processor": "AMD64 Family 25 Model 97 Stepping 2, AuthenticAMD", "logical_cpus": 32, "physical_cpus": 16, "ram_bytes": 67768807424, "opencv_threads": 4, "hardware_model": "CIM unavailable in sandbox; no guessed commercial CPU model"}

相同帧配对FULL_LOCAL减OFF的最大新增Process耗时（配对仍包含系统计时波动）：

|组|最大新增 ms|frame_id|
|---|---:|---:|
|group_a|7.1947|318|
|group_c|4.0005|379|
|ct2|15.9775|388|
|group_h|11.8064|392|
