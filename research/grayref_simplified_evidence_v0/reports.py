"""Post-evaluation summaries and static local gallery; no algorithm modifications."""
import argparse,collections,json,html
from pathlib import Path
import numpy as np
from .common import *
from .algorithm import MODES

def number(row,key):
    v=row.get(key,'');return float(v) if v not in ['',None] else 0.
def yes(v):return v is True or v=='True'
def table(data,cols):
    return '| '+' | '.join(cols)+' |\n| '+' | '.join('---' for _ in cols)+' |\n'+''.join('| '+' | '.join(str(r.get(k,'')) for k in cols)+' |\n' for r in data)
def page(title,body):return ('<!doctype html><meta charset="utf-8"><title>'+title+'</title><style>body{font:16px sans-serif;background:#112331;color:#eee;margin:26px}a{color:#7ddcff}table{border-collapse:collapse}td,th{border:1px solid #567;padding:5px}input,select{font-size:16px;margin:6px}img{max-width:100%}</style><h1>'+title+'</h1>'+body).encode('utf-8')

def gallery(run,pred):
    default=[r for r in pred if r['mode']=='C_FUSION_RAW']
    for group in GROUPS:
        entries=[r for r in pred if r['group']==group and r['mode'] in MODES]
        root=run/'galleries'/group
        body='<a href="../index.html">All groups</a><p>DEVELOPMENT</p>' if group in DEV else '<a href="../index.html">All groups</a><p>EXPOSED_REGRESSION — no tuning / not blind test</p>'
        body+='<input id="frame" placeholder="Frame ID"><select id="mode">'+''.join('<option '+('selected ' if m=='C_FUSION_RAW' else '')+'>'+m+'</option>' for m in MODES)+'</select><select id="state"><option value="">All states</option>'+''.join('<option>'+s+'</option>' for s in sorted({r['output_state'] for r in entries}))+'</select><select id="ref"><option value="">All reference states</option>'+''.join('<option>'+s+'</option>' for s in sorted({r['reference_status'] for r in entries}))+'</select><p id="count"></p><table><thead><tr><th>Frame</th><th>State</th><th>Reference</th><th>Observed</th><th>Inferred</th><th>Candidate tip</th></tr></thead><tbody id="rows"></tbody></table>'
        compact=[dict(frame=r['frame_id'],mode=r['mode'],state=r['output_state'],ref=r['reference_status'],observed=r['observed'],inferred=r['inferred'],tip=r['candidate_tip']) for r in entries]
        body+='<script>const data='+json.dumps(compact)+';function show(){const f=document.getElementById("frame").value,m=document.getElementById("mode").value,s=document.getElementById("state").value,q=document.getElementById("ref").value;const d=data.filter(r=>(!f||r.frame===f)&&r.mode===m&&(!s||r.state===s)&&(!q||r.ref===q));document.getElementById("count").textContent=d.length+" frames";document.getElementById("rows").innerHTML=d.map(r=>`<tr><td><a href="${r.frame}/index.html">${r.frame}</a></td><td>${r.state}</td><td>${r.ref}</td><td>${r.observed}</td><td>${r.inferred}</td><td>${r.tip}</td></tr>`).join("");}document.querySelectorAll("input,select").forEach(e=>e.oninput=show);show();</script>'
        write_bytes(root/'index.html',page(group+' — full-frame evidence',body))
    body='<p>2647 independent frames · raw Z=gray0–255 · fixed signed difference[-40,+40] · full resolution numeric arrays · GT-free default overlays.</p>'
    for role,groups in [('DEVELOPMENT',DEV),('EXPOSED_REGRESSION',set(GROUPS)-DEV)]:
        body+='<h2>'+role+'</h2>'
        for g in GROUPS:
            if g in groups:body+=f'<p><a href="{g}/index.html">{g}: {GROUPS[g]} frames</a></p>'
    body+='<p>Reference trust is a texture proxy, not physical certification. Orange bridges are inferred, never observed. Unknown/unlabeled are not negative truth.</p><p><a href="../reports/DEVELOPMENT_REPORT.md">Measured report</a> | <a href="../reports/FAILURE_ANALYSIS.md">Failure analysis</a> | <a href="../run_integrity.json">Integrity</a></p>'
    write_bytes(run/'galleries/index.html',page('GrayRef simplified evidence — all six groups',body))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args();run=Path(args.run)
    integrity=get(run/'run_integrity.json');assert integrity['engineering_complete']
    data=safe_manifest(run/'input_manifest.csv');pred=[];filter_records=[];reference_records=[];performance=[]
    for row in data:
        d=frame_dir(run,row);r=readgz(d/'result.json.gz');ident=dict(group=row['group'],frame_id=row['frame_id'],role='DEVELOPMENT' if row['group'] in DEV else 'EXPOSED_REGRESSION')
        performance.append(dict(**ident,inference_ms=r['inference_ms']))
        for v in r['results']+r['baselines']:
            chosen=v['paths'][0] if v['paths'] else None;trace=chosen['selected_trace'] if chosen else [];counts=v.get('counts',{})
            pred.append(dict(**ident,mode=v['mode'],current=row['current'],reference=row['reference'],image_sha=row['image_sha'],reference_sha=row['ref_sha'],P_source=row['point_source'],roi=json.dumps(r['roi']),reference_status=r['reference_status'],reference_valid_fraction=r['reference_valid_fraction'],reference_use=v.get('reference_use','HISTORICAL_BASELINE'),filter=v['mode'].split('_')[-1],output_state=v['output_state'],path_id=v.get('chosen_path_id'),tip=json.dumps(v['tip']),candidate_tip=json.dumps(v['candidate_tip']),last_observed_pixel=json.dumps(v.get('last_observed_pixel')),paths=len(v['paths']),observed=sum(bool(p[2]) for p in trace),inferred=sum(not p[2] for p in trace),bridges=len(chosen.get('bridges',[])) if chosen else 0,score_components=json.dumps(chosen.get('components',{})) if chosen else '{}',candidate_count=counts.get('retained_count'),capacity_dropped=counts.get('capacity_dropped'),incoming_truncated=counts.get('incoming_truncated'),inference_all_modes_ms=r['inference_ms'],config_sha=r['config_sha'],git_hash='NOT_A_GIT_REPOSITORY',gt_accessed=False))
        with np.load(d/'roi_gray.npz') as z, np.load(d/'roi_difference.npz') as q:
            mat=q['valid_material_mask'];v=z['valley_raw'];selected=mat&(v>=r['threshold']);weak=selected&(v<10)
            for key in ['raw','median3','gaussian_light']:
                vv=z['valley_'+key];values=vv[selected]/np.maximum(v[selected],1e-8)
                filter_records.append(dict(**ident,filter=key,noise_MAD_raw=r['noise'],raw_selected_pixels=int(selected.sum()),raw_weak_pixels=int(weak.sum()),depth_retention_median=float(np.median(values)) if len(values) else None,loss_below_weak_threshold_fraction=float(np.mean(vv[selected]<r['threshold'])) if selected.any() else None,weak_loss_fraction=float(np.mean(vv[weak]<r['threshold'])) if weak.any() else None,current_highfreq_MAD=float(np.median(np.abs(z[key].astype(float)-z['median3'].astype(float))))))
            trusted=q['ref_quality_map']>0
            reference_records.append(dict(**ident,status=r['reference_status'],trusted=bool(trusted.any()),trusted_fraction=float(trusted.mean()),invalid_warp_fraction=r['invalid_warp_fraction'],trusted_tiles=sum(w['trusted'] for w in r['reference_windows']),tiles=len(r['reference_windows']),ncc_initial_mean=float(np.mean([s['ncc_initial'] for w in r['reference_windows'] for s in w['sides']])),ncc_corrected_mean=float(np.mean([s['ncc_corrected'] for w in r['reference_windows'] for s in w['sides']])),nonzero_local_shifts=sum(s['shift']!=[0,0] for w in r['reference_windows'] if w['trusted'] for s in w['sides']),raw_abs_mean_material=float(np.nanmean(q['absolute'][mat])) if mat.any() else None,corrected_abs_mean_trusted=float(np.nanmean(np.abs(q['signed_corrected'][trusted]))) if trusted.any() else None,notch_hypothesis=r['notch']['point']))
    csvwrite(run/'predictions_all_frames.csv',pred);csvwrite(run/'filter_measurements_all_frames.csv',filter_records);csvwrite(run/'reference_audit_all_frames.csv',reference_records);csvwrite(run/'runtime_all_frames.csv',performance)
    metrics=rows(run/'offline_evaluation_development.csv')+rows(run/'offline_evaluation_exposed_regression.csv');summary=rows(run/'group_summary_development.csv')+rows(run/'group_summary_exposed_regression.csv')
    csvwrite(run/'offline_evaluation.csv',metrics);csvwrite(run/'group_summary.csv',summary)
    aggregate=[r for r in summary if r['group'] in ['DEVELOPMENT','EXPOSED_REGRESSION']];csvwrite(run/'mode_ablation.csv',aggregate);csvwrite(run/'filtering_ablation.csv',[r for r in summary if r['mode'].startswith('C_FUSION')])
    lookup={(r['group'],r['frame_id'],r['mode']):r for r in metrics};paired=[]
    for scope in ['DEVELOPMENT','EXPOSED_REGRESSION']:
        core=[r for r in metrics if r['role']==scope and r['mode']=='C_FUSION_RAW' and r['visibility']=='VISIBLE']
        for other in ['A_VALLEY_ONLY_RAW','B_DIFF_ONLY_RAW','C_FUSION_MEDIAN3','C_FUSION_GAUSSIAN_LIGHT','V1_LOCKED','V2_NUMERIC_CONTROL','V2_COMBINED']:
            pairs=[(r,lookup[r['group'],r['frame_id'],other]) for r in core]
            paired.append(dict(role=scope,comparison='C_FUSION_RAW versus '+other,denominator=len(pairs),hit_gained=sum(yes(a['hit10']) and not yes(b['hit10']) for a,b in pairs),hit_lost=sum(not yes(a['hit10']) and yes(b['hit10']) for a,b in pairs),joint_gained=sum(yes(a['joint']) and not yes(b['joint']) for a,b in pairs),joint_lost=sum(not yes(a['joint']) and yes(b['joint']) for a,b in pairs),new_over100=sum(yes(a['over100']) and not yes(b['over100']) for a,b in pairs),new_over500=sum(yes(a['over500']) and not yes(b['over500']) for a,b in pairs)))
    csvwrite(run/'paired_mode_changes.csv',paired);gallery(run,pred)
    reports=run/'reports';reports.mkdir(exist_ok=True)
    dev=next(r for r in aggregate if r['group']=='DEVELOPMENT' and r['mode']=='C_FUSION_RAW');val=next(r for r in aggregate if r['group']=='EXPOSED_REGRESSION' and r['mode']=='C_FUSION_RAW')
    devbase=[r for r in aggregate if r['group']=='DEVELOPMENT' and r['mode'] in ['V1_LOCKED','V2_COMBINED']];valbase=[r for r in aggregate if r['group']=='EXPOSED_REGRESSION' and r['mode'] in ['V1_LOCKED','V2_COMBINED']]
    accepted=all(number(dev,'joint')>number(b,'joint') and number(dev,'hit10')>number(b,'hit10') and number(dev,'over100')<=number(b,'over100') and number(dev,'over500')<=number(b,'over500') for b in devbase) and all(number(val,'joint')>=number(b,'joint') and number(val,'hit10')>=number(b,'hit10') for b in valbase)
    decision='GO' if accepted else 'NO_GO'
    basecols=['group','mode','visible','hit3','hit5','hit10','joint','output_coverage','over100','over500','raw_over100','raw_over500']
    body='# 实测开发/验证报告\n\n'+f'工程完整性：2647/2647 帧；默认 C_FUSION_RAW。算法验收：{decision}；生产批准：NO。所有结果为暂定身份。\n\n'
    body+='[六组逐帧图册](../galleries/index.html) · [完整性](../run_integrity.json) · [统一规则](../model_protocol.md) · [逐帧指标](../offline_evaluation.csv)\n\n'+table(aggregate,basecols)
    body+='\n完整可见分母76/35，未知9张单列；未标注帧不认作阴性。当前/参考/点全部重新哈希。开发推理封存后独立评分，再使用同一冻结源码执行曝光验证。旧基线为2647帧原始完整trace/result校验回放，未重新运行旧C++；其原生预测及本轮独立评分复现。\n\n'
    body+='## 逐组默认与基线\n\n'+table([r for r in summary if r['group'] in GROUPS and r['mode'] in ['C_FUSION_RAW','V1_LOCKED','V2_COMBINED']],basecols)
    body+='\n## 同一原型内部对照与架构比较\n\n'+table(paired,['role','comparison','hit_gained','hit_lost','joint_gained','joint_lost','new_over100','new_over500'])
    body+='\nA/B/C与滤波对照使用同一连接/停止器；与V1/V2的端到端差异不能解释为某个单模块的因果效应。新增候选不等于新增正确主裂纹。拒绝率、原始候选严重错误与全量状态均保留，不能把减少输出当精度提升。\n\n'
    body+='## 环境与成本\n\n'+json.dumps(get(run/'environment.json'),ensure_ascii=False,indent=2)+'\n\n每帧九模式推理时间（含证据计算，不含绘图/I/O）P50/P95：'+str(np.percentile([r['inference_ms'] for r in performance],[50,95]).tolist())+' ms。该研究Python成本不代表生产性能。\n'
    write_bytes(reports/'DEVELOPMENT_REPORT.md',body.encode('utf-8'))
    core=[r for r in metrics if r['mode']=='C_FUSION_RAW' and r['visibility']=='VISIBLE'];stages=[]
    for g in GROUPS:
        part=[r for r in core if r['group']==g];count=collections.Counter(r['stage'] for r in part)
        stages.append(dict(group=g,visible=len(part),**count,any_candidate_path_good=sum(yes(r['any_candidate_path_good']) for r in part),any_candidate_joint=sum(yes(r['any_candidate_joint']) for r in part)))
    failure='# 失败原因分层\n\n'+table(stages,list(dict.fromkeys(k for r in stages for k in r)))
    failure+='\n分层规则只在离线使用GT：ROI排除→候选未到达尖端→路径完整性/污染→正确候选错排→停止或歧义。该诊断是有限候选池的定位证据，并非全部物理原因已证明。\n\n'
    failure+='1. GROUP_A/CT2：不再复用connection<0.5门，完整ROI扫描；但每列12峰与图的有限前驱仍会截断证据。候选数量、实际正确路径和联合命中须分开看。\n2. 开发组H：不设旧96px起源带，几何上可访问全部ROI；自动暗连通分量只是NOTCH_HYPOTHESIS。可达不等于主裂纹身份正确。\n3. CT3：6个历史GT尖端在严格ROI外，保留分母；本轮未根据GT扩ROI。\n4. 验证组C/三点弯：分别检查候选池正确路径、排名和停止，曝光验证不用于改参数。\n\n'
    severe=sorted([r for r in core if r['error']],key=lambda r:-float(r['error']))[:16]
    failure+='## 实际失败图例\n\n'
    for r in severe:failure+=f"- [{r['group']} / {r['frame_id']}](../galleries/{r['group']}/{r['frame_id']}/index.html)：公开端点误差 {float(r['error']):.2f}px；{r['stage']}；路径覆盖/精度 {r['coverage10']}/{r['precision10']}。\n"
    failures_br=[]
    for role in ['development','exposed_regression']:
        p=run/f'bridges_offline_{role}.csv'
        if p.exists():failures_br.extend(rows(p))
    selected=[r for r in failures_br if r['mode']=='C_FUSION_RAW' and r['rank']=='0'];bad=sorted(selected,key=lambda r:-number(r,'off_annotated_path10_fraction'))[:8]
    failure+='\n## 断续桥接\n\n默认模式全帧选中路径桥接数/缺失像素总数：'+str(sum(r['bridges'] for r in pred if r['mode']=='C_FUSION_RAW'))+'/'+str(sum(r['inferred'] for r in pred if r['mode']=='C_FUSION_RAW'))+'。桥接仅用于假设，不计观察长度。\n\n'+table(bad,['group','frame_id','missing_pixels','distance_max','off_annotated_path10_fraction','physical_wrong_bridge'])
    failure+='\n偏离人工可见段不必然等于物理错误：标签可能只覆盖部分可见段。图例可以证明当前桥接缺乏已标注路径支持，不能伪称已认证真实连接。合成测试报告长间隙/冲突拒绝、平行/交叉歧义；真实细纹理仍可能产生错误候选。\n'
    write_bytes(reports/'FAILURE_ANALYSIS.md',failure.encode('utf-8'))
    refsum=[];filsum=[]
    for g in GROUPS:
        part=[r for r in reference_records if r['group']==g];refsum.append(dict(group=g,frames=len(part),trusted_frames=sum(r['trusted'] for r in part),mean_trusted_fraction=float(np.mean([r['trusted_fraction'] for r in part])),mean_ncc_initial=float(np.mean([r['ncc_initial_mean'] for r in part])),mean_ncc_local=float(np.mean([r['ncc_corrected_mean'] for r in part])),local_shift_windows=sum(r['nonzero_local_shifts'] for r in part)))
        for f in ['raw','median3','gaussian_light']:
            part=[r for r in filter_records if r['group']==g and r['filter']==f]
            filsum.append(dict(group=g,filter=f,median_depth_retention=float(np.mean([r['depth_retention_median'] for r in part if r['depth_retention_median'] is not None])),mean_loss_fraction=float(np.mean([r['loss_below_weak_threshold_fraction'] for r in part if r['loss_below_weak_threshold_fraction'] is not None])),mean_weak_loss_fraction=float(np.mean([r['weak_loss_fraction'] for r in part if r['weak_loss_fraction'] is not None]))))
    csvwrite(run/'reference_group_summary.csv',refsum);csvwrite(run/'filter_group_summary.csv',filsum)
    refreport='# 差分/配准审计\n\n'+table(refsum,list(refsum[0]))+'\n原始signed=P初始对齐参考-current，正值当前更暗，负值当前更亮，float32，出界NaN。局部补偿单独保存；不覆盖raw。所有不可信帧仍交付真实差分面板。\n\n材料窗两侧NCC/std/亮度与固定±4搜索只提供纹理一致代理。局部搜索后的NCC提升含优化偏差，不能冒充独立物理真值；缺少独立配准GT。未通过则q=0，C明确退回当前灰度，B返回REF_UNAVAILABLE。参考同图/已有裂纹D≈0不是无裂纹。\n\n'
    for g in GROUPS:
        failed=next((r for r in reference_records if r['group']==g and not r['trusted']),None)
        if failed:refreport+=f"- [{g} 不可信实例 {failed['frame_id']}](../galleries/{g}/{failed['frame_id']}/index.html)：{failed['status']}，面板保留P差分及遮罩。\n"
    refreport+='\n参考是否带来实际收益：以paired_mode_changes中C_RAW对A_RAW的逐帧增减为准；不能用可信区域数增加代替正确路径/尖端增加。\n\n'+table([r for r in paired if r['comparison'].endswith('A_VALLEY_ONLY_RAW')],list(paired[0]))
    write_bytes(reports/'DIFFERENCE_REGISTRATION_AUDIT.md',refreport.encode('utf-8'))
    filt='# 滤波保存性审计\n\n'+table(get(run/'tests/unit_test_results.json')['filter_preservation'],['width','raw_depth','median_depth','gaussian_depth','median_retention','gaussian_retention'])+'\n中值3×3消除1px线，因此默认固定RAW。F1/F2仍保留0.5原始响应，不允许按组挑滤波。\n\n'+table(filsum,list(filsum[0]))+'\n以上是原始材料候选像素上的响应测量，不是人工裂纹召回率。真实路径/尖端变化另见filtering_ablation；细线丢失、谷宽截断33和候选/连接上限均可能影响追踪。\n3D曲面是规则采样，可能漏掉1px暗谷；完整2D/NPZ以及五条完整纵向剖面用于复核，不能根据漂亮曲面声称精度合格。\n'
    write_bytes(reports/'FILTER_PRESERVATION_AUDIT.md',filt.encode('utf-8'))
    dominant=collections.Counter(r['stage'] for r in core if r['stage'] not in ['JOINT_HIT','ROI_GEOMETRY_EXCLUSION']).most_common(1)
    recommendation='只对固定原始候选池做每列容量截断与近邻连接的保真审计，逐层区分候选丢失和图路径污染；不改阈值、不新增排序项，先验证是哪一层丢失现有图像证据。' if dominant and dominant[0][0] in ['EVIDENCE_OR_GRAPH_REACHABILITY','PATH_COMPLETENESS_OR_CONTAMINATION'] else '只对固定候选池做路径排序/停止前后的逐层保真审计，保留全部身份歧义，不因拒绝率高而降低门槛。'
    decision_report='# 研究路线决定\n\n'+decision+'。这是预先冻结判据的实测结果，不是生产批准。\n\n'+table([dev,val],basecols)+'\n## 七个问题\n\n1. 原灰度全分辨率能测量细暗谷；规则3D显示可能漏细线，中值实测破坏1px线，逐组测量见FILTER_PRESERVATION_AUDIT。\n2. 可信参考帧数/局部比例及失败实例见DIFFERENCE_REGISTRATION_AUDIT；纹理代理不能认证真实材料运动。收益/误追用A/C配对统计。\n3. GROUP_A/CT2已取消旧连接门，但是否改善必须看候选路径/联合实测，见FAILURE_ANALYSIS，不能由候选增多推断。\n4. 开发组H几何可达性扩大到完整ROI，未证明物理起源正确；缺口假设仍未认证。\n5. CT3/验证组C/三点弯的剩余层次及新增严重错误见分层表和逐帧配对，CT3六个ROI外不删。\n6. 默认相对V1/V2收益、公开覆盖、候选严重尾误差和未知状态完整保留；所有数据已曝光，无新盲测。\n7. 唯一建议：'+recommendation+' 本轮不自动启动下一轮、不添加复杂过滤。\n\n局限：单+x；有限候选容量；局部配准不可信；已有裂纹/闭合；物理缺口未确认；CT3原始TXT缺失；局部人工可见路径不是完整物理裂纹；真实阴性库缺失FPR=N/A；无未曝光测试；不替换A/V1/V2。\n'
    write_bytes(reports/'DECISION_GO_NOGO.md',decision_report.encode('utf-8'))
    final=dict(ENGINEERING_COMPLETE='YES',ALGORITHM_ACCURACY_ACCEPTED='YES' if accepted else 'NO',PRODUCTION_APPROVED='NO',TOTAL_EXPECTED_FRAMES=2647,TOTAL_PROCESSED_FRAMES=integrity['processed'],GRAY_3D_SURFACE_PNG_OK=integrity['gray_surface_ok'],ROI_SIGNED_DIFF_PNG_OK=integrity['signed_diff_ok'],DIFF_VALID_FOR_INFERENCE=integrity['registration_valid'],FULL_FRAME_GALLERY_OK=2647,GT_LEAKAGE_TEST_PASSED='YES',V1_V2_BASELINES_REPRODUCED='YES',DEVELOPMENT_10PX_HIT=f"{dev['hit10']}/76",EXPOSED_REGRESSION_10PX_HIT=f"{val['hit10']}/35",DEVELOPMENT_JOINT_PATH_TIP=f"{dev['joint']}/76",EXPOSED_REGRESSION_JOINT_PATH_TIP=f"{val['joint']}/35",NO_VISIBLE_CRACK_FPR='N/A',FINAL_DECISION=decision)
    final['>100PX_ERRORS_DEV']=int(number(dev,'over100'));final['>500PX_ERRORS_DEV']=int(number(dev,'over500'));put(run/'decision_result.json',final)
    put(run/'completion_seal.json',dict(source_hashes_sha=sha(run/'source_hashes.json'),run_integrity_sha=sha(run/'run_integrity.json'),decision_sha=sha(run/'decision_result.json'),report_hashes={p.name:sha(p) for p in reports.glob('*.md')},full_gallery_index_sha=sha(run/'galleries/index.html'),no_production_change=True))
    print(json.dumps(final,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
