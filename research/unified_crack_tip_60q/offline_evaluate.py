"""Separate post-seal process. This module is never imported by inference."""
import argparse,zipfile,hashlib,collections,json
import numpy as np
from scipy.spatial import cKDTree
from .common import *
from .config import ARMS
from .pipeline import load_evidence,resultdir

def dense(p):
    p=np.asarray(p,float);out=[]
    for a,b in zip(p[:-1],p[1:]):out.extend(np.linspace(a,b,max(2,int(np.ceil(np.linalg.norm(b-a)))+1)))
    return np.asarray(out or p.tolist(),float).reshape(-1,2)
def distance(points,target):return float(cKDTree(points).query(np.asarray(target))[0]) if len(points) else None
def coverage(points,path):return float(np.mean(cKDTree(points).query(path)[0]<=10)) if len(points) and len(path) else 0.
def curve(e,p):return np.concatenate([e['xy'][e['ptr'][k]:e['ptr'][k+1]] for k,_ in p['chain']]) if p['chain'] else np.empty((0,2))

def segment_label_geometry(e,path):
    """Exact reuse of per-segment distances; labels remain exclusively offline."""
    n=len(e['ptr'])-1;bits=[0]*n;lengths=np.diff(e['ptr']);hits=np.zeros(n,np.int64)
    if not len(path) or not len(e['xy']):return bits,hits,lengths
    near=cKDTree(path).query(e['xy'])[0]<=10
    hits=np.add.reduceat(near.astype(np.int64),e['ptr'][:-1])
    for j,indices in enumerate(cKDTree(e['xy']).query_ball_point(path,10)):
        ids=np.unique(np.searchsorted(e['ptr'],indices,side='right')-1)
        for k in ids:bits[int(k)]|=1<<j
    return bits,hits,lengths

def candidate_geometry(p,cache,path_count):
    bits,hits,lengths=cache;covered=0;hit=0;total=0
    for k,_ in p['chain']:covered|=bits[k];hit+=int(hits[k]);total+=int(lengths[k])
    return covered.bit_count()/path_count if path_count else 0.,hit/total if total else 0.

def verify_seal(run,split):
    seal=get(run/'manifests'/f'{split}_inference_seal.json')
    for job,h in seal['jobs'].items():
        folder=run/'raw_inference'/job;assert sha(folder/'seal.json')==h
        for name,value in get(folder/'seal.json')['files'].items():assert sha(folder/name)==value
    return seal

