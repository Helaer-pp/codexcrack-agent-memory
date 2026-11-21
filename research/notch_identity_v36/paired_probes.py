"""Full-mode synthetic replay with a separately generated, unloaded notch image."""
import numpy as np
from scipy.spatial import cKDTree
from .batch import OUT
from . import terminal
from research.notch_identity_v31.probes import sample,original
from research.v3_labelme_comparison.compare import write_csv

def run():
    OUT.mkdir(exist_ok=True,parents=True)
    rows=[]
    for case,width,residual in ([(c,0,1.) for c in original.CASES]+[('P1_weak_gap',w,v) for w in (4,9,16) for v in (0.,.2)]):
        for zoom in (.5,1.,2.):
            for noise in (1,5):
                for seed in (17,31):
                    raw,h,s,gt=sample(case,zoom,noise,seed,width,residual)
                    fixed=original.scene('UNLOADED',zoom,noise,seed+101)[0]
                    for photo,g,b in [('nominal',1.,0),('dim',.65,9),('bright',1.16,15)]:
                        a=np.clip(g*raw+b,0,255).astype('uint8')
                        ref=np.clip(g*fixed+b,0,255).astype('float32')
                        p=terminal.prepare(a,h,s)
                        bonus=None if p is None else .04*np.clip((ref[p[0]]-a[p[0]])/max(.12*p[-1],1e-6),0,1)
                        result=terminal.predict(p,bonus,ref)
                        tip=result['tip']
                        error=np.linalg.norm(gt[-1]-tip)/zoom if len(gt) and tip else None
                        coverage=np.mean(cKDTree(result['points']).query(gt)[0]<=2.5*zoom) if len(gt) and tip else 0.
                        ok=(error is not None and error<=10 and (not case.startswith('P1') or coverage==1)) if len(gt) else tip is None
                        rows.append(dict(case=case,zoom=zoom,noise=noise,seed=seed,width=width,contrast=residual,photo=photo,
                            stage='v3_6',passed=bool(ok),negative=not len(gt),valid=tip is not None,error=error,tip=tip,coverage=coverage))
    write_csv(OUT/'paired_probes.csv',rows)
if __name__=='__main__':run()
