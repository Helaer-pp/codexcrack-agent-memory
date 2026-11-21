# 差分/配准审计

| group | frames | trusted_frames | mean_trusted_fraction | mean_ncc_initial | mean_ncc_local | local_shift_windows |
| --- | --- | --- | --- | --- | --- | --- |
| group_a | 551 | 550 | 0.06315639281637724 | 0.31635726333126657 | 0.48987938695662214 | 122 |
| ct2 | 468 | 467 | 0.06320836934516309 | 0.20190935669186544 | 0.281878218300857 | 506 |
| group_h | 410 | 0 | 0.0 | 0.06516255179031119 | 0.07882811449849819 | 0 |
| ct3 | 136 | 135 | 0.06982296853859955 | 0.5173280764713373 | 0.7326295503124781 | 291 |
| group_c | 562 | 561 | 0.3064583225878105 | 0.7246844641295276 | 0.7756018417042615 | 7569 |
| three_point_bend | 520 | 519 | 0.03700167707489536 | 0.559303220552558 | 0.5725901921302597 | 4 |

原始signed=P初始对齐参考-current，正值当前更暗，负值当前更亮，float32，出界NaN。局部补偿单独保存；不覆盖raw。所有不可信帧仍交付真实差分面板。

材料窗两侧NCC/std/亮度与固定±4搜索只提供纹理一致代理。局部搜索后的NCC提升含优化偏差，不能冒充独立物理真值；缺少独立配准GT。未通过则q=0，C明确退回当前灰度，B返回REF_UNAVAILABLE。参考同图/已有裂纹D≈0不是无裂纹。

- [group_a 不可信实例 1](../galleries/group_a/1/index.html)：SAME_IMAGE_NO_INCREMENT，面板保留P差分及遮罩。
- [ct2 不可信实例 1](../galleries/ct2/1/index.html)：SAME_IMAGE_NO_INCREMENT，面板保留P差分及遮罩。
- [group_h 不可信实例 1](../galleries/group_h/1/index.html)：SAME_IMAGE_NO_INCREMENT，面板保留P差分及遮罩。
- [ct3 不可信实例 1](../galleries/ct3/1/index.html)：SAME_IMAGE_NO_INCREMENT，面板保留P差分及遮罩。
- [group_c 不可信实例 1](../galleries/group_c/1/index.html)：SAME_IMAGE_NO_INCREMENT，面板保留P差分及遮罩。
- [three_point_bend 不可信实例 1](../galleries/three_point_bend/1/index.html)：SAME_IMAGE_NO_INCREMENT，面板保留P差分及遮罩。

参考是否带来实际收益：以paired_mode_changes中C_RAW对A_RAW的逐帧增减为准；不能用可信区域数增加代替正确路径/尖端增加。

| role | comparison | denominator | hit_gained | hit_lost | joint_gained | joint_lost | new_over100 | new_over500 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEVELOPMENT | C_FUSION_RAW versus A_VALLEY_ONLY_RAW | 76 | 0 | 0 | 0 | 0 | 0 | 0 |
| EXPOSED_REGRESSION | C_FUSION_RAW versus A_VALLEY_ONLY_RAW | 35 | 0 | 0 | 0 | 0 | 0 | 0 |
