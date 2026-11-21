# P1/P2-GrayRef V1 冻结跨试件实测报告

## 实测结论

全量执行完成：开发1565帧、锁后验证1082帧，共2647帧；每帧固定 joint/current × T8/10/12，Python和独立C++各15882组结果。全部输入可读取，未删除失败或无端点帧。六档BMP黄金回归完全一致，源码SHA256保持任务书值。

默认 joint T10 开发尖端≤10px为12/76（15.8%），全部来自CT3；GROUP_A、CT2、开发组H均0命中。验证≤10px为5/35，>100/500px为4/0。**工程链路可运行，开发移植parity通过；锁后验证暴露current分支的浮点边界放大，跨组精度与完整移植验收均未通过。保留A，不发布本研究DLL为生产版本。**

全部V1 tip是暂定候选，无独立主裂纹认证。formal_observed字段0仅表示未实现该确认合同，不是安全或低误检证明。没有NO_VISIBLE_CRACK负例；FPR=N/A。4个开发UNCERTAIN、5个验证UNCERTAIN单独保留，不能当负例。其余2527张无标签图像只用于运行/状态/一致性统计。

## 表一：冻结Python V1原生准确率（固定 joint T10）

缺端点仍计入所有VISIBLE分母，不能当零误差。分位数仅有可比较端点的n，不包含缺输出；单位全部为原始图像像素。

| 组 | 完整帧 | VISIBLE | 暂定输出 | ≤3/5/10px | >100/500px | 误差 n / P50 / P95 / max | GT在ROI外 |
|---|---|---|---|---|---|---|---|
| GROUP_A | 551 | 19 | 13 | 0/0/0 | 13/1 | 13 / 365.913 / 497.285 / 502.050 | 0 |
| CT2 | 468 | 20 | 0 | 0/0/0 | 0/0 | 0 / N/A / N/A / N/A | 0 |
| 开发组H | 410 | 18 | 18 | 0/0/0 | 18/17 | 18 / 565.991 / 876.774 / 1002.528 | 0 |
| CT3 | 136 | 19 | 19 | 6/8/12 | 0/0 | 19 / 6.657 / 49.839 / 52.185 | 6 |
| 开发合计 | 1565 | 76 | 50 | 6/8/12 | 31/18 | 50 / 334.603 / 659.963 / 1002.528 | 6 |
| 验证组C | 562 | 20 | 6 | 0/0/0 | 4/0 | 6 / 200.000 / 261.167 / 266.377 | 0 |
| 三点弯 | 520 | 15 | 14 | 0/2/5 | 0/0 | 14 / 11.543 / 54.669 / 74.002 | 0 |
| 验证合计 | 1082 | 35 | 20 | 0/2/5 | 4/0 | 20 / 18.074 / 246.577 / 266.377 | 0 |


## 表二：C++相对Python移植一致性

| 组 | 帧×模式 | 端点完全一致 | 逐列选择一致 | ROI/P点一致 | 端点差max(px) | 预测y最大浮点差 |
|---|---|---|---|---|---|---|
| GROUP_A | 3306 | 3306 | 3306 | 3306/3306 | 0.000 | 7.73e-12 |
| CT2 | 2808 | 2808 | 2808 | 2808/2808 | 0.000 | 2.27e-12 |
| 开发组H | 2460 | 2460 | 2460 | 2460/2460 | 0.000 | 1.71e-13 |
| CT3 | 816 | 816 | 816 | 816/816 | 0.000 | 3.64e-12 |
| 验证组C | 3372 | 3359 | 3272 | 3372/3372 | 209.022 | 16.2 |
| 三点弯 | 3120 | 3118 | 3094 | 3120/3120 | 45.000 | 36 |


开发锁前9390/9390端点、逐列整数坐标/缺失计数/观测位、点与ROI完全一致；80选帧×8数组全部逐像素相同。锁后验证另计6492组模式结果。合计15882组中15867端点完全一致。120选帧×8数组共960份，其中960份逐像素完全一致。

