# 失败定位：观测证据与推断分开

TEST A正确但C撤销157帧：120 NO_SUPPORTED_CURRENT_ENDPOINT，13 ROI_LIMITED_OR_FORWARD_AUDIT_UNAVAILABLE，12 H_CONTINUE_COMPETES_WITH_STOP，12 MULTIPLE_SUPPORTED_TRANSITIONS。这是实际输出条件，不等价于157个已验证的物理原因。各候选before/after/heldout/margin/origin条件见A_correct_rejection_conditions.csv。重叠条件计数（不相加）：{"total": 157, "any_candidate_low_or_missing_before": 16, "any_candidate_post_not_low": 140, "any_candidate_low_heldout": 32, "has_continuation": 20, "all_margin_failed": 0, "all_origin_failed": 0, "any_supported": 12}。

1. 局部证据判据比A更保守。法向最大响应含选择偏差；实际宽度、纹理、弯曲、弱渐浅会使前后窗/半步验证不同时通过。120帧无受支持端点，不能全部归因配准。要对具体因果归因仍需新DEV干预试验；本轮TEST不再调参。
2. 前方审查余量和搜索图耦合。TEST反事实ROI放大1.5倍时，10条原已确认结果消失或移动>2px，独立ROI稳定性未过。扩域会改变选路和候选集；虽然root不再硬性要求，搜索域仍会限制尖端证据。
3. 高分强假尾未被区分。strong_serial_false_tail中A过长54帧/9独立案例，C修复0独立案例；强纹理/尾部仍有可见暗线，局部before高/after低会把表面线的终点当裂纹终点。参考同形线仅记录H_FALSE_BRANCH，光度变化仅有界排序辅助；两者都没有提供足以区分物理归属的独立信息。matched true/false controls共享当前外观但参考不同，不能声称当前灰度端点就是物理裂纹端点。
4. 曲线与分叉。三条±20°前方射线、有限候选和窗口假设会在弯曲/纹理上产生竞争或选错。S_curve、curve55、curve75、weak_fading_tip保护门槛均失败；真实长裂纹新增“已确认截短”计数为0，但这不等于未拒绝真长样本。
5. 光度/几何。失败拟合→UNKNOWN，不当作裂纹反证；phase-correlation采用高通纹理，FIT与HOLDOUT分开。已验证同张图的空间独立patch仍相关，并非独立传感器证据。真实局部非刚性和点误差不能仅由两点确定。

受控各族机制、修复/误伤逐例见TEST_mechanism_by_family.csv及failure_matrix.csv。真实CT2 num6/18/84、排除组Xnum51/473和三点弯关键帧见05_regression/known_historical_cases.csv及候选日志，只有算法状态变化，没有人工GT，不能报“真实修复成功”。

失败的DEVv1（oracle及早停事件不足）和DEVv2、合同失败与修正均保留09_dev_archive及00_protocol/DEV_v*_addendum.md。所有实质参数/算法修正发生在TEST生成前。冻结后仅修复工具导入、显示排版及统计聚类，不再检测TEST。
