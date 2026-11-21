# 可达性与根因证据

阶段是冻结查询合同下的直接追踪结果，不把“离GT较远”当成物理误报。只有反事实显示单变量使不可达→可达，才声称该变量有局部因果贡献。G1/G2/G3基于10px粗标注邻域；没有独立误差校准，不声称无限精度真值。

## ct2/395

首失效 `G1` / `LOCAL_REFERENCE_fewer_than_two_corr_ge062_votes`；GT在端点ROI=True，ROI=[2584, 2329, 1673, 769]；10px邻域score最大值=-3.0；最近真实峰候选距离=739.7845492213505px；端点配准分支=phase，inliers=2，残差=0.159048。局部DP真实子条件计数：{'accepted_best': 1, 'rank_gain_stop': 1, 'not_visited_after_rank_stop': 2}。

源码责任范围：src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差=9.094947017729282e-13，内部路径终点与返回点差=0.0。

- CF1: generic ROI extent x2; reference transform fixed; ROI内=True; 非空路径=True; 误差=928.9363675792426px; 10px近峰数=0; 远离GT的峰数=11（不是误报率）。

- CF2: local-reference drift from main transform; actual ROI/direction fixed; ROI内=True; 非空路径=True; 误差=928.9363675792426px; 10px近峰数=0; 远离GT的峰数=2（不是误报率）。

- CF3: disjoint-path ambiguity return bypassed; all other gates unchanged; ROI内=True; 非空路径=True; 误差=928.9363675792426px; 10px近峰数=0; 远离GT的峰数=4（不是误报率）。

- CF4（仅补入原本reason2被参考门排除像素的当前valley）：误差=238.55323798209693px；10px近峰=1；候选数 4→34。原始score控制重算与生产DP逐点一致。


尖端所在64px参考块的真实小模板审计：`{"tile": [3776, 2816, 64, 64], "votes": 0, "agree": 0, "offset": [0, 0], "stage": "fewer_than_two_corr_ge062_votes", "correlations": [0.1577354520559311, 0.13266198337078094, 0.2094123661518097, 0.19113032519817352, 0.16089282929897308, 0.19457393884658813, 0.17821535468101501, 0.12939488887786865, 0.13516907393932343]}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{"2": 314}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。


[原图拼图](key_ct2_395.jpg) · [真实trace](traces/ct2__000395.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。

## group_h/78

首失效 `G1` / `LOCAL_REFERENCE_fewer_than_two_consistent_votes_within2px`；GT在端点ROI=True，ROI=[2273, 363, 1729, 769]；10px邻域score最大值=-3.0；最近真实峰候选距离=115.26596072197832px；端点配准分支=template，inliers=2，残差=0.458363。局部DP真实子条件计数：{'accepted_best': 1, 'rank_gain_stop': 1, 'not_visited_after_rank_stop': 6}。

源码责任范围：src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差=4.547473508864641e-13，内部路径终点与返回点差=0.0。

- CF1: generic ROI extent x2; reference transform fixed; ROI内=True; 非空路径=False; 误差=N/Apx; 10px近峰数=0; 远离GT的峰数=28（不是误报率）。

- CF2: local-reference drift from main transform; actual ROI/direction fixed; ROI内=True; 非空路径=True; 误差=900.7066836598076px; 10px近峰数=0; 远离GT的峰数=7（不是误报率）。

- CF3: disjoint-path ambiguity return bypassed; all other gates unchanged; ROI内=True; 非空路径=True; 误差=900.7066836598076px; 10px近峰数=0; 远离GT的峰数=8（不是误报率）。

- CF4（仅补入原本reason2被参考门排除像素的当前valley）：误差=279.6087812104432px；10px近峰=0；候选数 8→43。原始score控制重算与生产DP逐点一致。


尖端所在64px参考块的真实小模板审计：`{"tile": [2752, 704, 64, 64], "votes": 3, "agree": 0, "offset": [8, 29], "stage": "fewer_than_two_consistent_votes_within2px", "correlations": [1, 0.7117998003959656, 0.3082510232925415, 0.6194192171096802, 0.568284809589386, 0.7531697154045105, 0.2628350555896759, 0.20465882122516632, 0.34377720952033997]}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{"2": 312}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。


