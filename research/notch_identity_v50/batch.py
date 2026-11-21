"""Frozen native ROI inference and sealed same-frame baseline comparison."""
import argparse,csv,json,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from research.notch_identity_v3.run import OLD,ROOT,RUN as V3,read,sha,save,globalize,sources as v3_sources
from research.notch_identity_v42.batch import OUT as BASE,sources as base_sources,SELECT,GROUPS
from research.unified_crack_tip_60q.common import clean
from . import terminal as new

OUT=ROOT/'output/experiments/v50_global_dp_20261119_r06'
HERE=Path(__file__).resolve().parent
ALGS=('r02','v3_6','v4_2',*new.STAGES)
def sources():
    return {**base_sources(),**{str(p.relative_to(ROOT)):sha(p) for p in [HERE/n for n in ('batch.py','terminal.py','probes.py','score.py')]}}

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
        for stage in new.STAGES if annotated else ('v5_0',):
            result={}
            for mode,reference,field in [('full',fixed,'seconds'),('raw_only',None,'raw_seconds')]:
                surface={} if stage=='v5_0' and annotated else None
                t=time.perf_counter()
                prep=new.prepare(raw,hint,scene['scale'],stage)
                m=new.predict(prep,None,reference,surface)
                result[field]=time.perf_counter()-t
                if surface:
                    surface['origin']+=off
                    dest=OUT/'surfaces'/g;dest.mkdir(exist_ok=True,parents=True)
                    np.savez_compressed(dest/f'{f:04d}_{mode}.npz',**surface)
                dual=m['diagnostics']['dual']
                if 'front' in dual:dual['front']+=off[0]
                if dual.get('peak'):dual['peak']=[a+b for a,b in zip(dual['peak'],off)]
                result[mode]=globalize(m,off)
            records[stage]=result
    return clean(dict(group=g,frame=f,source_sha=row['image_sha'],models=records))

def freeze():
    assert not (OUT/'freeze.json').exists()
    assert v3_sources()==read(V3/'freeze.json')['sources']
    assert read(OUT/'group_a_seal.json')['sources']==sources()
    from .probes import synthetic_gate
    assert synthetic_gate(OUT)
    save(OUT/'freeze.json',dict(sources=sources(),primary='v5_0',group_a=sha(OUT/'group_a.jsonl'),
                                events=sha(OUT/'weak_events.csv'),dev_scores=sha(OUT/'group_a_scores.csv'),
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
    with path.with_suffix('.partial').open('x',encoding='utf-8') as f,ProcessPoolExecutor(6,initializer=warm) as pool:
        historical=BASE/(g+'.jsonl')
        assert sha(historical)==read(BASE/(g+'_seal.json'))['predictions']
        with historical.open(encoding='utf8') as prior:
            for i,record in enumerate(pool.map(run_one,((r,int(r['frame_id']) in selected) for r in rows),chunksize=2),1):
                old=json.loads(next(prior))
                assert (old['group'],old['frame'],old['source_sha'])==(g,i,record['source_sha'])
                for stage in ALGS[:3]:
                    if stage in old['models'] and (i in selected or i==347):
                        record['models'][stage]=old['models'][stage]
                f.write(json.dumps(record,separators=(',',':'),allow_nan=False)+'\n')
                if i%150==0:print(g,i,flush=True)
            assert not prior.readline()
    path.with_suffix('.partial').rename(path)
    save(OUT/(g+'_seal.json'),dict(sources=sources(),frames=len(rows),predictions=sha(path)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=[*GROUPS,'freeze']);act=p.parse_args().action
    if act=='freeze':freeze()
    else:run(act)
