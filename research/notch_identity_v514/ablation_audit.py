"""Cross the old/new upstream map with the old/new local detector for attribution."""
from concurrent.futures import ProcessPoolExecutor
import json
import numpy as np
from research.notch_identity_v513 import batch as old_model
from . import batch as b, domain
from .run import frozen, workers, load
from research.v3_labelme_comparison.compare import write_csv


def run(job):
    g,record,pl=job;i=record['frame']
    m,image,old_map,fixed=load(g,i)
    l,t,r,bt=record['box'];ox,oy=m['evidence']['scene']['bounds'][:2]
    local=np.s_[t-oy:bt-oy,l-ox:r-ox]
    raw=image[local];origin=np.array([l,t]);ref=fixed[t:bt,l:r]
    mapping=record['mappings'][pl];cp,rp=np.array(mapping['cur']),np.array(mapping['ref'])
    box=mapping['bounds']
    new_map=domain.embed(domain.replay(fixed,cp,rp,box,mapping) if box else None,box,record['box'])
    rows=[]
    for engine,stage,version in [(old_model,'S3','V5.13'),(b,'S1','V5.14-S1')]:
        for family,aligned in [('旧',old_map[local]),('新',new_map)]:
            model,_=engine.run_mode(raw,ref,cp,rp,origin,stage,'full',aligned=aligned)
            d=model['diagnostics']['dual']
            rows.append(dict(group=g,frame=i,placement=pl,engine=version,mapping=family,tip=model['tip'],
                status=model['status'],shift=(d.get('registration') or {}).get('shift'),source=d.get('decision'),
                reproduced=(model['tip']==record['placements'][pl]['S1']['full']['tip'] if engine is b and family=='新' else None)))
    return rows


if __name__=='__main__':
    import sys
    frozen()
    for g in sys.argv[1:]:
        assert b.read(b.OUT/(g+'_seal.json'))['predictions']==b.sha(b.OUT/(g+'.jsonl'))
        ids={int(r['frame_id']) for r in b.read_csv(b.SELECT) if r['dataset_id']==g}
        jobs=[(g,r,pl) for r in map(json.loads,(b.OUT/(g+'.jsonl')).open()) if r['frame'] in ids for pl in r['placements']]
        with ProcessPoolExecutor(4,initializer=workers) as pool:
            rows=[r for block in pool.map(run,jobs,chunksize=1) for r in block]
        write_csv(b.OUT/(g+'_mapping_cross.csv'),rows)
