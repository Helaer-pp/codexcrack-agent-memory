# R05H 完整算法与六组验证报告

1. **已有完整可调用、已编译并实际执行的 C++ 算法。** `research/uctt_r05h/detector.hpp` 的 `Pipeline::process`，C ABI 在 `runtime.cpp`，DLL 在 `output/build/uctt_r05h/Release/R05H.dll`。完整回放2647张原图，开发4变体6260次 + 验证1082次 =7342次调用。运行命令见源码 README / tests/repro_commands.md。生产 A 没有替换。
2. **开发76张可见标注：正式确认 36/76；正式≤3/5/10px=1/3/7；正式>100/500px=19/0。** 工作端点 76/76，≤3/5/10px=8/12/17；>100/500px=33/1。拒绝40/76。不是只统计正确确认子集。
3. **CT2 可见选帧 20 张，相对 R05G AUTO BEAM 工作误差下降 19 张。** 距GT≤10px STOP保留17张，其中15张仍选择错误位置。误差下降不等于进入10px。多个哨兵从旧版过冲变为本轮提前停止：CT2/431、457、GROUP_A504、开发组H78的有符号前向误差均为负。正确STOP未被覆盖，却被较早高分STOP击败；CT2/395没有保留10px正确STOP。逐候选分数与失败阶段见 candidate_stop_audit.csv / error_attribution.csv。
4. **参考模块真实执行：全六组候选/历史参考尝试33476次，有效2022次（6.04%），NEW票896次。** 其余为UNCERTAIN/UNAVAILABLE；有效注册不等于正确身份。开发组启用固定参考使工作10px命中19→17，正式10px命中7→7，没有测得精度增益。开发真实序列历史导航VALID=0，故FULL与NO_HISTORY结果相同；验证组C历史导航实际有效208次。相同图像不产生NEW票的合同检查已执行。
5. **CT3自动起源：136/136帧获得起点；旧R05G为0/136。** 路径和端点精度仍须看下表。原始R03 coherent_wrong_first_lock依然FAIL，并会错误写历史；这是旧候选注入状态机，不能把它的失败掩盖成新算法通过。R05H原图划痕负例另行运行，见测试表；真实被误确认的帧仍会写入R05H历史，无法宣称首次锁定安全已解决。
6. **建议冻结为可正常输出、但不达生产精度的研究工程基线。** 正式远错误、弱末端漏选及STOP歧义仍存在。完整模块交付不代表算法验收成功；不得部署替换A。后续如继续研发，保留这次验证结果，不能把验证组变成调参集。

## 验证组优先结论

验证组C、三点弯在源码/DLL/规则冻结后各一次性只读回放，共1082帧。35张VISIBLE、5张UNCERTAIN。正式确认12/35，正式≤10px 4/35，正式>100/500px 2/0；工作≤10px 11/35，>100/500px 14/0。验证结果未用于修改参数或选择版本；两组已历史曝光，不能称独立未见TEST。

| dataset_id | visible | uncertain | observed | observed_hit3 | observed_hit5 | observed_hit10 | observed_over100 | observed_over500 | working_hit10 | working_over100 | working_over500 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 19 | 1 | 4 | 1 | 1 | 1 | 0 | 0 | 3 | 9 | 0 |
| ct2 | 20 | 0 | 16 | 0 | 0 | 2 | 10 | 0 | 2 | 13 | 1 |
| group_h | 18 | 2 | 16 | 0 | 2 | 4 | 9 | 0 | 5 | 9 | 0 |
| ct3 | 19 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 2 | 0 |
| group_c | 20 | 0 | 12 | 1 | 3 | 4 | 2 | 0 | 10 | 4 | 0 |
| three_point_bend | 15 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 10 | 0 |
| DEVELOPMENT | 76 | 4 | 36 | 1 | 3 | 7 | 19 | 0 | 17 | 33 | 1 |
| VALIDATION_ONLY | 35 | 5 | 12 | 1 | 3 | 4 | 2 | 0 | 11 | 14 | 0 |

## 路径覆盖、精度与同条件消融

可见折线按1原像素加密；推断间隙不计为观察路径。所有可见标注共同分母；无输出路径计0。合取要求recall10、precision10都≥0.9且工作端点≤10px。GT为人工路径，间隙本身的可见性未逐像素标注，覆盖率存在该标注限制。

