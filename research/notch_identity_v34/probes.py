import numpy as np
from scipy.spatial import cKDTree
from research.notch_identity_v31.probes import sample,original
from research.notch_identity_v3.check_public import check
from research.notch_identity_v32.probes import gap_events
from research.notch_identity_v33 import terminal as v33
from research.v3_labelme_comparison.compare import write_csv
from . import terminal
from .reference import Support
from .batch import OUT,save

def reference_tests():
    rng=np.random.default_rng(167)
    base=np.clip(150+15*rng.normal(size=(200,360)),0,255).astype('uint8')
    pts=np.column_stack((np.arange(70,221),np.full(151,100)))
    cur=base.copy();cur[100,70:221]=65
    tests=[]
    for case in ('static_suffix','new_line','persistent','flat','missing','weak_suffix'):
        a=cur.copy();b=base.copy().astype('float32')
        if case=='static_suffix':b[100,203:221]=a[100,203:221]
        if case=='persistent':b[:]=a
        if case=='weak_suffix':a[100,203:221]=b[100,203:221]
        if case=='flat':a[:]=140;b[:]=140
        if case=='missing':b[:]=np.nan
        sup=Support(a,np.roll(b,(2,-3),(0,1)),np.s_[:,:],(0,0),(88,100),240.,2.,140.)
        rev=sup.review(pts)
        if case in ('static_suffix','weak_suffix'):
            assert rev['cut'] is not None and abs(rev['cut']-203)<=3 and rev['shift']==[-3,2],(case,rev)
        else:assert rev['cut'] is None
        shield=sup.protect(*pts.T,80)
        assert shield==(case in ('new_line','static_suffix','weak_suffix')),(case,shield)
        tests.append(dict(case=case,coarse=sup.coarse,review=rev,protect=shield,rank=sup.rank(pts)))
    save(OUT/'reference_tests.json',tests)

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
                        for stage in ('v3_3','v3_4'):
                            model=v33 if stage=='v3_3' else terminal
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
