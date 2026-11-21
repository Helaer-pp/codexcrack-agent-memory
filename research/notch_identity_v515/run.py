"""Seal the inference code before scoring. Stage speed measurements run in isolated pools."""
from concurrent.futures import ProcessPoolExecutor
from time import perf_counter
from pathlib import Path
import json
import os
import cv2
import numpy as np
from . import batch as b
from . import probes,domain
from research.v3_labelme_comparison.compare import write_csv


def workers():
    cv2.setNumThreads(1)
    b.old.warm()
    probes.trial_stage(('active_fork',0,1.,1.,1,17),'S3')


def load(group,i):
    folder=b.OLD/'evidence'/group/str(i)
    meta=b.read(folder/'metadata.json')
    with np.load(folder/'arrays.npz') as z:
        image,aligned=z['raw'],z['fixed__aligned']
    assert b.sha(folder/'arrays.npz')==meta['arrays_sha']
    fixed=b.old.read_fixed(meta['input']['reference'],meta['input']['ref_sha'])
    return meta,image,aligned,fixed


def frame(job):
    g,i,selected,stages,locked=job
    meta=b.read(b.OLD/'evidence'/g/str(i)/'metadata.json')
    current=b.old.current(meta['input']['current'],meta['input']['image_sha'])
    fixed=b.old.read_fixed(meta['input']['reference'],meta['input']['ref_sha'])
    x,y,r,bottom=meta['evidence']['scene']['bounds']
    image=current[y:bottom,x:r]
    geo=None
    pairs=[('original',np.array(meta['current_points']),np.array(meta['fixed_points']))]
    bounds=[x,y,r,bottom]
    if g=='group_c':
        policy=b.read(b.POLICY)
        geo=b.geometry(image,[x,y],fixed,meta,policy)
        bounds=geo['box']
        pairs.append(('bright',np.array(geo['cur_points']),np.array(geo['ref_points'])))
    l,t,r,bottom=bounds
    origin=np.array([l,t])
    raw=image[t-y:bottom-y,l-x:r-x]

    fixed_roi=fixed[t:bottom,l:r]
    placements={}
    mappings={}
    sweeps=[]
    for place,cp,rp in pairs:
        start=perf_counter()
        prep=b.terminal.prepare(raw,cp.mean(0)-origin,b.SCALE,'S1',fixed_roi,rp.mean(0)-origin)
        prepared_ms=(perf_counter()-start)*1000
        maps={}
        models={}
        mappings[place]={}
        for stage in stages:
            key=bool(stage!='S1' and prep and prep[0].local.size>250000)
            if key not in maps:
                tick=perf_counter()
                compact,domain_bounds,info=domain.align_frame(current,fixed,cp,rp,bounds,prep,stage)
                maps[key]=(domain.embed(compact,domain_bounds,bounds),domain_bounds,info,perf_counter()-tick)
            aligned,domain_bounds,info,upstream=maps[key]
            mappings[place][stage]=dict(bounds=domain_bounds,windows=info['windows'],cur=cp,ref=rp)
            model,seconds=b.run_mode(raw,fixed_roi,cp,rp,origin,stage,'full',{} if selected else None,aligned,prepared=prep)
            detector=seconds+prepared_ms/1000
            models[stage]=dict(full=model,seconds=detector+upstream,detector_seconds=detector,upstream_ms=1000*upstream)
        placements[place]=models
    return b.old.clean(dict(group=g,frame=i,source_sha=meta['input']['image_sha'],box=bounds,
                            geometry=geo,placements=placements,sweeps=sweeps,mappings=mappings))


def frozen():
    data=b.read(b.OUT/'freeze.json')
    assert data['sources']==b.sources() and data['operator']==b.sha(b.POLICY)
    assert data['runner']==b.sha(Path(__file__))
    return data


def seal():
    b.OUT.mkdir(parents=True,exist_ok=True)
    if (b.OUT/'freeze.json').exists():
        frozen()
        return
    b.save(b.OUT/'freeze.json',dict(sources=b.sources(),runner=b.sha(Path(__file__)),operator=b.sha(b.POLICY)))


def jobs(g,stages,locked):
    policy=b.read(b.ROOT/'config/dataset_usage_policy.json')['groups']
    assert g in b.GROUPS and policy[g] in ('DEVELOPMENT','VALIDATION_ONLY')
    ids={int(r['frame_id']) for r in b.read_csv(b.SELECT) if r['dataset_id']==g}
    return [(g,i,i in ids,stages,locked) for i in range(1,b.GROUPS[g]+1)]


def predict(g):
    frozen()
    dst=b.OUT/(g+'.jsonl')
    with ProcessPoolExecutor(4,initializer=workers) as pool, dst.with_suffix('.partial').open('w',encoding='utf8') as out:
        for rec in pool.map(frame,jobs(g,b.ALGS,False),chunksize=2):
            out.write(json.dumps(rec,separators=(',',':'),allow_nan=False)+'\n')
            if rec['frame']%100==0:print(g,rec['frame'],flush=True)
    dst.with_suffix('.partial').replace(dst)
    b.save(b.OUT/(g+'_seal.json'),dict(predictions=b.sha(dst),frames=b.GROUPS[g],sources=b.sources()))


def bench(g,stage,n):
    frozen()
    tasks=jobs(g,(stage,),False)
    rows=[]
    with ProcessPoolExecutor(n,initializer=workers) as pool:
        # Exclude worker start and cached compiler initialization from steady-state rates.
        list(pool.map(frame,[tasks[0]]*(2*n),chunksize=1))
        start=perf_counter()
        for rec in pool.map(frame,tasks,chunksize=2):
            bundle=rec['placements']['original'][stage]
            m=bundle['full']
            d=m['diagnostics']['dual']
            clocks=d.get('timing_ms',{})
            rows.append(dict(frame=rec['frame'],seconds=bundle['seconds'],tip=m['tip'],status=m['status'],
                      detector_seconds=bundle['detector_seconds'],upstream_ms=bundle['upstream_ms'],**{'sub_'+k:v for k,v in [(key,d.get('substeps_ms',{}).get(key,0.)) for key in ('gray_ridge','registration','diff_ridge_prior','fusion_background','bridge_texture','tail_filters','seeds_and_gate')]},fields_ms=clocks.get('fields',0)-d.get('registration_ms',0),lattice_ms=clocks.get('lattice',0),field_pixels=d.get('field_pixels',0),registration_ms=d.get('registration_ms',0),normal_ms=clocks.get('normal',0)))
        wall=perf_counter()-start
    write_csv(b.OUT/f'bench_{stage}_{n}.csv',rows)
    print('BENCH',stage,n,len(rows)/sum(r['seconds'] for r in rows),flush=True)
    b.save(b.OUT/f'bench_{stage}_{n}.json',dict(n=len(rows),workers=n,wall_seconds=wall,seconds=sum(r['seconds'] for r in rows)))


if __name__=='__main__':
    import sys
    args=sys.argv[1:]
    if args[0]=='seal':seal()
    elif args[0]=='predict':predict(args[1])
    elif args[0]=='probes':frozen();probes.run()
    
    elif args[0]=='bench':bench('three_point_bend',args[1],int(args[2]))