| dataset_id | variant | visible | observed | observed_hit10 | working_hit10 | working_over100 | working_over500 | path_recall5 | path_recall10 | path_precision5 | path_precision10 | path_and_endpoint10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEVELOPMENT | FULL | 76 | 36 | 7 | 17 | 33 | 1 | 0.6111864252681825 | 0.648835045108426 | 0.8598720192072968 | 0.9114437530796727 | 17 |
| DEVELOPMENT | NO_REFERENCE | 76 | 36 | 7 | 19 | 31 | 1 | 0.6172782328258449 | 0.6552650636552795 | 0.8598720192072968 | 0.917703721181746 | 19 |
| DEVELOPMENT | LAST_ENDPOINT | 76 | 0 | 0 | 14 | 50 | 28 | 0.9414807374485629 | 0.9694509122167727 | 0.6352764019174927 | 0.6554553168399563 | 13 |
| DEVELOPMENT | NO_HISTORY | 76 | 36 | 7 | 17 | 33 | 1 | 0.6111864252681825 | 0.648835045108426 | 0.8598720192072968 | 0.9114437530796727 | 17 |
| VALIDATION_ONLY | FULL | 35 | 12 | 4 | 11 | 14 | 0 | 0.344331353532944 | 0.4229764245983948 | 0.44979049223340284 | 0.641669522251443 | 8 |

NO_REFERENCE关闭固定参考评分，仍保留同一历史导航机制；NO_HISTORY关闭历史导航及写入；LAST_ENDPOINT选择最前方保留STOP作为远端策略。各变体独立状态，输入顺序和采样规则相同，因决策反馈导致历史不同是消融结果的一部分。验证组不运行消融以避免版本选择。

## 全序列状态与实际耗时

| dataset_id | frames | states | seed_missing | incomplete | history_writes | history_navigation_valid | p50 | p95 | p99 | max | over50 | over500 | reference_attempts | reference_valid | reference_new |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 551 | {'TENTATIVE': 366, 'OBSERVED': 185} | 0 | 0 | 185 | 0 | 9.6911 | 22.54645 | 26.42925 | 32.9841 | 0 | 0 | 7154 | 1 | 0 |
| ct2 | 468 | {'OBSERVED': 271, 'TENTATIVE': 197} | 0 | 0 | 271 | 0 | 25.3375 | 38.47594999999999 | 44.55196999999999 | 48.5589 | 0 | 0 | 6083 | 3 | 0 |
| group_h | 410 | {'OBSERVED': 323, 'TENTATIVE': 87} | 0 | 0 | 323 | 0 | 7.7409 | 13.807199999999996 | 19.90360299999998 | 25.9043 | 0 | 0 | 5065 | 0 | 0 |
| ct3 | 136 | {'TENTATIVE': 136} | 0 | 0 | 0 | 0 | 8.170300000000001 | 13.09825 | 15.068165 | 23.7377 | 0 | 0 | 1632 | 150 | 70 |
| group_c | 562 | {'TENTATIVE': 255, 'OBSERVED': 307} | 0 | 0 | 307 | 208 | 12.950849999999999 | 22.872524999999992 | 37.40259999999997 | 48.4112 | 0 | 0 | 7302 | 214 | 0 |
| three_point_bend | 520 | {'TENTATIVE': 520} | 0 | 0 | 0 | 0 | 21.3532 | 35.40594499999999 | 43.014042999999994 | 63.521 | 3 | 0 | 6240 | 1654 | 826 |

| dataset_id | io_decode_hash_ms_p95 | debug_export_ms_p95 | root_ms_p95 | tracking_ms_p95 | terminal_ms_p95 | reference_ms_p95 | state_ms_p95 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 41.84480000003532 | 3.61844999861205 | 0.18645 | 7.35405 | 8.3504 | 6.2607 | 0.8691 |
| ct2 | 190.66807499966671 | 8.50723000094149 | 0.21486 | 14.182784999999999 | 14.680124999999997 | 8.245909999999999 | 5.9623349999999995 |
| group_h | 66.97141999939049 | 2.6763499992739517 | 0.397555 | 4.8563799999999935 | 4.620444999999996 | 6.471164999999999 | 1.7432899999999993 |
| ct3 | 34.155475001171 | 2.433399998153618 | 0.146725 | 4.51995 | 4.9407499999999995 | 3.752725 | 0.0001 |
| group_c | 197.72537500175522 | 4.20981999777723 | 0.146995 | 7.70213499999996 | 7.543014999999952 | 5.108459999999999 | 6.352625 |
| three_point_bend | 253.08463999936058 | 4.554079999070379 | 0.58354 | 13.149849999999997 | 11.244589999999997 | 10.795449999999994 | 0.0001 |

