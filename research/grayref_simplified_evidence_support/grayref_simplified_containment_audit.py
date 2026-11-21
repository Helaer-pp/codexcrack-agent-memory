"""Read-only exact replay of PRE-selection route ranking. GT joins only after both seals.

Tests whether a high-score prefix suppresses a longer route through exact fragment
containment. Never changes candidates, detector thresholds, endpoints or accuracy.
"""
import argparse,math,collections,json,zipfile,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from grayref_simplified_evidence_v0.common import *
from grayref_simplified_evidence_v0.algorithm import CONFIG,slope,graph_paths
from grayref_simplified_evidence_v0.offline_evaluate import dense,observed_dense,path_metrics
from grayref_simplified_evidence_v0.reports import table

def replay(nodes,segments,edges,g,notch):
    segs=collections.defaultdict(list);values={(int(p[0]),int(p[1])):float(p[7]) for p in nodes}
    for k,x,y in segments:segs[int(k)].append([int(x)-g['xa'],int(y)-g['ya']])
    incoming=collections.defaultdict(list)
    for j,k,_,__ in edges:incoming[int(k)].append(int(j))
    order=sorted(segs,key=lambda k:(segs[k][-1][0],segs[k][-1][1],k));dp={};ranked=[]
    for k in order:
        s=segs[k];options=[]
        for j in incoming[k]:
            t=segs[j];dx=s[0][0]-t[-1][0];penalty=.12*(dx-1)+.25*abs(slope(t)-slope(s,False));options.append((dp[j]['utility']-penalty,j,dx-1))
        options.sort(key=lambda z:(-z[0],z[1]));best=options[0] if options and options[0][0]>0 else None
        dp[k]=dict(prev=best[1] if best else None,utility=sum(min(2.,values[tuple(p)]) for p in s)+(best[0] if best else 0),count=len(s)+(dp[best[1]]['count'] if best else 0),gaps=best[2]+dp[best[1]]['gaps'] if best else 0)
    for k in order:
        state=dp[k]
        if state['count']<4:continue
        chain=[];j=k
        while j is not None:chain.append(j);j=dp[j]['prev']
        chain.reverse();first=segs[chain[0]][0];last=segs[k][-1];mean=state['utility']/state['count'];gapfrac=state['gaps']/max(1,last[0]-first[0]+1);origin=notch['point'];dist=math.hypot(first[0]+g['xa']-origin[0],first[1]+g['ya']-origin[1]) if origin else None;prior=.35*math.exp(-dist/max(30,.25*(g['lower']-g['upper']))) if dist is not None else 0.
        score=mean+.3*(1-math.exp(-state['count']/40))-.6*gapfrac+prior;ranked.append(dict(id=k,score=score,chain=chain,observed=state['count']))
    ranked.sort(key=lambda z:(-z['score'],z['id']));kept=[]
    for r in ranked:
        if len(kept)>=CONFIG['paths_cap']:r['reason']='PATH_BUDGET';r['suppressor']=None;continue
        duplicate=next((p for p in kept if set(r['chain']).issubset(p['chain']) or set(p['chain']).issubset(r['chain'])),None)
        if duplicate:r['reason']='EXACT_FRAGMENT_CONTAINMENT';r['suppressor']=duplicate['id'];continue
        kept.append(r);r['reason']='KEPT';r['suppressor']=None
    return segs,ranked,kept

