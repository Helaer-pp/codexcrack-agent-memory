# 驻留内存算法计算耗时

## 测量方法

Ryzen9 7950X，64GB RAM，Windows x64，C++17 Release v142 /O2 /fp:precise，严格链接 D:/opencv-4.4.0/build。4个OpenCV线程，生产DLL关闭profiling及调试采集。最终DLL与本报告 environment.json 的hash一致。

逐组将**整组全部图像解码并常驻内存**，然后才开始计时。开发组A约1.97GiB，验证组C13.72GiB、CT2 11.43GiB、开发组H2.74GiB。独立实例预热10帧后丢弃，再建立真实序列实例。5个版本在同一帧交替顺序调用，实例各自保持真实时序：旧默认、新默认、新实验244、旧Verified、新实验Verified。

当前帧全部计入统计，包括第一当前帧、错误与fallback，不剔除最坏帧。参考查询/初始化单列，不混入15Hz当前帧考核。外部计时只包围准备好输入结构之后的一次原生CrackV4Process；包括输入验证、配准、seed、tile/DP、审计、时序和结果填充。**不含读取/解码、JSON查询/解析、CopyPath、绘图、写盘和相机UI等待**。LastJson/CopyPath另外测量。

## 全部当前帧C API调用，ms

| 组别 | 版本 | n | P50 | P95 | P99 | Max | >66.67ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 开发组A测试-1 | old_default | 550 | 8.039 | 9.810 | 11.317 | 12.248 | 0 |
| 开发组A测试-1 | new_default | 550 | 7.904 | 10.106 | 11.327 | 12.802 | 0 |
| 开发组A测试-1 | new_experiments | 550 | 7.889 | 10.190 | 11.701 | 13.263 | 0 |
| 开发组A测试-1 | old_verified | 550 | 7.886 | 10.330 | 11.755 | 12.758 | 0 |
| 开发组A测试-1 | new_verified | 550 | 7.921 | 10.155 | 11.542 | 12.148 | 0 |
| 验证组C | old_default | 561 | 4.302 | 5.725 | 6.182 | 6.869 | 0 |
| 验证组C | new_default | 561 | 4.262 | 5.622 | 6.228 | 7.958 | 0 |
| 验证组C | new_experiments | 561 | 4.261 | 5.665 | 6.130 | 6.804 | 0 |
| 验证组C | old_verified | 561 | 4.277 | 5.487 | 6.147 | 6.845 | 0 |
| 验证组C | new_verified | 561 | 4.278 | 5.513 | 6.257 | 6.696 | 0 |
| CT2 | old_default | 467 | 16.173 | 21.906 | 25.045 | 28.744 | 0 |
| CT2 | new_default | 467 | 15.920 | 21.851 | 25.483 | 28.633 | 0 |
| CT2 | new_experiments | 467 | 16.184 | 21.802 | 24.215 | 28.862 | 0 |
| CT2 | old_verified | 467 | 15.806 | 22.238 | 25.226 | 28.022 | 0 |
| CT2 | new_verified | 467 | 16.314 | 22.020 | 25.202 | 27.722 | 0 |
| 开发组HMT | old_default | 409 | 33.492 | 40.493 | 44.220 | 48.233 | 0 |
| 开发组HMT | new_default | 409 | 33.449 | 40.971 | 44.547 | 53.358 | 0 |
| 开发组HMT | new_experiments | 409 | 33.521 | 40.705 | 45.477 | 52.846 | 0 |
| 开发组HMT | old_verified | 409 | 33.577 | 40.451 | 43.143 | 47.968 | 0 |
| 开发组HMT | new_verified | 409 | 33.578 | 40.761 | 43.179 | 44.144 | 0 |

同条件旧默认与新默认/实验相近，没有实证支持显著加速的说法。当前四组、当前机器的生产调用均在15Hz预算内；开发组H实验P95<=55、P99<=60的暂定目标也通过。该结果不保证其他分辨率/间距或系统负载下的硬实时，不代表采集/显示整体15Hz。

## 正常、错误、恢复帧分开

