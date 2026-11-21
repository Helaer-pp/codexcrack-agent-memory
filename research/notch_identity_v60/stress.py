"""Time paired anchor displacements from original pixels; score only after sealing outputs."""
from time import perf_counter
import json
import math
import numpy as np
import cv2
from research.unified_crack_tip_60q.features import CONFIG, scene_geometry
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b,domain
from .run import frozen,workers


def run_group(group):
    frozen()
    assert (b.OUT/(group+'_seal.json')).exists()
    assert b.read(b.ROOT/'config/dataset_usage_policy.json')['groups'][group] in ('DEVELOPMENT','VALIDATION_ONLY')
    ids=sorted(int(r['frame_id']) for r in b.read_csv(b.SELECT) if r['dataset_id']==group)
    policy=b.read(b.POLICY) if group=='group_c' else None
    rows=[]
    for ix,i in enumerate(ids):
        meta=b.read(b.OLD/'evidence'/group/str(i)/'metadata.json')
        info=meta['input']
        current=b.old.current(info['current'],info['image_sha'])
        fixed=b.old.read_fixed(info['reference'],info['ref_sha'])
        cp,rp=map(np.asarray,(meta['current_points'],meta['fixed_points']))
        l,t,r,bt=meta['evidence']['scene']['bounds']
        small=current[t:bt,l:r]
        if policy:
            geo=b.geometry(small,[l,t],fixed,meta,policy)
            cp,rp=np.array(geo['cur_points']),np.array(geo['ref_points'])
        cases=[('left',d,cp+[d,0],rp+[d,0]) for d in (0,-50,-100,-150)]
        if group=='three_point_bend' and i in (84,248):
            cases.extend((key,d,ac,ar) for _,key,d,ac,ar in b.synchronized(cp,rp) if d!=0)
        # Rotate order per frame and repetition to distribute cache/warm-up effects.
        nominal={}
        for repeat in range(3 if ix in (len(ids)//4,len(ids)//2,3*len(ids)//4) else 1):
            offset=(ix+repeat)%len(cases)
            for direction,delta,ac,ar in cases[offset:]+cases[:offset]:
                requested=ar.copy()
                start=perf_counter()
                if policy:
                    alt=b.geometry(small,[l,t],fixed,meta,policy,ar-np.array(policy['reference_virtual_points']))
                    ac,ar=np.array(alt['cur_points']),np.array(alt['ref_points'])
                    box=alt['box']
                    assert all(b.patch_min(im,off,pt)>=floor for im,off,pair,floor in
                        [(fixed,[0,0],ar,alt['floors'][0]),(small,[l,t],ac,alt['floors'][1])] for pt in pair)
                else:box=scene_geometry(current,ac,fixed,ar,None,CONFIG)['bounds']
                x,y,right,bottom=box
                origin=np.array([x,y]);raw=current[y:bottom,x:right];ref=fixed[y:bottom,x:right]
                geometry_seconds=perf_counter()-start
                for stage in b.ALGS:
                    tick=perf_counter()
                    prep=b.terminal.prepare(raw,ac.mean(0)-origin,b.SCALE,stage,ref,ar.mean(0)-origin)
                    locate=geometry_seconds+perf_counter()-tick
                    mapped=domain.ReferenceMap(current,fixed,ac,ar,box,prep,stage)
                    pred,dt=b.run_mode(raw,ref,ac,ar,origin,stage,'full',aligned=mapped,prepared=prep)
                    common=locate
                    domain_box=mapped.bounds
                    registration=mapped.info
                    rows.append(dict(group=group,frame=i,placement='bright' if policy else 'original',stage=stage,
                        repeat=repeat,direction=direction,delta=delta,requested=requested.tolist(),
                        actual=ar.tolist(),actual_current=ac.tolist(),actual_dx=(ar-rp)[:,0].mean(),exact_request=bool(np.max(np.abs(requested-ar))<.01),
                        correction=float(np.max(np.linalg.norm(requested-ar,axis=1))),raw_pixels=raw.size,
                        raw_box=[int(v) for v in box],map_box=domain_box,map_pixels=mapped.pixels,field_pixels=pred['diagnostics']['dual'].get('field_pixels',0),
                        front=(int(prep[0].origin[0]+prep[0].front+x) if prep else None),
                        windows=len(registration['windows']),seconds=common+dt,
                        detector_ms=1000*(dt-mapped.seconds),tip=pred['tip'],status=pred['status']))
                    if direction=='left' and delta==0:nominal[stage]=(pred['tip'],pred['status'])
        for row in reversed(rows):
            if row['frame']!=i:break
            tip,status=nominal[row['stage']]
            row['drift']=math.dist(tip,row['tip']) if tip and row['tip'] else None
            row['status_change']=row['status']!=status
    dst=b.OUT/(group+'_stress.csv')
    write_csv(dst,rows)
    print(group,'stress',len(rows),flush=True)


if __name__=='__main__':
    import sys
    workers()
    for g in sys.argv[1:] or b.GROUPS:run_group(g)
