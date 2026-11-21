"""Frozen native ROI inference and sealed same-frame baseline comparison."""
import argparse,csv,json,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from research.notch_identity_v3.run import OLD,ROOT,RUN as V3,read,sha,save,globalize,sources as v3_sources
from research.notch_identity_v57.batch import OUT as BASE,sources as base_sources,SELECT,GROUPS
from research.v3_labelme_comparison.infer import current
from functools import lru_cache

COMPARISON=BASE
read_fixed=lru_cache(maxsize=2)(current)
from research.unified_crack_tip_60q.common import clean
from . import terminal as new

OUT=ROOT/'output/experiments/v58_valley_bridge_20261120_r04'
HERE=Path(__file__).resolve().parent
ALGS=('v3_6','v4_2','v5_0','v5_1','v5_2','v5_3','v5_4','v5_5','v5_7',*new.STAGES)
def sources():
    return {**base_sources(),**{str(p.relative_to(ROOT)):sha(p) for p in [HERE/n for n in ('batch.py','terminal.py','probes.py','score.py','jitter.py','optics.py')]}}

def lengths(m,scene):
    arc=projected=None
    if m['tip'] is not None:
        path=np.array(m['points'],dtype=float)
        assert np.array_equal(path[-1],m['tip']) and np.array_equal(path[0],m['root'])
        arc=float(np.linalg.norm(np.diff(path,axis=0),axis=1).sum())
        if scene['points_observed']:
            a,b=np.asarray(scene['points_geometry'],dtype=float);dx,dy=b-a
            normal=np.array([dy,-dx])
            if normal[0]<0:normal=-normal
            if np.linalg.norm(normal)>0:projected=float(np.dot(path[-1]-(a+b)*.5,normal/np.linalg.norm(normal)))
    return dict(path_length_px=arc,projected_length_px=projected)

def warm():
    cv2.setNumThreads(1)
    v=np.ones((8,4),np.float32)
    new.global_free_end_dp(v,np.ones((1,4),np.uint8),100.)

def run_one(job):
    row,annotated=job;g=row['group'];f=int(row['frame_id'])
    folder=OLD/'evidence'/g/str(f)
    meta=read(folder/'metadata.json');scene=meta['evidence']['scene']
    assert meta['input']['image_sha']==row['image_sha'] and sha(folder/'arrays.npz')==meta['arrays_sha']
    off=scene['bounds'][:2]
    hint=np.rint(np.asarray(scene['root'] or scene['center'])-off).astype(int).tolist()
    records={}
    with np.load(folder/'arrays.npz') as data:
        raw=data['raw'];fixed=data['fixed__aligned']
        for stage in new.STAGES if annotated else ('v5_8',):
            result={}
            if stage=='v5_8':
                l,t,r,bt=scene['bounds']
                native=read_fixed(meta['input']['reference'],meta['input']['ref_sha'])[t:bt,l:r]
            else:
                native=fixed
            for mode,reference,field in [('full',native,'seconds'),('raw_only',None,'raw_seconds')]:
                surface={} if stage=='v5_8' and annotated else None
                t=time.perf_counter()
                prep=new.prepare(raw,hint,scene['scale'],stage)
                m=new.predict(prep,None,reference,surface)
                result[field]=time.perf_counter()-t
                if surface:
                    surface['origin']+=off
                    dest=OUT/'surfaces'/g;dest.mkdir(exist_ok=True,parents=True)
                    np.savez_compressed(dest/f'{f:04d}_{mode}.npz',**surface)
                dual=m['diagnostics']['dual']
                if 'front' in dual:
                    dual['front']+=off[0]
                    dual['roi_y']=[y+off[1] for y in dual['roi_y']]
                for key in ('peak','global_tip','distal_tip'):
                    if dual.get(key):dual[key]=[a+b for a,b in zip(dual[key],off)]
                for branch in dual['branches']:
                    for key in ('root','tip','base_tip'):
                        branch[key]=[a+b for a,b in zip(branch[key],off)]
                m=globalize(m,off)
                m.update(lengths(m,scene))
                result[mode]=m
            records[stage]=result
    return clean(dict(group=g,frame=f,source_sha=row['image_sha'],models=records))

def freeze():
    assert not (OUT/'freeze.json').exists()
    assert v3_sources()==read(V3/'freeze.json')['sources']
    assert read(OUT/'group_a_seal.json')['sources']==sources()
    from .probes import synthetic_gate
    assert synthetic_gate(OUT)
    seal=read(OUT/'jitter_seal.json')
    assert seal['sources']==sources() and sha(OUT/'jitter_predictions.jsonl')==seal['predictions']
    save(OUT/'freeze.json',dict(jitter=sha(OUT/'jitter_summary.csv'),sources=sources(),primary='v5_8',group_a=sha(OUT/'group_a.jsonl'),
                                events=sha(OUT/'weak_events.csv'),dev_scores=sha(OUT/'group_a_scores.csv'),
                                paired_probes=sha(OUT/'paired_probes.csv')))

def run(g):
    if g not in GROUPS:raise ValueError(g)
    assert base_sources()==read(BASE/'freeze.json')['sources']
    assert v3_sources()==read(V3/'freeze.json')['sources']
    from .probes import synthetic_gate
    assert synthetic_gate(OUT), 'Synthetic prerequisite not met'
    if g!='group_a':
        lock=read(OUT/'freeze.json')
        assert lock['sources']==sources() and lock['group_a']==sha(OUT/'group_a.jsonl')
        if g=='group_c':assert (OUT/'three_point_bend_scores.csv').exists()
    with SELECT.open(encoding='utf-8-sig',newline='') as f:
        selected={int(r['frame_id']) for r in csv.DictReader(f) if r['dataset_id']==g}
    with (OLD/'manifests/input_inventory.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=[r for r in csv.DictReader(f) if r['group']==g]
    assert len(selected)==20 and [int(r['frame_id']) for r in rows]==list(range(1,GROUPS[g]+1))
    path=OUT/(g+'.jsonl');assert not path.exists()
    (OUT/'frames'/g).mkdir(parents=True,exist_ok=True)
    started=time.perf_counter()
    with path.with_suffix('.partial').open('x',encoding='utf-8') as f,ProcessPoolExecutor(3,initializer=warm) as pool:
        historical=COMPARISON/(g+'.jsonl')
        assert sha(historical)==read(COMPARISON/(g+'_seal.json'))['predictions']
        with historical.open(encoding='utf8') as prior:
            for i,record in enumerate(pool.map(run_one,((r,int(r['frame_id']) in selected) for r in rows),chunksize=2),1):
                old=json.loads(next(prior))
                assert (old['group'],old['frame'],old['source_sha'])==(g,i,record['source_sha'])
                for stage in ALGS[:-len(new.STAGES)]:
                    if stage in old['models'] and (i in selected or i==347):
                        record['models'][stage]=old['models'][stage]
                f.write(json.dumps(record,separators=(',',':'),allow_nan=False)+'\n')
                if i%150==0:print(g,i,flush=True)
            assert not prior.readline()
    path.with_suffix('.partial').rename(path)
    save(OUT/(g+'_seal.json'),dict(sources=sources(),frames=len(rows),wall_seconds=time.perf_counter()-started,predictions=sha(path)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=[*GROUPS,'freeze']);act=p.parse_args().action
    if act=='freeze':freeze()
    else:run(act)
