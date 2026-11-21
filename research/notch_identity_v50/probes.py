"""Use identical paired probes for longitudinal comparison and additional isolated controls."""
from concurrent.futures import ProcessPoolExecutor
from itertools import product
import cv2
import numpy as np
from scipy.spatial import cKDTree
from research.notch_identity_v40.probes import original,sample,stress
from research.v3_labelme_comparison.compare import write_csv
from research.v3_labelme_comparison.infer import read_csv
from . import terminal
from .batch import OUT,sha,sources,save,read

def isolated(case,z,noise,seed):
    raw,h,s,_=original.scene('UNLOADED',z,noise,seed)
    y,x=np.indices(raw.shape);u=x/z;v=y/z
    gt=np.array([(j,80+round(.04*(j-70))) for j in range(70,200)])*z
    line=np.zeros((160,310),np.uint8)
    for j in range(70,200):line[80+round(.04*(j-70)),j]=80
    ink=cv2.resize(line,(raw.shape[1],raw.shape[0]),interpolation=cv2.INTER_AREA if z<1 else cv2.INTER_LINEAR)
    a=raw.astype(float)-ink
    f=original.scene('UNLOADED',z,noise,seed+101)[0].astype(float)
    if case=='P5_isolated':
        a-=(10 if seed==17 else 25)*np.exp(-.5*((u-208)/30)**2-.5*((v-85)/23)**2)
    if case=='P6_isolated':
        for im,off in ((a,0),(f,5 if seed==17 else -7)):
            im-=60*np.exp(-.5*((v-(85-.38*(u-200)+off))/.8)**2)*np.clip((u-193)/5,0,1)*np.clip((273-u)/5,0,1)
    return np.clip(a,0,255).astype('uint8'),np.clip(f,0,255).astype('uint8'),h,s,gt

def trial(job):
    case,width,contrast,z,noise,seed=job
    if case.endswith('_isolated'):a,f,h,s,gt=isolated(case,z,noise,seed)
    elif case.startswith(('P5','P6')):a,f,h,s,gt=stress(case,z,noise,seed)
    else:
        a,h,s,gt=sample(case,z,noise,seed,width,contrast)
        f=original.scene('UNLOADED',z,noise,seed+101)[0]
    rows=[]
    for photo,g,bias in [('nominal',1.,0),('dim',.65,9),('bright',1.16,15)]:
        raw=np.clip(g*a+bias,0,255).astype('uint8')
        fixed=np.clip(g*f+bias,0,255).astype('float32')
        p=terminal.prepare(raw,h,s);m=terminal.predict(p,None,fixed);tip=m['tip'];pts=np.asarray(m['points'])
        dual=m['diagnostics']['dual'];d=m['diagnostics'];j=d.get('selected')
        tr=d['candidates'][j]['trace'] if j is not None else {}
        err=np.linalg.norm(gt[-1]-tip)/z if tip and len(gt) else None
        coverage=(cKDTree(pts).query(gt)[0]/z<=2.5).mean() if tip and len(gt) else 0
        precision=(cKDTree(gt).query(pts)[0]/z<=2.5).mean() if tip and len(gt) else 0
        passed=not tip if not len(gt) else err is not None and err<=10 and (not case.startswith('P1') or coverage==1.) and (not case.startswith('P6') or precision>=.95)
        acc=wrong=0
        if width and tip:
            # A dense DP path has no missing columns. Compare the post-gap segment with truth.
            band_end=(94+width)*z
            if pts[0,0]<=94*z and pts[-1,0]>=band_end+max(1,round(4*z)):
                post=pts[(pts[:,0]>=band_end)&(pts[:,0]<=band_end+max(1,round(8*z)))]
                acc=1;wrong=int((cKDTree(gt).query(post)[0]/z<=2.5).mean()<.8)
        rows.append(dict(case=case,width=width,contrast=contrast,zoom=z,noise=noise,seed=seed,photo=photo,negative=not len(gt),valid=bool(tip),passed=bool(passed),error=err,tip=tip,coverage=coverage,precision=precision,track=dual['decision'],stop=dual.get('stop'),accepted=acc,wrong=wrong))
    return rows

def synthetic_gate(folder):
    rows=read_csv(folder/'paired_probes.csv')
    if read(folder/'probe_seal.json')!={'sources':sources(),'csv':sha(folder/'paired_probes.csv')}:return False
    return len(rows)==720

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    cases=[(c,0,1.) for c in (*original.CASES,'P5_plastic_zone','P5_plastic_zone_negative','P6_deformed_scratch','P6_deformed_scratch_negative','P2_isolated','P5_isolated','P6_isolated')]
    cases.extend(('P1_weak_gap',w,c) for w,c in product((4,9,16),(0.,.2)))
    jobs=[(*case,z,n,seed) for case,z,n,seed in product(cases,(.5,1.,2.),(1,5),(17,31))]
    with ProcessPoolExecutor(6,initializer=warm) as pool:rows=sum(pool.map(trial,jobs,chunksize=2),[])
    write_csv(OUT/'paired_probes.csv',rows);write_csv(OUT/'weak_events.csv',[r for r in rows if r['width']])
    save(OUT/'probe_seal.json',{'sources':sources(),'csv':sha(OUT/'paired_probes.csv')})
    print('Synthetic gate:',synthetic_gate(OUT),flush=True)
def warm():cv2.setNumThreads(1)
if __name__=='__main__':run()