**锁后验证15组端点不一致，126组轨迹不一致；不能将开发parity通过延伸成全数据严格一致。** 全部端点差异在current分支；joint三阈值端点仍全部一致。首次离散分歧的预测y差均小于1e-9，却跨过floor/ceil取整边界，导致搜索范围差1像素。Python np.polyfit与C++ OpenCV SVD在最近12点线性拟合上的微差可触发离散放大。典型验证组C440/current/T8：首次x=2280，预测2343.9999999999995与2344.0，搜索下界不同，Python接受y2336而C++未接受，最终端点差209.02px。验证组C2/current/T12差16.40px；三点弯32/current/T12差45px。不能以“只是浮点微差”淡化最终端点影响。现有可见选帧上的原生3/5/10px与>100/500px计数恰好和Python相同，但不消除全序列移植失败。完整记录见[first_divergence_audit.csv](tables/first_divergence_audit.csv)，未重新推理或修补验证帧。

完整trace含前50/后50与所有中间列；候选计数另列CSV。锁定版本继续保留，未按验证差异改floor/ceil、加epsilon或改SVD。下一候选只能在新版本中研究可移植数值等价性；本次结果不得覆盖。另存[原生选帧准确率](tables/cpp_selected_accuracy.csv)，避免把Python精度表不加说明地当成全部C++精度。图像/ROI错误合同比较“均拒绝”，Python分类错误与native ERROR文案不要求相同。

## 表三：研究A55a0与V1，同一VISIBLE分母

A55复用R05D封存回放，未重新执行/选择旧A参数；A55列是formal observed，V1列是provisional，输出语义不同但端点误差可同分母对照。没有把历史发布A1c742混入表中。

| 组 | 输出 | VISIBLE | 覆盖 | ≤3/5/10px | >100/500px | P50/P95/max |
|---|---|---|---|---|---|---|
| GROUP_A | A55a0 | 19 | 4 | 2/2/3 | 0/0 | 3.495 / 20.478 / 23.205 |
| GROUP_A | joint | 19 | 13 | 0/0/0 | 13/1 | 365.913 / 497.285 / 502.050 |
| GROUP_A | current | 19 | 19 | 0/0/0 | 19/0 | 357.295 / 487.090 / 499.447 |
| CT2 | A55a0 | 20 | 14 | 0/0/0 | 14/4 | 310.127 / 854.414 / 928.936 |
| CT2 | joint | 20 | 0 | 0/0/0 | 0/0 | N/A / N/A / N/A |
| CT2 | current | 20 | 3 | 0/0/0 | 3/3 | 600.249 / 671.381 / 679.285 |
| 开发组H | A55a0 | 18 | 16 | 0/0/0 | 14/9 | 628.411 / 922.675 / 951.915 |
| 开发组H | joint | 18 | 18 | 0/0/0 | 18/17 | 565.991 / 876.774 / 1002.528 |
| 开发组H | current | 18 | 18 | 0/0/0 | 18/18 | 571.067 / 882.548 / 1002.528 |
| CT3 | A55a0 | 19 | 18 | 6/9/14 | 0/0 | 4.485 / 11.795 / 12.507 |
| CT3 | joint | 19 | 19 | 6/8/12 | 0/0 | 6.657 / 49.839 / 52.185 |
| CT3 | current | 19 | 19 | 4/5/8 | 0/0 | 11.670 / 49.839 / 52.185 |
| 开发合计 | A55a0 | 76 | 52 | 8/11/17 | 28/13 | 172.227 / 907.670 / 951.915 |
| 开发合计 | joint | 76 | 50 | 6/8/12 | 31/18 | 334.603 / 659.963 / 1002.528 |
| 开发合计 | current | 76 | 59 | 4/5/8 | 40/21 | 368.695 / 680.927 / 1002.528 |
| 验证组C | A55a0 | 20 | 18 | 5/6/9 | 8/0 | 27.686 / 134.836 / 150.686 |
| 验证组C | joint | 20 | 6 | 0/0/0 | 4/0 | 200.000 / 261.167 / 266.377 |
| 验证组C | current | 20 | 20 | 6/6/11 | 1/0 | 8.581 / 85.780 / 101.149 |
| 三点弯 | A55a0 | 15 | 3 | 0/0/0 | 0/0 | 20.125 / 37.403 / 39.323 |
| 三点弯 | joint | 15 | 14 | 0/2/5 | 0/0 | 11.543 / 54.669 / 74.002 |
| 三点弯 | current | 15 | 15 | 0/0/2 | 1/0 | 27.569 / 80.446 / 142.393 |
| 验证合计 | A55a0 | 35 | 21 | 5/6/9 | 8/0 | 20.125 / 132.039 / 150.686 |
| 验证合计 | joint | 35 | 20 | 0/2/5 | 4/0 | 18.074 / 246.577 / 266.377 |
| 验证合计 | current | 35 | 35 | 6/6/13 | 2/0 | 16.145 / 89.824 / 142.393 |


