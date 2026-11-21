"""Deterministic synthetic weak bands, photometric perturbations and identity checks."""
import csv,time
import cv2
import numpy as np
from scipy.spatial import cKDTree
from .batch import OUT,save
from . import terminal
from research.notch_identity_v3 import terminal as v3,probes as original
from research.notch_identity_v3.check_public import check
from research.raw_notch_trace_v2b import detector as r02
from research.v3_labelme_comparison.compare import write_csv

def sample(case,z,noise,seed,width=0,factor=1.):
    img,hint,scale,gt=original.scene('P1_lower' if width else case,z,noise,seed)
    if width:
        # Fade only the lower lip. Preserve random noise and the upper distractor.
        y,x=np.indices(img.shape)
        center=(80+8*np.maximum(0,1-(x/z-70)/72))*z
        mask=(x>=94*z)&(x<(94+width)*z)&(np.abs(y-center)<=max(1,2*z))
        bg=172+np.random.default_rng(seed+7).normal(0,noise,img.shape)
        img[mask]=np.clip(bg[mask]+factor*(img[mask]-bg[mask]),0,255).astype('uint8')
    return img,hint,scale,gt

def run():
    save(OUT/'public_check.json',dict(verified=check(OUT/'selftest')))
    cases=[(c,0,1.) for c in original.CASES]+[('P1_weak_gap',w,f) for w in (4,9,16) for f in (0.,.20)]
    rows=[]
    for case,width,factor in cases:
        for zoom in (.5,1.,2.):
            for noise in (1,5):
                for seed in (17,31):
                    img,h,s,gt=sample(case,zoom,noise,seed,width,factor)
                    for photo,gain,bias in [('nominal',1.,0),('dim',.65,9),('bright',1.16,15)]:
                        gray=np.clip(img*gain+bias,0,255).astype(np.uint8)
                        for stage in (('r02','s3t',*terminal.STAGES) if photo=='nominal' else ('s3t','v3_1')):
                            model=r02 if stage=='r02' else v3 if stage=='s3t' else terminal
                            start=time.perf_counter()
                            p=model.prepare(gray,h,s) if stage=='r02' else model.prepare(gray,h,s,stage)
                            out=model.predict(p,np.zeros_like(p[3]) if p is not None else None)
                            elapsed=time.perf_counter()-start
                            valid=out['tip'] is not None
                            err=float(np.linalg.norm(gt[-1]-out['tip'])/zoom) if len(gt) and valid else None
                            ds=cKDTree(out['points']).query(gt)[0]/zoom if len(gt) and out['points'] else np.full(len(gt),np.inf)
                            coverage=float(np.mean(ds<=2.5)) if len(gt) else None
                            passed=valid and err<=10 and (not case.startswith('P1') or coverage==1.) if len(gt) else not valid
                            tip=out['tip']
                            # Geometry check in the first recovery window before the lips coalesce.
                            resumed=None;wrong=None;first=None;trace_loss=None
                            if width:
                                pts=np.array(out['points']).reshape(-1,2)
                                gap_end=(94+width)*zoom
                                after=pts[(pts[:,0]>=gap_end)&(pts[:,0]<gap_end+.05*s)]
                                resumed=len(after)>=.5*.05*s
                                wrong=bool(resumed and np.mean(cKDTree(gt).query(after)[0]/zoom<=2.5)<.8)
                                if np.any(ds>2.5):first=float(gt[np.flatnonzero(ds>2.5)[0],0]/zoom)
                                d=out.get('diagnostics',{});i=d.get('selected')
                                if i is not None:trace_loss=d['candidates'][i].get('trace',{}).get('first_loss')
                            rows.append(dict(case=case,width=width,factor=factor,zoom=zoom,noise=noise,seed=seed,photo=photo,
                                stage=stage,passed=bool(passed),negative=not len(gt),valid=valid,error=err,coverage=coverage,tip=tip,
                                postgap_observed=resumed,wrong_postgap=wrong,first_path_miss_x=first,first_signal_loss_x=trace_loss,
                                status=out['status'],seconds=elapsed))
    write_csv(OUT/'probes.csv',rows)
if __name__=='__main__':run()

