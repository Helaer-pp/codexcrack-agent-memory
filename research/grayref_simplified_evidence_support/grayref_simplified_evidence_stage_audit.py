"""Post-hoc diagnostic ONLY. Never imported by the detector or used to change outputs.

Declared before label scoring: measure current-peak -> retained-node -> graph-fragment
-> finite-path-pool losses, using existing full-resolution frozen evidence.
"""
import argparse,json,zipfile,hashlib,collections
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from grayref_simplified_evidence_v0.common import *
from grayref_simplified_evidence_v0.offline_evaluate import dense,observed_dense,path_metrics

def coverage(points,gt,tip):
    if not len(points):return 0.,None
    tree=cKDTree(points);return float(np.mean(tree.query(gt)[0]<=10)) if len(gt) else 0.,float(tree.query(tip)[0]) if tip is not None else None

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--declare-only',action='store_true');a=p.parse_args();run=Path(a.run)
    out=run/'stage_diagnostics';out.mkdir(parents=True,exist_ok=True)
    if a.declare_only:
        put(out/'plan.json',dict(utc=utc(),script_sha=sha(__file__),purpose='Offline cause isolation only; no output/rule change',sequence='only after BOTH inference seals and role evaluations',mode='C_FUSION_RAW',stages=['raw eligible full-resolution local peaks','post column-cap retained nodes','observed fragments','finite six-path pool','chosen path','independent termination'],tolerance_px=10,coverage_threshold=.8,prohibition='Never write inference/config; no threshold selection or GT fitting'))
        return
    assert get(out/'plan.json')['script_sha']==sha(__file__)
    for role in ['development','exposed_regression']:
        assert (run/f'evaluation_complete_{role}.json').exists()
        for rel,h in get(run/f'inference_frozen_{role}.json')['files'].items():assert sha(run/rel)==h
    selected=[r for r in rows(ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv') if r['dataset_id'] in GROUPS]
    records=[];access=[];filter_samples=[]
    with zipfile.ZipFile(ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip') as z:
        for s in selected:
            b=z.read(s['selected_json']);label=json.loads(b);g=s['dataset_id'];fid=s['frame_id']
            tips=[t['points'][0] for t in label['shapes'] if t['label']=='crack_tip'];parts=[dense(t['points']) for t in label['shapes'] if t['label']=='crack_path'];gt=np.concatenate(parts) if parts else np.empty((0,2))
            access.append(dict(group=g,frame_id=fid,member=s['selected_json'],sha256=hashlib.sha256(b).hexdigest(),purpose='OFFLINE_DIAGNOSTIC_ONLY'))
            if not tips or not len(gt):continue
            tip=np.asarray(tips[0]);d=run/'galleries'/g/fid;r=readgz(d/'result.json.gz');geo=r['roi'];mode='C_FUSION_RAW';pred=next(v for v in r['results'] if v['mode']==mode)
            with np.load(d/'roi_gray.npz') as q,np.load(d/'roi_difference.npz') as ref,np.load(d/'candidate_graphs.npz') as graph:
                V=q['valley_raw'];scale=3*r['noise']+6;D=np.nan_to_num(ref['aligned_local'],nan=0)-q['raw'].astype(np.float32)-ref['local_bias'];E=np.clip(V/scale,0,4)+.35*ref['ref_quality_map']*np.clip(np.maximum(D,0)/scale,0,4)
                eligible=ref['valid_material_mask']&(V>=r['threshold']);peaks=eligible&(E>=np.roll(E,1,0))&(E>np.roll(E,-1,0));yy,xx=np.nonzero(peaks);rawpoints=np.column_stack((xx+geo['xa'],yy+geo['ya']))
                nodes=graph[mode+'__nodes'];points=nodes[:,:2]+[geo['xa'],geo['ya']];frags=graph[mode+'__segments'];fragmentpoints=frags[:,1:3]
                rawcov,rawdist=coverage(rawpoints,gt,tip);nodecov,nodedist=coverage(points,gt,tip);fragcov,fragdist=coverage(fragmentpoints,gt,tip)
                assert len(rawpoints)==pred['counts']['raw_peak_count'] and len(points)==pred['counts']['retained_count']
                pmetrics=[];poolpoints=[]
                for rank,path in enumerate(pred['paths']):
                    pts=observed_dense(path['observed_trace']);m=path_metrics(pts,gt);_,dist=coverage(pts,gt,tip);pmetrics.append(dict(rank=rank,**m,nearest_tip=dist));poolpoints.extend(pts.tolist())
                poolcov,pooldist=coverage(np.asarray(poolpoints).reshape(-1,2),gt,tip)
                joint_paths=[m for m in pmetrics if m['coverage10']>=.8 and m['precision10']>=.8]
                state=('RAW_IMAGE_EVIDENCE_INCOMPLETE' if rawcov<.8 else 'COLUMN_SELECTION_LOSS' if nodecov<.8 else 'GRAPH_ROUTE_OR_RANK_BUDGET_LOSS' if not joint_paths else 'FINAL_PATH_RANK_LOSS' if joint_paths[0]['rank']!=0 else 'STOP_OR_PUBLIC_AMBIGUITY')
                chosen=pred['paths'][0] if pred['paths'] else None
                record=dict(group=g,frame_id=fid,raw_peak_coverage10=rawcov,raw_peak_tip_distance=rawdist,retained_node_coverage10=nodecov,retained_node_tip_distance=nodedist,fragment_coverage10=fragcov,fragment_tip_distance=fragdist,pool_union_coverage10=poolcov,pool_nearest_tip_distance=pooldist,finite_pool_good_paths=len(joint_paths),chosen_good=bool(joint_paths and joint_paths[0]['rank']==0),first_failure=state,capacity_dropped=pred['counts']['capacity_dropped'],raw_peaks=pred['counts']['raw_peak_count'],retained=pred['counts']['retained_count'],graph_edges=pred['counts']['graph_edges'],incoming_truncated=pred['counts']['incoming_truncated'],notch_status=r['notch']['status'],notch_point=r['notch']['point'],GT_start_to_notch=float(np.linalg.norm(gt[0]-r['notch']['point'])) if r['notch']['point'] else None,output=pred['output_state'],candidate_tip=pred['candidate_tip'],public_tip=pred['tip'])
                if pred['tip'] is not None and np.linalg.norm(np.subtract(pred['tip'],tip))<=10 and joint_paths and joint_paths[0]['rank']==0:record['first_failure']='JOINT_SUCCESS'
                if not(geo['xleft']<=tip[0]<geo['xr'] and geo['upper']<=tip[1]<=geo['lower']):record['first_failure']='ROI_TIP_EXCLUDED'
                records.append(record)
                ix=np.round(gt[:,0]-geo['xa']).astype(int);iy=np.round(gt[:,1]-geo['ya']).astype(int);ok=(ix>=0)&(ix<V.shape[1])&(iy>=0)&(iy<V.shape[0]);ix=ix[ok];iy=iy[ok]
                for name in ['raw','median3','gaussian_light']:
                    samples=q['valley_'+name][iy,ix];baseline=V[iy,ix];strong=baseline>=r['threshold']
                    filter_samples.append(dict(group=g,frame_id=fid,filter=name,gt_samples_total=len(gt),inside_crop_samples=len(ix),raw_supported_samples=int(strong.sum()),mean_valley_on_GT=float(samples.mean()) if len(samples) else None,loss_of_raw_supported_GT_fraction=float(np.mean(samples[strong]<r['threshold'])) if strong.any() else None,offline_comparison_only=True))
    assert len(records)==111
    csvwrite(out/'candidate_stage_losses.csv',records);csvwrite(out/'annotation_access.csv',access);csvwrite(out/'filter_on_visible_path.csv',filter_samples)
    summaries=[]
    for g in GROUPS:
        part=[r for r in records if r['group']==g];summaries.append(dict(group=g,visible=len(part),raw_coverage80=sum(r['raw_peak_coverage10']>=.8 for r in part),retained_coverage80=sum(r['retained_node_coverage10']>=.8 for r in part),finite_pool_good=sum(r['finite_pool_good_paths']>0 for r in part),chosen_good=sum(r['chosen_good'] for r in part),**collections.Counter(r['first_failure'] for r in part)))
    csvwrite(out/'stage_summary.csv',summaries)
    from grayref_simplified_evidence_v0.reports import table
    text='# 额外逐层失效定位（离线，只读冻结输出）\n\n'+table(summaries,list(dict.fromkeys(k for r in summaries for k in r)))
    text+='\n原始局部峰与保留节点覆盖率只是GT附近存在证据，不是正确整条主裂纹。图阶段包含邻接匹配、桥接、单前驱动态规划及六路径预算，不能仅凭终态确定是哪一个子项造成损失。此报告不会回写推理或调参。\n\n'
    dominant=collections.Counter(r['first_failure'] for r in records if r['group'] in DEV and r['first_failure'] not in ['JOINT_SUCCESS','ROI_TIP_EXCLUDED']).most_common(1)
    text+='开发组主要首败：'+str(dominant)+'。\n\n'
    if dominant and dominant[0][0]=='GRAPH_ROUTE_OR_RANK_BUDGET_LOSS':
        text+='唯一建议：固定现有暗谷候选与分数，单独检查片段邻接/前驱保留/路径预算导致的路径保真损失，先用现有原图证据逐项定位；不要通过增加末端门或降低不确定门掩盖路径池缺失。这里只提出诊断，不自动改算法。\n'
    elif dominant and dominant[0][0]=='COLUMN_SELECTION_LOSS':text+='唯一建议：固定当前证据和连接器，隔离审计每列强度排序/容量截断，保留截断前后对应关系；先证明细弱路径丢失位置，禁止按标注挑阈值。\n'
    else:text+='唯一建议：只审计上表主要首败层的输入/输出对应关系；不因错误多而叠加新的过滤或用GT选择运行路径。\n'
    for g in GROUPS:
        examples=sorted([r for r in records if r['group']==g],key=lambda r:-(r['retained_node_coverage10']-r['pool_union_coverage10']))[:2]
        for r in examples:text+=f"\n- [{g}/{r['frame_id']}](../galleries/{g}/{r['frame_id']}/index.html)：原始峰覆盖{r['raw_peak_coverage10']:.3f}，保留节点{r['retained_node_coverage10']:.3f}，有限路径池并集{r['pool_union_coverage10']:.3f}；{r['first_failure']}。\n"
    write_bytes(out/'STAGE_CAUSE_REPORT.md',text.encode('utf-8'));put(out/'seal.json',dict(script_sha=sha(__file__),plan_sha=sha(out/'plan.json'),frames=111,no_inference_changed=True,files={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='seal.json'}));print(json.dumps(summaries,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