单位ms，CPU为本机Ryzen7950X；未验证i7部署。预处理为8bit Mat视图，灰度解码在Python IO项；native含root/tracking/terminal/reference/state，debug JSON导出另计。跟踪研究预算350ms，STOP循环450ms后标为不完整，最多12个候选参考注册在其后执行，因此总耗时并非硬保证≤500ms。参考细分匹配与暗谷比较合记reference_ms；没有虚构不可测分项。视频8fps不是算法吞吐。

## 特殊哨兵

负的signed_forward_error表示提前停止，正值表示前向超出；不能把所有大误差都归因为过冲。

| dataset_id | frame_id | R05G_auto_beam_error | status | working_error | observed_error | signed_forward_error | stop_nearest | correct_stop_preserved | first_failure | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| group_a | 504 | 523.1112280522221 | TENTATIVE | 314.80659775262825 |  | -314.4480154607828 | 1.7372276262109283 | True | STOP_SELECTION | competing_stops |
| ct2 | 395 | 401.4240795923844 | OBSERVED | 238.59371180785473 | 238.59371180785473 | -232.078949943005 | 63.77925566444289 | False | PATH_MISSES_TIP | current_identity_terminal_supported |
| ct2 | 196 | 898.9889641496925 | OBSERVED | 9.705070500293228 | 9.705070500293228 | 9.701995914623 | 1.748105880441753 | True | WITHIN_10 | current_identity_terminal_supported |
| ct2 | 431 | 521.9515637891435 | OBSERVED | 279.6019250966866 | 279.6019250966866 | -273.46846302717336 | 1.4186937548543743 | True | STOP_SELECTION | current_identity_terminal_supported |
| ct2 | 457 | 542.9665453652925 | OBSERVED | 299.152724031651 | 299.152724031651 | -293.22276636594523 | 0.16737617383047956 | True | STOP_SELECTION | current_identity_terminal_supported |
| group_h | 78 | 6.222698043192525 | OBSERVED | 142.6852391340934 | 142.6852391340934 | -142.65951931526251 | 1.4645477762269885 | True | STOP_SELECTION | current_identity_terminal_supported |
| group_h | 41 | 15.157928561860011 | OBSERVED | 76.73719609729511 | 76.73719609729511 | -76.67993811697625 | 1.475139453879924 | True | STOP_SELECTION | current_identity_terminal_supported |
| group_h | 115 | 8.346693835223071 | OBSERVED | 135.57068903305037 | 135.57068903305037 | -135.55869012549488 | 8.307836141310547 | True | STOP_SELECTION | current_identity_terminal_supported |
| ct3 | 65 |  | TENTATIVE | 3.4336797508720447 |  | 2.8850935821126784 | 2.008138734255506 | True | CONFIRMATION_REJECTED | origin_identity_unverified |

## 合成与安全检查

| test | expected | status | error | passed | history_written | reason |
| --- | --- | --- | --- | --- | --- | --- |
| continuous | positive | OBSERVED | 0.5 | True | True | current_identity_terminal_supported |
| preexisting_true_crack | positive | OBSERVED | 0.5 | True | True | current_identity_terminal_supported |
| reference_low_texture | positive | OBSERVED | 0.5 | True | True | current_identity_terminal_supported |
| coherent_wrong_first_lock | negative | TENTATIVE | 2.5 | True | False | origin_identity_unverified |
| reference_preexisting_scratch | negative | TENTATIVE | 153.05227865013967 | True | False | origin_identity_unverified |
| blank | negative | UNOBSERVED |  | True | False | no_current_support |
| gap_12 | positive | OBSERVED | 0.4452772625104488 | True | True | current_identity_terminal_supported |
| gap_24 | positive | OBSERVED | 0.33762003968562676 | True | True | current_identity_terminal_supported |
| gap_40 | positive | TENTATIVE | 0.42241643903537085 | False | False | competing_stops |
| weak_2_column | weak_visible_fragment_preserved | OBSERVED |  | False | True | current_identity_terminal_supported |
| weak_3_column | weak_visible_fragment_preserved | OBSERVED |  | False | True | current_identity_terminal_supported |
| parallel_scratch_beam | correct_or_unconfirmed | OBSERVED | 0.5 | True | True | current_identity_terminal_supported |
| closure_reopening | current_tip_can_retreat | OBSERVED |  | True | True |  |
| invalid_geometry |  |  |  | True |  |  |

