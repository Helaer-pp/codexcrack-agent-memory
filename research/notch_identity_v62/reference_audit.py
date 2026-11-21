"""Separate loss of the reference entity, band cropping and downstream preparation in MT."""
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from research.notch_identity_v59 import geometry as vertex
from research.unified_crack_tip_60q.features import CONFIG,scene_geometry
from research.notch_identity_v61.geometry import apex_with_center_fallback
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b,inputs,geometry
from .run import frozen,workers


def inspect(i):
    m=inputs.metadata('group_h',i)
    src=m['input']
    cur=b.old.current(src['current'],src['image_sha'])
    fixed=b.old.read_fixed(src['reference'],src['ref_sha'])
    p,q=map(np.asarray,(m['current_points'],m['fixed_points']))
    rows=[]
    for delta in (0,-150):
        cp,rp=p+[delta,0],q+[delta,0]
        l,t,r,bot=scene_geometry(cur,cp,fixed,rp,None,CONFIG)['bounds']
        origin=np.array([l,t])
        h,rh=cp.mean(0)-origin,rp.mean(0)-origin
        raw,ref=cur[t:bot,l:r],fixed[t:bot,l:r]
        u,v=vertex.material(raw,ref,h,rh,b.SCALE)
        band=ref[u:v];guess=rh-[0,u]
        global_tip,mode=geometry.locate_reference_notch(band,guess,b.SCALE,vertex.apex)
        old=apex_with_center_fallback(band,guess,b.SCALE,vertex.apex)
        sensor=lambda pt: None if pt is None else [int(pt[0]+l),int(pt[1]+t+u)]
        if delta==0:
            nominal_old=sensor(old)
            nominal_band=(u+t,v+t)
        assert nominal_old is not None
        sample=band[::2,::2]
        lo,hi=np.percentile(sample,(3,84))
        row=dict(frame=i,delta=delta,band_top=t+u,band_bottom=t+v,
                 old_nominal=nominal_old,old_in_band=t+u<=nominal_old[1]<t+v,
                 reference_apex=sensor(global_tip),mode=mode,global_low=lo,global_high=hi,
                 global_cut=lo+.29*(hi-lo))
        # Controlled replay: only restore the nominal vertical band, still use shifted hint.
        a,z=nominal_band
        band_pt,_=geometry.locate_reference_notch(fixed[a:z,l:r],rp.mean(0)-[l,a],b.SCALE,vertex.apex)
        row['nominal_band_replay']=[int(l+band_pt[0]),int(a+band_pt[1])] if band_pt else None
        rows.append(row)
    return rows


if __name__=='__main__':
    frozen()
    with ProcessPoolExecutor(4,initializer=workers) as pool:
        rows=[r for pair in pool.map(inspect,range(1,411),chunksize=4) for r in pair]
    write_csv(b.OUT/'group_h_reference_scan.csv',rows)
