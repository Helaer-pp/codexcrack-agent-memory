# 冻结后补充的生成挑战：不参与选择

仅生成像素，不读取第五组。用于补充原48场景未覆盖的分叉、遮挡、饱和末端和旋转；没有用结果调参，独立TEST的正式统计保持原样。与编码同时运行，耗时不纳入15Hz性能表。遮挡/饱和时物理GT由生成过程已知，但当前图像未必包含可辨识证据；分叉有两个合法端点，报告端点集合最小误差，不声称输出整个分叉网络。

| case | mode | tip确认 | 最后帧端点集合误差px | 最后状态 |
|---|---|---|---|---|
| photometric_gain_offset | A | 4/4 | 2.879236009777636 | terminal_supported |
| photometric_gain_offset | A2 | 4/4 | 1.645964762684819 | joint_absorbing_stop |
| photometric_gain_offset | B | 4/4 | 2.7891575789115763 | terminal_supported |
| photometric_gain_offset | C | 4/4 | 2.879236009777636 | terminal_supported |
| photometric_gain_offset | D | 4/4 | 2.391401262858213 | terminal_supported |
| shadow_without_crack | A | 0/4 | None | no_candidate |
| shadow_without_crack | A2 | 0/4 | None | no_candidate |
| shadow_without_crack | B | 0/4 | None | no_candidate |
| shadow_without_crack | C | 0/4 | None | no_candidate |
| shadow_without_crack | D | 0/4 | None | no_candidate |
| occlusion_30px | A | 0/4 | None | gap_unresolved |
| occlusion_30px | A2 | 4/4 | 207.57433560052647 | joint_absorbing_stop |
| occlusion_30px | B | 0/4 | None | gap_unresolved |
| occlusion_30px | C | 0/4 | None | gap_unresolved |
| occlusion_30px | D | 4/4 | 206.06761657281328 | terminal_supported |
| saturated_tip | A | 0/4 | None | gap_unresolved |
| saturated_tip | A2 | 0/4 | None | joint_stop_forward_conflict |
| saturated_tip | B | 0/4 | None | gap_unresolved |
| saturated_tip | C | 0/4 | None | gap_unresolved |
| saturated_tip | D | 4/4 | 22.638454010819725 | terminal_supported |
| rotation_translation_tracked_anchors | A | 4/4 | 2.9560966766513035 | terminal_supported |
| rotation_translation_tracked_anchors | A2 | 4/4 | 1.5668304574816898 | joint_absorbing_stop |
| rotation_translation_tracked_anchors | B | 4/4 | 2.9474423733975192 | terminal_supported |
| rotation_translation_tracked_anchors | C | 4/4 | 2.9560966766513035 | terminal_supported |
| rotation_translation_tracked_anchors | D | 4/4 | 2.593660083665877 | terminal_supported |
| two_real_branches | A | 4/4 | 2.3643120320582627 | terminal_supported |
| two_real_branches | A2 | 4/4 | 2.259619702050796 | joint_absorbing_stop |
| two_real_branches | B | 4/4 | 2.3643120320582627 | terminal_supported |
| two_real_branches | C | 4/4 | 2.3643120320582627 | terminal_supported |
| two_real_branches | D | 4/4 | 2.931391243210063 | terminal_supported |
| noise_sigma4 | A | 4/4 | 2.8939419482774658 | terminal_supported |
| noise_sigma4 | A2 | 4/4 | 1.995720421301559 | joint_absorbing_stop |
| noise_sigma4 | B | 4/4 | 2.8966359798911734 | terminal_supported |
| noise_sigma4 | C | 4/4 | 2.928566202085946 | terminal_supported |
| noise_sigma4 | D | 4/4 | 2.4475497952034035 | terminal_supported |
