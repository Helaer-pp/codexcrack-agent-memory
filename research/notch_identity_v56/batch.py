"""Frozen native ROI inference and sealed same-frame baseline comparison."""
import argparse,csv,json,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from research.notch_identity_v3.run import OLD,ROOT,RUN as V3,read,sha,save,globalize,sources as v3_sources
from research.notch_identity_v55.batch import OUT as BASE,sources as base_sources,SELECT,GROUPS
from research.unified_crack_tip_60q.common import clean
from . import terminal as new

OUT=ROOT/'output/experiments/v56_decoupled_20261120_r04'
HERE=Path(__file__).resolve().parent
ALGS=('v3_6','v4_2','v5_0','v5_1','v5_2','v5_3','v5_4','v5_5',*new.STAGES)
def sources():
    return {**base_sources(),**{str(p.relative_to(ROOT)):sha(p) for p in [HERE/n for n in ('batch.py','terminal.py','native.py','probes.py','score.py','jitter.py')]}}

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
    from research.v3_labelme_comparison.infer import current
    from .native import prepare,reference
    raw=current(meta['input']['current'],row['image_sha'])
    fixed=reference(meta['input']['reference'],meta['input']['ref_sha'])
    records={}
    for stage in new.STAGES if annotated else ('v5_6',):
        result={}
        for mode,im,field in [('full',fixed,'seconds'),('raw_only',None,'raw_seconds')]:
            surface={} if stage=='v5_6' and annotated else None
            t=time.perf_counter()
            prep=prepare(raw,scene['points_geometry'],stage)
            m=new.predict(prep,None,im,surface)
            result[field]=time.perf_counter()-t
            if surface:
                dest=OUT/'surfaces'/g;dest.mkdir(exist_ok=True,parents=True)
                np.savez_compressed(dest/f'{f:04d}_{mode}.npz',**surface)
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
    from research.v3_labelme_comparison.infer import read_csv
    assert (OUT/'jitter_summary.csv').exists()
    save(OUT/'freeze.json',dict(sources=sources(),primary='v5_6',group_a=sha(OUT/'group_a.jsonl'),
                                jitter=sha(OUT/'jitter_summary.csv'),events=sha(OUT/'weak_events.csv'),dev_scores=sha(OUT/'group_a_scores.csv'),
                                paired_probes=sha(OUT/'paired_probes.csv')))

def run(g):
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
    with path.with_suffix('.partial').open('x',encoding='utf-8') as f,ProcessPoolExecutor(6,initializer=warm) as pool:
        historical=BASE/(g+'.jsonl')
        assert sha(historical)==read(BASE/(g+'_seal.json'))['predictions']
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
