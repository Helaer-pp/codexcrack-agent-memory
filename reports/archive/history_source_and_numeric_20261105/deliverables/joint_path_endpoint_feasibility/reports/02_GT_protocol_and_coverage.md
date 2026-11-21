# GT 与数据隔离

用户确认暂无人工标注与业务像素容差。真实裂纹/背景分类、尖端MAE/P95、误报率、漏报率与弧长误差全部N/A。旧算法输出、两点坐标、确认覆盖均不是GT。

annotation/index.html提供可运行raw-only标注工具，annotation_tasks.json为空GT模板，校验器 tests/joint_annotation.py --validate human_gt.json。真实完整长度GT仅由独立折线弧长产生。四折LOGO协议见 tests/cross_group_validation.json；因为四组均无标签，没有执行虚假的训练/测试或概率校准。局部评分仅为未标定的带符号证据。

第五组既往已曝光51/473和超时，不是未接触盲测。本轮开发脚本只接受四组白名单，没有扫描第五组；独立第六组才可作为真正外部泛化检查。
