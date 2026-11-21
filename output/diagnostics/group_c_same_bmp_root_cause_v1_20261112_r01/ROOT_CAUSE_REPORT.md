# 验证组C同一BMP：冻结V1根因复盘

## 一句话结论

**已证实：正式P点让起始列由2265移到2255；在这个新首列，参考差分抑制了current首选候选，单列联合排序转而锁到y=2282，±7px局部追踪无法接入相隔69px的另一候选，最终21列缺失停止。原因是几何、参考证据与贪心初始化的耦合，不是单纯“P点不同”或“gap_limit”。材料物理配准失真仅有局部支持，正式点物理语义是否相同仍未解决。**

2026-11-12，已曝光回归/验证案例故障审计，非V2开发、盲测、训练或参数优化。本轮所有检测阈值保持冻结，未把验证组C的较好分支或扰动值选作新默认。生产A、冻结Python、C++ DLL与旧评估不改。图中端点均为provisional，不能当独立物理确认。

## 1. 同图同代码与真实P点身份

两张BMP均5120×5120、8-bit、无压缩、正高度bottom-up存储；解码后uint8。文件SHA、ASCII中转SHA、OpenCV imdecode与冻结imread结果、Pillow转灰度全部一致，无EXIF方向信息。没有重编码、缩放或GT裁切。当前`3 (175).bmp`在正式序列是frame_id=237，对应原始TXT num236；参考是frame1/num0，不把文件名175当全局序号。

冻结Python SHA256 `2e2e5ebef80ab33e486c561b6dec09ee15d23033020cc1886a7de24c7ce2baf6`，当前仍精确匹配任务书。真实原始跟踪源为`.\data\anchors\验证组C_基准点坐标.txt`，SHA `1d50f07af5032707dd006943b60023987c4afdba8da3c4c494d692dc1bd251fc`；原始num0/236行已存[tracking_source_records.txt](tracking_source_records.txt)。点以十进制原精度传入，没有预取整。黄金参考点还核对了冻结源码默认常量；黄金当前点经本轮原始CLI NCC重跑精确复现。完整[输入身份核验](input_identity_audit.md)、[机器记录](input_provenance.csv)。

| 点集 | P1 | P2 | 来源 |
|---|---|---|---|
| R_G | [2243.75, 2247.5] | [2260.0, 2431.25] | task frozen reference defaults |
| C_G | [2242.75, 2252.5] | [2259.0, 2435.25] | saved original NCC; independently rerun exact |
| R_S | [2248.46, 2250.77] | [2244.49, 2439.53] | original tracking TXT num record |
| C_S | [2248.22, 2256.98] | [2243.74, 2442.37] | original tracking TXT num record |


S−G四点差：

| 参考/当前 | 点 | S−G dx | S−G dy |
|---|---|---|---|
| R | 1 | 4.71000 | 3.27000 |
| R | 2 | -15.51000 | 8.28000 |
| C | 1 | 5.47000 | 4.48000 |
| C | 2 | -15.26000 | 7.12000 |


当前中点从(2250.875,2343.875)到(2245.98,2349.675)，y相差5.8px；x右端2259→2248.22，ceil后2259→2249。参考上下间距183.75→188.76，当前上下间距182.75→185.39。当前P2的x差−15.26px，不能把这四点输入差异笼统说成全部是“小数误差”。

## 2. A/B/C/D真实执行结果

A=R_G/C_G；B=R_G/C_S；C=R_S/C_G；D=R_S/C_S。四组均先独立原始Python CLI，再只读观察器执行。每组六行summary和六份逐列trace与未观察CLI完全相同，overlay解码像素也完全相同。A六档与旧黄金记录逐列相同，D六档与旧正式237帧逐列相同；两个重放Gate均通过。

