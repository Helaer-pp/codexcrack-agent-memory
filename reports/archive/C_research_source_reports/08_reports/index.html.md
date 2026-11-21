C 自适应尖端研究：KEEP_A

视频与逐帧对比 全部逐帧CSV 消融汇总

executive_summary

# C 自适应尖端研究开发报告

结论：**KEEP_A / C_RESEARCH_ONLY**。独立受控 TEST 未通过效果门槛，因此按任务书不进入 C++ 新核心/DLL 集成。生产 A 源码、DLL、ABI、参数及原正式结果均保持不变。

本轮完成独立 C 的动态 ROI、实际运行的三尺度响应、鲁棒噪声、可校验光度拟合、法向尖端重定位、局部前后证据及候选竞争；通过38项合同检查。6组真实输入共3035张（3029变形帧+6参考）完成原生 A 精确复现，3035张状态、坐标、长度、原始双精度路径全部一致。真实组只作已曝光回归，未用于调参；排除组X保持退役历史诊断，三点弯也不再宣称未见holdout。

新受控 DEV：156案例/936帧；TEST：234案例/1404帧，26场景、3种新背景过程，TEST算法/参数/生成器/评价器在生成前冻结，输入/GT在检测前冻结，执行一次。TEST 1107帧可观察正例：A确认1065（96.21%），C_FULL确认833（75.25%）；二维条件MAE 40.46→40.53px，P95 286.86→279.73px；全正例拒绝或>8px 271→432帧。C撤销157帧原本A≤8px结果，又把19帧从≤8px改到>8px。216阴性中误确认108→90；这项下降不能抵消正例损失。强假尾族修复为0独立案例，不支持宣称解决473型长尾。

|algorithm|coverage|conditional_MAE_2d|conditional_P95_2d|all_positive_mean_penalized_loss|negative_false_confirmed_n|A_correct_revoked|A_correct_changed_gt8|

|---|---|---|---|---|---|---|---|

|A0|0.9621|40.4639|286.8617|14.8042|108.0000|0.0000|0.0000|

|C_BASE|0.4571|37.3093|291.0194|23.6212|45.0000|450.0000|0.0000|

|C_ROI|0.9061|41.5030|290.9241|15.7446|103.0000|54.0000|0.0000|

|C_SCALE|0.2809|40.4726|290.9845|27.1585|31.0000|604.0000|0.0000|

|C_NOISE|0.4788|36.1797|291.0804|23.1801|47.0000|432.0000|0.0000|

|C_PHOTO|0.4571|37.3093|291.0194|23.6212|45.0000|450.0000|0.0000|

|C_TIP|0.4878|34.8723|292.0304|22.5217|53.0000|419.0000|0.0000|

|C_FULL|0.7525|40.5286|279.7277|18.2877|90.0000|157.0000|19.0000|

表内误差仅是程序可观察GT，非真实物理精度。配对共同确认的帧平均误差变化+1.82px；校正为共享渲染pair/单case聚类后的区间见case_bootstrap_ci.csv。原冻结统计文件保留，统计修正没有触发重测或改参。已曝光真实组没有人工GT：物理尖端误差、真实改善帧数均N/A；PHASE_UNKNOWN。

输出长度为 `(T−(P1+P2)/2)·u`，u=(dy,−dx)/|P2−P1|，原图右向投影px；不冒充根部弧长，不沿用其他试件mm比例。CSV失效值为空+validity，画面显示0+有效位。

原生 A 预解码完整核心六组最慢55.3822ms，开发组H53.8664ms，均小于66.67ms。C仅Python研究耗时，未实现/测量原生C；15FPS视频是演示速度，不表示C满足15Hz。

实际媒体、逐帧PNG、CSV、冻结证据、失败实验、源代码从本目录index.html和../07_media/index.html进入。没有新的真实独立试件/人工标注是本轮已确认的数据限制。

adaptive_universality_results

# 自适应与普适性

同一全局P配置运行26类受控场景及6组已曝光真实数据；没有试件名/路径/帧号/GT条件分支。38项合同测试含元数据改名不变、GRAY8/16显式编码、尺度/噪声趋势、光度失败UNKNOWN、坐标回投、root/path可选及C_BASE/C_TIP共享搜索图。

