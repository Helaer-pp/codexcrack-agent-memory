# 长度与统计分母补充

本导出仅从已经锁定算法输出的缓存路径计算预注册的水平投影、物理轴投影和有序弧长，没有更改原始数值、确认状态、评分或 DEV 选择。原始逐帧配对 CSV 不覆盖。

真实 A0/F0 的原生起点不保证是同一物理点：同时保留 declared_root、实际 path_start、根部间隙、common_program_root。共同根部仅用于统一几何投影，无法凭它验证物理根部或补齐弧长。未确认用 null，不把根部占位/0 当测量。

合成总体报告主表按右侧比较。tip_and_length_metrics.csv 的 stratum=ALL 对各版本包含其可用方向，Frangi 的额外左侧不与单向 A 混作同一分母；做严格横向比较请取 stratum=side/value=right。分层、逐样本 side 与程序 GT 始终保留。配对区间按相同 case/frame/side 连接，算法对照名 left/right 是对照/处理版本，不是物理左/右裂纹。