| test | passed | status | history_written | error |
| --- | --- | --- | --- | --- |
| identical_reference_not_new | True |  |  |  |
| material_translation | True | OBSERVED |  | 0.5 |
| image_size_mismatch | True |  |  |  |
| fresh_handle_repeat | True |  |  |  |
| coherent_notch_attached_distractor | True | TENTATIVE | False |  |
| image_boundary_not_tip | True | TENTATIVE |  |  |

12/24/40px间隙的工作端点与正式确认分别考察；40px可以到达但确认歧义仍失败。2/3列弱响应采样没有被旧最短片段门删除，最终主路径弱片段保留测试仍失败，不能声称弱尖端问题解决。原始R03测试16项15通过，coherent_wrong_first_lock失败，完整原输出见tests/R03_original.csv。原图合成负例不能替代真实阴性FPR；真实阴性GT不足，FPR=N/A。未标注起始帧均已回放，仍不可把它们擅自当无裂纹真值。

## 实现与已知限制

- 自动起源使用宽松P1/P2几何、宽暗缺口结构、弱暗谷备选，不再要求三个连续强截面。仍只按有序P1/P2右法向展开，未覆盖物理前向不确定时的双向识别。
- R05G `crossSection` 原样保留；缺失点不更新方向；间隙上限48–64像素；保留所有有意义支持下降/缺失STOP。STOP评分由有界当前支持、前后证据、身份、覆盖/间隙与有效参考组成，没有无限长度奖励。每候选沿向前3–50尺度像素探测；预算不足显式标注。
- 两侧各2个材料块分别NCC匹配，纹理、唯一性、正反一致、侧内位移残差和边界共同质控。只有两侧可靠才用于NEW/OLD判断；单侧UNCERTAIN和不可用均为中性。仅局部平移模型，无法保证复杂形变。只审查排名前12个STOP的参考，未审查候选不能称参考支持。
- 起源缺口与过去可信材料导航提供身份。历史导航使用以前OBSERVED路径的起始点和局部双侧映射，并重新读取当前横截面；未实现整条历史曲线形变模型。只有正式OBSERVED写历史，但开发19张、验证2张正式误差>100px的标注帧都写入了历史。因此错误历史写入并未解决；开发导航VALID=0使本次错误存储尚未产生可测导航效应，不能将此误称为安全通过。
- 局部末端0.5像素步进补扫，仅接受实际当前暗谷；path末节点和精定位working_tip可能相差≤3像素。预算边界或图像边界不直接变正式尖端。搜索完成只指当前有限假设搜索，不代表全局最优或无歧义。
- 图像边界会抑制相关STOP确认，但冻结版本未把任何分支触边都提升为全局search_complete=false；需结合STOP的boundary/reason审查。完整逐帧日志保留主路径与全部STOP，未导出每个未选beam节点和原始截面数组。
- 部分TENTATIVE帧因最少当前支持条件未满足，其reason仍为current_identity_terminal_supported：这是冻结版本原因字符串不够细的缺陷；status/observed/历史写入字段才是实际状态，未在验证后改算法掩盖。
- 完整结果中的失败阶段是离线直接可见的首类失败，不是未经测量的因果结论；原图和局部对比保留供审查。未实施GT拟合、自动阈值搜索、训练或未来帧读取。

## 视频、每帧对比与复现

[六组视频索引](galleries/index.html) · [2647帧局部对比](galleries/all_frames.html)。验证组C/三点弯视频置顶，每组包括4秒指标卡及全部原帧；不丢弃失败帧。左列原图，右列输出，两个局部视野分别显示整条路径与末端放大。有人工标注时放大中心可用GT，仅影响离线裁切；算法在这之前已完成并冻结。

```
videos/R05H_group_c.mp4
videos/R05H_three_point_bend.mp4
videos/R05H_group_a.mp4
videos/R05H_ct2.mp4
videos/R05H_group_h.mp4
videos/R05H_ct3.mp4
```

原研究基线55a0与历史发布1c742保持独立身份；本轮视频蓝色点来自旧A55a0已冻结逐帧结果，不重新编译A冒充新算法进步。源文件、配置、原DLL、标注快照均hash核对。全部2647输入原图读取时SHA256核对，排除组X图像/标签打开数0。