## 固定六模式消融

| 组/分母 | 分支 | T | 暂定输出 | ≤3/5/10px | >100/500px |
|---|---|---|---|---|---|
| GROUP_A/19 | joint | 8 | 16 | 0/0/0 | 16/1 |
| GROUP_A/19 | joint | 10 | 13 | 0/0/0 | 13/1 |
| GROUP_A/19 | joint | 12 | 13 | 0/0/0 | 13/1 |
| GROUP_A/19 | current | 8 | 19 | 0/0/0 | 19/0 |
| GROUP_A/19 | current | 10 | 19 | 0/0/0 | 19/0 |
| GROUP_A/19 | current | 12 | 19 | 0/0/0 | 19/0 |
| CT2/20 | joint | 8 | 0 | 0/0/0 | 0/0 |
| CT2/20 | joint | 10 | 0 | 0/0/0 | 0/0 |
| CT2/20 | joint | 12 | 0 | 0/0/0 | 0/0 |
| CT2/20 | current | 8 | 4 | 0/0/0 | 4/4 |
| CT2/20 | current | 10 | 3 | 0/0/0 | 3/3 |
| CT2/20 | current | 12 | 3 | 0/0/0 | 3/3 |
| 开发组H/18 | joint | 8 | 18 | 0/0/0 | 18/17 |
| 开发组H/18 | joint | 10 | 18 | 0/0/0 | 18/17 |
| 开发组H/18 | joint | 12 | 18 | 0/0/0 | 18/17 |
| 开发组H/18 | current | 8 | 18 | 0/0/0 | 18/18 |
| 开发组H/18 | current | 10 | 18 | 0/0/0 | 18/18 |
| 开发组H/18 | current | 12 | 18 | 0/0/0 | 18/18 |
| CT3/19 | joint | 8 | 19 | 6/7/10 | 0/0 |
| CT3/19 | joint | 10 | 19 | 6/8/12 | 0/0 |
| CT3/19 | joint | 12 | 18 | 7/8/12 | 0/0 |
| CT3/19 | current | 8 | 19 | 0/0/1 | 3/0 |
| CT3/19 | current | 10 | 19 | 4/5/8 | 0/0 |
| CT3/19 | current | 12 | 19 | 7/8/12 | 0/0 |
| 开发合计/76 | joint | 8 | 53 | 6/7/10 | 34/18 |
| 开发合计/76 | joint | 10 | 50 | 6/8/12 | 31/18 |
| 开发合计/76 | joint | 12 | 49 | 7/8/12 | 31/18 |
| 开发合计/76 | current | 8 | 60 | 0/0/1 | 44/22 |
| 开发合计/76 | current | 10 | 59 | 4/5/8 | 40/21 |
| 开发合计/76 | current | 12 | 59 | 7/8/12 | 40/21 |
| 验证组C/20 | joint | 8 | 12 | 0/0/0 | 10/0 |
| 验证组C/20 | joint | 10 | 6 | 0/0/0 | 4/0 |
| 验证组C/20 | joint | 12 | 5 | 0/0/0 | 3/0 |
| 验证组C/20 | current | 8 | 20 | 2/3/7 | 2/0 |
| 验证组C/20 | current | 10 | 20 | 6/6/11 | 1/0 |
| 验证组C/20 | current | 12 | 20 | 9/9/13 | 0/0 |
| 三点弯/15 | joint | 8 | 14 | 1/1/4 | 0/0 |
| 三点弯/15 | joint | 10 | 14 | 0/2/5 | 0/0 |
| 三点弯/15 | joint | 12 | 14 | 2/3/7 | 0/0 |
| 三点弯/15 | current | 8 | 15 | 0/0/0 | 2/0 |
| 三点弯/15 | current | 10 | 15 | 0/0/2 | 1/0 |
| 三点弯/15 | current | 12 | 15 | 1/2/7 | 1/0 |
| 验证合计/35 | joint | 8 | 26 | 1/1/4 | 10/0 |
| 验证合计/35 | joint | 10 | 20 | 0/2/5 | 4/0 |
| 验证合计/35 | joint | 12 | 19 | 2/3/7 | 3/0 |
| 验证合计/35 | current | 8 | 35 | 2/3/7 | 4/0 |
| 验证合计/35 | current | 10 | 35 | 6/6/13 | 2/0 |
| 验证合计/35 | current | 12 | 35 | 10/11/20 | 1/0 |


