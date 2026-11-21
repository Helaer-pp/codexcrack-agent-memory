"""Recrop native MT inputs after moving both anchor pairs; compare against the sealed nominal run."""
from concurrent.futures import ProcessPoolExecutor
import json
import math
import numpy as np
from research.unified_crack_tip_60q.features import CONFIG,scene_geometry
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b,domain,inputs
from .run import workers,frozen


def replay(job):
    i,nominal=job
    m=inputs.metadata('group_h',i)
    src=m['input']
    cur=b.old.current(src['current'],src['image_sha'])
    fixed=b.old.read_fixed(src['reference'],src['ref_sha'])
    rows=[]
    for dx in (-150,-350):
        cp,rp=[np.array(m[k])+[dx,0] for k in ('current_points','fixed_points')]
        box=scene_geometry(cur,cp,fixed,rp,None,CONFIG)['bounds']
        l,t,r,bot=box; origin=np.array([l,t])
        raw=cur[t:bot,l:r];ref=fixed[t:bot,l:r]
        prep=b.terminal.prepare(raw,cp.mean(0)-origin,b.SCALE,'S2',ref,rp.mean(0)-origin)
        mapped=domain.ReferenceMap(cur,fixed,cp,rp,box,prep,'S2')
        model,_=b.run_mode(raw,ref,cp,rp,origin,'S2','full',aligned=mapped,prepared=prep)
        d=model['diagnostics']['dual']
        row=dict(frame=i,dx=dx,status=model['status'],nominal_status=nominal['status'],
                 status_equal=model['status']==nominal['status'],path_equal=model['points']==nominal['points'],
                 tip_drift=math.dist(model['tip'],nominal['tip']) if model['tip'] and nominal['tip'] else None)
        for key in ('material_band','reference_apex','current_apex'):
            row[key]=d.get(key); row['nominal_'+key]=nominal[key]
            row[key+'_equal']=d.get(key) is not None and d[key]==nominal[key]
        rows.append(row)
    return rows


def main():
    frozen()
    file=b.OUT/'group_h.jsonl'
    assert b.sha(file)==b.read(b.OUT/'group_h_seal.json')['predictions']
    jobs=[]
    for rec in map(json.loads,file.open(encoding='utf8')):
        model=rec['placements']['original']['S2']['full']
        d=model['diagnostics']['dual']
        jobs.append((rec['frame'],{**{k:model[k] for k in ('points','tip','status')},
                                   **{k:d.get(k) for k in ('material_band','reference_apex','current_apex')}}))
    with ProcessPoolExecutor(4,initializer=workers) as pool:
        rows=[row for pair in pool.map(replay,jobs,chunksize=3) for row in pair]
    assert len(rows)==820
    write_csv(b.OUT/'group_h_shift.csv',rows)

if __name__=='__main__':main()