| 原生实验 | 分支 | T | 暂定端点 | 近似锚点误差(px) | y0 | 首观测 | 有效观测/访问列 | 末访问x/最大缺失 |
|---|---|---|---|---|---|---|---|---|
| A | joint | 8 | [2424.0, 2344.0] | 1.00000 | 2332 | [2265, 2332] | 160/181 | 2445/21 |
| A | joint | 10 | [2423.0, 2344.0] | 0.00000 | 2332 | [2265, 2332] | 156/180 | 2444/21 |
| A | joint | 12 | [2418.0, 2345.0] | 5.09902 | 2332 | [2265, 2332] | 154/175 | 2439/21 |
| A | current | 8 | [2282.0, 2316.0] | 143.75326 | 2308 | [2265, 2308] | 10/39 | 2303/21 |
| A | current | 10 | [2285.0, 2307.0] | 142.87407 | 2308 | [2265, 2308] | 10/42 | 2306/21 |
| A | current | 12 | [2268.0, 2304.0] | 160.07811 | 2308 | [2265, 2308] | 4/25 | 2289/21 |
| B | joint | 8 | [2277.0, 2347.0] | 146.03082 | 2351 | [2255, 2351] | 21/44 | 2298/21 |
| B | joint | 10 | [2424.0, 2344.0] | 1.00000 | 2351 | [2255, 2351] | 161/191 | 2445/21 |
| B | joint | 12 | [2423.0, 2344.0] | 0.00000 | 2351 | [2255, 2351] | 159/190 | 2444/21 |
| B | current | 8 | [2425.0, 2344.0] | 2.00000 | 2351 | [2255, 2351] | 171/192 | 2446/21 |
| B | current | 10 | [2424.0, 2344.0] | 1.00000 | 2351 | [2255, 2351] | 170/191 | 2445/21 |
| B | current | 12 | [2423.0, 2344.0] | 0.00000 | 2351 | [2255, 2351] | 169/190 | 2444/21 |
| C | joint | 8 | [2424.0, 2344.0] | 1.00000 | 2332 | [2265, 2332] | 158/181 | 2445/21 |
| C | joint | 10 | [2423.0, 2344.0] | 0.00000 | 2332 | [2265, 2332] | 152/180 | 2444/21 |
| C | joint | 12 | [2414.0, 2345.0] | 9.05539 | 2332 | [2265, 2332] | 149/171 | 2435/21 |
| C | current | 8 | [2282.0, 2316.0] | 143.75326 | 2308 | [2265, 2308] | 10/39 | 2303/21 |
| C | current | 10 | [2285.0, 2307.0] | 142.87407 | 2308 | [2265, 2308] | 10/42 | 2306/21 |
| C | current | 12 | [2268.0, 2304.0] | 160.07811 | 2308 | [2265, 2308] | 4/25 | 2289/21 |
| D | joint | 8 | [2255.0, 2282.0] | 179.07540 | 2282 | [2255, 2282] | 1/22 | 2276/21 |
| D | joint | 10 | [2255.0, 2282.0] | 179.07540 | 2282 | [2255, 2282] | 1/22 | 2276/21 |
| D | joint | 12 | [2255.0, 2282.0] | 179.07540 | 2282 | [2255, 2282] | 1/22 | 2276/21 |
| D | current | 8 | [2425.0, 2344.0] | 2.00000 | 2351 | [2255, 2351] | 171/192 | 2446/21 |
| D | current | 10 | [2424.0, 2344.0] | 1.00000 | 2351 | [2255, 2351] | 170/191 | 2445/21 |
| D | current | 12 | [2423.0, 2344.0] | 0.00000 | 2351 | [2255, 2351] | 169/190 | 2444/21 |


上表误差只相对任务书的**近似回归锚点**(2423,2344)，不是为237帧新增的LabelMe真值；该BMP不在旧20个可见选帧中，不能拿A/D结果直接解释“20帧中0命中”的统计分母。其他4个代表帧另用真实人工标签评分。B的joint T8也失败，所有档位照实保留，不能只展示B的T10成功。

