# 源码合同审计（实现前）

所有行号为本轮校验通过的实际源码。冻结 DLL 的 flags=3572、policy=1(SHADOW)、terminal_validation=1、refine=true、4线程；灰度8传入，16位固定除257四舍五入。SHADOW 输出仍遵循原A，不擅自改为VERIFIED。

## A
`crack_v4_cpp/frozen_dp_tip_20261030/baseline/src/CrackV4.cpp`：797–939 两点刚体初值/原生refine；1015 refineRoot独立保留；1516–1535前缀历史关联不是端点精度证明；1636–1725取路停止，evidence_ended才是legacy尖端，1709边界审查。1729–1782终点审计/历史/原坐标输出。1789–1893 terminalAudit使用路径质量、tail、forward continuation与历史端点，仅VERIFIED policy覆盖legacy输出。2055–2095 Process推进历史，2100 GetBaseline纯缓存查询，2116 CopyPath返回double原图路径，2145 GetResultV2来自d.last；GetBaseline不会让LastJson切换为reference_result，调用次序必须完整复现。r.length是root/path完整长度合同，C2 tip不依赖它。原A材料根部与本轮P1/P2投影零基线分开。

## 旧 C 的候选与确认
`旧02_source/research_c.py:22–41` A raw_path若可用沿用，否则anchor band DP；动态ROI与宽度/噪声重估后可重新search。C_BASE固定width/noise/ROI且localize关闭，C_FULL五模块开启；二者不是A内部单一模块消融。
`candidate_search.py:7–12` resample最多1800点：长路径和延伸后会改变实际步长。`adaptive_roi.py:22–25` ROI本身按最坏域固定sample_step；扩ROI改变tile背景分布→MAD噪声，可能重估width/重search；`tip_localization.py:15–20` 审核窗n按中位路径步长换算，候选与reference/support再受重采样影响；同cap不等于同像素。margin_ok也直接读取SearchROI；旧反事实非纯审核解耦实验。
`tip_localization.py:58–71` supported是before>=4、heldout>=4、after<=3、drop>=3、无forward competition、margin和origin的逻辑与。`tip_validation.py:4–13` 有多个supported且rank差<2就拒绝；没有supported依次优先报告margin、continue、no_supported。因此reason是优先级汇总，不是唯一失败条件。完整逐候选故障表附CSV。

## reference_ratio 与光度
`tip_localization.py:34–56` 先将已法向重定位当前路径按两点刚体逆变换到reference（不含原A内部refine），对参考同路径profile的所有法向offset取最大valley/noise，再取候选前n点中位数，除以当前before中位数。大值表示参考邻域也有暗线响应，不能等价“非裂纹”或差分为零；此比值既不乘photo_gain也未要求配准验证。>=0.65仅标H_FALSE_BRANCH，不在validate使用。参考已有裂纹和旧划痕都可高；低值也可能错位。
`adaptive_scale_noise_photo.py:64–104` 固定20patch布局；仅20百分位亮材质及梯度下75%，每patch>=35%有效。各>=3个fit/hold patch及128像素；高通phase response>.4至少6patch，center<=1px、P90dispersion<=.75px；gain可辨识std(x)>=noise；4次鲁棒拟合gain[.5,2]且hold90残差<=max(2,3noise)。初值偏移没有修正，超过1px仅拒绝；低纹理高通匹配覆盖不足会阻断。失败分层CSV通过实际保存patch复算；不把UNKNOWN当无变化。

## 范围和统计
旧TEST=234case×6=1404当前帧×8版，C_FULL光度分母1404；真实6组3035含参考，物理GT无。真假尾9共享渲染pair×6=54对帧，不能当108独立case。新评估按共享pair/独立case聚类bootstrap，GT仅评估器读取。两点右法向不根据输出方向反转。旧GT只用于曝光机制复算，不能进入C2运行时。

本文件在C2实现之前写出；旧DLL/源码/媒体只读。新原生重放在独立06_performance输出，逐状态/尖端/长度/double路径比较后才进行研究检测。


旧关键算术均实际复算：157/19、54对帧、0/1404及66/3035通过核对；ROI文档10是损失确认+位移，新增确认8后双向总18。全部旧输入ZIP通过CRC和SHA。