C_BASE为新研究系统的基线，A0为完整冻结原生系统；A内部ROI/响应没有被无损注入替换，A↔C是系统级对照。C_ROI/C_SCALE/C_NOISE/C_PHOTO/C_TIP均相对C_BASE只启用对应开关；其中C_TIP与C_BASE同搜索图/响应/尺度/噪声，尖端定位机制单独改变。C_FULL联合全部，不能把其收益归于某一模块。

真实A的clean/auto参考模式沿用原归档，以确保原始结果完全复现（开发组A/验证组C/开发组Hclean，CT2/排除组X/三点弯auto）；这不是本轮用真实结果选择的参数。C自身所有组使用同一P规则。受控DEV/TEST的A统一auto，16位按固定round(code/257)适配；原生A内部逻辑没有改动。

全局动态ROI由标距、路径/新种子及前方余量确定，最多一次更新、有空间/像素上限；尺度由剖面FWHM估计三尺度并真正参与响应；噪声由稳定材料高通MAD及量化下限确定；光度用稳健仿射FIT及独立HOLDOUT验证。所有实际参数、角点、采样步长、扩域原因和UNKNOWN状态见adaptive_params_per_frame.csv；数值常量审计见adaptive_policy.yaml及01_audit/all_numeric_literals.csv。

新TEST采用新种子、新背景随机过程、新分辨率，尺度/运动参数独立抽样但支持区间部分重叠；data_split_manifest.json最初24族草稿不代表最终26族，最终actual_data_split_manifest.json及冻结manifest列明。不是全新物理材质验证。

可以统一执行，但不等于统一可靠：C_FULL覆盖下降、保护失败、ROI反事实不稳定，不能宣称已具备跨材料精度泛化。饱和、极弱线、宽度快速变化、强表面纹理、急弯/多分叉和局部非刚性运动仍是限制。

真实状态变化（不含参考；坐标接近/改变均非精度证据）：

|dataset_alias|algorithm|current_frames|tip_confirmed|root_valid|path_valid|A_valid_C_invalid|A_invalid_C_valid|coordinate_change_gt8|

|---|---|---|---|---|---|---|---|---|

|group_a|A0|550|497|499|496|0|0|0|

|group_a|C_FULL|550|306|499|296|198|7|16|

|group_c|A0|561|543|546|543|0|0|0|

|group_c|C_FULL|561|289|546|245|263|9|81|

|ct2|A0|467|403|467|403|0|0|0|

|ct2|C_FULL|467|134|467|133|297|28|45|

|group_h|A0|409|345|358|344|0|0|0|

|group_h|C_FULL|409|358|358|89|44|57|242|

|group_x|A0|523|269|480|263|0|0|0|

|group_x|C_FULL|523|252|480|174|141|124|70|

|three_point_bend|A0|519|445|448|428|0|0|0|

|three_point_bend|C_FULL|519|113|448|104|341|9|32|

tip_accuracy_and_abstention

# 尖端误差、拒绝和统计单位

|algorithm|coverage|conditional_MAE_2d|conditional_P95_2d|all_positive_mean_penalized_loss|negative_false_confirmed_n|A_correct_revoked|A_correct_changed_gt8|

|---|---|---|---|---|---|---|---|

|A0|0.9621|40.4639|286.8617|14.8042|108.0000|0.0000|0.0000|

|C_BASE|0.4571|37.3093|291.0194|23.6212|45.0000|450.0000|0.0000|

|C_ROI|0.9061|41.5030|290.9241|15.7446|103.0000|54.0000|0.0000|

|C_SCALE|0.2809|40.4726|290.9845|27.1585|31.0000|604.0000|0.0000|

|C_NOISE|0.4788|36.1797|291.0804|23.1801|47.0000|432.0000|0.0000|

|C_PHOTO|0.4571|37.3093|291.0194|23.6212|45.0000|450.0000|0.0000|

|C_TIP|0.4878|34.8723|292.0304|22.5217|53.0000|419.0000|0.0000|

