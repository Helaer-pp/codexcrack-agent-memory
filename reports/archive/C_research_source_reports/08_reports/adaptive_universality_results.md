# 自适应与普适性

同一全局P配置运行26类受控场景及6组已曝光真实数据；没有试件名/路径/帧号/GT条件分支。38项合同测试含元数据改名不变、GRAY8/16显式编码、尺度/噪声趋势、光度失败UNKNOWN、坐标回投、root/path可选及C_BASE/C_TIP共享搜索图。

C_BASE为新研究系统的基线，A0为完整冻结原生系统；A内部ROI/响应没有被无损注入替换，A↔C是系统级对照。C_ROI/C_SCALE/C_NOISE/C_PHOTO/C_TIP均相对C_BASE只启用对应开关；其中C_TIP与C_BASE同搜索图/响应/尺度/噪声，尖端定位机制单独改变。C_FULL联合全部，不能把其收益归于某一模块。

真实A的clean/auto参考模式沿用原归档，以确保原始结果完全复现（开发组A/验证组C/开发组Hclean，CT2/排除组X/三点弯auto）；这不是本轮用真实结果选择的参数。C自身所有组使用同一P规则。受控DEV/TEST的A统一auto，16位按固定round(code/257)适配；原生A内部逻辑没有改动。

全局动态ROI由标距、路径/新种子及前方余量确定，最多一次更新、有空间/像素上限；尺度由剖面FWHM估计三尺度并真正参与响应；噪声由稳定材料高通MAD及量化下限确定；光度用稳健仿射FIT及独立HOLDOUT验证。所有实际参数、角点、采样步长、扩域原因和UNKNOWN状态见adaptive_params_per_frame.csv；数值常量审计见adaptive_policy.yaml及01_audit/all_numeric_literals.csv。

新TEST采用新种子、新背景随机过程、新分辨率，尺度/运动参数独立抽样但支持区间部分重叠；data_split_manifest.json最初24族草稿不代表最终26族，最终actual_data_split_manifest.json及冻结manifest列明。不是全新物理材质验证。

可以统一执行，但不等于统一可靠：C_FULL覆盖下降、保护失败、ROI反事实不稳定，不能宣称已具备跨材料精度泛化。饱和、极弱线、宽度快速变化、强表面纹理、急弯/多分叉和局部非刚性运动仍是限制。

真实状态变化（不含参考；坐标接近/改变均非精度证据）：

|dataset_alias|algorithm|current_frames|tip_confirmed|root_valid|path_valid|A_valid_C_invalid|A_invalid_C_valid|coordinate_change_gt8|
|---|---|---|---|---|---|---|---|---|
|group_a|A0|550|497|499|496|0|0|0|
|group_a|C_FULL|550|306|499|296|198|7|16|
|group_c|A0|561|543|546|543|0|0|0|
|group_c|C_FULL|561|289|546|245|263|9|81|
|ct2|A0|467|403|467|403|0|0|0|
|ct2|C_FULL|467|134|467|133|297|28|45|
|group_h|A0|409|345|358|344|0|0|0|
|group_h|C_FULL|409|358|358|89|44|57|242|
|group_x|A0|523|269|480|263|0|0|0|
|group_x|C_FULL|523|252|480|174|141|124|70|
|three_point_bend|A0|519|445|448|428|0|0|0|
|three_point_bend|C_FULL|519|113|448|104|341|9|32|