def route_trace(chain,segs,g):
    trace=[]
    for j in chain:
        s=segs[j]
        if trace:
            px,py=trace[-1][:2];tx,ty=s[0];tx+=g['xa'];ty+=g['ya']
            for xx in range(int(px)+1,int(tx)):trace.append([xx,py+(ty-py)*(xx-px)/(tx-px),0])
        trace.extend([[x+g['xa'],y+g['ya'],1] for x,y in s])
    return trace

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--declare-only',action='store_true');a=p.parse_args();run=Path(a.run);out=run/'containment_diagnostics';out.mkdir(exist_ok=True)
    if a.declare_only:
        g=dict(xa=0,ya=0,xleft=0,xr=400,upper=0,lower=160);E=np.zeros((160,400),np.float32);segs=[[[x,80] for x in range(20,61)],[[x,80] for x in range(66,140)]]
        for x,y in segs[0]:E[y,x]=2
        for x,y in segs[1]:E[y,x]=.4
        paths,edges,counts=graph_paths(segs,E,g,dict(point=None),CONFIG)
        assert len(edges)==1 and paths[0]['fragment_ids']==[0] and all(1 not in p['fragment_ids'] for p in paths)
        put(out/'plan.json',dict(utc=utc(),script_sha=sha(__file__),no_GT_read=True,purpose='Exact graph-state/route-score replay; assess prefix containment loss separately from route budget; no modified predictions',synthetic_weak_extension=dict(edge_exists=True,strong_prefix_kept=True,weak_extension_route_suppressed=True),acceptance='All replayed kept path IDs, fragment chains and scores must match native frozen results before any GT claim',offline_metric='pre-selection observed-only path coverage/precision>=.8 at10px; NOT tip or actual-accuracy gain'))
        print('Declared containment audit; synthetic weak-extension suppression reproduced');return
    assert sha(__file__)==get(out/'plan.json')['script_sha']
    for role in ['development','exposed_regression']:
        assert (run/f'evaluation_complete_{role}.json').exists()
        for rel,h in get(run/f'inference_frozen_{role}.json')['files'].items():assert sha(run/rel)==h
    selected=[r for r in rows(ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv') if r['dataset_id'] in GROUPS];frame_rows=[];route_rows=[];access=[]
    with zipfile.ZipFile(ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip') as z:
        for row in selected:
            labelbytes=z.read(row['selected_json']);label=json.loads(labelbytes);gname=row['dataset_id'];fid=row['frame_id'];tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];parts=[dense(s['points']) for s in label['shapes'] if s['label']=='crack_path']
            access.append(dict(group=gname,frame_id=fid,member=row['selected_json'],sha256=hashlib.sha256(labelbytes).hexdigest(),usage='OFFLINE_PRESELECTION_DIAGNOSTIC'))
            if not tips or not parts:continue
            gt=np.concatenate(parts);tip=np.asarray(tips[0]);folder=run/'galleries'/gname/fid;data=readgz(folder/'result.json.gz');native=next(r for r in data['results'] if r['mode']=='C_FUSION_RAW');g=data['roi']
            with np.load(folder/'candidate_graphs.npz') as arr:segs,ranked,kept=replay(arr['C_FUSION_RAW__nodes'],arr['C_FUSION_RAW__segments'],arr['C_FUSION_RAW__edges'],g,data['notch'])
            assert [r['id'] for r in kept]==[r['id'] for r in native['paths']]
            assert len(ranked)==native['counts']['eligible_routes']
            for x,y in zip(kept,native['paths']):assert x['chain']==y['fragment_ids'] and abs(x['score']-y['score'])<1e-9
            good=[];reasons=collections.Counter()
            for rank,r in enumerate(ranked):
                pts=observed_dense(route_trace(r['chain'],segs,g));m=path_metrics(pts,gt);ok=m['coverage10']>=.8 and m['precision10']>=.8
                if ok:good.append(r);reasons[r['reason']]+=1
                # Keep every route's compact quality and lineage, not just successful cases.
                route_rows.append(dict(group=gname,frame_id=fid,rank=rank,path_id=r['id'],score=r['score'],observed=r['observed'],reason=r['reason'],suppressor=r['suppressor'],fragment_chain=json.dumps(r['chain']),**m,path_good=ok,tip_not_evaluated=True))
            good_kept=[r for r in good if r['reason']=='KEPT'];lost=[r for r in good if r['reason']=='EXACT_FRAGMENT_CONTAINMENT'];goodids={r['id'] for r in good};suppressor_bad=[r for r in lost if r['suppressor'] not in goodids]
            frame_rows.append(dict(group=gname,frame_id=fid,native_replay_exact=True,preselection_routes=len(ranked),good_preselection_paths=len(good),good_kept_paths=len(good_kept),good_containment_suppressed=len(lost),good_budget_dropped=reasons['PATH_BUDGET'],good_suppressed_with_bad_keeper=len(suppressor_bad),containment_loss_without_good_kept=bool(suppressor_bad and not good_kept),not_actual_accuracy_gain=True))
            if len(frame_rows)%10==0:print('Containment audit '+str(len(frame_rows))+'/111',flush=True)
    assert len(frame_rows)==111;csvwrite(out/'frame_loss.csv',frame_rows);csvwrite(out/'all_preselection_routes.csv',route_rows);csvwrite(out/'annotation_access.csv',access)
    summary=[]
    for g in GROUPS:
        part=[r for r in frame_rows if r['group']==g];summary.append(dict(group=g,visible=len(part),preselection_good_frames=sum(r['good_preselection_paths']>0 for r in part),kept_good_frames=sum(r['good_kept_paths']>0 for r in part),containment_loss_without_good_keeper=sum(r['containment_loss_without_good_kept'] for r in part),frames_good_budget_dropped=sum(r['good_budget_dropped']>0 for r in part)))
    csvwrite(out/'summary.csv',summary)
    md='# 包含关系去重的只读因果定位\n\n'+table(summary,list(summary[0]))+'\n所有111帧的原生保留路径ID、片段链、排序分数均与存量数值图精确重放一致。原始图确实曾形成的排序前路线才纳入表，不引入新图像候选、不修改连接、权重或停止。\n\n'
    md+='同一路线的强前缀可能比“强前缀+弱延伸”平均分更高。当前包含关系去重把二者看作重复，从而可能保留短前缀、删除较完整路线。独立合成强弱两段已复现该机制；上表是真实可见帧的实际损失，不从合成推断真实成功率。\n\n'
    md+='`containment_loss_without_good_keeper`要求：被删除路线满足离线路径覆盖/精度≥0.8，其压制者不满足，而且最终池没有其他合格路径。仅近邻点被删不计损失；若该值为0，不应归咎于去重。\n\n排序前路径质量不是原生尖端成功；这些被删路线未在原始流程中进行停止评估，因此不得把它们当新增联合命中或已验证改进。\n\n'
    for r in frame_rows:
        if r['containment_loss_without_good_kept']:md+=f"- [{r['group']}/{r['frame_id']}](../galleries/{r['group']}/{r['frame_id']}/index.html)：排序前合格{r['good_preselection_paths']}，包含关系压制{r['good_containment_suppressed']}，最终池合格0。\n"
    write_bytes(out/'CONTAINMENT_CAUSE_REPORT.md',md.encode('utf-8'));put(out/'seal.json',dict(script_sha=sha(__file__),plan_sha=sha(out/'plan.json'),frames=111,all_native_routes_exact=True,summary=summary,no_modified_prediction=True,files={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='seal.json'}));print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