| 案例 | xleft / xr | upper / lower | xstart | ctr | joint y0 / current y0 | 位移P1 / P2 |
|---|---|---|---|---|---|---|
| A | 2259 / 4338 | 2253 / 2435 | 2265 | 2343.875 | 2332/2308 | [[-1.0, 5.0], [-1.0, 4.0]] |
| B | 2249 / 4339 | 2257 / 2442 | 2255 | 2349.675 | 2351/2351 | [[4.4699999999998, 9.480000000000018], [-16.26000000000022, 11.11999999999989]] |
| C | 2259 / 4338 | 2253 / 2435 | 2265 | 2343.875 | 2332/2308 | [[-5.710000000000036, 1.7300000000000182], [14.510000000000218, -4.2800000000002]] |
| D | 2249 / 4339 | 2257 / 2442 | 2255 | 2349.675 | 2282/2351 | [[-0.24000000000023647, 6.210000000000036], [-0.75, 2.8399999999996908]] |


只替换当前点的B、只替换参考点的C在T10仍到达近似端点；这排除了“任一套S点单独出现就必然失败”的解释。B/C轨迹与A并非全部相同：端点近似相同不能代替逐列一致性。

## 3. 第一条决定路线的离散决策

第一条路线决定就是首列的argmax。A在x2265选y2332；D在x2255选y2282。因为起始x也不同，不能把两条trace第0行称为同一列。D相对自己current分支（同几何、同当前灰度）则是同一x2255上的y2282与y2351之争。

| 案例 | x | y | valley | newdark | 材料通过 | prior | 联合加权分数 | rank | joint T10通过 |
|---|---|---|---|---|---|---|---|---|---|
| A | 2265 | 2332 | 53.24405 | 58.20042 | True | 0.96056 | 53.47162 | 1 | True |
| B | 2255 | 2351 | 27.39870 | 57.68085 | True | 0.99952 | 39.73472 | 1 | True |
| C | 2265 | 2332 | 53.24405 | 53.72704 | True | 0.96056 | 51.37558 | 1 | True |
| D | 2255 | 2282 | 16.03516 | 20.42429 | True | 0.28229 | 5.10866 | 1 | True |
| D | 2255 | 2351 | 27.39870 | -5.24261 | True | 0.99952 | 0.00000 | 123 | False |


在D，y2351的材料门通过、valley=27.3987、prior=0.999515，本来是current首选；但newdark=−5.242615，使联合score及加权分数为0，且必定不满足newdark≥10。y2282的valley=16.0352、newdark=20.4243、prior=0.282291，加权得分5.108664，为唯一第一名，也通过两个灰度阈值。第二名y2387得4.103677，差1.004987；D有37个非零初始化分数，**不是全零argmax或近乎机器精度tie导致本帧错误**。

D只有首列一次有效观测(2255,2282)。后续预测中心一直2282，未获得5个观测启动方向拟合；搜索大致y2275…2289。它与current首选的纵距69px、与A首观测纵距50px，均远大于7px半宽。在共同x2265，A选2332且accept=True，D选2279但accept=False，missing_run已经10。D在x2276累计21列缺失退出，最终tip保留最后有效像素2255,2282。`gap_limit`是这一错误起源之后的停止现象，不是最初原因。

| 对照 | 分歧层 | 首个共同x | A值 | 另一值 |
|---|---|---|---|---|
| A vs B | joint_first_shared_x_selected_y | 2265 | 2332 | 2342 |
| A vs B | joint_first_shared_x_is_observed | 2274 | True | False |
| A vs B | joint_first_shared_x_missing_run | 2274 | 0 | 1 |
| A vs C | joint_first_shared_x_selected_y | 2341 | 2339 | 2340 |
| A vs C | joint_first_shared_x_is_observed | 2416 | True | False |
| A vs C | joint_first_shared_x_missing_run | 2416 | 0 | 1 |
| A vs D | joint_first_shared_x_selected_y | 2265 | 2332 | 2279 |
| A vs D | joint_first_shared_x_is_observed | 2265 | True | False |
| A vs D | joint_first_shared_x_missing_run | 2265 | 0 | 10 |