joint T10开发12/76优于current T10的8/76，但增益集中于CT3，不能宣称跨材料显著优势。CT2 joint全部无端点，current也未命中。验证验证组Cjoint T10为0/20而current T10为11/20，三点弯joint为5/15、current为2/15：参考分支没有统一优势。参考首帧可能已有裂纹，current与joint共享当前图/ROI/追踪规则，差异支持“增量证据与可见裂纹不等价”，不独立证明旧裂纹或配准是哪一个原因。T8、T12保持预设对照，没有逐组/逐帧挑最佳阈值。验证表仅报告，不反向选择模式。

## P点、ROI与路径可行性

| 组 | 完整帧/运行成功 | 全帧无暂定端点 | GT在ROI外/采样ROI外 | 人工路径落在ROI比例均值 | 10px路径覆盖/精度均值 |
|---|---|---|---|---|---|
| GROUP_A | 551/551 | 175 | 0/0 | 100.0% | 0.0%/0.0% |
| CT2 | 468/468 | 468 | 0/0 | 100.0% | 0.0%/0.0% |
| 开发组H | 410/410 | 1 | 0/0 | 100.0% | 0.0%/0.0% |
| CT3 | 136/136 | 10 | 6/6 | 93.2% | 94.3%/88.6% |
| 验证组C | 562/562 | 256 | 0/0 | 97.2% | 0.0%/0.0% |
| 三点弯 | 520/520 | 46 | 0/0 | 97.1% | 84.8%/84.9% |


每组首帧固定参考、原图坐标xy、P1上/P2下、frame_id=frame_order+1。2647条P点原记录映射与读入图像SHA逐一核对通过。CT3来源为显式原帧名和坐标num的历史坐标CSV；独立原始跟踪TXT仍缺失，不能夸大其外部可追溯性。全部帧提供当前P点；NCC回退仅黄金回归实测，不能把本批统计解释为全量NCC成功率。

ROI严格保持冻结上下边界与自动右边界，实际采样另有上2/下1像素内缩。CT3六个GT在ROI外是适用假设失败，未为GT扩ROI。路径覆盖是人工路径中距可见算法线段≤10px的比例；路径精度是反方向比例，按全部VISIBLE逐帧均值，空路径为0；不把跨缺口的预测连线当观测。5px数据同样在group_summary.csv。完整人工路径可能从P点左侧起始，ROI路径比例与尖端包含是不同指标。

## 失败类别与直接证据