|C_FULL|0.7525|40.5286|279.7277|18.2877|90.0000|157.0000|19.0000|

共同确认样本仅818帧，不能代表全部1107正例。A/C共同确认的逐帧平均误差差为+1.8228px；把每个共享渲染pair/独立case先平均后聚类bootstrap的估计如下，估计量与逐帧平均有意分开。

|metric|n_cases|delta_mean|ci95_low|ci95_high|

|---|---|---|---|---|

|penalized_loss_C_minus_A|180|3.541967212869392|2.159161777165054|4.913578450621626|

|common_confirmed_error_C_minus_A|162|1.7524312872301484|1.5715115372930288|1.921294386914496|

|coverage_C_minus_A|180|-0.20046296296296293|-0.24490740740740738|-0.1574074074074074|

|common_projection_abs_error_C_minus_A|162|0.7990690143932316|0.653380341292116|0.9545384471092663|

absolute_metrics_cluster_ci.csv补充ALL及各背景的MAE、P95、覆盖、条件>8px、全正例失败率和阴性率95%区间：帧加权比值，按shared-render-pair/single-case进行2000次bootstrap。不存在把同序列6帧当独立样本的区间。误差阈值8px、拒绝成本32px、误差封顶64px为事前研究门槛，非用户确认的业务容差。

coverage_error_curve.png / CSV仅描述冻结分数的排序子集；未据其挑选阈值或删掉困难帧。不可观察但形成的裂纹独立列出，不以虚构零误差纳入可观察尖端精度分母。216阴性中包含无裂纹/参考线等程序类别；50%的A阴性误确认反映这些标签/外观的歧义，不能据此重标或筛除负例。

全部1188形成正例（含81帧闭合/不可辨识、无可见端点GT）也保留完整确认分母：

|algorithm|all_formed_positive_n|all_formed_confirmed_n|all_formed_confirmation_rate|unobservable_formed_n|unobservable_confirmed_n|

|---|---|---|---|---|---|

|A0|1188|1119|0.9419|81|54|

|C_FULL|1188|875|0.7365|81|42|

不可观察形成正例的确认不能自行解释为正确；其尖端误差N/A。主要精度/风险门槛按事前约定的1107可观察正例计算，没有在看TEST后变更分母。

failure_root_causes

# 失败定位：观测证据与推断分开

TEST A正确但C撤销157帧：120 NO_SUPPORTED_CURRENT_ENDPOINT，13 ROI_LIMITED_OR_FORWARD_AUDIT_UNAVAILABLE，12 H_CONTINUE_COMPETES_WITH_STOP，12 MULTIPLE_SUPPORTED_TRANSITIONS。这是实际输出条件，不等价于157个已验证的物理原因。各候选before/after/heldout/margin/origin条件见A_correct_rejection_conditions.csv。重叠条件计数（不相加）：{"total": 157, "any_candidate_low_or_missing_before": 16, "any_candidate_post_not_low": 140, "any_candidate_low_heldout": 32, "has_continuation": 20, "all_margin_failed": 0, "all_origin_failed": 0, "any_supported": 12}。

1. 局部证据判据比A更保守。法向最大响应含选择偏差；实际宽度、纹理、弯曲、弱渐浅会使前后窗/半步验证不同时通过。120帧无受支持端点，不能全部归因配准。要对具体因果归因仍需新DEV干预试验；本轮TEST不再调参。

2. 前方审查余量和搜索图耦合。TEST反事实ROI放大1.5倍时，10条原已确认结果消失或移动>2px，独立ROI稳定性未过。扩域会改变选路和候选集；虽然root不再硬性要求，搜索域仍会限制尖端证据。

3. 高分强假尾未被区分。strong_serial_false_tail中A过长54帧/9独立案例，C修复0独立案例；强纹理/尾部仍有可见暗线，局部before高/after低会把表面线的终点当裂纹终点。参考同形线仅记录H_FALSE_BRANCH，光度变化仅有界排序辅助；两者都没有提供足以区分物理归属的独立信息。matched true/false controls共享当前外观但参考不同，不能声称当前灰度端点就是物理裂纹端点。

