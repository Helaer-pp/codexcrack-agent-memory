"""Editorial delivery derived solely from sealed inference/evaluation artifacts."""
import argparse, collections, datetime, shutil
import numpy as np
from grayref_roi_geometry_ablation.common import *
from grayref_roi_geometry_ablation.geometry import MODES

def table(records, fields):
    return '| '+' | '.join(fields)+' |\n| '+' | '.join('---' for _ in fields)+' |\n'+''.join('| '+' | '.join(str(r.get(k,'')) for k in fields)+' |\n' for r in records)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    run=Path(parser.parse_args().run);check_sources(run)
    seal=get(run/'completion_seal.json');assert seal['engineering_complete']
    for name,h in seal['files'].items():assert sha(run/name)==h,name
    integrity=get(run/'run_integrity.json');assert integrity['frame_PNGs']==8165
    summary=get(run/'evaluation_complete_group_a.json')['summary']+get(run/'evaluation_complete_exposed.json')['summary']
    geometry=rows(run/'roi_mode_summary.csv');stats=rows(run/'frame_roi_geometry.csv');runtime=rows(run/'runtime_performance.csv')
    paired=rows(run/'paired_ablation_summary.csv');decision=get(run/'decision.json')
    metrics=rows(run/'offline_evaluation_group_a.csv')+rows(run/'offline_evaluation_exposed.csv')
    out=run/'final_delivery';out.mkdir(exist_ok=True)
    compact=[];costs=[]
    for group in GROUPS:
        base=next(r for r in geometry if r['group']==group and r['mode']==MODES[0])
        for mode in MODES:
            r=next(r for r in geometry if r['group']==group and r['mode']==mode)
            part=[v for v in stats if v['group']==group and v['mode']==mode]
            compact.append(dict(group=group,mode=mode,area_remaining_pct=round(100*float(r['area_ratio_mean']),2),nodes_remaining_pct=round(100*int(r['nodes_total'])/int(base['nodes_total']),2),edges_total=sum(int(v['graph_edges']) for v in part),unvisited_budget=int(r['path_budget_not_visited']),containment_deleted=int(r['containment_deleted']),ROI_LIMITED=int(r['ROI_LIMITED']),path_P50_ms=round(float(r['inference_P50_ms']),2),path_P95_ms=round(float(r['inference_P95_ms']),2)))
        # Shared costs appear on all three mode rows; count A rows once per frame.
        rr=[v for v in runtime if v['group']==group and v['mode']==MODES[0]]
        c=dict(group=group,frames=len(rr))
        for key in ['shared_evidence_cache_load_verify_ms','shared_geometry_controller_ms','lineage_audit_ms','render_ms']:
            values=[float(v[key]) for v in rr]
            c[key+'_P50']=round(float(np.median(values)),2)
            c[key+'_P95']=round(float(np.percentile(values,95)),2)
        c['max_worker_peak_MiB']=round(max(int(v['worker_peak_rss_bytes']) for v in rr)/2**20,2)
        costs.append(c)
    csvwrite(out/'geometry_cost_summary.csv',compact);csvwrite(out/'shared_costs.csv',costs)
    gates=[dict(item=k,result=v) for k,v in [('ENGINEERING_COMPLETE','PASS'),('INPUT_COVERAGE','PASS'),('PROTOCOL_FROZEN','PASS'),('GT_LEAKAGE_CHECK','PASS'),('BASELINE_PARITY','PASS'),('ALGORITHM_ACCEPTED','FAIL'),('PRODUCTION_APPROVED','FAIL')]]
    md='# ROI几何单因素：最终交付报告\n\n结论：B、C均为GEOMETRY_HARMFUL / NO_GO。工程完成，算法不通过，不替换生产。默认C事前冻结，未事后按组选择B。\n\n'
    md+=table(gates,['item','result'])
    md+='\n实查GROUP_A551开发、验证组C562/三点弯520曝光回归，共1633帧×3模式=4899份真实推理结果。排除组0；人工标签仅封存后独立进程比较，不训练或调参。原A完整原生结果/图1633帧一致；30帧原BMP/P重算差分最大误差0，30次检测重复一致。8165张逐帧PNG、1633套数值引用、1637个HTML页面、三段视频共1633帧通过核验和完整解码。\n\n'
    md+='[原因与反例](ROI_CAUSAL_FINDINGS.md) · [完整图册](../galleries/index.html) · [原始自动报告](../REPORT.md) · [完整性](../run_integrity.json) · [冻结源码](../source_hashes.json) · [可执行复现](../README.md)\n\n## 实际输出：可见分母固定\n\n'
    md+=table(summary,['group','mode','visible','outputs','no_public','hit3','hit5','hit10','hit20','joint','over100','over500','any_candidate_path_good','GT_EXCLUDED'])
    md+='\nno_public包含不确定/歧义/ROI限制，仍计入可见分母。joint同时要求尖端≤10px及原观测路径覆盖/精度均≥0.8。GT_EXCLUDED此处仅指人工尖端点不在mask，不等价于完整路径没有被裁剪。验证组C266的B/C均产生(2448,2345)暂定尖端，该帧无标签，不能计正确或错误，也不能从54张可见表的零严重错误推断真实FPR=0。真实FPR=N/A。\n\n## 路径与被隐藏的误差尾部\n\n'
    md+=table(summary,['group','mode','path_coverage10','path_precision10','candidate_over100','candidate_over500','last_observed_over100','last_observed_over500'])
    md+='\n候选端点与最后观测点单独列出；无端点不填零误差。最后观测点不是已确认尖端，尾部仅用于路径诊断。\n\n## 几何与成本\n\n'+table(compact,list(compact[0]))
    md+='\n面积是相对A的实际mask像素均值，非包围矩形面积。B保留原完整x范围，只缩y。C真实多分支非矩形mask完整存盘。缩区会释放原每列候选容量，因此节点和邻接边不必按面积同比减少。unvisited_budget是达到6条保留路线后尚未访问的排序尾部，不能声称其中每条都能通过去重。\n\n'+table(costs,list(costs[0]))
    md+='\nA/B/C计时仅缓存证据上的路径引擎，执行顺序固定且有并发/热缓存影响；未宣称全流程等比例加速。共享geometry项还含边界检查与封装，不是纯C内核时间。RAM为单工作进程截至该帧的峰值，不是整机峰值。绘图单列，未混入推理性能。旧特征缓存经SHA核验复用，非本轮新提取特征成绩。\n\n## 逐帧成对得失\n\n'+table(paired,list(paired[0]))
    md+='\n完整状态分布和首败阶段见[离线开发汇总](../evaluation_complete_group_a.json)与[回归汇总](../evaluation_complete_exposed.json)。GROUP_A未知1、三点弯未知5，单独保留；未标注帧不作阴性。两验证组已曝光，不是新盲测；GROUP_A仅19可见样本，不作显著性结论。\n\n## 使用与复现\n\n从项目根目录按[源码README](../../../..//research/grayref_roi_geometry_ablation/README.md)执行run_group_a.ps1，再执行run_regression.ps1，使用全新RunId；后者完成回归、图像、核验及视频。原图/点只读，数值缓存引用需保留上一轮简化运行目录。\n\n视频：[验证组C](../videos/group_c.mp4) · [三点弯](../videos/three_point_bend.mp4) · [GROUP_A](../videos/group_a.mp4)。6FPS是播放速率，不是算法速度。\n'
    # final_delivery sits four levels below the project root.
    md=md.replace('../../../..//research/','../../../../research/')
    write_bytes(out/'REPORT.md',md.encode('utf-8'))
    findings='''# ROI原因与决策：复核版

**GEOMETRY_HARMFUL / NO_GO。** B有一个新增实际成功，但损失原合格路径；C没有新增可见尖端成功，并在三个试件各损失一帧原合格候选。依事前冻结的不可接受退化条件，两者均不通过。不调整本轮参数，不替换生产。

面积确实缩小：按GROUP_A/验证组C/三点弯顺序，B剩余30.45%/30.62%/30.48%，C剩余51.60%/29.40%/63.05%。但三点弯邻接边由A的5,967,386增至B的11,838,323、C的9,397,642；预算未访问尾部由3,197,103增至3,755,488/4,015,740。不能宣称缩ROI普遍解决候选竞争。全序列ROI_LIMITED分别为B的1/1/0帧、C的1/50/4帧；人工尖端排除仍均0，两者口径不同。

1. **收益确实存在，但很局部。** GROUP_A451的B尖端(1356,1161)误差0.98276px，同时通过路径联合标准；原停止后负证据20/24达到旧门槛。A/C仍不确定。B的399个路径点含330观测和69推测，不把推测桥接当作观测。
2. **GROUP_A113：节点保留，连接改变。** 原合格路径73观测点在B/C均保留，未被ROI直接删掉。但新保留的(998,1142)距前点(997,1143)为1px，优先于原后继(998,1145)的2px。冻结一对一匹配改变片段连接，原合格池路径消失。原灰度证据和匹配规则没有改，ROI通过候选容量产生间接效应。
3. **验证组C232：C直接裁掉路径。** 原合格路径168观测点中23点不在C mask，首次为(2256,2336)；B保留全部168点。人工尖端仍在C范围内，所以单看GT_EXCLUDED=0会漏掉这种损失。
4. **三点弯1：节点、邻接仍在，路线预算变化。** 原A合格15点片段在B/C延伸成17点片段；原15点及相邻连接均保留。该17点片段在B为保留路线，离线覆盖/精度仍为1；在C排序rank11，处于路径预算未访问尾部。原A该15点路线rank1保留。不能将此例说成ROI几何直接删除了节点。
5. **候选池改善不等于尖端改善。** 验证组CB由16/20变18/20有合格路径，新增38/95两帧，但正确公开尖端仍0/20。C由16/20到16/20掩盖232损失、95新增。三点弯C由1/15降0/15。
6. **停止与参考仍有限制。** 验证组CB有10/20首败在停止/歧义，新增路线并未自动具备可信停止证据。纹理代理通过只代表局部参考窗口满足冻结门槛，不代表全ROI物理对齐或裂纹身份已认证。低可信区仍保留差分诊断，不能强行用于停止。

上述案例从已封存结果事后选取，只作解释，不回灌算法或重新选参数。数据规模、所有模式和失败帧均保留。全部54个可见尖端都在三种mask内，但完整路径的裁剪和间接图变化依然存在。

**自动报告口径更正：** 根目录原自动生成的ROI_CAUSAL_FINDINGS.md用GT_EXCLUDED（仅尖端点）筛选“正确候选被裁剪”，据此输出“无案例”；该标题过宽。正确说法是“无可见人工尖端点被排除”，不能否定验证组C232的23个原合格路径节点被C裁掉。冻结自动产物原样保留，本复核版明确更正解释，不改推理、评价数字或预注册决策。

唯一后续研究建议仍是隔离检验原A候选池中不同终止跨度的独立保留，不继续在这19张GROUP_A标签上搜索ROI宽度。该后续试验必须保留本轮113/232/三点弯1候选保真反例；它不承诺修复匹配、预算和停止全部问题，本轮未实施。

[GROUP_A详细证据](../case_audit/GROUP_A_CASE_FINDINGS.md) · [113局部匹配](../case_audit/LOCAL_LINK_CAUSE.md) · [回归节点存活](../case_audit/exposed_good_path_survival.csv) · [三点弯路线排序](../case_audit/three_point_1_fragment_routes.json) · [全量成对表](../paired_frame_comparison.csv) · [交付报告](REPORT.md)
'''
    write_bytes(out/'ROI_CAUSAL_FINDINGS.md',findings.encode('utf-8'))
    csvwrite(out/'unlabeled_public_outputs.csv',[{k:r[k] for k in ['group','frame_id','mode','visibility','output_state','error']} for r in metrics if r['visibility']!='VISIBLE' and r['output_state']=='PROVISIONAL_TIP'])
    t0=datetime.datetime.fromisoformat(get(run/'source_hashes.json')['utc'])
    t1=datetime.datetime.fromisoformat(seal['utc'])
    put(out/'delivery_cost.json',dict(freeze_to_core_completion_seconds=(t1-t0).total_seconds(),generated_run_bytes_before_editorial_seal=sum(p.stat().st_size for p in run.rglob('*') if p.is_file()),free_disk_bytes=shutil.disk_usage(ROOT).free,prelabel_development_time_excluded=True))
    print('Editorial reports generated; core seals unchanged.')

if __name__=='__main__':main()