完整首列逐y分数/排名/材料/阈值状态见[initial_candidate_audit.csv](initial_candidate_audit.csv)；真实被采样的每列全部y候选与merit在各runs目录`column_candidates.csv`，可在[交互逐列查看器](trace_audit_A_B_C_D.html)切换case/mode/x。首30列单独导出[first_30_columns.csv](first_30_columns.csv)。数组比较使用共同原图坐标并分别统计1e-6、0.1和1灰度差阈值，未把光栅扫描遇到的第一个浮点差当根因。共同实际采样ROI内ca/csm/valley/flank_low/valid_material全相同，见[current_evidence_common_ROI_gate.csv](current_evidence_common_ROI_gate.csv)；整裁剪边缘的np.roll/平滑差别不冒充首列决策原因。

## 4. 几何与参考的两因素控制

以下均标记**诊断反事实，不是原生V1结果或新算法精度**。保留几何组的当前图裁剪、ROI、ctr、候选边界及当前证据，仅在参考remap前替换alpha/dx/dy为供体A或D的原公式值。不同几何网格需要在其坐标上计算同一个供体位移函数；共同全局坐标上的alpha/dx/dy/reference_aligned逐像素完全相同，并非用GT外推。固定几何时ca/csm/valley/flank_low/roi_mask/valid_material均完全一致。

纯A/A与D/D：13种数组各自逐像素相同，所有六模式summary和完整trace相同，证明诊断副本镜像成立。只改诊断副本，原冻结SHA未变。

| 诊断反事实 | 分支 | T | 暂定端点 | y0 | 首观测 | 有效观测/访问列 |
|---|---|---|---|---|---|---|
| 几何A / 位移A | joint | 10 | [2423.0, 2344.0] | 2332 | [2265, 2332] | 156/180 |
| 几何A / 位移A | current | 10 | [2285.0, 2307.0] | 2308 | [2265, 2308] | 10/42 |
| 几何A / 位移D | joint | 10 | [2423.0, 2344.0] | 2332 | [2265, 2332] | 156/180 |
| 几何A / 位移D | current | 10 | [2285.0, 2307.0] | 2308 | [2265, 2308] | 10/42 |
| 几何D / 位移A | joint | 10 | NO_TIP | 2352 | NONE | 0/21 |
| 几何D / 位移A | current | 10 | [2424.0, 2344.0] | 2351 | [2255, 2351] | 170/191 |
| 几何D / 位移D | joint | 10 | [2255.0, 2282.0] | 2282 | [2255, 2282] | 1/22 |
| 几何D / 位移D | current | 10 | [2424.0, 2344.0] | 2351 | [2255, 2351] | 170/191 |


A几何+D位移仍成功，因此“D参考位移场本身足以让所有几何失败”不成立。D几何+A位移已无端点，说明提前10列的几何改变足以让A的原结果丢失；但它并不产生D的同一个错误端点。D几何+D位移才锁y2282。

固定D几何时，A位移场下y2351的newdark=5.155151，虽然使score非零，仍低于T10；初始最高候选为y2352，周围缺少联合合格观测，故NO_TIP。换D位移后y2351变为−5.242615，排序改到69px之外的y2282并接受。**初始化使用连续score×prior，不先强制valley与newdark都≥T；初始化和后续接受是两道不同规则。** 这同时解释“初始分数最高却完全无观测”的反事实。

首1/20/100个固定ROI列（不等同于实际访问长度）、黄金joint轨迹邻域及D current轨迹邻域的材料/暗谷/联合通过率见[reference_evidence_rates.csv](reference_evidence_rates.csv)。固定几何、只换位移的前100列中，A→D的newdark跨阈值降级候选数：A几何10，D几何10；反向升级数量A几何37，D几何34。每个候选的原图坐标和灰度见[reference_threshold_crossings.csv](reference_threshold_crossings.csv)，不是只统计均值。

