# 性能验收

环境：Windows x64，AMD Ryzen 9 7950X，MSVC v142 Release /O2 /fp:precise，D:/opencv-4.4.0 OpenCV4.4.0，OpenCV4线程。一次驻留一组全量灰度图像，准备Image/Point结构，独立实例预热10帧后丢弃，再从参考帧新建正式时序实例。以perf_counter围绕原生Process计时，包括原生基准点有效性检查、配准、DP/tile、root/terminal/temporal、结果填充；不含读图、解码、JSON、CopyPath、绘图或编码。

所有正常/错误/恢复帧都在分母内，不剔除异常值。参考帧GetBaseline为只读查询，初始化与参考结果单列，不混入当前帧统计。最初完整消融交替调用顺序；最后候选与控制额外完整驻留配对回放。数据和二进制哈希位于config/modes.json，各个历史消融的冻结DLL单独保留。

## 正式候选 ANCHOR_OPT

| 数据组 | 当前帧 | P50 ms | P95 ms | P99 ms | Max ms | >66.67 ms | 进程峰值 GiB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 550 | 7.968 | 10.119 | 11.508 | 12.148 | 0 | 2.633 |
| 验证组C | 561 | 4.820 | 6.147 | 6.697 | 7.940 | 0 | 14.531 |
| CT2 | 467 | 16.335 | 21.340 | 22.987 | 27.541 | 0 | 13.165 |
| 开发组H MT | 409 | 36.096 | 42.912 | 44.648 | 47.948 | 0 | 3.905 |

本次1987张当前帧中，超66.67ms共0张。 本机本次检测计算15Hz预算通过。 不能据此声称包含视频/UI的应用吞吐率达到15Hz，也不能保证其他机器的最坏时延。

## 初始化、驻留图像与尺寸

| 组别 | 图像尺寸 | 驻留输入GiB | 参考初始化ms |
| --- | --- | --- | --- |
| 开发组A | [1856, 2072] | 1.973 | 1.469 |
| 验证组C | [5120, 5120] | 13.721 | 5.658 |
| CT2 | [5120, 5120] | 11.426 | 22.433 |
| 开发组H MT | [5112, 1406] | 2.744 | 8.703 |

进程峰值包括整组预解码图像、Python验证框架和各独立实例，不是DLL内部缓存大小。

## 全配置与异常分层

