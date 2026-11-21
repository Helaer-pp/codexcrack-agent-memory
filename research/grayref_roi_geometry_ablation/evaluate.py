"""Separate-process, post-seal label comparison. Never imported by inference."""
import argparse,collections,hashlib,json,zipfile
import numpy as np
from grayref_simplified_evidence_v0.offline_evaluate import score,dense
from .common import *
from .geometry import MODES

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--phase',choices=['group_a','exposed'],required=True);a=p.parse_args();run=Path(a.run);check_sources(run)
    seal=get(run/f'frozen_{a.phase}.json')
    for rel,h in seal['files'].items():assert sha(run/rel)==h
    groups=['group_a'] if a.phase=='group_a' else ['group_c','three_point_bend'];data=[r for r in manifest(run/'input_manifest.csv') if r['group'] in groups];labels={};access=[]
    selected=[r for r in rows(ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv') if r['dataset_id'] in groups]
    lookup={(r['group'],r['frame_id']):r for r in data}
    with zipfile.ZipFile(ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip') as z:
        for r in selected:
            assert r['sha256']==lookup[r['dataset_id'],r['frame_id']]['image_sha']
            b=z.read(r['selected_json']);label=json.loads(b);labels[r['dataset_id'],r['frame_id']]=label
            access.append(dict(group=r['dataset_id'],frame_id=r['frame_id'],member=r['selected_json'],sha=hashlib.sha256(b).hexdigest(),inference_seal_sha=sha(run/f'frozen_{a.phase}.json'),usage='POST_FREEZE_COMPARISON_ONLY'))
    metrics=[];pool=[];bridge=[]
    for row in data:
        d=directory(run,row);r=readgz(d/'result.json.gz');label=labels.get((row['group'],row['frame_id']));adapt={**r,'baselines':[]}
        mm,pp,bb=score(row,adapt,label)
        with np.load(d/'evidence_arrays.npz') as q:
            gt=np.concatenate([dense(s['points']) for s in label['shapes'] if s['label']=='crack_path']) if label and any(s['label']=='crack_path' for s in label['shapes']) else np.empty((0,2))
            tip=next((s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'),None) if label else None
            for m in mm:
                mask=q[m['mode']];g=r['roi'];inside=None;fraction=None
                if tip:
                    x,y=np.rint(np.asarray(tip)-[g['xa'],g['ya']]).astype(int);inside=bool(0<=x<mask.shape[1] and 0<=y<mask.shape[0] and mask[y,x])
                if len(gt):
                    xy=np.rint(gt-[g['xa'],g['ya']]).astype(int);valid=(xy[:,0]>=0)&(xy[:,0]<mask.shape[1])&(xy[:,1]>=0)&(xy[:,1]<mask.shape[0]);hit=np.zeros(len(gt),bool);hit[valid]=mask[xy[valid,1],xy[valid,0]];fraction=float(hit.mean())
                m.update(hit20=m['error'] is not None and m['error']<=20,tip_inside_search=inside,GT_EXCLUDED=inside is False,GT_path_inside_fraction=fraction,tip_gt=json.dumps(tip),mask_only_offline=True)
                if inside is False:m['stage']='SEARCH_ROI_GT_EXCLUDED'
        metrics+=mm;pool+=pp;bridge+=bb
    csvwrite(run/f'offline_evaluation_{a.phase}.csv',metrics);csvwrite(run/f'candidate_pool_{a.phase}.csv',pool);csvwrite(run/f'annotation_access_{a.phase}.csv',access)
    if bridge:csvwrite(run/f'bridges_{a.phase}.csv',bridge)
    summary=[]
    for group in groups:
        for mode in MODES:
            part=[r for r in metrics if r['group']==group and r['mode']==mode];v=[r for r in part if r['visibility']=='VISIBLE']
            out=dict(group=group,mode=mode,frames=len(part),visible=len(v),unknown=sum(r['visibility']=='UNKNOWN' for r in part),unlabeled=sum(r['visibility']=='UNLABELED' for r in part),outputs=sum(r['error'] is not None for r in v),no_public=sum(r['error'] is None for r in v),**{k:sum(bool(r[k]) for r in v) for k in ['hit3','hit5','hit10','hit20','joint','over100','over500','any_candidate_path_good','GT_EXCLUDED']},path_coverage10=float(np.mean([r['coverage10'] for r in v])),path_precision10=float(np.mean([r['precision10'] for r in v])),**{name:sum(r[field] is not None and r[field]>cut for r in v) for name,field,cut in [('candidate_over100','raw_candidate_error',100),('candidate_over500','raw_candidate_error',500),('last_observed_over100','last_observed_error',100),('last_observed_over500','last_observed_error',500)]},states=dict(collections.Counter(r['output_state'] for r in part)),failure_stages=dict(collections.Counter(r['stage'] for r in v)))
            summary.append(out)
    put(run/f'evaluation_complete_{a.phase}.json',dict(utc=utc(),summary=summary,frames=len(data),visible=sum(s['visible'] for s in summary if s['mode']==MODES[0]),GT_comparison_only=True,no_training=True));print('OFFLINE '+json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
