# 性能范围

A_native_replay.csv: 3029个当前帧，预解码全序列，计Process+GetResultV2+CopyPath和必要分配；不计图像读盘/JSON/媒体/Python。4线程OpenCV4.4，采集/解码/队列和总延时未验证；部分运行期间有研究脚本并发，属于本次机器实测，不是调度保证。

C2_python_per_frame.csv为Python参考实现额外全流程计时，不能据此声明C++15Hz。效果gate未过，按文档禁止开发C2原生核心；CPP_C2_NOT_BUILT。峰值内存见A_peak_memory.csv（包含整段预解码），不等于流式常驻内存。
