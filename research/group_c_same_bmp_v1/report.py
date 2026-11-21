"""Chinese evidence report from executed audits; no detector or parameter change."""
from analyze import *
from collections import Counter
import re

def fmt(v):
 if v is None or v=='':return 'N/A'
 if isinstance(v,float):return f'{v:.5f}'
 return str(v).replace('|','/').replace('\n',' ')
def table(headers,items):return '| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(fmt(v) for v in r)+' |\n' for r in items)+'\n'
def doc(name,s):(OUT/name).write_text(s,encoding='utf8')
def main():
 assert read(OUT/'controls_audit_complete.json')['frozen_sha_unchanged'];config=read(OUT/'inputs.json');points=config['points'];cases={n:load_case(n) for n in 'ABCD'};images=[r for r in rows(OUT/'input_provenance.csv') if r['kind'] in ['reference','current']];point_sources=[]
 m,_,_,_=module();assert points['R_G']==[list(m.P1_REFERENCE),list(m.P2_REFERENCE)]
 for name,pts in points.items():
  source=OLD/'regression/metadata.json' if name.endswith('G') else Path(config['tracking_source']);point_sources.append(dict(kind='points',point_set=name,original_path=str(source),file_sha256=sha(source),points=pts,coordinate_system='original_image_xy',tracking_num=(0 if name=='R_S' else config['tracking_num']) if name.endswith('S') else None,point_source='task frozen reference defaults' if name=='R_G' else 'saved original NCC; independently rerun exact' if name=='C_G' else 'original tracking TXT num record',image_reference=config['reference_original'] if name.startswith('R') else config['current_original']))
 save(OUT/'input_provenance.csv',images+point_sources);save(OUT/'point_provenance.csv',point_sources)
 source_lines=Path(config['tracking_source']).read_bytes().decode('gb18030').splitlines();chosen=[line for line in source_lines if int(re.findall(r'\d+',line)[0]) in [0,config['tracking_num']]];doc('tracking_source_records.txt','\n'.join(chosen)+'\n')
 # Posthoc reachability near the approximate endpoint and the golden computation trace.
 reach=[]
 for name,case in cases.items():
  aa=case['arrays'];xa,ya,xb,yb=aa['crop'];sampled=np.zeros_like(aa['valid_material']);
  for r in case['candidates']:
   if r['mode']=='joint':sampled[int(r['y'])-ya,int(r['x'])-xa]=True
  for region in ['approximate_anchor_3px','A_joint_observed_trace_3px']:
   mask=np.zeros_like(sampled);centers=[[2423,2344]] if region.startswith('approx') else [[int(r['x']),int(r['selected_y'])] for r in trace('A') if r['is_observed']=='True']
   for x,y in centers:
    xx=x-xa;yy=y-ya
    if 0<=xx<mask.shape[1] and 0<=yy<mask.shape[0]:mask[max(0,yy-3):yy+4,max(0,xx-3):xx+4]=True
   current=mask&aa['valid_material']&(aa['valley']>=10);joint=current&(aa['newdark']>=10);reach.append(dict(case=name,region=region,pixels=int(mask.sum()),current_accepted=int(current.sum()),joint_accepted=int(joint.sum()),actually_sampled_pixels=int((mask&sampled).sum()),joint_accepted_actually_sampled=int((joint&sampled).sum()),interpretation='Offline approximate anchor/computational path neighborhood, not a newly supplied human full-path GT'))
 save(OUT/'posthoc_reachability.csv',reach)
 abcd=rows(OUT/'abcd_runs.csv');cf=rows(OUT/'geometry_vs_reference_ablation.csv');sensitivity=rows(OUT/'point_sensitivity.csv');sentinels=rows(OUT/'group_sentinels.csv');div=rows(OUT/'first_causal_divergence.csv');mats=rows(OUT/'independent_material_motion.csv');cross=Counter((r['geometry'],r['direction']) for r in rows(OUT/'reference_threshold_crossings.csv'))
 ptable=table(['点集','P1','P2','来源'],[[r['point_set'],r['points'][0],r['points'][1],r['point_source']] for r in point_sources])
 deltas=table(['参考/当前','点','S−G dx','S−G dy'],[[r['coordinates'],r['point'],float(r['dx']),float(r['dy'])] for r in rows(OUT/'point_deltas.csv')])
 allmodes=table(['原生实验','分支','T','暂定端点','近似锚点误差(px)','y0','首观测','有效观测/访问列','末访问x/最大缺失'],[[r['case'],r['mode'],r['threshold'],r['tip'] or 'NO_TIP',float(r['approximate_anchor_error']) if r['approximate_anchor_error'] else None,r['y0'],r['first_observed'] or 'NONE',r['observed_points']+'/'+r['visited_columns'],r['last_visited_x']+'/'+r['maximum_missing_run']] for r in abcd])
 geometry=table(['案例','xleft / xr','upper / lower','xstart','ctr','joint y0 / current y0','位移P1 / P2'],[[name,str(cases[name]['observer']['geometry']['xleft'])+' / '+str(cases[name]['observer']['geometry']['xr']),str(cases[name]['observer']['geometry']['upper'])+' / '+str(cases[name]['observer']['geometry']['lower']),next(r['xstart'] for r in abcd if r['case']==name),next(r['ctr'] for r in abcd if r['case']==name),'/'.join(next(r['y0'] for r in abcd if r['case']==name and r['mode']==mode and r['threshold']=='10') for mode in ['joint','current']),[[r['dx'],r['dy']] for r in cases[name]['observer']['point_translations']]] for name in 'ABCD'])
 candidate_rows=[]
 for name in 'ABCD':
  for r in cases[name]['init']:
   if r['mode']=='joint' and (r['selected']=='True' or name in ['B','D'] and r['y']=='2351'):
    candidate_rows.append([name,r['x'],r['y'],float(r['valley']),float(r['newdark']),r['is_valid_material'],float(r['prior']),float(r['weighted_score']),r['rank'],r['accept_joint_T10']])
 ctable=table(['案例','x','y','valley','newdark','材料通过','prior','联合加权分数','rank','joint T10通过'],candidate_rows)
 commondiv=table(['对照','分歧层','首个共同x','A值','另一值'],[[r['comparison'],r['layer'],r.get('x'),r['a'],r['b']] for r in div if r['layer'].startswith('joint_first_shared')])
 cftable=table(['诊断反事实','分支','T','暂定端点','y0','首观测','有效观测/访问列'],[[r['case'].replace('CF_geometry_','几何').replace('_motion_',' / 位移'),r['mode'],r['threshold'],r['tip'] or 'NO_TIP',r['y0'],r['first_observed'] or 'NONE',r['observed_points']+'/'+r['visited_columns']] for r in cf if r['threshold']=='10'])
 senttable=table(['帧','分支T10','端点','人工误差(px)','y0','联合与current初始化距离','current首选newdark','证据标签'],[[r['frame_id'],r['mode'],r['tip'] or 'NO_TIP',float(r['offline_error']) if r.get('offline_error') else '未标注/无端点',r['y0'],r.get('winner_vs_current_y'),r.get('current_winner_newdark'),r['evidence_tags']] for r in sentinels])
 motiontable=table(['材料窗','位移场','独立匹配NCC','匹配位移','预测位移','位移差(px)','补偿后NCC','去均值残差RMSE','可靠性'],[[r['patch'],r['motion'],float(r['template_peak_ncc']),r['independent_translation'],r['predicted_translation'],float(r['translation_delta']),float(r['aligned_current_ncc']),float(r['zero_mean_residual_rmse']),r['texture_reliability']] for r in mats])
 reachtable=table(['案例','事后区域','当前门通过','joint门通过','joint通过且实际采样'],[[r['case'],r['region'],r['current_accepted'],r['joint_accepted'],r['joint_accepted_actually_sampled']] for r in reach])
 interp=table(['t','joint T10端点','y0','首观测'],[[r['t'],r['tip'] or 'NO_TIP',r['y0'],r['first_observed'] or 'NONE'] for r in sensitivity if r['scope']=='four_point_linear_interpolation' and r['mode']=='joint' and r['threshold']=='10'])
 hypotheses=[dict(hypothesis='H1 geometry',status='CONFIRMED_INTERVENTION_EFFECT',evidence='A geometry + D motion keeps tip; D geometry + A motion loses tip; geometry alone changes feasibility but does not alone reproduce the exact D wrong tip'),dict(hypothesis='H2 reference evidence / veto',status='CONFIRMED',evidence='Fixed D geometry, identical current arrays: changing donor field changes initial score/order and accept; D y2351 newdark=-5.2426 vs A-field5.1552'),dict(hypothesis='H2 physical material misregistration',status='SUPPORTED_LOCALLY_NOT_ESTABLISHED_AS_SOLE_CAUSE',evidence='Two NCC>=.8 fixed material patches show greater D motion discrepancy; photometric metrics mixed, four low-NCC windows, no independent deformation truth'),dict(hypothesis='H3 one-column greedy capture',status='CONFIRMED',evidence='D selects y2282; one observation fixes prediction there; 69px from current first-choice exceeds7px;21 misses then stop'),dict(hypothesis='H3 zero/tie causes actual D failure',status='NOT_SUPPORTED',evidence='D has37 nonzero initial scores and unique weighted winner5.1087; zero tie instead occurs in real reference=first-current sentinel1'),dict(hypothesis='H4 adapter mapping/scale/swap',status='NOT_SUPPORTED_BY_OBSERVED_RECORDS',evidence='Original num236, one-based237, BMP bytes and decoded pixels exact; no adapter point rounding/resizing/swap'),dict(hypothesis='H4 same physical point semantics',status='UNRESOLVED',evidence='G/S centers differ; source click/feature-definition records absent from supplied task/package/tracking manifest; NCC is not point-semantic truth')]
 save(OUT/'hypothesis_evidence.csv',hypotheses)
 report=f'''# 验证组C同一BMP：冻结V1根因复盘

## 一句话结论

**已证实：正式P点让起始列由2265移到2255；在这个新首列，参考差分抑制了current首选候选，单列联合排序转而锁到y=2282，±7px局部追踪无法接入相隔69px的另一候选，最终21列缺失停止。原因是几何、参考证据与贪心初始化的耦合，不是单纯“P点不同”或“gap_limit”。材料物理配准失真仅有局部支持，正式点物理语义是否相同仍未解决。**

2026-11-12，已曝光回归/验证案例故障审计，非V2开发、盲测、训练或参数优化。本轮所有检测阈值保持冻结，未把验证组C的较好分支或扰动值选作新默认。生产A、冻结Python、C++ DLL与旧评估不改。图中端点均为provisional，不能当独立物理确认。

## 1. 同图同代码与真实P点身份

两张BMP均5120×5120、8-bit、无压缩、正高度bottom-up存储；解码后uint8。文件SHA、ASCII中转SHA、OpenCV imdecode与冻结imread结果、Pillow转灰度全部一致，无EXIF方向信息。没有重编码、缩放或GT裁切。当前`3 (175).bmp`在正式序列是frame_id=237，对应原始TXT num236；参考是frame1/num0，不把文件名175当全局序号。

冻结Python SHA256 `{SHA}`，当前仍精确匹配任务书。真实原始跟踪源为`{config['tracking_source']}`，SHA `{config['tracking_sha256']}`；原始num0/236行已存[tracking_source_records.txt](tracking_source_records.txt)。点以十进制原精度传入，没有预取整。黄金参考点还核对了冻结源码默认常量；黄金当前点经本轮原始CLI NCC重跑精确复现。完整[输入身份核验](input_identity_audit.md)、[机器记录](input_provenance.csv)。

{ptable}
S−G四点差：

{deltas}
当前中点从(2250.875,2343.875)到(2245.98,2349.675)，y相差5.8px；x右端2259→2248.22，ceil后2259→2249。参考上下间距183.75→188.76，当前上下间距182.75→185.39。当前P2的x差−15.26px，不能把这四点输入差异笼统说成全部是“小数误差”。

## 2. A/B/C/D真实执行结果

A=R_G/C_G；B=R_G/C_S；C=R_S/C_G；D=R_S/C_S。四组均先独立原始Python CLI，再只读观察器执行。每组六行summary和六份逐列trace与未观察CLI完全相同，overlay解码像素也完全相同。A六档与旧黄金记录逐列相同，D六档与旧正式237帧逐列相同；两个重放Gate均通过。

{allmodes}
上表误差只相对任务书的**近似回归锚点**(2423,2344)，不是为237帧新增的LabelMe真值；该BMP不在旧20个可见选帧中，不能拿A/D结果直接解释“20帧中0命中”的统计分母。其他4个代表帧另用真实人工标签评分。B的joint T8也失败，所有档位照实保留，不能只展示B的T10成功。

{geometry}
只替换当前点的B、只替换参考点的C在T10仍到达近似端点；这排除了“任一套S点单独出现就必然失败”的解释。B/C轨迹与A并非全部相同：端点近似相同不能代替逐列一致性。

## 3. 第一条决定路线的离散决策

第一条路线决定就是首列的argmax。A在x2265选y2332；D在x2255选y2282。因为起始x也不同，不能把两条trace第0行称为同一列。D相对自己current分支（同几何、同当前灰度）则是同一x2255上的y2282与y2351之争。

{ctable}
在D，y2351的材料门通过、valley=27.3987、prior=0.999515，本来是current首选；但newdark=−5.242615，使联合score及加权分数为0，且必定不满足newdark≥10。y2282的valley=16.0352、newdark=20.4243、prior=0.282291，加权得分5.108664，为唯一第一名，也通过两个灰度阈值。第二名y2387得4.103677，差1.004987；D有37个非零初始化分数，**不是全零argmax或近乎机器精度tie导致本帧错误**。

D只有首列一次有效观测(2255,2282)。后续预测中心一直2282，未获得5个观测启动方向拟合；搜索大致y2275…2289。它与current首选的纵距69px、与A首观测纵距50px，均远大于7px半宽。在共同x2265，A选2332且accept=True，D选2279但accept=False，missing_run已经10。D在x2276累计21列缺失退出，最终tip保留最后有效像素2255,2282。`gap_limit`是这一错误起源之后的停止现象，不是最初原因。

{commondiv}
完整首列逐y分数/排名/材料/阈值状态见[initial_candidate_audit.csv](initial_candidate_audit.csv)；真实被采样的每列全部y候选与merit在各runs目录`column_candidates.csv`，可在[交互逐列查看器](trace_audit_A_B_C_D.html)切换case/mode/x。首30列单独导出[first_30_columns.csv](first_30_columns.csv)。数组比较使用共同原图坐标并分别统计1e-6、0.1和1灰度差阈值，未把光栅扫描遇到的第一个浮点差当根因。共同实际采样ROI内ca/csm/valley/flank_low/valid_material全相同，见[current_evidence_common_ROI_gate.csv](current_evidence_common_ROI_gate.csv)；整裁剪边缘的np.roll/平滑差别不冒充首列决策原因。

## 4. 几何与参考的两因素控制

以下均标记**诊断反事实，不是原生V1结果或新算法精度**。保留几何组的当前图裁剪、ROI、ctr、候选边界及当前证据，仅在参考remap前替换alpha/dx/dy为供体A或D的原公式值。不同几何网格需要在其坐标上计算同一个供体位移函数；共同全局坐标上的alpha/dx/dy/reference_aligned逐像素完全相同，并非用GT外推。固定几何时ca/csm/valley/flank_low/roi_mask/valid_material均完全一致。

纯A/A与D/D：13种数组各自逐像素相同，所有六模式summary和完整trace相同，证明诊断副本镜像成立。只改诊断副本，原冻结SHA未变。

{cftable}
A几何+D位移仍成功，因此“D参考位移场本身足以让所有几何失败”不成立。D几何+A位移已无端点，说明提前10列的几何改变足以让A的原结果丢失；但它并不产生D的同一个错误端点。D几何+D位移才锁y2282。

固定D几何时，A位移场下y2351的newdark=5.155151，虽然使score非零，仍低于T10；初始最高候选为y2352，周围缺少联合合格观测，故NO_TIP。换D位移后y2351变为−5.242615，排序改到69px之外的y2282并接受。**初始化使用连续score×prior，不先强制valley与newdark都≥T；初始化和后续接受是两道不同规则。** 这同时解释“初始分数最高却完全无观测”的反事实。

首1/20/100个固定ROI列（不等同于实际访问长度）、黄金joint轨迹邻域及D current轨迹邻域的材料/暗谷/联合通过率见[reference_evidence_rates.csv](reference_evidence_rates.csv)。固定几何、只换位移的前100列中，A→D的newdark跨阈值降级候选数：A几何{cross['A','A_pass_D_veto']}，D几何{cross['D','A_pass_D_veto']}；反向升级数量A几何{cross['A','A_veto_D_pass']}，D几何{cross['D','A_veto_D_pass']}。每个候选的原图坐标和灰度见[reference_threshold_crossings.csv](reference_threshold_crossings.csv)，不是只统计均值。

## 5. 有证据但未采样，与材料物理配准证据等级

{reachtable}
这些邻域在推理完成之后计算：近似锚点来自任务书，A轨迹是计算对照，**不是独立人工完整路径GT**。原始BMP/候选窗口图展示D远处仍有可接受证据，但D短走廊没有到达它；不能因此把观察到的所有暗线都认证为物理裂纹。没有将它们送回检测器重置起点。

在固定、与GT无关的上下材料纹理候选窗独立做±20px NCC，并比较A/D补偿后的NCC和去均值残差。窗口位置只由P几何及事前固定偏移450/850/1250决定，未把独立估计写回V1。

{motiontable}
只有两窗峰值NCC≥0.8，分别0.92865/0.83803；其余四窗为LOW_NCC，不能当可靠位移真值。两个高相关窗均得到整像素位移(−1,5)：A场偏差约0.170/0.826px，D约1.001/1.497px。下侧高相关窗补偿NCC由A0.85856降为D0.76148、去均值RMSE由4.7830升为6.0692；上侧差异较小且MAE与NCC排序不完全一致。加上P点自身NCC与正式当前记录的1.4289/1.1866px差距，**局部支持D粗补偿存在位移不一致，但没有独立稠密变形真值或人工认证无裂纹材料mask，不足以认定整体物理配准失真，更不能将它作为唯一根因。**

## 6. 点语义H4与全零argmax

原始TXT→项目零基frame_id236→正式一基frame237→BMP哈希的映射全部一致，未发现本轮adapter的x/y交换、显示缩放、裁剪坐标或提前取整。对各自参考中心的NCC：G两点相关性0.99405/0.98509，恰好复现C_G；S两点0.99450/0.98492，却得到(2247.46,2255.77)/(2243.49,2443.53)，与正式C_S差1.43/1.19px。这是**记录值与另一个测量器的差异**，不是把正式点判成错误的依据。

G与S的参考中心本身不同，截图红框中心/原点击语义与物理特征定义没有在本次任务书、包、TXT或manifest中提供可核对的原始记录；也没有独立采集同步证据推翻已有num约定。点位图只展示真实数值，不能证明其物理语义相同或不同。H4语义保留UNRESOLVED。

实际首帧1提供全零反例：R=C、零位移，rsm=csm，newdark全零，joint全部初始分数零，np.argmax选择init_ys的第一个y2258，随后21列无观测停止。current仍有暗谷响应。这个真实反例说明全零行为存在，但**不能把它套用到D，D的37个非零分数和唯一winner已直接反证**。见[zero_initialization.png](figures/zero_initialization.png)。

## 7. 预定义输入扰动

在ABCD前保存了[sensitivity_plan.json](sensitivity_plan.json)：A/D各45组（共同y平移7、仅当前11、仅参考11、四个单点分别y±2/±5共16），再加四点A→D插值11，共101组、606模式。单点扰动轴明确为y；x差异包含在真实A/D和四点插值中，没有独立单点x扫描。全部是结构敏感性实验，不是实际追踪误差分布，不选最优参数。所有零扰动和插值端点控制都与原生A/D六模式逐列相同。

A仅当前两点y−4确实得到joint T10=(2285,2307)，复现任务书的待证扰动现象；y−5也如此。参考与当前共同平移的A七档均保持(2423,2344)，D共同平移前六档保持错误端点，+5变NO_TIP。共同平移并不数学上保证所有图像采样不变，原位移函数alpha还依赖当前P的y，这里只报告实测稳定/不稳定。

{interp}
从t0.6的正确近似端点到t0.7的错误端点是**预定0.1采样网格上**第一次终点大跃迁，不能声称精确临界值就是0.7；未追加细化搜索。t0.8无输出同样保留。所有点、y0、首观测、首次共同x分歧、首次无支持位置和六模式端点见[point_sensitivity.csv](point_sensitivity.csv)。首次失败原因字段只描述所选被拒像素，不冒充全部候选的物理因果。

## 8. 同组其他帧：复用机制及不同机制

237不属于既有20个LabelMe选帧，因此额外选择4个不同VISIBLE帧38、1、232、7，均按原追踪点真正同输入回放，并与旧六模式trace完全一致。选择来自旧报告预先确定的分歧/无输出/远错误类别，不改变推理。标签只在全部ABCD、控制、101扰动和代表帧推理完成后用于离线评分。

{senttable}
帧232与D最相近：joint首列选y2283、current首选y2352，差69px；current候选newdark=−1.519，joint错误约176.01px，current约0.714px。38/7也有排序抑制，分别偏离current首选36/20px，但联合winner的newdark仅3.416/2.984，不形成有效观测，所以是NO_TIP而非D的“先误观测再停止”。帧1是参考中已有全部相同结构导致newdark全零。**4个复核帧中1个复现D式错首观测、2个为联合排序/阈值不足无输出、1个为全零增量退化；这不能外推成整组20帧或562帧的原因占比。**

current输出接近端点也不保证完整路径正确。38/232首观测与人工路径距离约10.68/12.80px，故不能以最终误差小反证其起点语义。1/7 current端点误差较大且首观测距人工路径>10px，本报告将其保留ROI/INIT_GEOMETRY+UNRESOLVED，未无证据地标成“已锁正确后丢失”。证据标签允许重叠，不是互斥物理真值。

## 9. 假设结论与最小后续建议

{table(['假设','证据等级','支持/限制'],[[r['hypothesis'],r['status'],r['evidence']] for r in hypotheses])}
值得讨论V2，但只建议首先针对**起点身份与参考差分缺失的耦合**做一个可独立证伪的机制改动：把起源可信度/参考证据状态明确分开，并在开发数据及合成控制上预注册验收规则。不能简单全局切current（A current本身失败），不能把B的错配点或“dy−4避开值”当推荐参数，也不能只放宽ROI或增大gap来掩盖错首锁。材料运动改进需要独立纹理/点语义证据；本任务没有实现V2、没有修改生产或冻结V1，也没有以验证组C选择下一版参数。

## 10. 运行、可重复性与交付

实际执行：114次原冻结Python（5次独立CLI，109次观察器/输入扰动/代表帧）、4次明确诊断反事实，共118次Python六模式执行；另有4次C++辅助对照。上述114包括用于观察器对照的重复A/B/C/D，不能当114张独立图像。C++只作一致性附表，未用它替代原Python解释。

观察器只读frame.f_locals，未写回变量；8组主要/反事实共16份T10逐列候选记录与原trace逐列一致；纯A/A、D/D的26份数组完全一致；原生四组的CLI图像解码像素一致。全部异常日志和失败/NO_TIP输出保留，没有静默丢分母。复现完整命令见[reproduction_commands.md](reproduction_commands.md)，已执行阶段的真实原图和argv在各run/observer.json或cli_identity.json中。

优先查看：[交互逐列图册](trace_audit_A_B_C_D.html) · [54秒证据视频](root_cause_walkthrough.mp4) · [ABCD四联图](figures/same_bmp_ABCD_overlay.png) · [首个分歧图](figures/first_divergence_panels.png) · [控制矩阵](geometry_vs_reference_ablation.csv) · [验收矩阵](acceptance_matrix.csv) · [完整性](final_integrity.json)。

为遵守项目当前生成文件只能在output内的约束，本轮使用新的`output/diagnostics/group_c_same_bmp_root_cause_v1_20261112_r01/`，没有写到项目外或覆盖旧评估。当前BMP没有独立完整路径标注，物理语义/配准真值不足处明确保留UNRESOLVED；它们不是捏造已经完成的物理因果证明。
'''
 doc('ROOT_CAUSE_REPORT.md',report)
 identity='# 输入身份与调用链审计\n\n'+table(['角色','完整原图路径','文件SHA256','解码uint8数组SHA256','shape/bpp'],[[r['kind'],r['original_path'],r['file_sha256'],r['ndarray_sha256'],r['shape']+'/'+r['bits_per_pixel']] for r in images])+ptable+deltas+'''原始记录采用GB18030读取，四个坐标保留原精度；源TXT没有图像文件名，映射沿用已记录的num=项目零基frame_id，正式评估frame_id=num+1。对照项目manifest中对应图片完整路径、filename和图像SHA逐一一致。来源行、manifest、旧adapter/worker版本均在run_identity记录。没有独立采集日志可额外认证上游num语义；本轮未发现执行层映射不一致。

旧黄金与新NCC重跑/current显式传入彼此一致。A/D重新执行旧summary与完整trace完全一致。所有原生调用只传reference/current、P点和输出路径；没有gt-tip、right-edge或阈值覆盖参数。模板29、search25、NCC0.8和所有检测常量均来自冻结源。

BMP存储高度正值，解码器按正常BMP方向恢复；无EXIF方向字段。OpenCV imdecode原始字节、ASCII staging imread和Pillow L数组逐像素一致。灰度读入不会改变原文件；没有翻转、旋转、重采样或截取后作为输入。更多字段见input_provenance.csv。读取路径与数组hash只说明同输入身份，不能证明物理点语义相同。
''';doc('input_identity_audit.md',identity)
 doc('reproduction_commands.md',f'''# 环境与准确复现命令

工作目录`{ROOT}`。Python3.12.7 / OpenCV4.12.0 / NumPy1.26.4 / SciPy1.17.1，完整环境和工具SHA见run_identity.json。每次原始CLI/观察器argv及耗时分别在runs/*/cli_identity.json或observer.json；本次原生main耗时包含输出与绘图、观察器开销，不是内核或部署性能基准。

```powershell
Set-Location .
$env:PYTHONPYCACHEPREFIX='./output/pycache'
$env:PYTHONIOENCODING='utf-8'
# 选择全新的ASCII目录；已有目录会被拒绝：
& ./research/group_c_same_bmp_v1/reproduce.ps1 -Output './output/diagnostics/group_c_same_bmp_root_cause_v1_replay01'
```

同一复现脚本随证据复制在scripts/，也可从那里调用。它先校验图片/源身份并执行原生ABCD，再运行纯控制与交叉控制、101个预定义扰动、4个可见代表帧，然后离线标签、图表、报告、封存。不引入GT作为参数；不修改任何冻结规则。脚本默认输出目录指本轮，直接重跑会拒绝覆盖；新复现必须设GROUP_C_AUDIT_OUTPUT或使用上面的-Output。

分步入口：`run.py primary`、`run.py controlled`、`run.py sensitivity`、`run.py sentinels`、`analyze.py`、`controls_audit.py`、`visualize.py`、`report.py`、`seal.py`。当前实际执行中sensitivity与sentinels并行，评分等待两者完成；新编排顺序执行，算法输出应一致，时间不应直接等同。完整新编排仅做语法/安全路径检查，不为检查编排而再重复一次118次执行；各阶段均已真实运行。

输入文件依赖：原始F盘两张主BMP和4张同组已标注代表帧、data/anchors验证组C原始TXT、data/inputs六组manifest（仅选验证组C）、前轮冻结输出作为只读比较、四个人工LabelMe记录作为推理后离线比较。旧代码不作为运行依赖；冻结根源码是唯一算法来源，旧结果只用于核对。

诊断副本由冻结源AST插入一条alpha/dx/dy供体替换，写入scripts/diagnostic_motion_copy.py，供体函数在core.py。没有改滤波、ROI启发式、阈值、初始化或track。该副本不能作为生产V1发布。脚本快照、原源码副本、source_diff.patch与每个产物哈希随最终清单保存。
''')
 acceptance=[('IMAGE_BYTE_AND_DECODE_IDENTITY','PASS'),('TRACKING_NUM_AND_PRECISION','PASS'),('ORIGINAL_ABCD_24_RESULTS','PASS'),('A_OLD_GOLDEN_AND_D_OLD_SEQUENCE_TRACE','PASS'),('OBSERVER_UNMODIFIED_CLI_AND_PIXELS','PASS'),('PURE_COUNTERFACTUAL_AA_DD_ARRAYS_AND_TRACE','PASS'),('GEOMETRY_REFERENCE_TWO_FACTOR_ISOLATION','PASS'),('FIRST_COLUMN_FULL_CANDIDATES_AND_DECISIONS','PASS'),('FIXED_SENSITIVITY_101_CASES','PASS'),('GOLDEN_PLUS_4_VISIBLE_SENTINELS','PASS'),('PHYSICAL_MATERIAL_REGISTRATION_GROUND_TRUTH','UNRESOLVED'),('ORIGINAL_CLICK_POINT_SEMANTICS','UNRESOLVED'),('NO_V2_NO_TUNING_NO_PRODUCTION_CHANGE','PASS')];save(OUT/'acceptance_matrix.csv',[dict(requirement=k,status=s) for k,s in acceptance]);write(OUT/'report_complete.json',dict(root_cause_computational_chain='CONFIRMED',physical_material_distortion='LOCAL_SUPPORT_NOT_SOLE_PROVEN_CAUSE',point_semantics='UNRESOLVED',native_python_executions=114,counterfactual_python_executions=4,cpp_auxiliary_executions=4,source_sha256=sha(FROZEN),no_v2=True));print('REPORT COMPLETE',flush=True)
if __name__=='__main__':main()
