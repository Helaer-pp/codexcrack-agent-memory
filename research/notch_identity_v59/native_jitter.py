"""Supplementary development-only audit that rebuilds the upstream crop for every point change."""
import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
from research.unified_crack_tip_60q.features import scene_geometry,CONFIG
from research.notch_identity_v58_strict.jitter import synchronized
from research.v3_labelme_comparison.compare import write_csv,evaluate,PACKAGE
from .batch import OUT,OLD,SELECT,read,sha,save,read_csv,old,run_mode,sources


def one(i):
    meta=read(OLD/'evidence/group_a'/str(i)/'metadata.json');info=meta['input']
    raw=old.current(info['current'],info['image_sha']);fixed=old.read_fixed(info['reference'],info['ref_sha'])
    pts=np.array(meta['current_points']);ref=np.array(meta['fixed_points'])
    out=[]
    for _,direction,delta,cp,rp in synchronized(pts,ref):
        box=scene_geometry(raw,cp,fixed,rp,None,CONFIG)['bounds'];l,t,r,b=box
        m,_=run_mode(raw[t:b,l:r],fixed[t:b,l:r],cp,rp,np.array([l,t]),'v5_9','full')
        out.append(old.clean(dict(frame=i,direction=direction,delta=delta,bounds=box,tip=m['tip'],status=m['status'],points=m['points'])))
    return out


def main():
    assert read(OUT/'freeze.json')['sources']==sources()
    sel={int(r['frame_id']):r for r in read_csv(SELECT) if r['dataset_id']=='group_a'}
    with ProcessPoolExecutor(4,initializer=old.warm) as pool: rows=sum(pool.map(one,sel),[])
    path=OUT/'group_a_native_predictions.json'
    save(path,rows)
    save(OUT/'group_a_native_seal.json',dict(predictions=sha(path),audit_source=sha(Path(__file__)),freeze=sha(OUT/'freeze.json')))
    sealed={r['frame']:r['placements']['original']['v5_9']['full'] for r in map(json.loads,(OUT/'group_a.jsonl').open())}
    scores=[];base={}
    for r in read(path):
        i=r['frame'];shapes=read(PACKAGE/sel[i]['selected_json'])['shapes']
        gt=next((s['points'][0] for s in shapes if s['label']=='crack_tip'),None)
        paths=[np.array(s['points']) for s in shapes if s['label']=='crack_path']
        metric=evaluate(r,paths,gt)
        if not r['delta']:
            assert r['points']==sealed[i]['points']
            base[i]=r,metric
        prev,old_metric=base[i]
        scores.append(dict(frame=i,direction=r['direction'],delta=r['delta'],bounds=r['bounds'],tip=r['tip'],
              baseline_tip=prev['tip'],drift=math.dist(r['tip'],prev['tip']) if r['tip'] and prev['tip'] else None,
              base_joint=old_metric['joint'],joint=metric['joint']))
    write_csv(OUT/'group_a_native_jitter.csv',scores)
    print('Verified',len(scores),'native field-of-view predictions')


if __name__=='__main__':main()
