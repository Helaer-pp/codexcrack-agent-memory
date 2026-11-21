"""Crossed exposure/scale probes and event-level identity audit on the selected trace."""
import cv2
import numpy as np
from scipy.spatial import cKDTree
from research.notch_identity_v31.probes import sample,original
from research.notch_identity_v3.check_public import check
from research.notch_identity_v31 import terminal as v31
from research.notch_identity_v31.detector import px
from research.v3_labelme_comparison.compare import write_csv
from . import terminal,reference
from .batch import OUT,save

def gap_events(p,out,stage,gt,width,z):
    if out['tip'] is None:return 0,0,0
    d=out['diagnostics'];i=d['selected']
    start=p[2][i];x,y=start;s=p[5];sig=p[3];org=p[1]
    radius=px(s,.014)
    sy=max(range(max(0,y-radius),min(len(sig),y+radius+1)),key=lambda yy:min(4.,sig[yy,x])-.35*abs(yy-y)*288/s)
    gap=px(s,.014);win=px(s,.05)
    track,_,_,_=v31.trace_windowed(sig,np.zeros_like(sig),x,sy,px(s,.07),px(s,.076),px(s,.017),gap,px(s,.35),px(s,.045),win,.8)
    arr=np.array(track)
    if stage=='v3_1':
        from .guards import inspect_track
        _,_,events=inspect_track(arr,p[7],s,x,False,False)
        events=[(a+org[0],b+org[0],c+org[0],r,k,ok) for a,b,c,r,k,ok in events]
    else:
        events=d['candidates'][i]['trace'].get('events',[])
    accepted=wrong=rejected=0
    for first,left,right,residual,ratio,ok in events:
        if first/z>=94+width or right/z<94:continue
        if not ok:
            rejected+=1;continue
        indices=(arr[:,0]+org[0]>=left)&(arr[:,0]+org[0]<=right)
        pts=arr[indices,:2]+org
        accepted+=1
        wrong+=int(np.mean(cKDTree(gt).query(pts)[0]/z<=2.5)<.8)
    return accepted,wrong,rejected

def reference_tests():
    rng=np.random.default_rng(5);raw=np.clip(145+12*rng.normal(size=(110,210)),0,255).astype('uint8')
    x=np.arange(40,150); pts=np.column_stack((x,np.full_like(x,55)))
    raw[55,x]=68
    cases=[]
    for case in ('changed_trunk_static_suffix','all_static','new_line','missing_pixels','flat_context'):
        current=raw.copy();fixed=raw.astype(np.float32)
        if case=='changed_trunk_static_suffix':fixed[55,:128]=150
        if case=='new_line':fixed[55,x]=150
        if case=='missing_pixels':fixed[:]=np.nan
        if case=='flat_context':
            current[:]=150;current[55,x]=68;fixed[:]=current
        fixed=np.roll(fixed,(2,-3),(0,1))
        result=reference.review(current,fixed,pts,288.,2.,130.)
        if case=='changed_trunk_static_suffix':
            assert result['cut'] is not None and abs(result['cut']-128)<6 and result['shift']==[-3,2],result
        else:assert result['cut'] is None,(case,result)
        cases.append(dict(case=case,**result))
    save(OUT/'reference_tests.json',cases)

def run():
    save(OUT/'public_check.json',dict(verified=check(OUT/'selftest')))
    reference_tests()
    rows=[]
    cases=[(c,0,1.) for c in original.CASES]+[('P1_weak_gap',w,v) for w in (4,9,16) for v in (0.,.2)]
    for case,width,contrast in cases:
        for zoom in (.5,1.,2.):
            for noise in (1,5):
                for seed in (17,31):
                    raw,hint,scale,gt=sample(case,zoom,noise,seed,width,contrast)
                    for photo,gain,bias in [('nominal',1.,0),('dim',.65,9),('bright',1.16,15)]:
                        gray=np.clip(raw*gain+bias,0,255).astype(np.uint8)
                        for stage in ('v3_1','v3_2'):
                            model=v31 if stage=='v3_1' else terminal
                            prep=model.prepare(gray,hint,scale,stage)
                            res=model.predict(prep,None)
                            tip=res['tip'];valid=tip is not None
                            err=float(np.linalg.norm(gt[-1]-tip)/zoom) if len(gt) and valid else None
                            dist=cKDTree(res['points']).query(gt)[0]/zoom if len(gt) and res['points'] else np.full(len(gt),np.inf)
                            coverage=float((dist<=2.5).mean()) if len(gt) else None
                            passed=valid and err<=10 and (not case.startswith('P1') or coverage==1.) if len(gt) else not valid
                            events=gap_events(prep,res,stage,gt,width,zoom) if width and photo=='nominal' else (None,)*3
                            rows.append(dict(case=case,width=width,contrast=contrast,zoom=zoom,noise=noise,seed=seed,photo=photo,
                                             stage=stage,passed=passed,negative=not len(gt),valid=valid,tip=tip,error=err,coverage=coverage,
                                             accepted=events[0],wrong=events[1],rejected=events[2]))
    write_csv(OUT/'probes.csv',rows)
if __name__=='__main__':run()

