"""One frozen sweep per group. Full sequences for V4.0, all presets on annotated frames."""
import argparse,csv,json,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from research.notch_identity_v3.run import OLD,ROOT,RUN as V3,read,sha,save,draw_card,globalize,sources as v3_sources
from research.notch_identity_v3 import terminal as s3t
from research.raw_notch_trace_v2b import detector as r02
from research.unified_crack_tip_60q.common import clean
from . import terminal as new
from research.notch_identity_v31 import terminal as v31
from research.notch_identity_v36.batch import sources as base_sources,OUT as BASE
from research.notch_identity_v36 import terminal as v36
from research.notch_identity_v32 import terminal as v32

OUT=ROOT/'output/experiments/v40_decoupled_20261119_r06'
SELECT=ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv'
HERE=Path(__file__).resolve().parent
GROUPS={'group_a':551,'three_point_bend':520,'group_c':562}
ALGS=('r02','s3t','v3_6',*new.STAGES)
def sources():
    return {**base_sources(),**{str(p.relative_to(ROOT)):sha(p) for p in [HERE/n for n in ('batch.py','terminal.py','evidence.py','tracking.py','probes.py','score.py')]}}

def warm():
    cv2.setNumThreads(1)
    a=np.ones((32,32),np.float32)
    v31.trace_windowed(a,a*0,0,16,12,6,3,4,20,8,6,.8)

def run_one(job):
    row,annotated=job;g=row['group'];f=int(row['frame_id'])
    folder=OLD/'evidence'/g/str(f)
    meta=read(folder/'metadata.json');scene=meta['evidence']['scene']
    assert meta['input']['image_sha']==row['image_sha'] and sha(folder/'arrays.npz')==meta['arrays_sha']
    off=scene['bounds'][:2]
    hint=np.rint(np.asarray(scene['root'] or scene['center'])-off).astype(int).tolist()
    modes=ALGS if annotated else ('v4_0',)
    records={}
    with np.load(folder/'arrays.npz') as data:
        raw=data['raw'];ref=[(data[k+'__signed'],data[k+'__valid']) for k in ('fixed','prev')]
        fixed=data['fixed__aligned']
        for stage in modes:
            model=r02 if stage=='r02' else s3t if stage=='s3t' else v36 if stage=='v3_6' else new
            t=time.perf_counter()
            prep=model.prepare(raw,hint,scene['scale']) if stage=='r02' else model.prepare(raw,hint,scene['scale'],stage)
            bonus=None
            if prep is not None:
                sl=prep[0];bonus=np.zeros_like(prep[3])
                denom=max(1e-6,.12*prep[-1]) if stage not in ('r02','s3t') else 20.
                for signed,valid in ref:
                    bonus+=np.where(valid[sl],.04*np.clip(signed[sl]/denom,0,1),0)
                if stage in ('r02','s3t','gap','taper'):bonus[prep[3]<1]=0
            res=model.predict(prep,bonus,fixed) if model in (v36,new) else model.predict(prep,bonus)
            elapsed=time.perf_counter()-t
            ctrl=model.predict(prep,np.zeros_like(bonus) if bonus is not None else None)
            def coords(r):
                dual=r.get('diagnostics',{}).get('dual',{})
                for key in ('track_a_tip','track_a_root','track_b_tip','track_b_root'):
                    if dual.get(key) is not None:dual[key]=[a+b for a,b in zip(dual[key],off)]
                for event in dual.get('events',[]):
                    for j in range(3):event[j]+=off[0]

                if stage=='r02':r['diagnostics']=dict(candidates=[],pairs=[])
                for cand in r['diagnostics']['candidates']:
                    tr=cand.get('trace')
                    if tr and tr['first_loss'] is not None:tr['first_loss']+=off[0]
                    if tr:
                        for key in ('waived','waived_lip'):
                            if key in tr:tr[key]=[z+off[0] for z in tr[key]]
                        for name in ('extinction_limit','geometry_cut','rebound_cut'):
                            if tr.get(name) is not None:tr[name]+=off[0]
                        for e in tr.get('events',[]):
                            for j in range(3):e[j]+=off[0]
                        rev=tr.get('reference',{})
                        for key in ('prior_cut','break_x'):
                            if rev.get(key) is not None:rev[key]+=off[0]
                        if rev.get('cut') is not None:
                            rev['cut']+=off[0]
                            rev['before_tip']=[a+b for a,b in zip(rev['before_tip'],off)]
                return globalize(r,off)
            records[stage]=dict(full=coords(res),raw_only=coords(ctrl),seconds=elapsed)
    return clean(dict(group=g,frame=f,source_sha=row['image_sha'],models=records))

def freeze():
    assert not (OUT/'freeze.json').exists()
    assert v3_sources()==read(V3/'freeze.json')['sources']
    assert read(OUT/'group_a_seal.json')['sources']==sources()
    save(OUT/'freeze.json',dict(sources=sources(),primary='v4_0',group_a=sha(OUT/'group_a.jsonl'),
                                events=sha(OUT/'weak_events.csv'),dev_scores=sha(OUT/'group_a_scores.csv'),
                                paired_probes=sha(OUT/'paired_probes.csv')))

def run(g):
    assert base_sources()==read(BASE/'freeze.json')['sources']
    assert v3_sources()==read(V3/'freeze.json')['sources']
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
        for i,record in enumerate(pool.map(run_one,((r,int(r['frame_id']) in selected) for r in rows),chunksize=2),1):
            f.write(json.dumps(record,separators=(',',':'),allow_nan=False)+'\n')
            if i%150==0:print(g,i,flush=True)
    path.with_suffix('.partial').rename(path)
    save(OUT/(g+'_seal.json'),dict(sources=sources(),frames=len(rows),predictions=sha(path)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=[*GROUPS,'freeze']);act=p.parse_args().action
    if act=='freeze':freeze()
    else:run(act)
