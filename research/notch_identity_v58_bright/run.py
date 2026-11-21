"""Freeze the screenshot instruction, then run the group_c-only validation."""
import argparse,csv,json,shutil,time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from research.notch_identity_v58_strict import batch as base,terminal
from research.notch_identity_v3.run import read,save,sha,globalize
from research.v3_labelme_comparison.infer import read_csv
from research.unified_crack_tip_60q.common import clean
from . import region

ROOT,OLD,SELECT=base.ROOT,base.OLD,base.SELECT
OUT=ROOT/'output/experiments/v58_bright_group_c_r06'
SOURCE=Path(__file__).resolve()
GROUP='group_c'
N=base.GROUPS[GROUP]


def sources():
    return {**base.sources(),**{p.relative_to(ROOT).as_posix():sha(p) for p in (SOURCE,SOURCE.with_name('region.py'))}}


def configure(screenshot):
    assert base.sources()==read(base.OUT/'freeze.json')['sources']
    if (OUT/'freeze.json').exists():raise FileExistsError(OUT)
    OUT.mkdir(exist_ok=True,parents=True)
    meta=read(OLD/'evidence'/GROUP/'1/metadata.json');info=meta['input']
    fixed=base.read_fixed(info['reference'],info['ref_sha'])
    img=cv2.imdecode(np.fromfile(screenshot,np.uint8),1)
    red=(img[:,:,2].astype(float)-img[:,:,0]>65)&(img[:,:,2].astype(float)-img[:,:,1]>65)
    # Long horizontal and vertical red strokes define the rectangle, excluding the arrows.
    ys=np.flatnonzero(red.sum(1)>.35*img.shape[1]);xs=np.flatnonzero(red.sum(0)>.18*img.shape[0])
    rect=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]
    cx,cy=np.mean(meta['fixed_points'],axis=0).astype(int)
    l=max(0,cx-850);t=max(0,cy-550)
    crop=fixed[t:t+1100,l:l+2250]
    sift=cv2.SIFT_create(4500,contrastThreshold=.015)
    mask=1-cv2.dilate(red.astype('uint8'),np.ones((9,9),np.uint8))
    k,desc=sift.detectAndCompute(cv2.cvtColor(img,cv2.COLOR_BGR2GRAY),255*mask)
    q,db=sift.detectAndCompute(crop,None)
    pairs=[a for a,b in cv2.BFMatcher().knnMatch(desc,db,k=2) if a.distance<.78*b.distance]
    src=np.float32([k[a.queryIdx].pt for a in pairs]);dst=np.float32([q[a.trainIdx].pt for a in pairs])+[l,t]
    cv2.setRNGSeed(57)
    mat,ok=cv2.estimateAffinePartial2D(src,dst,ransacReprojThreshold=3.)
    assert mat is not None and ok.sum()>=12
    use=ok.ravel().astype(bool)
    errors=np.linalg.norm(src[use]@mat[:,:2].T+mat[:,2]-dst[use],axis=1)
    corners=np.array([[x,y] for y in rect[1::2] for x in rect[::2]])@mat[:,:2].T+mat[:,2]
    box=[np.ceil(corners[:,0].min()),np.ceil(corners[:,1].min()),
         np.floor(corners[:,0].max())+1,np.floor(corners[:,1].max())+1]
    box=list(map(int,box))
    band,floor=region.band(fixed,[0,0],box);assert band is not None
    pts=np.asarray(meta['fixed_points'])
    a,c=region.paired_points(fixed,fixed,[0,0],band,[floor,floor],pts,np.zeros((2,2)))
    assert a is not None
    settings=dict(reference_box=box,fixed_band=band,fixed_floor=floor,reference_virtual_points=a.tolist(),
        screen_box=rect,screenshot_sha=sha(screenshot),reference_sha=info['ref_sha'],affine=mat.tolist(),
        inliers=int(ok.sum()),matches=len(pairs),median_residual=float(np.median(errors)),sources=sources())
    shutil.copyfile(screenshot,OUT/'user_region.png')
    save(OUT/'freeze.json',settings);print('Frozen ROI',box,band,a.tolist(),flush=True)


def model(raw,fixed,hint,span,origin,pair,mode,surface):
    started=time.perf_counter()
    scene=terminal.prepare(raw,hint,span)
    m=terminal.predict(scene,None,fixed if mode=='full' else None,surface)
    sec=time.perf_counter()-started
    d=m['diagnostics']['dual']
    if 'front' in d:
        d['front']+=origin[0]
        d['roi_y']=[y+origin[1] for y in d['roi_y']]
    for branch in d['branches']:
        for key in ('root','tip','base_tip'):branch[key]=(np.asarray(branch[key])+origin).tolist()
    if d.get('peak'):d['peak']=(np.asarray(d['peak'])+origin).tolist()
    m=globalize(m,origin)
    m.update(base.lengths(m,dict(points_geometry=pair,points_observed=True)))
    if surface:surface['origin']+=origin
    return m,sec