| 数据用途 | 类别 | 计数 | 代表帧 | 直接证据 |
|---|---|---|---|---|
| DEVELOPMENT | INPUT_OR_COORDINATE_ERROR | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| DEVELOPMENT | P1P2_TRACK_FAILURE | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| DEVELOPMENT | ROI_GEOMETRY_EXCLUSION | 6 | ct3/101 | GT_OUTSIDE_P1P2_ROI or frozen sampling inset/right boundary; no ROI adjustment |
| DEVELOPMENT | ORIGIN_WRONG_LOCK | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| DEVELOPMENT | REFERENCE_COMPENSATION_UNTRUSTWORTHY | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| DEVELOPMENT | MATERIAL_GRAY_VETO | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| DEVELOPMENT | CURRENT_VALLEY_MISSING | 17 | group_a/241 | No material-valid current valley reaches frozen threshold within3px of GT |
| DEVELOPMENT | REFERENCE_DELTA_MISSING | 2 | ct2/1 | Current valley exists but no joint threshold support near GT; motion cause not independently established |
| DEVELOPMENT | PATH_JUMP_OR_OVEREXTEND | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| DEVELOPMENT | PREMATURE_GAP_STOP | 38 | group_a/67 | Observed trace ends after21 misses before GT x, despite near-GT evidence or unavailable diagnosis |
| DEVELOPMENT | NOT_OBSERVABLE | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| DEVELOPMENT | UNKNOWN | 1 | ct3/46 | Insufficient evidence for a unique causal attribution; retain arrays and complete column trace |
| DEVELOPMENT | WITHIN_10 | 12 | ct3/12 | Provisional endpoint within10px; not independent confirmation |
| VALIDATION_ONLY | INPUT_OR_COORDINATE_ERROR | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| VALIDATION_ONLY | P1P2_TRACK_FAILURE | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| VALIDATION_ONLY | ROI_GEOMETRY_EXCLUSION | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| VALIDATION_ONLY | ORIGIN_WRONG_LOCK | 21 | group_c/1 | First predicted center at xleft+6 lies >10px from labeled path; recorded before any accepted observation |
| VALIDATION_ONLY | REFERENCE_COMPENSATION_UNTRUSTWORTHY | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| VALIDATION_ONLY | MATERIAL_GRAY_VETO | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| VALIDATION_ONLY | CURRENT_VALLEY_MISSING | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| VALIDATION_ONLY | REFERENCE_DELTA_MISSING | 3 | three_point_bend/144 | Current valley exists but no joint threshold support near GT; motion cause not independently established |
| VALIDATION_ONLY | PATH_JUMP_OR_OVEREXTEND | 5 | three_point_bend/306 | Final selected pixel extends >10px beyond labeled tip x |
| VALIDATION_ONLY | PREMATURE_GAP_STOP | 1 | three_point_bend/215 | Observed trace ends after21 misses before GT x, despite near-GT evidence or unavailable diagnosis |
| VALIDATION_ONLY | NOT_OBSERVABLE | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| VALIDATION_ONLY | UNKNOWN | 0 | N/A | No classified cases; not evidence that this failure mechanism is impossible |
| VALIDATION_ONLY | WITHIN_10 | 5 | three_point_bend/248 | Provisional endpoint within10px; not independent confirmation |


分类为离线、固定优先级的可观测证据归类，并非排他物理因果证明：输入→ROI排除→已命中→初始中心偏离→GT邻域材料/暗谷/差分→过冲→21列缺失早停→UNKNOWN。GT邻域为±3px，数字只用于说明已冻结结果，不能改路径。零计数只代表未归入该类，不代表该机制不存在。NOT_OBSERVABLE不据不确定标签臆断；9个UNCERTAIN另列。两点y线性位移插值不是严格两侧材料配准，REFERENCE_COMPENSATION_UNTRUSTWORTHY的独立证据仍不足。

| 开发哨兵 | joint误差/有向x误差 | 分类 | 初始中心距GT路径 | 最后访问x/缺失列 | GT处valley/newdark/两侧灰度 | GT邻域current/joint像素数 |
|---|---|---|---|---|---|---|
| group_a/504 | 无端点 / N/A | CURRENT_VALLEY_MISSING | 98.641 | 899.0/21 | 1.399 / 1.399 / 254.998 | 0/0 |
| ct2/395 | 无端点 / N/A | PREMATURE_GAP_STOP | 175.151 | 2747.0/21 | 15.651 / 14.628 / 241.558 | 25/22 |
| group_h/78 | 535.130 / -222.117 | CURRENT_VALLEY_MISSING | 436.452 | 2597.0/21 | 3.866 / 3.862 / 255.000 | 0/0 |
| ct3/65 | 6.657 / 5.594 | WITHIN_10 | 22.843 | 597.0/21 | 18.981 / 17.708 / 201.603 | 13/13 |


