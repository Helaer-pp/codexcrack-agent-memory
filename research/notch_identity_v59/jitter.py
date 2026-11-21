"""Perturb the coarsely supplied points on fixed synthetic image pairs."""
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from research.notch_identity_v58_strict.jitter import SYN,synchronized
from . import batch as b,terminal
from .probes import images


def one(key):
    raw,fixed,h,s,gt=images((key,9 if key=='P1_weak_gap' else 0,0.,1.,1,17))
    points=np.array([h+[-22,-44],h+[-22,44]],float)
    rows=[]
    for _,direction,delta,cp,rp in synchronized(points,points):
        p=terminal.prepare(raw,cp.mean(0),s,reference=fixed,reference_hint=rp.mean(0))
        m=terminal.predict(p,None,fixed)
        rows.append(dict(key=key,direction=direction,delta=delta,current=cp.tolist(),reference=rp.tolist(),
                         tip=m['tip'],points=m['points'],truth=gt.tolist()))
    return rows


if __name__=='__main__':
    b.OUT.mkdir(exist_ok=True,parents=True)
    with ProcessPoolExecutor(4,initializer=b.old.warm) as pool:rows=sum(pool.map(one,(*SYN,'material_edge_glare','weak_material_bridge')),[])
    b.save(b.OUT/'synthetic_jitter.json',rows)
    b.save(b.OUT/'jitter_seal.json',dict(sources=b.sources(),predictions=b.sha(b.OUT/'synthetic_jitter.json')))