def bounded(raw,off,fixed,meta,config,delta,mode,surface=None):
    geo=region.geometry(raw,off,fixed,meta,config,delta)
    if geo is None:
        m=terminal.predict(None)
        m.update(path_length_px=None,projected_length_px=None)
        return m,0.,None
    l,t,r,b=geo['box'];ox,oy=off
    pair=np.asarray(geo['cur_points'])
    hint=np.rint(pair.mean(0)-[l,t]).astype(int)
    m,sec=model(raw[t-oy:b-oy,l-ox:r-ox],fixed[t:b,l:r],hint,np.linalg.norm(pair[1]-pair[0]),[l,t],pair,mode,surface)
    pts=np.array(m['points'])
    if len(pts):assert np.all((pts>=[l,t])&(pts<[r,b]))
    return m,sec,geo


def perturbations(points):
    axis=points[1]-points[0];axis=axis/np.linalg.norm(axis)
    for name,unit in [('axis',axis),('normal',np.array([axis[1],-axis[0]]))]:
        for v in (-20,-10,10,20):yield name,v,np.tile(v*unit,(2,1))
    for v in (-20,20):yield 'span_pct',v,(points-points.mean(axis=0))*v/100


def one(job):
    i,selected,settings=job
    folder=OLD/'evidence'/GROUP/str(i);meta=read(folder/'metadata.json');info=meta['input']
    fixed=base.read_fixed(info['reference'],info['ref_sha'])
    assert info['ref_sha']==settings['reference_sha'] and sha(folder/'arrays.npz')==meta['arrays_sha']
    sc=meta['evidence']['scene'];l,t,r,b=sc['bounds'];off=[l,t]
    with np.load(folder/'arrays.npz') as z:raw=z['raw']
    models={'bright':{}};sweeps=[]
    for mode,field in [('full','seconds'),('raw_only','raw_seconds')]:
        surf={} if selected else None
        m,sec,geometry=bounded(raw,off,fixed,meta,settings,None,mode,surf)
        models['bright'][mode]=m;models['bright'][field]=sec
        if surf:
            dest=OUT/'surfaces';dest.mkdir(exist_ok=True)
            np.savez_compressed(dest/f'{i:04d}_{mode}.npz',**surf)
    if selected:
        models['r05_unrestricted']={}
        for mode,field in [('full','seconds'),('raw_only','raw_seconds')]:
            hint=np.rint(np.asarray(sc['root'] or sc['center'])-off).astype(int)
            m,sec=model(raw,fixed[t:b,l:r],hint,sc['scale'],off,sc['points_geometry'],mode,None)
            models['r05_unrestricted'][mode]=m;models['r05_unrestricted'][field]=sec
        pts=np.array(settings['reference_virtual_points'],float)
        for kind,v,delta in perturbations(pts):
            m,_,geo=bounded(raw,off,fixed,meta,settings,delta,'full')
            sweeps.append(dict(kind=kind,delta=v,status=m['status'],points=m['points'],tip=m['tip'],geo=geo))
    return clean(dict(group=GROUP,frame=i,source_sha=info['image_sha'],geometry=geometry,models=models,sweeps=sweeps))


def run():
    settings=read(OUT/'freeze.json')
    assert sources()==settings['sources']
    selected={int(r['frame_id']) for r in read_csv(SELECT) if r['dataset_id']==GROUP}
    assert len(selected)==20
    dest=OUT/'group_c.jsonl'
    if dest.exists():raise FileExistsError(dest)
    with dest.with_suffix('.partial').open('x',encoding='utf8') as fh,ProcessPoolExecutor(3,initializer=base.warm) as pool:
        for j,row in enumerate(pool.map(one,((i,i in selected,settings) for i in range(1,N+1)),chunksize=2),1):
            assert j==row['frame']
            fh.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n')
            if j%100==0:print('group_c',j,flush=True)
    dest.with_suffix('.partial').rename(dest)
    save(OUT/'seal.json',dict(predictions=sha(dest),freeze=sha(OUT/'freeze.json'),frames=N))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--screenshot',type=Path);args=a.parse_args()
    if args.screenshot:configure(args.screenshot)
    else:run()