[原图拼图](key_group_h_78.jpg) · [真实trace](traces/group_h__000078.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。

## group_a/504

首失效 `G4` / `NEAR_PEAK_REJECTED_competing_disjoint_paths`；GT在端点ROI=True，ROI=[760, 759, 1096, 769]；10px邻域score最大值=8.818374633789062；最近真实峰候选距离=7.118098585681481px；端点配准分支=phase，inliers=4，残差=0.576834。局部DP真实子条件计数：{'accepted_best': 1, 'competing_disjoint_paths': 1, 'not_visited_after_rank_stop': 1}。

源码责任范围：src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差=1.1368683772161603e-13，内部路径终点与返回点差=。

- CF1: generic ROI extent x2; reference transform fixed; ROI内=True; 非空路径=False; 误差=N/Apx; 10px近峰数=1; 远离GT的峰数=3（不是误报率）。

- CF2: local-reference drift from main transform; actual ROI/direction fixed; ROI内=True; 非空路径=False; 误差=N/Apx; 10px近峰数=1; 远离GT的峰数=2（不是误报率）。

- CF3: disjoint-path ambiguity return bypassed; all other gates unchanged; ROI内=True; 非空路径=True; 误差=360.9782016807199px; 10px近峰数=1; 远离GT的峰数=2（不是误报率）。

- CF4（仅补入原本reason2被参考门排除像素的当前valley）：误差=7.118098585681481px；10px近峰=1；候选数 3→448。原始score控制重算与生产DP逐点一致。


尖端所在64px参考块的真实小模板审计：`{"tile": [1344, 1152, 64, 64], "votes": 4, "agree": 4, "offset": [1, -7], "stage": "accepted", "correlations": [0.352353572845459, 0.19362862408161163, 0.31213459372520447, 0.4446871280670166, 0.7742998003959656, 0.9003006219863892, 0.3810478150844574, 0.8121635913848877, 0.8650754690170288]}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{"2": 44, "3": 53, "5": 215}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。


[原图拼图](key_group_a_504.jpg) · [真实trace](traces/group_a__000504.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。

## ct3/65

首失效 `NONE` / `OUTPUT_WITHIN_10PX_COMPARISON_TOLERANCE`；GT在端点ROI=True，ROI=[441, 479, 374, 215]；10px邻域score最大值=25.167037963867188；最近真实峰候选距离=1.6415242838213608px；端点配准分支=phase，inliers=4，残差=0.281808。局部DP真实子条件计数：{'accepted_best': 1, 'interior_shoulder': 1}。

源码责任范围：src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差=1.1368683772161603e-13，内部路径终点与返回点差=0.0。

- CF1: generic ROI extent x2; reference transform fixed; ROI内=True; 非空路径=True; 误差=8.408008204942192px; 10px近峰数=2; 远离GT的峰数=5（不是误报率）。

- CF2: local-reference drift from main transform; actual ROI/direction fixed; ROI内=True; 非空路径=True; 误差=8.408008204942192px; 10px近峰数=2; 远离GT的峰数=0（不是误报率）。

- CF3: disjoint-path ambiguity return bypassed; all other gates unchanged; ROI内=True; 非空路径=True; 误差=8.408008204942192px; 10px近峰数=2; 远离GT的峰数=0（不是误报率）。

- CF4（仅补入原本reason2被参考门排除像素的当前valley）：误差=8.408008204942192px；10px近峰=2；候选数 2→7。原始score控制重算与生产DP逐点一致。


尖端所在64px参考块的真实小模板审计：`{"tile": [512, 512, 64, 64], "votes": 6, "agree": 6, "offset": [1, 3], "stage": "accepted", "correlations": [0.8110066056251526, 0.7773409485816956, 0.8136722445487976, 0.7688503861427307, 0.6951802968978882, 0.7151857614517212, 0.5445486903190613, 0.36199650168418884, 0.3956924378871918]}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{"5": 318}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。


[原图拼图](key_ct3_65.jpg) · [真实trace](traces/ct3__000065.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。

## ct2/8

首失效 `G1` / `LOCAL_REFERENCE_fewer_than_two_corr_ge062_votes`；GT在端点ROI=True，ROI=[2583, 2325, 1673, 769]；10px邻域score最大值=-3.0；最近真实峰候选距离=159.69364804052069px；端点配准分支=phase，inliers=3，残差=0.955995。局部DP真实子条件计数：{'accepted_best': 1, 'rank_gain_stop': 1, 'not_visited_after_rank_stop': 2}。

源码责任范围：src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差=4.547473508864641e-13，内部路径终点与返回点差=0.0。

- CF1: generic ROI extent x2; reference transform fixed; ROI内=True; 非空路径=True; 误差=159.69364804052069px; 10px近峰数=0; 远离GT的峰数=5（不是误报率）。

- CF2: local-reference drift from main transform; actual ROI/direction fixed; ROI内=True; 非空路径=True; 误差=159.69364804052069px; 10px近峰数=0; 远离GT的峰数=4（不是误报率）。

- CF3: disjoint-path ambiguity return bypassed; all other gates unchanged; ROI内=True; 非空路径=True; 误差=159.69364804052069px; 10px近峰数=0; 远离GT的峰数=4（不是误报率）。

- CF4（仅补入原本reason2被参考门排除像素的当前valley）：误差=17.91419457712088px；10px近峰=1；候选数 4→32。原始score控制重算与生产DP逐点一致。


尖端所在64px参考块的真实小模板审计：`{"tile": [3328, 2752, 64, 64], "votes": 0, "agree": 0, "offset": [0, 0], "stage": "fewer_than_two_corr_ge062_votes", "correlations": [0.4890044331550598, 0.38799357414245605, 0.22652173042297363, 0.15029212832450867, 0.23900780081748962, 0.23467017710208893, 0.1447935402393341, 0.17102010548114777, 0.12739823758602142]}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{"2": 317}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。


[原图拼图](key_ct2_8.jpg) · [真实trace](traces/ct2__000008.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。

## ct2/457

首失效 `G1` / `LOCAL_REFERENCE_fewer_than_two_corr_ge062_votes`；GT在端点ROI=True，ROI=[2584, 2332, 1673, 769]；10px邻域score最大值=-3.0；最近真实峰候选距离=801.2039919612812px；端点配准分支=phase，inliers=3，残差=0.373514。局部DP真实子条件计数：{'accepted_best': 1, 'rank_gain_stop': 1}。

源码责任范围：src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差=9.094947017729282e-13，内部路径终点与返回点差=0.0。

- CF1: generic ROI extent x2; reference transform fixed; ROI内=True; 非空路径=True; 误差=801.2039919612812px; 10px近峰数=0; 远离GT的峰数=9（不是误报率）。

- CF2: local-reference drift from main transform; actual ROI/direction fixed; ROI内=True; 非空路径=False; 误差=N/Apx; 10px近峰数=0; 远离GT的峰数=2（不是误报率）。

- CF3: disjoint-path ambiguity return bypassed; all other gates unchanged; ROI内=True; 非空路径=True; 误差=801.2039919612812px; 10px近峰数=0; 远离GT的峰数=2（不是误报率）。

- CF4（仅补入原本reason2被参考门排除像素的当前valley）：误差=298.0177025285709px；10px近峰=1；候选数 2→27。原始score控制重算与生产DP逐点一致。


尖端所在64px参考块的真实小模板审计：`{"tile": [3840, 2816, 64, 64], "votes": 0, "agree": 0, "offset": [0, 0], "stage": "fewer_than_two_corr_ge062_votes", "correlations": [0.13607974350452423, 0.12313034385442734, 0.15036049485206604, 0.1838451474905014, 0.1375102698802948, 0.14241118729114532, 0.127694770693779, 0.11628646403551102, 0.17665421962738037]}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{"2": 316}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。


[原图拼图](key_ct2_457.jpg) · [真实trace](traces/ct2__000457.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。

## group_h/41

首失效 `G2` / `NO_GENERATED_LOCAL_MAXIMUM_WITHIN10PX`；GT在端点ROI=True，ROI=[2276, 374, 1729, 769]；10px邻域score最大值=4.2160491943359375；最近真实峰候选距离=291.45031563863614px；端点配准分支=phase，inliers=3，残差=0.319286。局部DP真实子条件计数：{'accepted_best': 1, 'rank_gain_stop': 1, 'not_visited_after_rank_stop': 5}。

源码责任范围：src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差=9.094947017729282e-13，内部路径终点与返回点差=0.0。

- CF1: generic ROI extent x2; reference transform fixed; ROI内=True; 非空路径=False; 误差=N/Apx; 10px近峰数=0; 远离GT的峰数=22（不是误报率）。

- CF2: local-reference drift from main transform; actual ROI/direction fixed; ROI内=True; 非空路径=True; 误差=951.9150626425983px; 10px近峰数=0; 远离GT的峰数=7（不是误报率）。

- CF3: disjoint-path ambiguity return bypassed; all other gates unchanged; ROI内=True; 非空路径=True; 误差=951.9150626425983px; 10px近峰数=0; 远离GT的峰数=7（不是误报率）。

- CF4（仅补入原本reason2被参考门排除像素的当前valley）：误差=227.01401062494395px；10px近峰=0；候选数 7→27。原始score控制重算与生产DP逐点一致。


尖端所在64px参考块的真实小模板审计：`{"tile": [2688, 704, 64, 64], "votes": 6, "agree": 5, "offset": [-15, 8], "stage": "accepted", "correlations": [1, 0.7734250426292419, 1, 1, 1, 1, 0.3781292140483856, 0.16659663617610931, 0.21400496363639832]}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{"2": 20, "3": 48, "5": 248}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。


[原图拼图](key_group_h_41.jpg) · [真实trace](traces/group_h__000041.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。

## group_h/96

首失效 `G1` / `LOCAL_REFERENCE_fewer_than_two_consistent_votes_within2px`；GT在端点ROI=True，ROI=[2273, 392, 1729, 769]；10px邻域score最大值=-3.0；最近真实峰候选距离=97.25587006844486px；端点配准分支=phase，inliers=3，残差=0.371612。局部DP真实子条件计数：{'accepted_best': 1, 'rank_gain_stop': 1, 'not_visited_after_rank_stop': 5}。

源码责任范围：src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差=4.547473508864641e-13，内部路径终点与返回点差=0.0。

- CF1: generic ROI extent x2; reference transform fixed; ROI内=True; 非空路径=True; 误差=97.25587006844486px; 10px近峰数=0; 远离GT的峰数=28（不是误报率）。

- CF2: local-reference drift from main transform; actual ROI/direction fixed; ROI内=True; 非空路径=True; 误差=33.30628556856204px; 10px近峰数=0; 远离GT的峰数=6（不是误报率）。

- CF3: disjoint-path ambiguity return bypassed; all other gates unchanged; ROI内=True; 非空路径=True; 误差=97.25587006844486px; 10px近峰数=0; 远离GT的峰数=7（不是误报率）。

- CF4（仅补入原本reason2被参考门排除像素的当前valley）：误差=3.9670177467667775px；10px近峰=1；候选数 7→33。原始score控制重算与生产DP逐点一致。


尖端所在64px参考块的真实小模板审计：`{"tile": [2752, 768, 64, 64], "votes": 6, "agree": 1, "offset": [-3, -4], "stage": "fewer_than_two_consistent_votes_within2px", "correlations": [0.2801535129547119, 0.3795514702796936, 0.3929433524608612, 1, 0.9805150032043457, 1, 0.9486284255981445, 0.6728808283805847, 1]}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{"2": 312}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。


[原图拼图](key_group_h_96.jpg) · [真实trace](traces/group_h__000096.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。

## group_a/67

首失效 `G1` / `LOCAL_REFERENCE_fewer_than_two_corr_ge062_votes`；GT在端点ROI=True，ROI=[761, 756, 1095, 769]；10px邻域score最大值=-3.0；最近真实峰候选距离=px；端点配准分支=phase，inliers=4，残差=0.409638。局部DP真实子条件计数：{}。

源码责任范围：src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差=1.1368683772161603e-13，内部路径终点与返回点差=。

- CF1: generic ROI extent x2; reference transform fixed; ROI内=True; 非空路径=True; 误差=482.0841837544879px; 10px近峰数=0; 远离GT的峰数=1（不是误报率）。

- CF2: local-reference drift from main transform; actual ROI/direction fixed; ROI内=True; 非空路径=False; 误差=N/Apx; 10px近峰数=0; 远离GT的峰数=0（不是误报率）。

- CF3: disjoint-path ambiguity return bypassed; all other gates unchanged; ROI内=True; 非空路径=False; 误差=N/Apx; 10px近峰数=0; 远离GT的峰数=0（不是误报率）。

- CF4（仅补入原本reason2被参考门排除像素的当前valley）：误差=556.4508689632411px；10px近峰=5；候选数 0→869。原始score控制重算与生产DP逐点一致。


尖端所在64px参考块的真实小模板审计：`{"tile": [960, 1088, 64, 64], "votes": 1, "agree": 0, "offset": [0, 0], "stage": "fewer_than_two_corr_ge062_votes", "correlations": [0.4388382136821747, 0.36158469319343567, 0.4521218538284302, 0.44734251499176025, 0.30746179819107056, 0.4462968409061432, 0.9689891338348389, 0.4272594153881073, 0.3753919005393982]}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{"2": 312}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。


[原图拼图](key_group_a_67.jpg) · [真实trace](traces/group_a__000067.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。

## group_c/528

首失效 `G1` / `LOCAL_REFERENCE_fewer_than_two_corr_ge062_votes`；GT在端点ROI=True，ROI=[2174, 2088, 923, 529]；10px邻域score最大值=-3.0；最近真实峰候选距离=22.6499423587537px；端点配准分支=phase，inliers=4，残差=0.191552。局部DP真实子条件计数：{'accepted_best': 1, 'rank_gain_stop': 1, 'not_visited_after_rank_stop': 1}。

源码责任范围：src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差=4.547473508864641e-13，内部路径终点与返回点差=0.0。


尖端所在64px参考块的真实小模板审计：`{"tile": [2496, 2304, 64, 64], "votes": 0, "agree": 0, "offset": [0, 0], "stage": "fewer_than_two_corr_ge062_votes", "correlations": [0.4148709774017334, 0.3210698664188385, 0.31453755497932434, 0.1137847900390625, 0.37573930621147156, 0.4045279324054718, 0.3402765989303589, 0.29029372334480286, 0.30630242824554443]}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{"2": 315}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。


[原图拼图](key_group_c_528.jpg) · [真实trace](traces/group_c__000528.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。

## three_point_bend/503

首失效 `G1` / `LOCAL_REFERENCE_fewer_than_two_corr_ge062_votes`；GT在端点ROI=True，ROI=[1366, 2321, 1400, 769]；10px邻域score最大值=-3.0；最近真实峰候选距离=191.99819332010702px；端点配准分支=phase，inliers=4，残差=0.525191。局部DP真实子条件计数：{'accepted_best': 1, 'competing_disjoint_paths': 1, 'not_visited_after_rank_stop': 2}。

源码责任范围：src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion；非空路径⇒terminal语义仍在roi_tip.inc:224附近。坐标往返误差=0.0，内部路径终点与返回点差=。


尖端所在64px参考块的真实小模板审计：`{"tile": [1728, 2688, 64, 64], "votes": 0, "agree": 0, "offset": [0, 0], "stage": "fewer_than_two_corr_ge062_votes", "correlations": [0.2884809672832489, 0.4328763484954834, 0.3883016109466553, 0.15520817041397095, 0.3280004858970642, 0.3363167345523834, 0.3453115224838257, 0.30449649691581726, 0.3162957429885864]}`。该stateless原生重算的registered浮点数组hash与D0完全一致。10px尖端邻域条件码：{"2": 310}。条件码2表示reference erosion≤75；代码初始化aligned为0，票数/一致性不足便continue，故当前帧可见裂纹仍可能完全失去score。


[原图拼图](key_three_point_bend_503.jpg) · [真实trace](traces/three_point_bend__000503.json)。未证明部分：参考模板匹配正确性不是几何往返正确性的推论，局部相关接受不等于物理对应正确。

## 原始trace默认值说明

原生Peak默认stage字符串为not_visited_after_rank_stop，表示尚未访问；如果前一个候选因竞争路径直接return，实际也未发生排名门。原始JSON保持不改，candidate_trace.csv保留raw_trace_stage并将该情形明确写为not_visited_after_ambiguity_return。未执行的hits/tail/shared导出为null，不能把默认0理解为测得0支持。局部参考votes<2时agree尚未执行，local_reference_vote_trace.csv中为null。