4. 曲线与分叉。三条±20°前方射线、有限候选和窗口假设会在弯曲/纹理上产生竞争或选错。S_curve、curve55、curve75、weak_fading_tip保护门槛均失败；真实长裂纹新增“已确认截短”计数为0，但这不等于未拒绝真长样本。

5. 光度/几何。失败拟合→UNKNOWN，不当作裂纹反证；phase-correlation采用高通纹理，FIT与HOLDOUT分开。已验证同张图的空间独立patch仍相关，并非独立传感器证据。真实局部非刚性和点误差不能仅由两点确定。

受控各族机制、修复/误伤逐例见TEST_mechanism_by_family.csv及failure_matrix.csv。真实CT2 num6/18/84、排除组Xnum51/473和三点弯关键帧见05_regression/known_historical_cases.csv及候选日志，只有算法状态变化，没有人工GT，不能报“真实修复成功”。

失败的DEVv1（oracle及早停事件不足）和DEVv2、合同失败与修正均保留09_dev_archive及00_protocol/DEV_v*_addendum.md。所有实质参数/算法修正发生在TEST生成前。冻结后仅修复工具导入、显示排版及统计聚类，不再检测TEST。

physical_accuracy_limits

# 真实精度边界

用户已确认暂无新真实试件/独立人工尖端GT，先完成受控验证。所有真实组均已曝光；三点弯不再作为新holdout，排除组X仍退役。真实尖端误差、真实改善数、物理裂纹长度精度均N/A。无同步载荷/触发数据，PHASE_UNKNOWN；不采用单调扩展先验，不回填上一帧尖端，不把疲劳闭合当成永久变短。

GT是新程序渲染的可观察端点：以裂纹/无裂纹反事实图像差，在光栅化、变形和理想量化后检查可见信号，分开formed_tip与observable_tip。它不等于显微材料中的真实裂纹尖端。两点只能给参考几何框架，不能唯一恢复整个试件的非刚性变形。参考帧已有裂纹可运行，但相同外观暗线的物理归属仍可能不可识别。

本轮未用历史材料的1.0753e-2mm/pixel强行换算所有试件。主要量为原图像素尖端与相对P1—P2基准线的右向投影；legacy_arc独立带validity，禁止把投影称为完整实际裂纹弧长。

release_decision

# 发布决策与五个明确回答

**KEEP_A / C_RESEARCH_ONLY**。完整逐项门槛见04_results/gate4_comprehensive.json，不因部分阴性下降或P95下降跳过保护失败。Gate4未过，按任务书跳过Gate5，不编译/替换C DLL，也不修改A默认接口。

1. 二维尖端误差没有证明下降：条件MAE40.46→40.53px，共同确认帧平均+1.82px；A原正确157帧被撤销、19帧被改错，覆盖96.21%→75.25%。条件P95下降不足以抵消全分母风险上升。

2. 强假尾和真长尚不能有效区分：强假尾修复0独立案例。当前端点前高后低、前方无连续证据且有足够余量时可给研究确认；证据竞争/不足则UNKNOWN。但灰度可见端点仍可能是表面线终点。

3. 一套规则能够跨输入执行，不能据此保证跨材料准确；ROI反事实10条失稳，弱线/曲线保护未过，无真实新材料GT。

4. 可以不依赖root/完整path确认尖端并算投影：38项合同通过，TEST有42帧在root或path无效时尖端≤8px。逐例日志可核验；不代表总体算法已合格。

5. 尚未证明C原生最坏66.67ms，因为按Gate4失败未开展C++。冻结A本次六组最坏55.3822ms、开发组H53.8664ms，计时仅预解码核心；C仅有Python研究剖析。最小成果是独立测量合同/可选root路径、真实运行自适应模块、候选诊断、冻结协议及保留失败的验证包；继续KEEP_A。

后续若继续，应开新的DEV/独立TEST轮次，聚焦强假尾与真长的可辨识性、局部证据校准及急弯覆盖，不能对本轮TEST补调参后再宣称独立验证。此为研究建议，不是本轮已经实现的修复。