## 5. 有证据但未采样，与材料物理配准证据等级

| 案例 | 事后区域 | 当前门通过 | joint门通过 | joint通过且实际采样 |
|---|---|---|---|---|
| A | approximate_anchor_3px | 10 | 1 | 1 |
| A | A_joint_observed_trace_3px | 712 | 602 | 590 |
| B | approximate_anchor_3px | 10 | 10 | 10 |
| B | A_joint_observed_trace_3px | 712 | 658 | 551 |
| C | approximate_anchor_3px | 10 | 1 | 1 |
| C | A_joint_observed_trace_3px | 712 | 562 | 557 |
| D | approximate_anchor_3px | 10 | 1 | 0 |
| D | A_joint_observed_trace_3px | 712 | 599 | 0 |


这些邻域在推理完成之后计算：近似锚点来自任务书，A轨迹是计算对照，**不是独立人工完整路径GT**。原始BMP/候选窗口图展示D远处仍有可接受证据，但D短走廊没有到达它；不能因此把观察到的所有暗线都认证为物理裂纹。没有将它们送回检测器重置起点。

在固定、与GT无关的上下材料纹理候选窗独立做±20px NCC，并比较A/D补偿后的NCC和去均值残差。窗口位置只由P几何及事前固定偏移450/850/1250决定，未把独立估计写回V1。

| 材料窗 | 位移场 | 独立匹配NCC | 匹配位移 | 预测位移 | 位移差(px) | 补偿后NCC | 去均值残差RMSE | 可靠性 |
|---|---|---|---|---|---|---|---|---|
| upper_450 | A | 0.92865 | [-1, 5] | [-1.0, 4.830369472503662] | 0.16963 | 0.97086 | 9.24058 | INFORMATIVE |
| upper_450 | D | 0.92865 | [-1, 5] | [-0.31295543909072876, 5.727921962738037] | 1.00095 | 0.96047 | 9.24864 | INFORMATIVE |
| upper_850 | A | 0.64521 | [-1, 5] | [-1.0, 4.830369472503662] | 0.16963 | 0.70845 | 5.14399 | LOW_NCC |
| upper_850 | D | 0.64521 | [-1, 5] | [-0.31295543909072876, 5.727921962738037] | 1.00095 | 0.69506 | 5.12469 | LOW_NCC |
| upper_1250 | A | 0.51944 | [-1, 5] | [-1.0, 4.830369472503662] | 0.16963 | 0.50419 | 5.40694 | LOW_NCC |
| upper_1250 | D | 0.51944 | [-1, 5] | [-0.31295543909072876, 5.727921962738037] | 1.00095 | 0.48509 | 5.20716 | LOW_NCC |
| lower_450 | A | 0.83803 | [-1, 5] | [-1.0, 4.173734664916992] | 0.82627 | 0.85856 | 4.78302 | INFORMATIVE |
| lower_450 | D | 0.83803 | [-1, 5] | [-0.6430703401565552, 3.546574354171753] | 1.49661 | 0.76148 | 6.06918 | INFORMATIVE |
| lower_850 | A | 0.58016 | [-1, 5] | [-1.0, 4.173734664916992] | 0.82627 | 0.58581 | 5.53211 | LOW_NCC |
| lower_850 | D | 0.58016 | [-1, 5] | [-0.6430703401565552, 3.546574354171753] | 1.49661 | 0.62141 | 5.06001 | LOW_NCC |
| lower_1250 | A | 0.74500 | [-1, 5] | [-1.0, 4.173734664916992] | 0.82627 | 0.75543 | 5.10715 | LOW_NCC |
| lower_1250 | D | 0.74500 | [-1, 5] | [-0.6430703401565552, 3.546574354171753] | 1.49661 | 0.79127 | 4.61495 | LOW_NCC |


