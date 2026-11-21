# DEV-4消融与精度边界

四组都已开发暴露。无独立人工真值，假确认、漏确认、真实首次可测延迟与真实尖端/长度误差均N/A。首次确认帧差与共同有效帧坐标差只表示算法差异。

| group | current | stable_full | new_full | first_base | first_new | real_tip_P95 | real_length_P95 | false_or_missed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 550 | 496 | 496 | 49 | 49 | N/A | N/A | N/A |
| group_c | 561 | 543 | 543 | 18 | 18 | N/A | N/A | N/A |
| ct2 | 467 | 403 | 456 | 1 | 1 | N/A | N/A | N/A |
| group_h | 409 | 344 | 344 | 42 | 42 | N/A | N/A | N/A |

| group | mode | tip | full | first | p95_ms | max_ms |
| --- | --- | --- | --- | --- | --- | --- |
| group_a | OFF | 497 | 496 | 49 | 11.157 | 12.836 |
| group_a | RIDGE_SHADOW | 497 | 496 | 49 | 13.649 | 15.685 |
| group_a | RIDGE_CP_SHADOW | 497 | 496 | 49 | 13.934 | 15.938 |
| group_a | RIDGE_CP_GATED | 497 | 496 | 49 | 14.245 | 17.042 |
| group_a | FULL_LOCAL | 497 | 496 | 49 | 13.969 | 16.406 |
| group_a | FULL_NO_REFINE | 497 | 497 | 47 | 12.948 | 15.586 |
| group_a | FULL_PRODUCTION | 497 | 496 | 49 | 14.102 | 15.924 |
| group_c | OFF | 543 | 543 | 18 | 7.138 | 9.346 |
| group_c | RIDGE_SHADOW | 543 | 543 | 18 | 8.584 | 9.95 |
| group_c | RIDGE_CP_SHADOW | 543 | 543 | 18 | 8.525 | 9.8 |
| group_c | RIDGE_CP_GATED | 543 | 543 | 18 | 8.453 | 10.639 |
| group_c | FULL_LOCAL | 543 | 543 | 18 | 8.592 | 10.599 |
| group_c | FULL_NO_REFINE | 542 | 542 | 18 | 7.654 | 10.125 |
| group_c | FULL_PRODUCTION | 543 | 543 | 18 | 8.697 | 10.831 |
| ct2 | OFF | 403 | 403 | 1 | 26.569 | 30.48 |
| ct2 | RIDGE_SHADOW | 403 | 403 | 1 | 32.092 | 37.677 |
| ct2 | RIDGE_CP_SHADOW | 403 | 403 | 1 | 32.905 | 38.372 |
| ct2 | RIDGE_CP_GATED | 403 | 403 | 1 | 33.251 | 38.763 |
| ct2 | FULL_LOCAL | 456 | 456 | 1 | 33.44 | 38.209 |
| ct2 | FULL_NO_REFINE | 457 | 457 | 1 | 32.172 | 38.554 |
| ct2 | FULL_PRODUCTION | 456 | 456 | 1 | 32.659 | 40.532 |
| group_h | OFF | 345 | 344 | 42 | 47.472 | 55.943 |
| group_h | RIDGE_SHADOW | 345 | 344 | 42 | 49.749 | 62.491 |
| group_h | RIDGE_CP_SHADOW | 345 | 344 | 42 | 50.559 | 62.501 |
| group_h | RIDGE_CP_GATED | 345 | 344 | 42 | 50.405 | 60.601 |
| group_h | FULL_LOCAL | 345 | 344 | 42 | 50.099 | 61.239 |
| group_h | FULL_NO_REFINE | 351 | 351 | 42 | 50.826 | 64.067 |
| group_h | FULL_PRODUCTION | 345 | 344 | 42 | 50.206 | 62.369 |

合成端到端失败：[]

合成挑战失败：[{"name": "positive_retained_weak_depth_6", "passed": false, "released_confirmed": false}]

全部GT观测、漏确认及断言保留，不以未确认的零坐标计算零误差。无裂纹/弱线/曲线/短间隙/静态与新生划痕/遮挡恢复/变焦模糊/过曝/已有裂纹参考与可见长度下降测试见tests。注意合成体不能覆盖真实材料纹理分布。

合成重复帧不是独立样本：端到端案例多将同一生成图连续输入5次，用于检验时序确认。GT表confirmed_observations按帧统计，不能作为独立样本量估计置信区间。14个基础端到端案例280个模式观测相关断言均通过；22个挑战中仅weak_depth_6未通过，稳定版同样漏检。另有72个纯局部路径案例全部通过。

稳定BASE为独立原DLL回放，OFF为新DLL关闭所有新特性，二者检测结果逐帧一致。为保留原二进制计时，附BASE独立回放表（API查询未拆分为native/parse，因此留空，不能混用）：

|组|BASE完整|BASE尖端|BASE Process P95 ms|BASE Max ms|
|---|---:|---:|---:|---:|
|group_a|496|497|11.324|13.678|
|group_c|543|543|7.094|12.857|
|ct2|403|403|25.991|31.250|
|group_h|344|345|47.771|53.832|

CT2新增4个相对稳定版丢失完整确认的程序原因：frame_id=26、32、59、77。四帧根部均仍有效，局部重定位也找到终点，但全路径证据可用比例分别为0.5133、0.4967、0.5033、0.5166，低于预先固定的0.7，故unknown=true，tip/full被清零。这不是12px根部连接失败，也不是CP裁剪；包含过曝/剖面不可用处理的保守影响。是否属于真实误拒仍需独立GT。未在冻结后修改阈值。
