"""Isolate upstream geometry, matched static direction, new lines and missing support."""
import numpy as np
from .batch import OUT,save
from .reference import Support,contour
def main():
    rng=np.random.default_rng(573)
    base=np.full((220,480),160,np.uint8)
    base[:,:203]=np.clip(160+rng.normal(0,15,(220,203)),0,255)
    p=np.c_[np.arange(230,381),np.full(151,110)]
    rows=[]
    for case in ('new_line','shifted_parallel','unrelated_dot','no_anchor'):
        a=base.copy();b=base.copy()
        if case=='no_anchor':a[:]=160;b[:]=160
        a[110,230:381]=80
        if case=='shifted_parallel':b[117,350:381]=80
        if case=='unrelated_dot':b[117,370]=80
        ctx=Support(a,b.astype('float32'),np.s_[:,:],(0,0),(93,110),260.,1.5,138.,'v3_5')
        ref=ctx.review(p)
        if case=='shifted_parallel':assert ref['decision']=='TRIM_MATCHED_SHAPE' and abs(ref['cut']-350)<=7,ref
        if case in ('new_line','unrelated_dot'):assert ref['cut'] is None and ref['source']!='NONE'
        if case=='no_anchor':assert ref['source']=='NONE'
        rows.append(dict(case=case,reference=ref))
    a=np.full((180,270),200,np.uint8)
    for x in range(131):
        rad=round(3+(130-x)*.32);a[90-rad:91+rad,x]=25
    b=np.roll(a,(2,1),axis=(0,1))
    reg=contour(a,b,(124,90),230,1.5,175)
    assert reg and abs(reg['shift'][1]-2)<=1 and abs(reg['shift'][0]-1)<=2,reg
    rows.append(dict(case='contour_translation',reference=reg))
    OUT.mkdir(exist_ok=True,parents=True);save(OUT/'fixtures.json',rows)
if __name__=='__main__':main()