只有两窗峰值NCC≥0.8，分别0.92865/0.83803；其余四窗为LOW_NCC，不能当可靠位移真值。两个高相关窗均得到整像素位移(−1,5)：A场偏差约0.170/0.826px，D约1.001/1.497px。下侧高相关窗补偿NCC由A0.85856降为D0.76148、去均值RMSE由4.7830升为6.0692；上侧差异较小且MAE与NCC排序不完全一致。加上P点自身NCC与正式当前记录的1.4289/1.1866px差距，**局部支持D粗补偿存在位移不一致，但没有独立稠密变形真值或人工认证无裂纹材料mask，不足以认定整体物理配准失真，更不能将它作为唯一根因。**

## 6. 点语义H4与全零argmax

原始TXT→项目零基frame_id236→正式一基frame237→BMP哈希的映射全部一致，未发现本轮adapter的x/y交换、显示缩放、裁剪坐标或提前取整。对各自参考中心的NCC：G两点相关性0.99405/0.98509，恰好复现C_G；S两点0.99450/0.98492，却得到(2247.46,2255.77)/(2243.49,2443.53)，与正式C_S差1.43/1.19px。这是**记录值与另一个测量器的差异**，不是把正式点判成错误的依据。

G与S的参考中心本身不同，截图红框中心/原点击语义与物理特征定义没有在本次任务书、包、TXT或manifest中提供可核对的原始记录；也没有独立采集同步证据推翻已有num约定。点位图只展示真实数值，不能证明其物理语义相同或不同。H4语义保留UNRESOLVED。

实际首帧1提供全零反例：R=C、零位移，rsm=csm，newdark全零，joint全部初始分数零，np.argmax选择init_ys的第一个y2258，随后21列无观测停止。current仍有暗谷响应。这个真实反例说明全零行为存在，但**不能把它套用到D，D的37个非零分数和唯一winner已直接反证**。见[zero_initialization.png](figures/zero_initialization.png)。

## 7. 预定义输入扰动

在ABCD前保存了[sensitivity_plan.json](sensitivity_plan.json)：A/D各45组（共同y平移7、仅当前11、仅参考11、四个单点分别y±2/±5共16），再加四点A→D插值11，共101组、606模式。单点扰动轴明确为y；x差异包含在真实A/D和四点插值中，没有独立单点x扫描。全部是结构敏感性实验，不是实际追踪误差分布，不选最优参数。所有零扰动和插值端点控制都与原生A/D六模式逐列相同。

A仅当前两点y−4确实得到joint T10=(2285,2307)，复现任务书的待证扰动现象；y−5也如此。参考与当前共同平移的A七档均保持(2423,2344)，D共同平移前六档保持错误端点，+5变NO_TIP。共同平移并不数学上保证所有图像采样不变，原位移函数alpha还依赖当前P的y，这里只报告实测稳定/不稳定。

| t | joint T10端点 | y0 | 首观测 |
|---|---|---|---|
| 0.0 | [2423.0, 2344.0] | 2332 | [2265, 2332] |
| 0.1 | [2423.0, 2344.0] | 2332 | [2264, 2332] |
| 0.2 | [2423.0, 2344.0] | 2333 | [2262, 2333] |
| 0.3 | [2423.0, 2344.0] | 2334 | [2261, 2334] |
| 0.4 | [2423.0, 2344.0] | 2334 | [2259, 2334] |
| 0.5 | [2423.0, 2344.0] | 2336 | [2259, 2334] |
| 0.6 | [2423.0, 2344.0] | 2340 | [2259, 2334] |
| 0.7 | [2255.0, 2282.0] | 2282 | [2255, 2282] |
| 0.8 | NO_TIP | 2353 | NONE |
| 0.9 | [2255.0, 2282.0] | 2283 | [2254, 2283] |
| 1.0 | [2255.0, 2282.0] | 2282 | [2255, 2282] |