def labels(run,split):
    seal=run/'manifests'/f'{split}_inference_seal.json';assert seal.exists()
    access_record=run/'offline_evaluation'/f'{split}_label_access_begin.json'
    if not access_record.exists():put(access_record,dict(time=utc(),inference_seal=sha(seal),purpose='POST_SEAL_COMPARISON_ONLY'))
    assert get(access_record)['inference_seal']==sha(seal)
    rs=inventory(run,split);lookup={(r['group'],r['frame_id']):r for r in rs};selected=rows(ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv');out={};access=[]
    with zipfile.ZipFile(ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip') as z:
        for r in selected:
            key=(r['dataset_id'],r['frame_id'])
            if key not in lookup:continue
            assert r['sha256']==lookup[key]['image_sha'];b=z.read(r['selected_json']);label=json.loads(b)
            assert label['imageWidth']==int(lookup[key]['width']) and label['imageHeight']==int(lookup[key]['height'])
            assert Path(label['imagePath'].replace('\\','/')).name==Path(r['selected_image']).name
            tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];paths=[dense(s['points']) for s in label['shapes'] if s['label']=='crack_path']
            assert len(tips)<=1
            out[key]=dict(tip=tips[0] if tips else None,path=np.concatenate(paths) if paths else np.empty((0,2)),visibility='VISIBLE' if tips else 'UNKNOWN')
            access.append(dict(group=key[0],frame_id=key[1],member=r['selected_json'],sha=hashlib.sha256(b).hexdigest(),inference_seal=sha(seal),access_begin_sha=sha(access_record),usage='COMPARISON_ONLY_NOT_TRAINING'))
    for group in dict.fromkeys(r['group'] for r in rs):assert sum(k[0]==group and v['tip'] is not None for k,v in out.items())==VISIBLE[group]
    csvwrite(run/'offline_evaluation'/f'{split}_annotation_access.csv',access)
    return out

def unscored_summary_view(summary):
    # Only used when no visible GT exists: candidate/Oracle errors are undefined.
    # Status, official coordinates and budget come from the checksummed per-job CSV.
    valid=summary['status']=='VALID'
    if valid:
        assert summary['tip_x'] and summary['tip_y']
        tip=[int(summary['tip_x']),int(summary['tip_y'])]
    else:
        assert not summary['tip_x'] and not summary['tip_y'];tip=None
    assert summary['budget'] in ['True','False']
    return dict(status=summary['status'],tip=tip,preferred_uncertain_tip=None,candidates=[],budget=dict(exhausted=summary['budget']=='True'))


def evaluate(run,split):
    if split=='LOCKED':check_freeze(run)
    verify_seal(run,split);gt=labels(run,split);rs=inventory(run,split);arms=list(ARMS) if split=='DEV' else ['FULL'];metrics=[];stages=[];candidate_scores=[]
    summary_lookup={(arm,group,s['frame_id']):s for group in dict.fromkeys(r['group'] for r in rs) for arm in arms for s in rows(resultdir(run,arm,group)/'summary.csv')}
    assert len(summary_lookup)==len(rs)*len(arms)
    for row in rs:
        key=row['group'],row['frame_id'];label=gt.get(key);gttip=label['tip'] if label else None
        e=None
        if gttip is not None:
            e,_=load_evidence(framedir(run,row));path=label['path'];geometry_cache=segment_label_geometry(e,path)
            xa,ya,xb,yb=e['scene']['bounds'];ys,xs=np.nonzero(e['valley']>=e['threshold']);rawpts=np.column_stack([xs+xa,ys+ya]);ids=np.flatnonzero(e['graph_eligible']);structured=np.concatenate([e['xy'][e['ptr'][k]:e['ptr'][k+1]] for k in ids]) if len(ids) else np.empty((0,2))
            s1=coverage(rawpts,path);s2=coverage(structured,path)
        for arm in arms:
            if gttip is None:r=unscored_summary_view(summary_lookup[arm,key[0],key[1]])
            else:r=readgz(resultdir(run,arm,row['group'])/(row['frame_id']+'.json.gz'))['result']
            tip=r['tip'];official=tip if r['status']=='VALID' else None
            error=float(np.linalg.norm(np.asarray(official)-gttip)) if official is not None and gttip is not None else None
            preferred=r['preferred_uncertain_tip'];pe=float(np.linalg.norm(np.asarray(preferred)-gttip)) if preferred is not None and gttip is not None else None
            oracle=min((float(np.linalg.norm(np.asarray(p['endpoint'])-gttip)) for p in r['candidates']),default=None) if gttip is not None else None
            omitted=[];generated_oracle=oracle
            if gttip is not None:
                lineage=readgz(resultdir(run,arm,row['group'])/(row['frame_id']+'_lineage.json.gz'));omitted=lineage['omitted_candidates']
                generated_errors=[float(np.linalg.norm(np.asarray(p['endpoint'])-gttip)) for p in omitted]
                if oracle is not None:generated_errors.append(oracle)
                generated_oracle=min(generated_errors,default=None)
            m=dict(group=key[0],frame_id=key[1],arm=arm,visibility=label['visibility'] if label else 'UNLABELED',status=r['status'],official_x=official[0] if official else None,official_y=official[1] if official else None,gt_x=gttip[0] if gttip else None,gt_y=gttip[1] if gttip else None,error=error,preferred_uncertain_error=pe,oracle_candidate_error=oracle,**{'hit'+str(k):error is not None and error<=k for k in [3,5,10,20]},over100=error is not None and error>100,over500=error is not None and error>500,budget=r['budget']['exhausted'],null=official is None)
            metrics.append(m)
            m.update(oracle_generated_including_budget_omissions_error=generated_oracle,omitted_candidate_count=len(omitted) if gttip is not None else None,oracle_scope='RETAINED_POOL; GENERATED_SCOPE_REPORTED_SEPARATELY')
            if gttip is None:continue
            s3=0.;s4=0.;chosen_cov=0.;chosen_precision=0.
            for p in r['candidates']:
                cov,precision=candidate_geometry(p,geometry_cache,len(path));s3=max(s3,cov)
                if p['verified']:s4=max(s4,cov)
                err=float(np.linalg.norm(np.asarray(p['endpoint'])-gttip))
                candidate_scores.append(dict(group=key[0],frame_id=key[1],arm=arm,candidate=p['id'],verified=p['verified'],tip_error=err,path_coverage10=cov,path_precision10=precision,rejected=';'.join(p['rejected_reasons']),scope='RETAINED_CANDIDATE'))
                if p.get('track_id')==r['selected_track_id'] and official is not None:chosen_cov=cov;chosen_precision=precision
            omitted_coverage=0.
            for p in omitted:
                cov,precision=candidate_geometry(p,geometry_cache,len(path));omitted_coverage=max(omitted_coverage,cov)
                candidate_scores.append(dict(group=key[0],frame_id=key[1],arm=arm,candidate=p['id'],verified=False,tip_error=float(np.linalg.norm(np.asarray(p['endpoint'])-gttip)),path_coverage10=cov,path_precision10=precision,rejected='CANDIDATE_BUDGET',scope='OMITTED_BY_BUDGET_NOT_OFFICIAL'))
            with np.load(resultdir(run,arm,key[0])/(key[1]+'_debug.npz')) as debug:
                mask=debug['mask'];xy=np.rint(path-[xa,ya]).astype(int);valid=(xy[:,0]>=0)&(xy[:,0]<mask.shape[1])&(xy[:,1]>=0)&(xy[:,1]<mask.shape[0]);kept=np.zeros(len(path),bool);kept[valid]=mask[xy[valid,1],xy[valid,0]];s5=float(kept.mean()) if len(path) else 0.
                gx,gy=np.rint(np.asarray(gttip)-[xa,ya]).astype(int);tipinside=bool(0<=gx<mask.shape[1] and 0<=gy<mask.shape[0] and mask[gy,gx])
            if r['budget']['exhausted']:stage='BUDGET_INCOMPLETE'
            elif s1<.8:stage='S1_RAW_COVERAGE'
            elif s2<.8:stage='S2_SEGMENT_STRUCTURE'
            elif s3<.8:stage='S3_CONNECTION_CANDIDATE'
            elif s4<.8:stage='S4_IDENTITY_VERIFICATION'
            elif not m['hit10']:stage='S6_ENDPOINT_OR_SELECTION'
            else:stage='OFFICIAL_HIT10'
            stages.append(dict(group=key[0],frame_id=key[1],arm=arm,earliest_observable_loss=stage,S1_raw_coverage10=s1,S2_structured_coverage10=s2,S3_best_candidate_coverage10=s3,S4_best_verified_coverage10=s4,S5_feedback_ROI_path_fraction=s5,S5_tip_in_working_mask=tipinside,official_path_coverage10=chosen_cov,official_path_precision10=chosen_precision,official_hit10=m['hit10'],joint_hit10=m['hit10'] and chosen_cov>=.8 and chosen_precision>=.8,causal_claim=False))
            stages[-1].update(S3_generated_best_coverage10=max(s3,omitted_coverage),S3_omitted_best_coverage10=omitted_coverage,retained_tip_oracle_error=oracle,generated_tip_oracle_error=generated_oracle)
        if int(row['frame_id'])%100==0:print('EVALUATE',split,key,flush=True)
    summaries=[]
    for group in dict.fromkeys(r['group'] for r in rs):
        for arm in arms:
            part=[m for m in metrics if m['group']==group and m['arm']==arm];v=[m for m in part if m['visibility']=='VISIBLE'];errors=[m['error'] for m in v if m['error'] is not None]
            out=dict(group=group,arm=arm,frames=len(part),visible=len(v),valid=len(errors),null=len(v)-len(errors),**{k:sum(m[k] for m in v) for k in ['hit3','hit5','hit10','hit20','over100','over500']},coverage=len(errors)/len(v),hit10_rate=sum(m['hit10'] for m in v)/len(v),severe100_rate=sum(m['over100'] for m in v)/len(v),mean_error=float(np.mean(errors)) if errors else None,median_error=float(np.median(errors)) if errors else None,p95_error=float(np.percentile(errors,95)) if errors else None,max_error=max(errors) if errors else None,oracle_hit10=sum(m['oracle_candidate_error'] is not None and m['oracle_candidate_error']<=10 for m in v),preferred_uncertain_hit10=sum(m['preferred_uncertain_error'] is not None and m['preferred_uncertain_error']<=10 for m in v),full_sequence_budget=sum(m['budget'] for m in part),full_sequence_valid=sum(m['status']=='VALID' for m in part),states=json.dumps(dict(collections.Counter(m['status'] for m in part))))
            targets={'group_a':(14,16,0),'three_point_bend':(11,12,0),'group_c':(14,16,1)}[group];out['passes_frozen_thresholds']=out['hit10']>=targets[0] and out['valid']>=targets[1] and out['over100']<=targets[2];summaries.append(out)
            out['oracle_generated_hit10']=sum(m['oracle_generated_including_budget_omissions_error'] is not None and m['oracle_generated_including_budget_omissions_error']<=10 for m in v)
    csvwrite(run/'offline_evaluation'/f'{split}_frames.csv',metrics);csvwrite(run/'offline_evaluation'/f'{split}_metrics.csv',summaries);csvwrite(run/'offline_evaluation'/f'{split}_candidate_oracle.csv',candidate_scores);csvwrite(run/'diagnostics'/f'{split}_failure_stages.csv',stages)
    put(run/'offline_evaluation'/f'{split}_summary.json',summaries)
    # Predictions remain byte-identical after annotation access.
    verify_seal(run,split);put(run/'offline_evaluation'/f'{split}_evaluation_seal.json',dict(inference_unchanged=True,files={str(p.relative_to(run)):sha(p) for p in sorted((run/'offline_evaluation').glob(split+'_*')) if p.name!=split+'_evaluation_seal.json'}))
    print(json.dumps(summaries,ensure_ascii=False),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--split',choices=['DEV','LOCKED'],required=True);a=ap.parse_args();evaluate(Path(a.run).resolve(),a.split)
