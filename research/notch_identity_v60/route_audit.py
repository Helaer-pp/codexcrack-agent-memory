"""Recover the native contour coordinates for differing original/bright routes."""
import json
import numpy as np
from . import batch as b
from research.notch_identity_v59 import geometry
from research.v3_labelme_comparison.compare import write_csv

def main():
    rows=[]
    for rec in map(json.loads,(b.OUT/'group_c.jsonl').open()):
        models=[rec['placements'][p]['S2']['full']['diagnostics']['dual'] for p in ('original','bright')]
        mismatch=models[0]['decision']!=models[1]['decision']
        if not mismatch and rec['frame'] not in (7,38,54,469):continue
        cache=b.OLD/'evidence'/'group_c'/str(rec['frame'])
        meta=b.read(cache/'metadata.json')
        left,top,right,bottom=rec['box'];origin=np.array([left,top])
        x,y,*_=meta['evidence']['scene']['bounds']
        with np.load(cache/'arrays.npz') as arrays:
            raw=arrays['raw'][top-y:bottom-y,left-x:right-x]
        fixed=b.old.read_fixed(meta['input']['reference'],meta['input']['ref_sha'])[top:bottom,left:right]
        for pl,d in zip(('original','bright'),models):
            mapping=rec['mappings'][pl]['S2']
            h,rh=[np.mean(mapping[k],axis=0)-origin for k in ('cur','ref')]
            t,z=geometry.material(raw,fixed,h,rh,b.SCALE);off=np.array([0,t])
            rt=geometry.apex(fixed[t:z],rh-off,b.SCALE)
            ct=geometry.apex(raw[t:z],np.array(rt)+h-rh,b.SCALE)
            rows.append(dict(frame=rec['frame'],placement=pl,route_mismatch=mismatch,
                             fixed_vertex=(rt+off+origin).tolist(),current_vertex=(ct+off+origin).tolist(),
                             scale=d['scale'],front=d['front'],residual=d['native_change'],
                             threshold=d['route_floor'],route=d['decision'],stop=d['stop']))
    write_csv(b.OUT/'native_vertices.csv',rows)

if __name__=='__main__':main()
