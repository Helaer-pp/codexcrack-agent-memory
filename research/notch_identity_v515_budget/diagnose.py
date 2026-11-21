"""Frozen counterfactual mapping/corridor replays and synthetic terminal diagnostics."""
import json
from itertools import product
import numpy as np
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b, domain, probes, terminal
from .run import workers, frozen, jobs

def synthetic():
    rows=[]
    for case,z,stage in product(('P4_open','P6_deformed_scratch','P6_isolated','weak_material_bridge'),(.5,1.,2.),b.ALGS):
        raw,fixed,h,s,gt=probes.images((case,0,1.,z,1,17))
        p=terminal.prepare(raw,h,s,stage,reference=fixed)
        m=terminal.predict(p,None,fixed.astype(np.float32),{})
        d=m['diagnostics']['dual']; branches=d['branches']
        branch=next((a for a in branches if 'BRANCH_'+str(a['id'])==d['pick']),max(branches,key=lambda a:a['merit'],default={}))
        info=branch.get('curve',{})
        rows.append(dict(stage=stage,case=case,zoom=z,noise=1,seed=17,photo='nominal',reason=d['stop'],
                         tip=m['tip'],gt=gt[-1].tolist() if len(gt) else None,dx=(m['tip'][0]-gt[-1,0])/z if m['tip'] and len(gt) else None,
                         registration=(d.get('registration') or {}).get('source'),dual_run=info.get('longest_dual_run'),
                         dual_columns=info.get('dual_columns'),cost=info.get('geometry_cost'),peak=info.get('peak')))
    write_csv(b.OUT/'synthetic_replay.csv',rows)

def crossed():
    group='three_point_bend'
    assert b.read(b.OUT/(group+'_seal.json'))['predictions']==b.sha(b.OUT/(group+'.jsonl'))
    roster={j[1] for j in jobs(group,b.ALGS,False) if j[2]}
    scores={int(r['frame']):r for r in b.read_csv(b.OUT/(group+'_scores.csv')) if r['stage']=='S1'}
    rows=[]
    for i in sorted(roster):
        meta=b.read(b.OLD/'evidence'/group/str(i)/'metadata.json')
        info=meta['input']
        cur=b.old.current(info['current'],info['image_sha'])
        fixed=b.old.read_fixed(info['reference'],info['ref_sha'])
        cp,rp=map(np.asarray,(meta['current_points'],meta['fixed_points']))
        box=meta['evidence']['scene']['bounds'];l,t,r,bt=box
        origin=np.array([l,t]);raw=cur[t:bt,l:r];ref=fixed[t:bt,l:r]
        prep=terminal.prepare(raw,cp.mean(0)-origin,b.SCALE,'S1',ref,rp.mean(0)-origin)
        for mapping in ('S1','S2'):
            for engine in ('S1','S2'):
                aligned=domain.ReferenceMap(cur,fixed,cp,rp,box,prep,mapping)
                m,_=b.run_mode(raw,ref,cp,rp,origin,engine,'full',aligned=aligned,prepared=prep)
                d=m['diagnostics']['dual']; tip=m['tip']; point=scores[i]['gt']
                rows.append(dict(frame=i,mapping=mapping,engine=engine,tip=tip,error=float(np.linalg.norm(np.array(tip)-json.loads(point))) if tip and point else None,
                                 source=d['decision'],stop=d['stop'],shift=(d.get('registration') or {}).get('shift'),
                                 field_pixels=d.get('field_pixels'),map_pixels=aligned.pixels,coarse_tip=d.get('coarse_tip')))
    write_csv(b.OUT/'mapping_cross.csv',rows)

if __name__=='__main__':
    import sys
    frozen();workers()
    for action in sys.argv[1:]:
        {'synthetic':synthetic,'crossed':crossed}[action]()