开发组H78的弱末端在当前灰度/差分图中可见局部响应，但实际路径远在其前方停止；不能把“GT附近有证据”写成“V1到达并正确终止”。GROUP_A504与CT2/395同样保留起始中心、最后访问列、21列缺失和近GT灰度，见哨兵放大图。CT3/65暂定误差6.66px，有效但不满足3/5px。裂纹闭合、喷漆遮挡与真实物理间隙没有单独同步物理标签，不能仅凭trace缺失给出分材料因果成功率；报告能确认的是暗谷/增量证据的数值与访问范围，物理原因仍需补证。

## 执行边界与偏差记录

冻结源码未改，source_diff.patch为空。为绕开冻结cv2.imread对中文Windows路径的限制，adapter仅按原字节复制到ASCII output/io_cache并校验SHA，不预裁剪、不重编码。实际逐帧调用原main，观察器只读取返回局部变量，包含观察开销；提供的batch_validate_V1先通过1565帧dry-run，完整回放用常驻worker以减少每帧导入开销。12个开发首/中/末帧另跑真实CLI，六行输出与常驻结果一致；不能把常驻main耗时标为含进程启动的CLI。

验证进入前已锁定算法、native DLL、adapter、评分规则与manifest。两组首次各完成Python第1帧后，provenance字段重名导致记录层中断；修正validation.py的日志键，并按validation_io_amendment.json复用这两份已完成Python输出，原始锁与初始错误日志保留。此前native验证帧数0，未读验证标签；检测规则、DLL、评估阈值均不改。恢复不是无记录地重跑首帧，也不能称所有驱动文件从未改动。40份验证标签在1082帧推理全部完成后读取；访问记录保留。各组历史已被研究曝光，含任务书明确回归图，不称外部独立盲测。

冻结源码本身对任意非空tip写stop_reason=gap_limit，即使循环到右边界也如此；保持该行为，真实终止应结合last_visited_x/missing_run判断。原overlay把非连续观测点相连，本轮视频忠实展示并注明跨缺失线不是观测；新增局部卡片以虚线区分缺失。C++只借用CrackV4Image/Point内存结构，未调用或链接A/R05G检测实现，使用独立导出GrayRef*。

## 最小V2建议（仅方案，未实施）

首先解决“当前P点几何中点附近的单列起始先验”与实际主裂纹身份/可达性不一致：在DEVELOPMENT预先固定局部起源证据规则，逐项对照V1，报告首个分歧、到达GT邻域率及严重错误；不拿人工tip作种子，不依据某组名字分支。单独研究reference-unavailable/已有裂纹的证据状态，current与增量证据不能互相当成物理真值。ROI物理假设若要放宽，应先定义独立几何依据与适用范围，不能以包含现有GT为优化目标。每次仅改一个机制，保持四组全序列、同76个可见分母、3/5/10与>100/500、路径精度和覆盖、无标签负例FPR=N/A；预注册规则后冻结，再考虑新的独立验证数据。本轮验证组不再作为这些改动的开发选型数据。需要用户明确批准V2后另开版本，不能覆写V1。

## 交付索引

- [六组视频与120张详细对比卡](galleries/index.html)，验证组优先；[2647帧局部对比](galleries/all_frames.html)。
- [原生准确率](tables/group_summary.csv)、[完整逐帧](tables/all_results.csv)、[移植parity](tables/py_cpp_parity.csv)、[A55对比](tables/A55_V1_comparison.csv)、[失败证据](tables/failure_stages.csv)。
- [环境与身份](baseline_and_versions.md)、[独立时间范围](performance_report.md)、[构建和复现](build_and_reproduce.md)、[最终完整性](final_integrity.json)。

## 回归点与实际批量点的额外核对

同一BMP在两条链路采用不同P点：黄金回归使用任务书点+NCC，完整序列使用原追踪点。相同图像字节并不等于相同输入，默认端点会不同；没有将回归点替代全序列实际点。[精确坐标、ROI与端点对照](regression_vs_sequence_inputs.md)。此核对仅读取已保存结果，额外推理0次。
