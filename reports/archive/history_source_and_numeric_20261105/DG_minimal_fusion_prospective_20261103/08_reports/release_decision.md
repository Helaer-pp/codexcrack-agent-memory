# 发布决策

主决策：**KEEP_A**。生产 A、接口及正式输出保持不变；不发布新的 DLL。

| gate | result |
|---|---|
| A_identity | True |
| intersection_coverage_preserved | False |
| intersection_FP_no_increase | True |
| weak_curve_false_revoke_zero | True |
| ROI_tip_coverage_99 | False |
| registration_false_pass_1pct | False |
| native_A_only_max_66_67 | True |
| combined_CPP_tested | False |
| production_output_change | False |
| decision | KEEP_A |

不实施撤销、截短、延长或补检分支。联合门槛没有证实通过；不把保持输出不变的旁路称作精度改善。条件 C++ 里程碑未进入：没有新 DLL、没有 C++/Python 边车数值等价或完整核心15Hz通过结论。最值得下一项实验：获取具有独立物理终点/受控线靶真值和同步触发的全新试件，对“真实长线/静态假尾”成对采集，验证图像同形时的不可辨识边界。
