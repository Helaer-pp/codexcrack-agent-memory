"""Offline comparison of sealed image-coordinate results against LabelMe paths and tips."""
import argparse
import csv
import json
import zipfile
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from experiment import ROOT,read,save,sha,GROUPS


def dense(points):
    if len(points)<2:return points
    return np.vstack([np.linspace(a,b,max(2,int(np.ceil(np.linalg.norm(b-a)))+1)) for a,b in zip(points,points[1:])])


def evaluate(run,split):
    path=run/(split+'.jsonl')
    assert sha(path)==read(run/(split+'_seal.json'))['predictions']
    pred={(r['group'],str(r['frame'])):r for r in map(json.loads,path.read_text().splitlines())}
    scored=[]
    with (ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv').open(encoding='utf-8-sig',newline='') as f:
        selected=list(csv.DictReader(f))
    with zipfile.ZipFile(ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip') as archive:
        for row in selected:
            key=row['dataset_id'],row['frame_id']
            if key not in pred:continue
            rec=pred[key]
            assert rec['source_sha']==row['sha256']
            label=json.loads(archive.read(row['selected_json']))
            assert (label['imageWidth'],label['imageHeight'])==(int(row['width']),int(row['height']))
            tip=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip']
            if not tip:continue
            assert len(tip)==1
            line=np.vstack([dense(np.asarray(s['points'])) for s in label['shapes'] if s['label']=='crack_path'])
            for mode in ('full','raw_only'):
                if mode not in rec:continue
                result=rec[mode]
                pts=np.asarray(result['points'])
                error=float(np.linalg.norm(np.array(result['tip'])-tip[0])) if result['tip'] else None
                coverage=float(np.mean(cKDTree(pts).query(line)[0]<=10)) if len(pts) else 0
                precision=float(np.mean(cKDTree(line).query(pts)[0]<=10)) if len(pts) else 0
                scored.append(dict(group=key[0],frame=key[1],mode=mode,status=result['status'],error=error,
                                   tip_dx=result['tip'][0]-tip[0][0] if result['tip'] else None,
                                   coverage=coverage,precision=precision,hit10=error is not None and error<=10,
                                   joint=error is not None and error<=10 and min(coverage,precision)>=.8))
    with (run/(split+'_visible.csv')).open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(scored[0]));w.writeheader();w.writerows(scored)
    summary=[]
    for g in GROUPS[split]:
        for mode in ('full','raw_only') if split=='dev' else ('full',):
            rs=[r for r in scored if r['group']==g and r['mode']==mode]
            n=len(rs)
            assert n=={'group_a':19,'three_point_bend':15,'group_c':20}[g]
            errors=[r['error'] for r in rs if r['error'] is not None]
            summary.append(dict(group=g,mode=mode,visible=n,valid=len(errors),hit10=sum(r['hit10'] for r in rs),
                                joint=sum(r['joint'] for r in rs),severe=sum(e>100 for e in errors),
                                max_error=max(errors,default=None),median_error=float(np.median(errors)) if errors else None,
                                full_sequence_valid=sum(bool(r[mode]['tip']) for r in pred.values() if r['group']==g)))
    save(run/(split+'_metrics.json'),summary)
    print(summary)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('split',choices=['dev','locked']);p.add_argument('run',type=Path)
    a=p.parse_args();evaluate(a.run,a.split)