从t0.6的正确近似端点到t0.7的错误端点是**预定0.1采样网格上**第一次终点大跃迁，不能声称精确临界值就是0.7；未追加细化搜索。t0.8无输出同样保留。所有点、y0、首观测、首次共同x分歧、首次无支持位置和六模式端点见[point_sensitivity.csv](point_sensitivity.csv)。首次失败原因字段只描述所选被拒像素，不冒充全部候选的物理因果。

## 8. 同组其他帧：复用机制及不同机制

237不属于既有20个LabelMe选帧，因此额外选择4个不同VISIBLE帧38、1、232、7，均按原追踪点真正同输入回放，并与旧六模式trace完全一致。选择来自旧报告预先确定的分歧/无输出/远错误类别，不改变推理。标签只在全部ABCD、控制、101扰动和代表帧推理完成后用于离线评分。

| 帧 | 分支T10 | 端点 | 人工误差(px) | y0 | 联合与current初始化距离 | current首选newdark | 证据标签 |
|---|---|---|---|---|---|---|---|
| 38 | joint | NO_TIP | 未标注/无端点 | 2384 | 36 | -9.470443725585938 | ["MULTIFACTOR", "ROI/INIT_GEOMETRY", "REFERENCE_REMAP/DELTA_VETO"] |
| 38 | current | [2296.0, 2330.0] | 6.67868 | 2348 | 0 | -9.470443725585938 | ["WITHIN_10_PROVISIONAL"] |
| 1 | joint | NO_TIP | 未标注/无端点 | 2258 | 89 | 0.0 | ["MULTIFACTOR", "ROI/INIT_GEOMETRY", "REFERENCE_REMAP/DELTA_VETO"] |
| 1 | current | [2298.0, 2331.0] | 22.75701 | 2347 | 0 | 0.0 | ["ROI/INIT_GEOMETRY", "UNRESOLVED"] |
| 232 | joint | [2255.0, 2283.0] | 176.01403 | 2283 | 69 | -1.5190277099609375 | ["MULTIFACTOR", "ROI/INIT_GEOMETRY", "REFERENCE_REMAP/DELTA_VETO"] |
| 232 | current | [2420.0, 2345.0] | 0.71429 | 2352 | 0 | -1.5190277099609375 | ["WITHIN_10_PROVISIONAL"] |
| 7 | joint | NO_TIP | 未标注/无端点 | 2368 | 20 | -6.303375244140625 | ["MULTIFACTOR", "ROI/INIT_GEOMETRY", "REFERENCE_REMAP/DELTA_VETO"] |
| 7 | current | [2284.0, 2328.0] | 16.14455 | 2348 | 0 | -6.303375244140625 | ["ROI/INIT_GEOMETRY", "UNRESOLVED"] |
| 237 | joint | [2255.0, 2282.0] | 未标注/无端点 | 2282 | N/A | N/A | ["MULTIFACTOR", "ROI/INIT_GEOMETRY", "REFERENCE_REMAP/DELTA_VETO"] |
| 237 | current | [2424.0, 2344.0] | 未标注/无端点 | 2351 | N/A | N/A | ["MULTIFACTOR", "ROI/INIT_GEOMETRY", "REFERENCE_REMAP/DELTA_VETO"] |


帧232与D最相近：joint首列选y2283、current首选y2352，差69px；current候选newdark=−1.519，joint错误约176.01px，current约0.714px。38/7也有排序抑制，分别偏离current首选36/20px，但联合winner的newdark仅3.416/2.984，不形成有效观测，所以是NO_TIP而非D的“先误观测再停止”。帧1是参考中已有全部相同结构导致newdark全零。**4个复核帧中1个复现D式错首观测、2个为联合排序/阈值不足无输出、1个为全零增量退化；这不能外推成整组20帧或562帧的原因占比。**