| 组别 | 版本 | 分组 | n | P50 | P95 | P99 | Max | 超预算 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CT2 | old_default | normal | 440 | 16.347 | 21.929 | 25.162 | 28.744 | 0 |
| CT2 | old_default | error | 27 | 0.568 | 0.747 | 0.764 | 0.765 | 0 |
| CT2 | old_default | fallback | 0 | n.a. | n.a. | n.a. | n.a. | 0 |
| CT2 | new_default | normal | 440 | 16.166 | 21.891 | 25.495 | 28.633 | 0 |
| CT2 | new_default | error | 27 | 0.568 | 0.837 | 1.206 | 1.325 | 0 |
| CT2 | new_default | fallback | 0 | n.a. | n.a. | n.a. | n.a. | 0 |
| CT2 | new_experiments | normal | 440 | 16.028 | 21.817 | 24.308 | 28.862 | 0 |
| CT2 | new_experiments | error | 0 | n.a. | n.a. | n.a. | n.a. | 0 |
| CT2 | new_experiments | fallback | 27 | 18.539 | 21.492 | 22.127 | 22.277 | 0 |
| CT2 | new_verified | normal | 440 | 16.229 | 22.196 | 25.229 | 27.722 | 0 |
| CT2 | new_verified | error | 0 | n.a. | n.a. | n.a. | n.a. | 0 |
| CT2 | new_verified | fallback | 27 | 18.729 | 21.276 | 21.592 | 21.685 | 0 |
| 开发组HMT | old_default | normal | 404 | 33.526 | 40.515 | 44.233 | 48.233 | 0 |
| 开发组HMT | old_default | error | 5 | 0.430 | 0.547 | 0.552 | 0.554 | 0 |
| 开发组HMT | old_default | fallback | 0 | n.a. | n.a. | n.a. | n.a. | 0 |
| 开发组HMT | new_default | normal | 404 | 33.459 | 40.998 | 44.566 | 53.358 | 0 |
| 开发组HMT | new_default | error | 5 | 0.402 | 0.590 | 0.618 | 0.626 | 0 |
| 开发组HMT | new_default | fallback | 0 | n.a. | n.a. | n.a. | n.a. | 0 |
| 开发组HMT | new_experiments | normal | 404 | 33.492 | 40.666 | 45.585 | 52.846 | 0 |
| 开发组HMT | new_experiments | error | 0 | n.a. | n.a. | n.a. | n.a. | 0 |
| 开发组HMT | new_experiments | fallback | 5 | 37.475 | 40.751 | 40.761 | 40.764 | 0 |
| 开发组HMT | new_verified | normal | 404 | 33.573 | 40.537 | 43.068 | 44.144 | 0 |
| 开发组HMT | new_verified | error | 0 | n.a. | n.a. | n.a. | n.a. | 0 |
| 开发组HMT | new_verified | fallback | 5 | 40.065 | 43.148 | 43.510 | 43.601 | 0 |

额外有界失败恢复压力场景（合成修改真实CT2：第一个标记仍可匹配、第二个标记被抹除，再尝试4个弱背景块）预热10次后128次驻留调用，均返回失败且未确认。P50=5.341、P95=6.378、P99=6.483、Max=7.362ms，超预算0。这是失败路径成本测试，不是新增真实样本。

恢复次数硬上限为两处标记加4处背景块，搜索半径64px。没有全图ECC/仿射或全图多尺度。正常帧不做这些模板补搜。没有依赖历史变换的无条件确认。

## 附加接口

| 组别 | 版本 | LastJson P95 | Max | CopyPath P95 | Max |
| --- | --- | --- | --- | --- | --- |
| 开发组A测试-1 | new_default | 1.0364 | 1.3507 | 0.0087 | 0.0162 |
| 开发组A测试-1 | new_experiments | 0.9870 | 1.3319 | 0.0084 | 0.0209 |
| 验证组C | new_default | 0.6977 | 0.8925 | 0.0068 | 0.0206 |
| 验证组C | new_experiments | 0.6973 | 0.9749 | 0.0068 | 0.0105 |
| CT2 | new_default | 2.1378 | 3.5171 | 0.0109 | 0.0179 |
| CT2 | new_experiments | 2.1861 | 3.2134 | 0.0110 | 0.0833 |
| 开发组HMT | new_default | 1.4527 | 2.5953 | 0.0106 | 0.0227 |
| 开发组HMT | new_experiments | 1.4600 | 2.5311 | 0.0099 | 0.0170 |

LastJson计时包含C++序列化和ctypes返回字节复制，不含后续json.loads；CopyPath有足够预分配缓冲区。扩展质量查询的逐帧耗时另在 timing.json，包含Python JSON解析，不混入上表或生产调用。生产若使用这些附加接口，应另外加上相应成本。

## 分阶段profiling

独立instrumented构建，仅分析代表帧（含异常/恢复），不能拿该构建数字充当主性能结果。`stage_profile.json`含16槽，motion / seed inclusive / tile inclusive / seed DP / extension DP / measure / median / percentile / tile各子阶段 / terminal audit。包含嵌套，不能把16槽直接相加。采样/局部统计/DP仍是大间距图像的主要成本，没有证据支持本轮再做全量FastTrack重构。

主数据：`results/resident_final/<dataset>/*_timing.json`，所有每帧状态与fallback标记保留；summary.json提供all/normal/error/fallback的core/api/call及附加接口统计；environment.json记录hash、线程与测量口径。
