"""Run the same detector for all experiments, sealing predictions before scoring."""
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from research.notch_identity_v58_strict import batch as old
from research.notch_identity_v58_material.region import geometry
from research.notch_identity_v58_strict.jitter import synchronized
from research.notch_identity_v58_bright.evaluate import patch_min
from research.v3_labelme_comparison.infer import read_csv
from . import terminal
from .registration import material_reference

ROOT,OLD,SELECT,GROUPS=old.ROOT,old.OLD,old.SELECT,old.GROUPS
OUT=ROOT/'output/experiments/v511_diff_unblock_r02'
sha,save,read=old.sha,old.save,old.read
POLICY=ROOT/'output/experiments/v58_material_group_c_r07/freeze.json'
BASELINE=ROOT/'output/experiments/v58_valley_bridge_20261120_r04'
SCALE=288.
ALGS=terminal.STAGES


def sources():
    here=Path(__file__).parent
    from research.notch_identity_v510.batch import sources as baseline_sources
    deps=[here/n for n in ('terminal.py','rules.py','fields.py','registration.py','batch.py','probes.py','jitter.py','native.py')]
    deps.extend([here.parent/'unified_crack_tip_60q/features.py',here.parent/'notch_identity_v59/terminal.py',here.parent/'notch_identity_v59/geometry.py',here.parent/'notch_identity_v59/probes.py',here.parent/'notch_identity_v58/terminal.py',here.parent/'notch_identity_v58_material/region.py',here.parent/'notch_identity_v58_bright/region.py',
                 here.parent/'notch_identity_v58_bright/evaluate.py'])
    return {**baseline_sources(),**{str(p.relative_to(ROOT)):sha(p) for p in deps}}


def run_mode(image,fixed,pair,rpair,origin,stage,mode,surf=None,aligned=None,locked_warp=False):
    start=time.perf_counter()
    prep=terminal.prepare(image,pair.mean(0)-origin,SCALE,stage,fixed,rpair.mean(0)-origin)
    if mode=='full' and aligned is None:raise ValueError('Pre-aligned reference required')
    warp=None
    if stage=='S4' and mode=='full' and prep is not None and not locked_warp:
        notch_y=prep[0].origin[1]+np.median(np.array(prep[0].starts)[:,1])
        aligned,warp=material_reference(fixed,pair,rpair,notch_y,SCALE)
    result=terminal.predict(prep,None,aligned if mode=='full' else None,surf)
    elapsed=time.perf_counter()-start
    d=result['diagnostics']['dual']
    if warp:d['sensor_warp']=warp
    if 'front' in d:
        d['front']+=origin[0]
        d['roi_y']=(np.asarray(d['roi_y'])+origin[1]).tolist()
        d['material_band']=(np.asarray(d['material_band'])+origin[1]).tolist()
    for branch in d['branches']:
        for key in ('root','tip','base_tip'):branch[key]=(np.asarray(branch[key])+origin).tolist()
    if d.get('peak'):d['peak']=(np.asarray(d['peak'])+origin).tolist()
    result=old.globalize(result,origin)
    result.update(old.lengths(result,dict(points_geometry=pair,points_observed=True)))
    if surf:surf['origin']+=origin
    return result,elapsed


