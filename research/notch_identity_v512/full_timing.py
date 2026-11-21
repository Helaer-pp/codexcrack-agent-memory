"""Time the frozen three-point sequence including uncached upstream reference construction."""
import json
from time import perf_counter
import cv2
import numpy as np
from research.unified_crack_tip_60q.features import CONFIG, scene_geometry, register_reference
from research.v3_labelme_comparison.compare import write_csv
from .batch import OUT,OLD,GROUPS,old,read,sha,run_mode,sources


def main():
    g='three_point_bend'
    assert read(OUT/'freeze.json')['sources']==sources()
    stream=OUT/(g+'.jsonl')
    assert read(OUT/(g+'_seal.json'))['predictions']==sha(stream)
    old.warm()
    cv2.setNumThreads(1)
    rows=[]
    for rec in map(json.loads,stream.open()):
        i=rec['frame']
        meta=read(OLD/'evidence'/g/str(i)/'metadata.json')
        info=meta['input']
        raw=old.current(info['current'],info['image_sha'])
        fixed=old.read_fixed(info['reference'],info['ref_sha'])
        cp,rp=map(np.asarray,(meta['current_points'],meta['fixed_points']))
        start=perf_counter()
        scene=scene_geometry(raw,cp,fixed,rp,None,CONFIG)
        l,t,r,b=scene['bounds']
        alignment,_=register_reference(fixed,raw,rp,cp,scene,CONFIG)
        prepared=perf_counter()
        pred,_=run_mode(raw[t:b,l:r],fixed[t:b,l:r],cp,rp,np.array([l,t]),'S4','full',aligned=alignment['aligned'])
        stop=perf_counter()
        ref=rec['placements']['original']['S4']['full']
        rows.append(dict(frame=i,upstream=prepared-start,detector=stop-prepared,total=stop-start,
                         identical=pred['status']==ref['status'] and pred['tip']==ref['tip'] and pred['points']==ref['points']))
    assert len(rows)==GROUPS[g]
    write_csv(OUT/'uncached_tpb_seconds.csv',rows)


if __name__=='__main__':main()