current输出接近端点也不保证完整路径正确。38/232首观测与人工路径距离约10.68/12.80px，故不能以最终误差小反证其起点语义。1/7 current端点误差较大且首观测距人工路径>10px，本报告将其保留ROI/INIT_GEOMETRY+UNRESOLVED，未无证据地标成“已锁正确后丢失”。证据标签允许重叠，不是互斥物理真值。

## 9. 假设结论与最小后续建议

| 假设 | 证据等级 | 支持/限制 |
|---|---|---|
| H1 geometry | CONFIRMED_INTERVENTION_EFFECT | A geometry + D motion keeps tip; D geometry + A motion loses tip; geometry alone changes feasibility but does not alone reproduce the exact D wrong tip |
| H2 reference evidence / veto | CONFIRMED | Fixed D geometry, identical current arrays: changing donor field changes initial score/order and accept; D y2351 newdark=-5.2426 vs A-field5.1552 |
| H2 physical material misregistration | SUPPORTED_LOCALLY_NOT_ESTABLISHED_AS_SOLE_CAUSE | Two NCC>=.8 fixed material patches show greater D motion discrepancy; photometric metrics mixed, four low-NCC windows, no independent deformation truth |
| H3 one-column greedy capture | CONFIRMED | D selects y2282; one observation fixes prediction there; 69px from current first-choice exceeds7px;21 misses then stop |
| H3 zero/tie causes actual D failure | NOT_SUPPORTED | D has37 nonzero initial scores and unique weighted winner5.1087; zero tie instead occurs in real reference=first-current sentinel1 |
| H4 adapter mapping/scale/swap | NOT_SUPPORTED_BY_OBSERVED_RECORDS | Original num236, one-based237, BMP bytes and decoded pixels exact; no adapter point rounding/resizing/swap |
| H4 same physical point semantics | UNRESOLVED | G/S centers differ; source click/feature-definition records absent from supplied task/package/tracking manifest; NCC is not point-semantic truth |


值得讨论V2，但只建议首先针对**起点身份与参考差分缺失的耦合**做一个可独立证伪的机制改动：把起源可信度/参考证据状态明确分开，并在开发数据及合成控制上预注册验收规则。不能简单全局切current（A current本身失败），不能把B的错配点或“dy−4避开值”当推荐参数，也不能只放宽ROI或增大gap来掩盖错首锁。材料运动改进需要独立纹理/点语义证据；本任务没有实现V2、没有修改生产或冻结V1，也没有以验证组C选择下一版参数。

## 10. 运行、可重复性与交付

实际执行：114次原冻结Python（5次独立CLI，109次观察器/输入扰动/代表帧）、4次明确诊断反事实，共118次Python六模式执行；另有4次C++辅助对照。上述114包括用于观察器对照的重复A/B/C/D，不能当114张独立图像。C++只作一致性附表，未用它替代原Python解释。

观察器只读frame.f_locals，未写回变量；8组主要/反事实共16份T10逐列候选记录与原trace逐列一致；纯A/A、D/D的26份数组完全一致；原生四组的CLI图像解码像素一致。全部异常日志和失败/NO_TIP输出保留，没有静默丢分母。复现完整命令见[reproduction_commands.md](reproduction_commands.md)，已执行阶段的真实原图和argv在各run/observer.json或cli_identity.json中。

优先查看：[交互逐列图册](trace_audit_A_B_C_D.html) · [54秒证据视频](root_cause_walkthrough.mp4) · [ABCD四联图](figures/same_bmp_ABCD_overlay.png) · [首个分歧图](figures/first_divergence_panels.png) · [控制矩阵](geometry_vs_reference_ablation.csv) · [验收矩阵](acceptance_matrix.csv) · [完整性](final_integrity.json)。

为遵守项目当前生成文件只能在output内的约束，本轮使用新的`output/diagnostics/group_c_same_bmp_root_cause_v1_20261112_r01/`，没有写到项目外或覆盖旧评估。当前BMP没有独立完整路径标注，物理语义/配准真值不足处明确保留UNRESOLVED；它们不是捏造已经完成的物理因果证明。