def trial(job):
    g,i,selected,settings=job
    folder=OLD/'evidence'/g/str(i);meta=read(folder/'metadata.json');info=meta['input']
    assert sha(folder/'arrays.npz')==meta['arrays_sha']
    with np.load(folder/'arrays.npz') as z:current=z['raw'];aligned=z['fixed__aligned']
    ref=old.read_fixed(info['reference'],info['ref_sha'])
    bounds=meta['evidence']['scene']['bounds'];ox,oy=bounds[:2]
    original=np.array(meta['current_points']);reference=np.array(meta['fixed_points'])
    geo=None;geom_seconds=0.
    if settings is not None:
        started=time.perf_counter()
        geo=geometry(current,[ox,oy],ref,meta,settings)
        geom_seconds=time.perf_counter()-started
        if geo is None:raise ValueError('No valid material measurement points')
        bounds=geo['box']
    l,t,r,b=bounds;origin=np.array([l,t])
    raw=current[t-oy:b-oy,l-ox:r-ox];fixed=ref[t:b,l:r]
    pairings=[('original',original,reference)]
    if geo:
        pairings.append(('bright',np.array(geo['cur_points']),np.array(geo['ref_points'])))
    results={};sweeps=[]
    for placement,pair,rpair in pairings:
        rec={}
        for stage in ALGS if selected else ('S4',):
            item={}
            for mode,field in [('full','seconds'),('raw_only','raw_seconds')]:
                surf={} if selected and stage=='S4' else None
                m,sec=run_mode(raw,fixed,pair,rpair,origin,stage,mode,surf,
                    aligned[t-oy:b-oy,l-ox:r-ox])
                item[mode]=m;item[field]=sec+geom_seconds
                if surf is not None:
                    folder=OUT/'surfaces'/g/placement;folder.mkdir(exist_ok=True,parents=True)
                    surf.setdefault('origin',origin);surf.setdefault('branch_ids',np.empty(0,int));surf.setdefault('curves',np.empty(0))
                    np.savez_compressed(folder/f'{i:04d}_{mode}.npz',**surf)
            rec[stage]=item
        results[placement]=rec
        if selected and (not geo or placement=='bright'):
            wd=rec['S4']['full']['diagnostics']['dual'].get('sensor_warp')
            locked=material_reference(fixed,pair,rpair,wd['center_y'],SCALE)[0] if wd else aligned[t-oy:b-oy,l-ox:r-ox]
            for _,direction,delta,cp,rp in synchronized(pair,rpair):
                if not delta:continue
                requested=rp.copy()
                if geo:
                    alt=geometry(current,[ox,oy],ref,meta,settings,rp-np.asarray(settings['reference_virtual_points']))
                    cp,rp=np.array(alt['cur_points']),np.array(alt['ref_points'])
                    for im,offset,pts,threshold in [(ref,[0,0],rp,alt['floors'][0]),(current,[ox,oy],cp,alt['floors'][1])]:
                        assert all(patch_min(im,offset,p)>=threshold for p in pts)
                alt,_=run_mode(raw,fixed,cp,rp,origin,'S4','full',aligned=locked,locked_warp=True)
                sweeps.append(dict(placement=placement,direction=direction,delta=delta,requested=requested,actual=rp,current=cp,
                    status=alt['status'],tip=alt['tip'],points=alt['points']))
    return old.clean(dict(group=g,frame=i,source_sha=info['image_sha'],box=bounds,geometry=geo,placements=results,sweeps=sweeps))


def run(g):
    OUT.mkdir(parents=True,exist_ok=True)
    assert g in GROUPS and read(ROOT/'config/dataset_usage_policy.json')['groups'][g] in ('DEVELOPMENT','VALIDATION_ONLY')
    if g!='group_a':
        assert read(OUT/'freeze.json')['sources']==sources()
        if g=='group_c':assert (OUT/'three_point_bend_seal.json').exists()
    settings=read(POLICY) if g=='group_c' else None
    if settings:assert sha(POLICY)==read(OUT/'freeze.json')['operator_config']
    selected={int(r['frame_id']) for r in read_csv(SELECT) if r['dataset_id']==g}
    dst=OUT/(g+'.jsonl');assert not dst.exists()
    start=time.perf_counter()
    with dst.with_suffix('.partial').open('w',encoding='utf8') as f,ProcessPoolExecutor(4,initializer=old.warm) as pool:
        for i,rec in enumerate(pool.map(trial,((g,i,i in selected,settings) for i in range(1,GROUPS[g]+1)),chunksize=2),1):
            assert rec['frame']==i
            f.write(json.dumps(rec,separators=(',',':'),allow_nan=False)+'\n')
            if i%100==0:print(g,i,flush=True)
    dst.with_suffix('.partial').rename(dst)
    save(OUT/(g+'_seal.json'),dict(sources=sources(),frames=i,predictions=sha(dst),seconds=time.perf_counter()-start))


def freeze():
    manifest=sources()
    assert read(OUT/'group_a_seal.json')['sources']==manifest
    assert read(OUT/'probe_seal.json')['sources']==manifest
    assert read(OUT/'jitter_seal.json')['sources']==manifest
    assert not (OUT/'freeze.json').exists()
    save(OUT/'freeze.json',dict(sources=manifest,operator_config=sha(POLICY),group_a=sha(OUT/'group_a.jsonl'),
         probes=sha(OUT/'paired_probes.csv'),jitter=sha(OUT/'synthetic_jitter.json'),group_a_scoring=sha(OUT/'group_a_scores.csv')))


if __name__=='__main__':
    import sys
    action=sys.argv[1]
    if action=='freeze':freeze()
    elif action in GROUPS:run(action)
    else:raise ValueError(action)