| 组别 | 模式 | 分层 | n | P50 ms | P95 ms | P99 ms | Max ms | 超预算 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A | AUTO_BASE | all | 550 | 7.826 | 9.781 | 10.801 | 12.285 | 0 |
| 开发组A | AUTO_BASE | normal | 550 | 7.826 | 9.781 | 10.801 | 12.285 | 0 |
| 开发组A | AUTO_BASE | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | AUTO_BASE | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | AUTO_NEW_SHADOW | all | 550 | 6.837 | 8.614 | 8.776 | 9.254 | 0 |
| 开发组A | AUTO_NEW_SHADOW | normal | 550 | 6.837 | 8.614 | 8.776 | 9.254 | 0 |
| 开发组A | AUTO_NEW_SHADOW | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | AUTO_NEW_SHADOW | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_NEW_SHADOW | all | 550 | 7.947 | 10.336 | 11.225 | 11.883 | 0 |
| 开发组A | ANCHOR_NEW_SHADOW | normal | 550 | 7.947 | 10.336 | 11.225 | 11.883 | 0 |
| 开发组A | ANCHOR_NEW_SHADOW | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_NEW_SHADOW | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_NEW_VERIFIED | all | 550 | 6.990 | 8.834 | 9.056 | 9.540 | 0 |
| 开发组A | ANCHOR_NEW_VERIFIED | normal | 550 | 6.990 | 8.834 | 9.056 | 9.540 | 0 |
| 开发组A | ANCHOR_NEW_VERIFIED | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_NEW_VERIFIED | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_NO_REFINE | all | 550 | 6.319 | 8.069 | 8.315 | 9.055 | 0 |
| 开发组A | ANCHOR_NO_REFINE | normal | 550 | 6.319 | 8.069 | 8.315 | 9.055 | 0 |
| 开发组A | ANCHOR_NO_REFINE | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_NO_REFINE | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | AUTO_OPT | all | 550 | 6.798 | 8.614 | 8.830 | 10.072 | 0 |
| 开发组A | AUTO_OPT | normal | 550 | 6.798 | 8.614 | 8.830 | 10.072 | 0 |
| 开发组A | AUTO_OPT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | AUTO_OPT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | COMPAT_ANCHOR | all | 550 | 7.977 | 9.982 | 11.306 | 12.621 | 0 |
| 开发组A | COMPAT_ANCHOR | normal | 550 | 7.977 | 9.982 | 11.306 | 12.621 | 0 |
| 开发组A | COMPAT_ANCHOR | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | COMPAT_ANCHOR | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | AUTO_REPORT_REPLAY | all | 550 | 6.926 | 8.766 | 8.896 | 9.132 | 0 |
| 开发组A | AUTO_REPORT_REPLAY | normal | 550 | 6.926 | 8.766 | 8.896 | 9.132 | 0 |
| 开发组A | AUTO_REPORT_REPLAY | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | AUTO_REPORT_REPLAY | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | AUTO_DEFAULT_COMPAT | all | 550 | 7.730 | 9.867 | 11.230 | 11.703 | 0 |
| 开发组A | AUTO_DEFAULT_COMPAT | normal | 550 | 7.730 | 9.867 | 11.230 | 11.703 | 0 |
| 开发组A | AUTO_DEFAULT_COMPAT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | AUTO_DEFAULT_COMPAT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_RIGID_EXPERIMENT | all | 550 | 6.307 | 8.076 | 8.320 | 8.955 | 0 |
| 开发组A | ANCHOR_RIGID_EXPERIMENT | normal | 550 | 6.307 | 8.076 | 8.320 | 8.955 | 0 |
| 开发组A | ANCHOR_RIGID_EXPERIMENT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_RIGID_EXPERIMENT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_GEOMETRY_ONLY | all | 550 | 7.501 | 9.283 | 9.469 | 11.465 | 0 |
| 开发组A | ANCHOR_GEOMETRY_ONLY | normal | 550 | 7.501 | 9.283 | 9.469 | 11.465 | 0 |
| 开发组A | ANCHOR_GEOMETRY_ONLY | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_GEOMETRY_ONLY | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_OPT | all | 550 | 7.968 | 10.119 | 11.508 | 12.148 | 0 |
| 开发组A | ANCHOR_OPT | normal | 550 | 7.968 | 10.119 | 11.508 | 12.148 | 0 |
| 开发组A | ANCHOR_OPT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组A | ANCHOR_OPT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | AUTO_BASE | all | 561 | 4.676 | 5.907 | 6.517 | 7.097 | 0 |
| 验证组C | AUTO_BASE | normal | 561 | 4.676 | 5.907 | 6.517 | 7.097 | 0 |
| 验证组C | AUTO_BASE | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | AUTO_BASE | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | AUTO_NEW_SHADOW | all | 561 | 5.043 | 6.692 | 7.540 | 7.944 | 0 |
| 验证组C | AUTO_NEW_SHADOW | normal | 561 | 5.043 | 6.692 | 7.540 | 7.944 | 0 |
| 验证组C | AUTO_NEW_SHADOW | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | AUTO_NEW_SHADOW | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_NEW_SHADOW | all | 561 | 4.807 | 6.085 | 6.870 | 8.022 | 0 |
| 验证组C | ANCHOR_NEW_SHADOW | normal | 561 | 4.807 | 6.085 | 6.870 | 8.022 | 0 |
| 验证组C | ANCHOR_NEW_SHADOW | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_NEW_SHADOW | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_NEW_VERIFIED | all | 561 | 5.196 | 6.967 | 7.779 | 8.445 | 0 |
| 验证组C | ANCHOR_NEW_VERIFIED | normal | 561 | 5.196 | 6.967 | 7.779 | 8.445 | 0 |
| 验证组C | ANCHOR_NEW_VERIFIED | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_NEW_VERIFIED | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_NO_REFINE | all | 561 | 4.294 | 5.739 | 6.447 | 6.900 | 0 |
| 验证组C | ANCHOR_NO_REFINE | normal | 561 | 4.294 | 5.739 | 6.447 | 6.900 | 0 |
| 验证组C | ANCHOR_NO_REFINE | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_NO_REFINE | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | AUTO_OPT | all | 561 | 5.042 | 6.733 | 7.581 | 9.854 | 0 |
| 验证组C | AUTO_OPT | normal | 561 | 5.042 | 6.733 | 7.581 | 9.854 | 0 |
| 验证组C | AUTO_OPT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | AUTO_OPT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | COMPAT_ANCHOR | all | 561 | 4.820 | 5.918 | 6.576 | 7.347 | 0 |
| 验证组C | COMPAT_ANCHOR | normal | 561 | 4.820 | 5.918 | 6.576 | 7.347 | 0 |
| 验证组C | COMPAT_ANCHOR | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | COMPAT_ANCHOR | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | AUTO_REPORT_REPLAY | all | 561 | 4.583 | 6.047 | 6.762 | 8.285 | 0 |
| 验证组C | AUTO_REPORT_REPLAY | normal | 561 | 4.583 | 6.047 | 6.762 | 8.285 | 0 |
| 验证组C | AUTO_REPORT_REPLAY | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | AUTO_REPORT_REPLAY | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | AUTO_DEFAULT_COMPAT | all | 561 | 4.655 | 5.924 | 6.344 | 7.302 | 0 |
| 验证组C | AUTO_DEFAULT_COMPAT | normal | 561 | 4.655 | 5.924 | 6.344 | 7.302 | 0 |
| 验证组C | AUTO_DEFAULT_COMPAT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | AUTO_DEFAULT_COMPAT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_RIGID_EXPERIMENT | all | 561 | 4.259 | 5.687 | 6.280 | 6.603 | 0 |
| 验证组C | ANCHOR_RIGID_EXPERIMENT | normal | 561 | 4.259 | 5.687 | 6.280 | 6.603 | 0 |
| 验证组C | ANCHOR_RIGID_EXPERIMENT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_RIGID_EXPERIMENT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_GEOMETRY_ONLY | all | 561 | 4.975 | 6.936 | 7.544 | 7.878 | 0 |
| 验证组C | ANCHOR_GEOMETRY_ONLY | normal | 561 | 4.975 | 6.936 | 7.544 | 7.878 | 0 |
| 验证组C | ANCHOR_GEOMETRY_ONLY | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_GEOMETRY_ONLY | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_OPT | all | 561 | 4.820 | 6.147 | 6.697 | 7.940 | 0 |
| 验证组C | ANCHOR_OPT | normal | 561 | 4.820 | 6.147 | 6.697 | 7.940 | 0 |
| 验证组C | ANCHOR_OPT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 验证组C | ANCHOR_OPT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | AUTO_BASE | all | 467 | 16.022 | 21.432 | 24.024 | 27.735 | 0 |
| CT2 | AUTO_BASE | normal | 444 | 16.146 | 21.439 | 24.305 | 27.735 | 0 |
| CT2 | AUTO_BASE | error | 23 | 0.566 | 0.716 | 0.912 | 0.965 | 0 |
| CT2 | AUTO_BASE | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | AUTO_NEW_SHADOW | all | 467 | 16.941 | 22.110 | 24.938 | 28.852 | 0 |
| CT2 | AUTO_NEW_SHADOW | normal | 444 | 16.725 | 21.658 | 24.167 | 28.852 | 0 |
| CT2 | AUTO_NEW_SHADOW | error | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | AUTO_NEW_SHADOW | fallback | 23 | 20.763 | 25.097 | 25.886 | 26.061 | 0 |
| CT2 | ANCHOR_NEW_SHADOW | all | 467 | 16.388 | 21.481 | 22.873 | 27.064 | 0 |
| CT2 | ANCHOR_NEW_SHADOW | normal | 467 | 16.388 | 21.481 | 22.873 | 27.064 | 0 |
| CT2 | ANCHOR_NEW_SHADOW | error | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | ANCHOR_NEW_SHADOW | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | ANCHOR_NEW_VERIFIED | all | 467 | 17.054 | 22.151 | 24.505 | 27.617 | 0 |
| CT2 | ANCHOR_NEW_VERIFIED | normal | 467 | 17.054 | 22.151 | 24.505 | 27.617 | 0 |
| CT2 | ANCHOR_NEW_VERIFIED | error | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | ANCHOR_NEW_VERIFIED | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | ANCHOR_NO_REFINE | all | 467 | 16.294 | 20.449 | 23.074 | 27.793 | 0 |
| CT2 | ANCHOR_NO_REFINE | normal | 467 | 16.294 | 20.449 | 23.074 | 27.793 | 0 |
| CT2 | ANCHOR_NO_REFINE | error | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | ANCHOR_NO_REFINE | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | AUTO_OPT | all | 467 | 17.460 | 23.357 | 26.073 | 30.842 | 0 |
| CT2 | AUTO_OPT | normal | 379 | 16.277 | 20.595 | 22.909 | 25.343 | 0 |
| CT2 | AUTO_OPT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | AUTO_OPT | fallback | 88 | 21.290 | 26.099 | 28.923 | 30.842 | 0 |
| CT2 | COMPAT_ANCHOR | all | 467 | 16.473 | 21.475 | 22.942 | 25.415 | 0 |
| CT2 | COMPAT_ANCHOR | normal | 467 | 16.473 | 21.475 | 22.942 | 25.415 | 0 |
| CT2 | COMPAT_ANCHOR | error | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | COMPAT_ANCHOR | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | AUTO_REPORT_REPLAY | all | 467 | 16.852 | 21.433 | 24.246 | 29.761 | 0 |
| CT2 | AUTO_REPORT_REPLAY | normal | 440 | 16.319 | 21.049 | 24.062 | 29.761 | 0 |
| CT2 | AUTO_REPORT_REPLAY | error | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | AUTO_REPORT_REPLAY | fallback | 27 | 19.876 | 24.201 | 24.498 | 24.598 | 0 |
| CT2 | AUTO_DEFAULT_COMPAT | all | 467 | 16.046 | 21.311 | 24.095 | 27.803 | 0 |
| CT2 | AUTO_DEFAULT_COMPAT | normal | 444 | 16.220 | 21.345 | 24.339 | 27.803 | 0 |
| CT2 | AUTO_DEFAULT_COMPAT | error | 23 | 0.591 | 0.798 | 2.636 | 3.154 | 0 |
| CT2 | AUTO_DEFAULT_COMPAT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | ANCHOR_RIGID_EXPERIMENT | all | 467 | 16.297 | 20.331 | 23.772 | 27.067 | 0 |
| CT2 | ANCHOR_RIGID_EXPERIMENT | normal | 467 | 16.297 | 20.331 | 23.772 | 27.067 | 0 |
| CT2 | ANCHOR_RIGID_EXPERIMENT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | ANCHOR_RIGID_EXPERIMENT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | ANCHOR_GEOMETRY_ONLY | all | 467 | 16.983 | 22.061 | 23.760 | 27.624 | 0 |
| CT2 | ANCHOR_GEOMETRY_ONLY | normal | 467 | 16.983 | 22.061 | 23.760 | 27.624 | 0 |
| CT2 | ANCHOR_GEOMETRY_ONLY | error | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | ANCHOR_GEOMETRY_ONLY | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | ANCHOR_OPT | all | 467 | 16.335 | 21.340 | 22.987 | 27.541 | 0 |
| CT2 | ANCHOR_OPT | normal | 467 | 16.335 | 21.340 | 22.987 | 27.541 | 0 |
| CT2 | ANCHOR_OPT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| CT2 | ANCHOR_OPT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | AUTO_BASE | all | 409 | 35.989 | 43.274 | 46.034 | 49.144 | 0 |
| 开发组H MT | AUTO_BASE | normal | 407 | 35.995 | 43.294 | 46.038 | 49.144 | 0 |
| 开发组H MT | AUTO_BASE | error | 2 | 1.666 | 2.642 | 2.728 | 2.750 | 0 |
| 开发组H MT | AUTO_BASE | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | AUTO_NEW_SHADOW | all | 409 | 33.012 | 39.189 | 40.491 | 40.919 | 0 |
| 开发组H MT | AUTO_NEW_SHADOW | normal | 407 | 33.009 | 39.160 | 40.492 | 40.919 | 0 |
| 开发组H MT | AUTO_NEW_SHADOW | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | AUTO_NEW_SHADOW | fallback | 2 | 37.219 | 39.717 | 39.939 | 39.995 | 0 |
| 开发组H MT | ANCHOR_NEW_SHADOW | all | 409 | 35.688 | 43.306 | 46.165 | 47.179 | 0 |
| 开发组H MT | ANCHOR_NEW_SHADOW | normal | 409 | 35.688 | 43.306 | 46.165 | 47.179 | 0 |
| 开发组H MT | ANCHOR_NEW_SHADOW | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | ANCHOR_NEW_SHADOW | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | ANCHOR_NEW_VERIFIED | all | 409 | 33.203 | 39.259 | 40.885 | 41.666 | 0 |
| 开发组H MT | ANCHOR_NEW_VERIFIED | normal | 409 | 33.203 | 39.259 | 40.885 | 41.666 | 0 |
| 开发组H MT | ANCHOR_NEW_VERIFIED | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | ANCHOR_NEW_VERIFIED | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | ANCHOR_NO_REFINE | all | 409 | 32.468 | 39.326 | 41.542 | 42.571 | 0 |
| 开发组H MT | ANCHOR_NO_REFINE | normal | 409 | 32.468 | 39.326 | 41.542 | 42.571 | 0 |
| 开发组H MT | ANCHOR_NO_REFINE | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | ANCHOR_NO_REFINE | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | AUTO_OPT | all | 409 | 33.011 | 39.499 | 40.806 | 41.585 | 0 |
| 开发组H MT | AUTO_OPT | normal | 379 | 32.878 | 39.335 | 40.820 | 41.585 | 0 |
| 开发组H MT | AUTO_OPT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | AUTO_OPT | fallback | 30 | 35.950 | 40.256 | 40.318 | 40.322 | 0 |
| 开发组H MT | COMPAT_ANCHOR | all | 409 | 35.851 | 43.172 | 45.448 | 46.971 | 0 |
| 开发组H MT | COMPAT_ANCHOR | normal | 409 | 35.851 | 43.172 | 45.448 | 46.971 | 0 |
| 开发组H MT | COMPAT_ANCHOR | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | COMPAT_ANCHOR | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | AUTO_REPORT_REPLAY | all | 409 | 31.034 | 37.385 | 38.801 | 39.595 | 0 |
| 开发组H MT | AUTO_REPORT_REPLAY | normal | 404 | 31.033 | 37.231 | 38.552 | 39.595 | 0 |
| 开发组H MT | AUTO_REPORT_REPLAY | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | AUTO_REPORT_REPLAY | fallback | 5 | 34.443 | 38.762 | 38.810 | 38.823 | 0 |
| 开发组H MT | AUTO_DEFAULT_COMPAT | all | 409 | 35.890 | 43.190 | 47.137 | 48.550 | 0 |
| 开发组H MT | AUTO_DEFAULT_COMPAT | normal | 407 | 35.897 | 43.196 | 47.145 | 48.550 | 0 |
| 开发组H MT | AUTO_DEFAULT_COMPAT | error | 2 | 0.456 | 0.474 | 0.476 | 0.476 | 0 |
| 开发组H MT | AUTO_DEFAULT_COMPAT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | ANCHOR_RIGID_EXPERIMENT | all | 409 | 32.640 | 39.248 | 41.431 | 42.234 | 0 |
| 开发组H MT | ANCHOR_RIGID_EXPERIMENT | normal | 409 | 32.640 | 39.248 | 41.431 | 42.234 | 0 |
| 开发组H MT | ANCHOR_RIGID_EXPERIMENT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | ANCHOR_RIGID_EXPERIMENT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | ANCHOR_GEOMETRY_ONLY | all | 409 | 35.961 | 43.745 | 49.452 | 51.914 | 0 |
| 开发组H MT | ANCHOR_GEOMETRY_ONLY | normal | 409 | 35.961 | 43.745 | 49.452 | 51.914 | 0 |
| 开发组H MT | ANCHOR_GEOMETRY_ONLY | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | ANCHOR_GEOMETRY_ONLY | fallback | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | ANCHOR_OPT | all | 409 | 36.096 | 42.912 | 44.648 | 47.948 | 0 |
| 开发组H MT | ANCHOR_OPT | normal | 409 | 36.096 | 42.912 | 44.648 | 47.948 | 0 |
| 开发组H MT | ANCHOR_OPT | error | 0 | N/A | N/A | N/A | N/A | 0 |
| 开发组H MT | ANCHOR_OPT | fallback | 0 | N/A | N/A | N/A | N/A | 0 |

## 分离的附加成本

| 组别 | LastJson P95 ms | CopyPath P95 ms | Quality查询P95 ms | 可视化读图解码P95 ms | 双画面绘图P95 ms | 3视频编码管道累计等待s |
| --- | --- | --- | --- | --- | --- | --- |
| 开发组A | 1.023 | 0.009 | 0.036 | 35.021 | 90.969 | 6.089 |
| 验证组C | 0.626 | 0.005 | 0.031 | 156.613 | 73.485 | 4.536 |
| CT2 | 1.921 | 0.011 | 0.039 | 159.688 | 80.171 | 4.180 |
| 开发组H MT | 1.424 | 0.010 | 0.038 | 59.102 | 136.900 | 3.455 |

JSON数值为原生序列化加返回文本复制，不含Python解析；编码为写入管道背压与结束等待，和工作线程计算存在重叠，不是独立CPU时间。视频绘图/编码阶段未用于检测计时。逐帧原始记录包含init、core/api、Process外层、回退标志。
