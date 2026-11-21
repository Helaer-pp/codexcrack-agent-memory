"""Read-only synthesis of frozen inference and completed offline scores; never tunes rules."""
import argparse,collections,json
from pathlib import Path
import numpy as np
from PIL import Image
from grayref_simplified_evidence_v0.common import *
from grayref_simplified_evidence_v0.reports import table,yes,number

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();run=Path(a.run)
    assert (run/'completion_seal.json').exists() and (run/'stage_diagnostics/seal.json').exists()
    result=get(run/'decision_result.json');metrics=rows(run/'offline_evaluation.csv');data=safe_manifest(run/'input_manifest.csv');details=[];summary=[];severity=[];window_rechecks=[]
    lookup={(r['group'],r['frame_id']):r for r in data};label_identity=[]
    for r in rows(ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv'):
        if r['dataset_id'] not in GROUPS:continue
        original=lookup[r['dataset_id'],r['frame_id']]
        assert r['sha256']==original['image_sha'] and r['width']==original['width'] and r['height']==original['height']
        label_identity.append(dict(group=r['dataset_id'],frame_id=r['frame_id'],image_sha256=r['sha256'],exact_original_BMP_identity=True))
    assert len(label_identity)==120
    put(run/'label_image_identity_check.json',dict(verified=120,records=label_identity,comparison_only=True))
    for row in data:
        folder=frame_dir(run,row)
        d=readgz(folder/'result.json.gz');g=d['roi']
        with np.load(folder/'roi_gray.npz') as numeric, np.load(folder/'roi_difference.npz') as reference:
            raw=numeric['raw'];aligned=np.nan_to_num(reference['aligned_reference'],nan=0);warp=reference['valid_warp_mask']
            with Image.open(folder/'gray_full_resolution.png') as image:assert np.array_equal(np.asarray(image),numeric['raw'])
            for key in ['raw','median3','gaussian_light']:
                expected=np.uint8(np.clip(numeric['valley_'+key]/80,0,1)*255)
                with Image.open(folder/('valley_'+key+'_full_resolution.png')) as image:assert np.array_equal(np.asarray(image),expected)
            for tile in d['reference_windows']:
                for side in tile['sides']:
                    x0,y0,x1,y1=side['bounds'];x0-=g['xa'];x1-=g['xa'];y0-=g['ya'];y1-=g['ya'];cw=raw[y0:y1,x0:x1];rw=aligned[y0:y1,x0:x1]
                    bright=float(np.mean((cw>100)&(rw>100)));inside=bool(warp[y0-4:y1+4,x0-4:x1+4].all());reasons=[]
                    if d['reference_status']=='SAME_IMAGE_NO_INCREMENT':reasons.append('SAME_IMAGE_NO_INCREMENT')
                    if cw.size<64:reasons.append('SMALL_WINDOW')
                    if side['std_current']<2:reasons.append('LOW_CURRENT_TEXTURE')
                    if side['std_reference']<2:reasons.append('LOW_REFERENCE_TEXTURE')
                    if bright<.5:reasons.append('INSUFFICIENT_BRIGHT_MATERIAL')
                    if not inside:reasons.append('INVALID_INITIAL_WARP')
                    if side['ncc_corrected']<.8:reasons.append('NCC_BELOW_FROZEN_GATE')
                    if abs(side['bias'])>20:reasons.append('PHOTOMETRIC_OFFSET_TOO_LARGE')
                    assert bool(not reasons)==side['trusted']
                    window_rechecks.append(dict(group=row['group'],frame_id=row['frame_id'],bounds=json.dumps(side['bounds']),bright_fraction=bright,expanded_warp_valid=inside,texture_current=side['std_current'],texture_reference=side['std_reference'],ncc_initial=side['ncc_initial'],ncc_local=side['ncc_corrected'],bias=side['bias'],trusted=side['trusted'],failed_gates='|'.join(reasons) if reasons else 'TRUSTED_TEXTURE_PROXY',reproduced_original_decision=True))
        r=next(x for x in d['results'] if x['mode']=='C_FUSION_RAW');chosen=r['paths'][0] if r['paths'] else None;stops=chosen['stop_candidates'] if chosen else []
        details.append(dict(group=row['group'],frame_id=row['frame_id'],state=r['output_state'],path_exists=bool(chosen),stop_count=len(stops),eligible_stop_count=sum(s['eligible'] for s in stops),material_adequate=sum(s['after_material_fraction']>=.65 for s in stops),negative_adequate=sum(s['after_observable_negative_fraction']>=.8 for s in stops),no_eligible_stop=bool(chosen and not any(s['eligible'] for s in stops)),capacity_dropped=r['counts']['capacity_dropped'],raw_peaks=r['counts']['raw_peak_count'],retained_nodes=r['counts']['retained_count'],incoming_truncated=r['counts']['incoming_truncated'],reference_fraction=d['reference_valid_fraction'],noise=d['noise'],weak_threshold=d['threshold'],chosen_observed=sum(p[2] for p in chosen['selected_trace']) if chosen else 0,chosen_inferred=sum(not p[2] for p in chosen['selected_trace']) if chosen else 0))
    for group in GROUPS:
        part=[r for r in details if r['group']==group];s=dict(group=group,frames=len(part),**collections.Counter(r['state'] for r in part),stops=sum(r['stop_count'] for r in part),eligible_stops=sum(r['eligible_stop_count'] for r in part),material_adequate_stops=sum(r['material_adequate'] for r in part),negative_adequate_stops=sum(r['negative_adequate'] for r in part),frames_no_eligible_stop=sum(r['no_eligible_stop'] for r in part),capacity_dropped=sum(r['capacity_dropped'] for r in part),raw_peaks=sum(r['raw_peaks'] for r in part),retained_nodes=sum(r['retained_nodes'] for r in part),incoming_truncated=sum(r['incoming_truncated'] for r in part),mean_reference_fraction=float(np.mean([r['reference_fraction'] for r in part])))
        summary.append(s)
    for scope in ['DEVELOPMENT','EXPOSED_REGRESSION']:
        part=[r for r in metrics if r['role']==scope and r['mode']=='C_FUSION_RAW' and r['visibility']=='VISIBLE'];last=[float(r['last_observed_error']) for r in part if r['last_observed_error']];candidate=[float(r['raw_candidate_error']) for r in part if r['raw_candidate_error']];public=[float(r['error']) for r in part if r['error']]
        severity.append(dict(role=scope,visible=len(part),public_outputs=len(public),public_over100=sum(e>100 for e in public),public_over500=sum(e>500 for e in public),candidate_tips=len(candidate),candidate_over100=sum(e>100 for e in candidate),candidate_over500=sum(e>500 for e in candidate),last_observed_count=len(last),last_observed_over100=sum(e>100 for e in last),last_observed_over500=sum(e>500 for e in last),warning='Last observed is a path diagnostic, not a tip prediction'))
    put(run/'full_resolution_png_numeric_check.json',dict(frames=len(data),raw_gray_exact=len(data),three_valley_pngs_exact=len(data)*3,valley_display_scale='fixed 0..80 gray-level depth mapped to uint8 0..255; numeric unclipped',no_inference_change=True))
    out=run/'mechanism_diagnostics';out.mkdir(exist_ok=True);csvwrite(out/'all_frame_stop_and_capacity.csv',details);csvwrite(out/'stop_and_capacity_by_group.csv',summary);csvwrite(out/'refusal_tail_audit.csv',severity)
    csvwrite(out/'reference_window_quality_recheck.csv',window_rechecks)
    reference_reasons=[]
    for group in GROUPS:
        part=[r for r in window_rechecks if r['group']==group];reasons=collections.Counter(reason for r in part for reason in r['failed_gates'].split('|'))
        reference_reasons.append(dict(group=group,windows=len(part),**reasons))
    csvwrite(out/'reference_failure_gates_by_group.csv',reference_reasons)
    put(out/'reference_quality_recheck.json',dict(windows=len(window_rechecks),original_trust_decisions_exact=True,brightness_statistics_reconstructed_from_full_resolution_arrays=True,no_rule_change=True))
    stage=rows(run/'stage_diagnostics/stage_summary.csv');devstage=[r for r in stage if r['group'] in DEV];counts=collections.Counter()
    for r in devstage:
        for key in ['RAW_IMAGE_EVIDENCE_INCOMPLETE','COLUMN_SELECTION_LOSS','GRAPH_ROUTE_OR_RANK_BUDGET_LOSS','FINAL_PATH_RANK_LOSS','STOP_OR_PUBLIC_AMBIGUITY']:counts[key]+=int(r.get(key) or 0)
    dominant=counts.most_common(1)[0] if counts else ('UNRESOLVED',0)
    if dominant[0]=='GRAPH_ROUTE_OR_RANK_BUDGET_LOSS':recommendation='只做固定候选池的片段连接/前驱保留/路径预算保真审计：保持暗谷和参考证据不变，定位可见段为何没有形成同一条候选路径。先证明具体损失点，再决定单点修复；不要先放宽尖端停止或不确定门。'
    elif dominant[0]=='COLUMN_SELECTION_LOSS':recommendation='只隔离审计每列候选强度排序与容量截断，保持证据与后续路径器不变，明确弱线在哪列丢失。不要依据标注挑阈值，也不要同时扩展路径和停止器。'
    elif dominant[0]=='STOP_OR_PUBLIC_AMBIGUITY':recommendation='只在已经冻结的同一路径上审计停止后负证据的可观测性，区分纹理、遮挡和真实暗线延续；不重新选路径、不降低不确定门后宣称准确率提升。'
    elif dominant[0]=='FINAL_PATH_RANK_LOSS':recommendation='只在冻结完整候选池上审计排名证据是否能区分主裂纹与其他暗线；缺口身份未被独立确认前，不把较长或较暗候选直接升格为主裂纹。'
    else:recommendation='只核查原始灰度可测性与当前暗谷响应之间的损失，保持全部阈值和路径器冻结；不增加额外过滤掩盖弱线缺失。'
    md='# 本轮最终结论与原因\n\n'+f"工程交付已完成，算法判定 **{result['FINAL_DECISION']}**，不替换生产 A/V1/V2。开发尖端10px命中 {result['DEVELOPMENT_10PX_HIT']}，联合命中 {result['DEVELOPMENT_JOINT_PATH_TIP']}；已曝光验证分别 {result['EXPOSED_REGRESSION_10PX_HIT']}、{result['EXPOSED_REGRESSION_JOINT_PATH_TIP']}。\n\n"
    md+='[2647帧图册](galleries/index.html) · [六组视频，验证组置顶](videos/index.html) · [离线人工标签对比](offline_label_overlays/index.html) · [全部模式与基线](reports/DEVELOPMENT_REPORT.md) · [完整性](run_integrity.json) · [阶段审计](stage_diagnostics/STAGE_CAUSE_REPORT.md)\n\n'
    md+='## 原因定位\n\n'+table(stage,list(dict.fromkeys(k for r in stage for k in r)))
    md+='\n开发组主要首败层为 '+str(dominant)+'。原始峰/保留节点靠近人工路径，只证明附近存在图像证据，不证明它们已构成正确路径。图阶段包含邻接连接、前驱选择和有限池排名；本轮不能把这些因素全部归结为单一阈值。\n\n'
    containment=run/'containment_diagnostics/summary.csv'
    if containment.exists():
        crows=rows(containment);loss=sum(int(r['containment_loss_without_good_keeper']) for r in crows if r['group'] in DEV)
        md+='### 包含关系去重的进一步定位\n\n'+table(crows,list(crows[0]))+'\n[完整候选重放证据](containment_diagnostics/CONTAINMENT_CAUSE_REPORT.md)。排序前路线被保留不等于尖端正确，不能计为新增准确率。\n\n'
        if loss and dominant[0]=='GRAPH_ROUTE_OR_RANK_BUDGET_LOSS':
            recommendation='下一轮只检验一项：把同一条路线的不同终止跨度保留为独立假设，不再仅因片段包含关系删除弱延伸路线；固定其余证据、连接边界、排名权重与停止规则。先验证候选保真是否恢复，不承诺这一项就能改善最终尖端，也不自动放行不确定结果。'
    md+='## 为什么有大量不确定输出\n\n'+table(summary,['group','frames','TIP_UNCERTAIN','PATH_AMBIGUOUS','PROVISIONAL_TIP','stops','eligible_stops','material_adequate_stops','negative_adequate_stops','frames_no_eligible_stop'])
    md+='\n有材料可测不等于已有可靠负证据。停止条件不足既可能来自路径提前断裂、末端后仍有线，也可能来自纹理触发；不能把这种拒绝直接解释为算法更安全。\n\n'+table(severity,['role','visible','public_outputs','public_over100','public_over500','candidate_tips','candidate_over100','candidate_over500','last_observed_count','last_observed_over100','last_observed_over500'])
    md+='\n最后观测点的尾误差仅作路径诊断，不计为算法尖端；单列它是为了暴露拒绝输出背后的错误路径，不能混入公开端点准确率。\n\n'
    controls=run/'supplementary_controls/noise_chain_controls.json'
    if controls.exists():
        md+='## 冻结规则下的补充噪点反例\n\n'+table(get(controls)['controls'],['pixel_width','spacing_px','output_state','public_tip','observed','inferred','physical_identity'])+'\n该检查在规则冻结后补充，只用于诊断，没有据此调参。2px点链仍能产生暂定尖端，说明有限桥接和停止证据并不认证主裂纹身份；不能把上述合成样例当作真实FPR，真实FPR仍为N/A。\n\n'
    md+='## 唯一下一步建议\n\n'+recommendation+' 本轮不自动启动下一轮。\n\n'
    md+='中值3×3在合成1px暗线上谷深保留为0，轻高斯约0.667，因此统一默认RAW。参考合格帧数表示至少一个局部窗口通过纹理检查，不代表全ROI配准可信，详见reference_group_summary.csv。\n\n'
    md+='## 参考不可信的具体门条件\n\n'+table(reference_reasons,list(dict.fromkeys(k for r in reference_reasons for k in r)))+'\n一个窗口可以同时违反多个条件，因此失败条件数不可直接相加当窗口数。逐窗亮度比例与扩展warp有效性由保存的完整分辨率数组补算，全部复现原始可信判断；没有改门槛或重新选择配准。\n\n'
    md+='约束保持：排除组X未使用；标签只比较不训练；验证组C/三点弯未调参且不是新盲测；CT3原始TXT缺失，历史CSV与每帧P核验一致，6个ROI外可见尖端保留分母；真实阴性FPR=N/A。基线是冻结结果与完整trace的校验回放，未重跑旧检测器。\n\n'
    md+='完整复现入口：`research/grayref_simplified_evidence_support/grayref_simplified_full_delivery.ps1 -RunId NEW_UNIQUE_RUN -Workers 12`。主试验源码冻结后未变；辅助脚本只做只读核查、事后报告和视频，不回写推理。\n'
    write_bytes(run/'FINAL_FINDINGS.md',md.encode('utf-8'));put(out/'seal.json',dict(script_sha=sha(__file__),final_findings_sha=sha(run/'FINAL_FINDINGS.md'),summary=summary,severity=severity,dominant_development_failure=dominant,recommendation=recommendation,no_inference_changes=True));print(json.dumps(dict(dominant=dominant,severity=severity),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
