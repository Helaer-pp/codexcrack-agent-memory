"""Independent post-freeze scoring process. NEVER imported by algorithm/renderer."""
import argparse,collections,hashlib,json,math,zipfile
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from .common import *
from .algorithm import MODES

def dense(points):
    p=np.asarray(points,float).reshape(-1,2);parts=[]
    for a,b in zip(p[:-1],p[1:]):
        n=max(1,math.ceil(float(np.linalg.norm(b-a))));parts.append(a+(b-a)*np.arange(n)[:,None]/n)
    if len(p):parts.append(p[-1:])
    return np.concatenate(parts) if parts else np.empty((0,2))

def observed_dense(trace):
    pieces=[];part=[]
    for p in trace:
        if p[2]:part.append(p[:2])
        elif part:pieces.append(dense(part));part=[]
    if part:pieces.append(dense(part))
    return np.concatenate(pieces) if pieces else np.empty((0,2))

def path_metrics(path,gt):
    if not len(gt):return dict(coverage5=None,coverage10=None,precision5=None,precision10=None)
    forward=cKDTree(path).query(gt)[0] if len(path) else np.full(len(gt),np.inf)
    backward=cKDTree(gt).query(path)[0] if len(path) else np.empty(0)
    return {**{f'coverage{t}':float(np.mean(forward<=t)) for t in [5,10]},**{f'precision{t}':float(np.mean(backward<=t)) if len(path) else 0. for t in [5,10]}}

