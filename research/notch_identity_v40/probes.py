"""Crossed exposure and scale stress tests; truth joins only after prediction."""
import cv2
import numpy as np
from scipy.spatial import cKDTree
from research.notch_identity_v31.probes import sample,original
from research.notch_identity_v32.probes import gap_events
from research.v3_labelme_comparison.compare import write_csv
from . import terminal
from .batch import OUT

def stress(case,z,n,seed):
    positive=not case.endswith('_negative')
    a,h,s,gt=original.scene('P2_fade' if positive else 'UNLOADED',z,n,seed)
    f=original.scene('UNLOADED',z,n,seed+101)[0]
    y,x=np.indices(a.shape);u=x/z;v=y/z
    if case.startswith('P5'):
        amp=10 if seed==17 else 25
        dark=amp*np.exp(-.5*((u-208)/30)**2-.5*((v-85)/23)**2)
        a=np.clip(a-dark,0,255).astype(np.uint8)
    else:
        displacement=5 if seed==17 else -7
        for im,off in ((a,0),(f,displacement)):
            dist=(v-(85-.38*(u-200)+off))
            ink=60*np.exp(-.5*(dist/.80)**2)*np.clip((u-193)/5,0,1)*np.clip((273-u)/5,0,1)
            im[:]=np.clip(im.astype(float)-ink,0,255)
    return a,f,h,s,gt

def run():
    OUT.mkdir(parents=True,exist_ok=True);rows=[];events=[]
    cases=[(c,0,1.) for c in (*original.CASES,'P5_plastic_zone','P5_plastic_zone_negative','P6_deformed_scratch','P6_deformed_scratch_negative')]
    cases.extend(('P1_weak_gap',w,c) for w in (4,9,16) for c in (0.,.2))
    for case,width,contrast in cases:
        for z in (.5,1.,2.):
            for noise in (1,5):
                for seed in (17,31):
                    if case.startswith(('P5','P6')):raw,fixed,h,s,gt=stress(case,z,noise,seed)
                    else:
                        raw,h,s,gt=sample(case,z,noise,seed,width,contrast)
                        fixed=original.scene('UNLOADED',z,noise,seed+101)[0]
                    for photo,g,bias in [('nominal',1.,0),('dim',.65,9),('bright',1.16,15)]:
                        a=np.clip(g*raw+bias,0,255).astype('uint8');f=np.clip(g*fixed+bias,0,255).astype('float32')
                        p=terminal.prepare(a,h,s);m=terminal.predict(p,None,f)
                        tip=m['tip'];dual=m['diagnostics']['dual'];valid=tip is not None
                        err=float(np.linalg.norm(gt[-1]-tip)/z) if valid and len(gt) else None
                        coverage=float(np.mean(cKDTree(m['points']).query(gt)[0]/z<=2.5)) if valid and len(gt) else 0.
                        precision=float(np.mean(cKDTree(gt).query(m['points'])[0]/z<=2.5)) if valid and len(gt) else 0.
                        passed=not valid if not len(gt) else err is not None and err<=10 and (not case.startswith('P1') or coverage==1.) and (not case.startswith('P6') or precision>=.95)
                        row=dict(case=case,width=width,contrast=contrast,zoom=z,noise=noise,seed=seed,photo=photo,negative=not len(gt),valid=valid,passed=passed,error=err,tip=tip,coverage=coverage,precision=precision,track=dual['decision'])
                        rows.append(row)
                        if not width:continue
                        if dual['decision']!='INCREMENT_CERTIFIED':
                            acc,wrong,rejected=gap_events(p,m,'v3_4',gt,width,z) if valid else (0,0,0)
                        else:
                            acc=wrong=0;rejected=None;pts=np.asarray(m['points'])
                            for start,left,right in dual['events']:
                                if start/z>=94+width or right/z<94:continue
                                subset=pts[(pts[:,0]>=left-.5)&(pts[:,0]<=right+.5)]
                                if len(subset):
                                    acc+=1;wrong+=int((cKDTree(gt).query(subset)[0]/z<=2.5).mean()<.8)
                        events.append(dict(**row,accepted=acc,wrong=wrong,rejected=rejected))
    assert len(rows)==612 and len(events)==216
    write_csv(OUT/'paired_probes.csv',rows);write_csv(OUT/'weak_events.csv',events)
if __name__=='__main__':run()
