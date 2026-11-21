"""Designed paired references exercising the residual-slip hypotheses."""
import numpy as np
from .reference import Support
from .batch import OUT,save

def run():
    rng=np.random.default_rng(4301)
    img=np.full((220,480),160,np.uint8)
    img[:,:205]=np.clip(160+rng.normal(0,15,(220,205)),0,255)
    path=np.c_[np.arange(230,381),np.full(151,110)]
    results=[]
    for case in ('new','misregistered_scratch','identical','no_anchor'):
        current=img.copy();fixed=img.copy();current[110,230:381]=85
        if case=='misregistered_scratch':fixed[112,350:381]=85
        if case=='identical':fixed[110,230:381]=85
        if case=='no_anchor':current[:,:205]=160;fixed[:,:205]=160
        s=Support(current,fixed.astype('float32'),np.s_[:,:],(0,0),(93,110),260.,1.5,138.)
        r=s.review(path);rank=s.rank(path)
        if case=='new':assert r['source']=='COARSE' and r['cut'] is None and r['fraction']==1
        if case=='misregistered_scratch':assert r['source']=='COARSE' and abs(r['cut']-350)<=3 and r['duplicate']>.8
        if case=='identical':assert rank['tier']==-1 and r['decision']=='NO_SUPPORTED_BOUNDARY'
        if case=='no_anchor':assert r['decision']=='NO_ALIGNMENT'
        results.append(dict(case=case,coarse=s.coarse,measure=r,rank=rank))
    save(OUT/'residual_tests.json',results)
if __name__=='__main__':run()