def get_labels(run,role,groups):
    seal=get(run/f'inference_frozen_{role}.json')
    for rel,h in seal['files'].items():
        if sha(run/rel)!=h:raise RuntimeError('Predictions changed before evaluation')
    labels={};access=[];archive=ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip';archive_sha=sha(archive)
    with zipfile.ZipFile(archive) as z:
        for r in rows(ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv'):
            g=r['dataset_id']
            if g not in groups:continue
            if g not in GROUPS:raise ValueError('Excluded labels')
            b=z.read(r['selected_json']);d=json.loads(b)
            assert d['imageWidth']==int(r['width']) and d['imageHeight']==int(r['height'])
            assert Path(d['imagePath'].replace('\\','/')).name==Path(r['selected_image']).name
            labels[g,str(r['frame_id'])]=d
            access.append(dict(group=g,frame_id=r['frame_id'],member=r['selected_json'],sha256=hashlib.sha256(b).hexdigest(),snapshot_sha=archive_sha,freeze_sha=sha(run/f'inference_frozen_{role}.json'),usage='OFFLINE_COMPARISON_ONLY'))
    csvwrite(run/f'annotation_access_{role}.csv',access);return labels

def score(row,record,label):
    tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'] if label else []
    parts=[dense(s['points']) for s in label['shapes'] if s['label']=='crack_path'] if label else []
    gt=np.concatenate(parts) if parts else np.empty((0,2));tip=np.asarray(tips[0],float) if tips else None
    visibility='VISIBLE' if tips else 'UNKNOWN' if label else 'UNLABELED';g=record['roi'];metrics=[];candidates=[];bridge_records=[]
    for r in record['results']+record['baselines']:
        paths=r['paths'];chosen=paths[0] if paths else None;predpath=observed_dense(chosen['selected_trace']) if chosen else np.empty((0,2))
        pm=path_metrics(predpath,gt);error=float(np.linalg.norm(np.subtract(r['tip'],tip))) if tip is not None and r['tip'] is not None else None
        rawerror=float(np.linalg.norm(np.subtract(r['candidate_tip'],tip))) if tip is not None and r['candidate_tip'] is not None else None
        last=r.get('last_observed_pixel');last_error=float(np.linalg.norm(np.subtract(last,tip))) if tip is not None and last else None
        roi_inside=bool(g['xleft']<=tip[0]<g['xr'] and g['upper']<=tip[1]<=g['lower']) if tip is not None else None
        candidate_good=[];candidate_reached=[];candidate_joint=[]
        for rank,p in enumerate(paths):
            full=observed_dense(p['observed_trace']);m=path_metrics(full,gt);nearest=float(cKDTree(full).query(tip)[0]) if len(full) and tip is not None else None
            cerr=float(np.linalg.norm(np.subtract(p.get('candidate_tip'),tip))) if tip is not None and p.get('candidate_tip') is not None else None
            good=bool(m['coverage10'] is not None and m['coverage10']>=.8 and m['precision10']>=.8)
            if good:candidate_good.append(rank)
            if nearest is not None and nearest<=10:candidate_reached.append(rank)
            if good and cerr is not None and cerr<=10:candidate_joint.append(rank)
            if label:
                candidates.append(dict(group=row['group'],frame_id=row['frame_id'],mode=r['mode'],rank=rank,path_id=p['id'],visibility=visibility,**m,nearest_observed_to_tip=nearest,candidate_tip_error=cerr,path_good=good,offline_only=True))
            for bi,b in enumerate(p.get('bridges',[])):
                points=dense([b['start'],b['end']]);dist=cKDTree(gt).query(points)[0] if len(gt) else np.empty(0)
                if label:bridge_records.append(dict(group=row['group'],frame_id=row['frame_id'],mode=r['mode'],rank=rank,bridge=bi,missing_pixels=b['missing'],start=b['start'],end=b['end'],distance_mean=float(dist.mean()) if len(dist) else None,distance_max=float(dist.max()) if len(dist) else None,off_annotated_path10_fraction=float(np.mean(dist>10)) if len(dist) else None,physical_wrong_bridge='UNDETERMINED_WITH_PARTIAL_GT',offline_only=True))
        public_joint=bool(error is not None and error<=10 and (pm['coverage10'] or 0)>=.8 and (pm['precision10'] or 0)>=.8)
        if visibility!='VISIBLE':stage=visibility
        elif not roi_inside:stage='ROI_GEOMETRY_EXCLUSION'
        elif not candidate_reached:stage='EVIDENCE_OR_GRAPH_REACHABILITY'
        elif not candidate_good:stage='PATH_COMPLETENESS_OR_CONTAMINATION'
        elif 0 not in candidate_good:stage='PATH_RANKING'
        elif not public_joint:stage='STOPPING_OR_AMBIGUITY'
        else:stage='JOINT_HIT'
        m=dict(group=row['group'],frame_id=row['frame_id'],role='DEVELOPMENT' if row['group'] in DEV else 'EXPOSED_REGRESSION',mode=r['mode'],visibility=visibility,output_state=r['output_state'],tip=json.dumps(r['tip']),candidate_tip=json.dumps(r['candidate_tip']),last_observed_pixel=json.dumps(last),error=error,raw_candidate_error=rawerror,last_observed_error=last_error,**pm,roi_contains_gt=roi_inside,joint=public_joint,any_candidate_reaches_tip=bool(candidate_reached),any_candidate_path_good=bool(candidate_good),any_candidate_joint=bool(candidate_joint),chosen_full_path_good=0 in candidate_good,stage=stage,observed_pixels=sum(bool(p[2]) for p in chosen['selected_trace']) if chosen else 0,inferred_pixels=sum(not p[2] for p in chosen['selected_trace']) if chosen else 0,bridges=len(chosen.get('bridges',[])) if chosen else 0,reference_status=record['reference_status'],notch_status=record['notch']['status'])
        for t in [3,5,10]:m[f'hit{t}']=error is not None and error<=t
        for t in [100,500]:m[f'over{t}']=error is not None and error>t
        metrics.append(m)
    return metrics,candidates,bridge_records

def summarize(metrics,scope):
    out=[];groups=sorted({r['group'] for r in metrics});modes=list(MODES)+['V1_LOCKED','V2_NUMERIC_CONTROL','V2_COMBINED']
    for group in groups+[scope]:
        for mode in modes:
            part=[r for r in metrics if r['mode']==mode and (group==scope or r['group']==group)];vis=[r for r in part if r['visibility']=='VISIBLE'];errs=[r['error'] for r in vis if r['error'] is not None];raw=[r['raw_candidate_error'] for r in vis if r['raw_candidate_error'] is not None]
            s=dict(group=group,mode=mode,frames=len(part),visible=len(vis),unknown=sum(r['visibility']=='UNKNOWN' for r in part),unlabeled=sum(r['visibility']=='UNLABELED' for r in part),output_coverage=len(errs),joint=sum(r['joint'] for r in vis),roi_outside=sum(r['roi_contains_gt'] is False for r in vis),error_p50=float(np.percentile(errs,50)) if errs else None,error_p95=float(np.percentile(errs,95)) if errs else None,error_max=max(errs) if errs else None,raw_candidate_count=len(raw),real_FPR='N/A',any_candidate_path_good=sum(r['any_candidate_path_good'] for r in vis),any_candidate_joint=sum(r['any_candidate_joint'] for r in vis))
            for k in ['hit3','hit5','hit10','over100','over500']:s[k]=sum(r[k] for r in vis)
            for t in [100,500]:s[f'raw_over{t}']=sum(e>t for e in raw)
            for k in ['coverage5','coverage10','precision5','precision10']:s[k]=float(np.mean([r[k] or 0 for r in vis])) if vis else None
            for k,v in collections.Counter(r['output_state'] for r in part).items():s['full_'+k]=v
            for k,v in collections.Counter(r['stage'] for r in vis).items():s['failure_'+k]=v
            out.append(s)
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--role',choices=['development','exposed_regression'],required=True);args=p.parse_args();run=Path(args.run)
    if (run/f'evaluation_complete_{args.role}.json').exists():print('Existing sealed evaluation '+args.role);return
    from .run_all import check_sources
    check_sources(run);groups=DEV if args.role=='development' else set(GROUPS)-DEV;labels=get_labels(run,args.role,groups)
    data=[r for r in safe_manifest(run/'input_manifest.csv') if r['group'] in groups];metrics=[];candidates=[];bridges=[]
    for row in data:
        rec=readgz(frame_dir(run,row)/'result.json.gz');m,c,b=score(row,rec,labels.get((row['group'],row['frame_id'])));metrics.extend(m);candidates.extend(c);bridges.extend(b)
    scope='DEVELOPMENT' if args.role=='development' else 'EXPOSED_REGRESSION';summary=summarize(metrics,scope)
    for mode,hits in [('V1_LOCKED',12 if scope=='DEVELOPMENT' else 5),('V2_COMBINED',4)]:
        base=next(r for r in summary if r['group']==scope and r['mode']==mode)
        assert base['visible']==(76 if scope=='DEVELOPMENT' else 35) and base['hit10']==hits,base
    csvwrite(run/f'offline_evaluation_{args.role}.csv',metrics);csvwrite(run/f'group_summary_{args.role}.csv',summary);csvwrite(run/f'candidate_offline_{args.role}.csv',candidates)
    if bridges:csvwrite(run/f'bridges_offline_{args.role}.csv',bridges)
    put(run/f'evaluation_complete_{args.role}.json',dict(utc=utc(),frames=len(data),visible=76 if scope=='DEVELOPMENT' else 35,unknown=len(labels)-(76 if scope=='DEVELOPMENT' else 35),labels_comparison_only=True,baseline_hit10_reproduced=True,no_training=True,default=next(r for r in summary if r['group']==scope and r['mode']=='C_FUSION_RAW')))
    print('OFFLINE '+scope+' '+json.dumps([(r['mode'],r['hit10'],r['joint'],r['over100']) for r in summary if r['group']==scope]),flush=True)

if __name__=='__main__':main()
