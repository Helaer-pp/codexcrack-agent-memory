"""Audit committed reconnects on independent synthetic gaps at the frozen settings."""
import numpy as np
from scipy.spatial import cKDTree
from . import terminal as model
from .probes import sample
from .batch import OUT
from .detector import px
from research.v3_labelme_comparison.compare import write_csv


def run():
    rows=[]
    for width in (4,9,16):
        for factor in (0.,.2):
            for z in (.5,1.,2.):
                for noise in (1,5):
                    for seed in (17,31):
                        im,h,s,gt=sample('P1_weak_gap',z,noise,seed,width,factor)
                        p=model.prepare(im,h,s,'v3_1')
                        out=model.predict(p,np.zeros_like(p[3]) if p is not None else None)
                        detail=dict(width=width,factor=factor,zoom=z,noise=noise,seed=seed,tip=out['tip'],
                                    first_loss_x=None,accepted=0,injected_band_accepted=0,wrong_injected=0)
                        rows.append(detail)
                        if out['tip'] is None:continue
                        sl,org,starts,sig,resp,_,_,gray,noise0,_,contrast=p
                        d=out['diagnostics'];winner=d['selected'];x,y=starts[winner];r=px(s,.014)
                        sy=max(range(max(0,y-r),min(len(gray),y+r+1)),key=lambda yy:min(4.,sig[yy,x])-.35*abs(yy-y)*288/s)
                        gap=px(s,.014);win=px(s,.05)
                        pts,loss,count,stop=model.trace_windowed(sig,np.zeros_like(sig),x,sy,px(s,.07),px(s,.076),px(s,.017),gap,px(s,.35),px(s,.045),win,.8)
                        detail['first_loss_x']=(loss+org[0])/z if loss>=0 else None
                        weak=0;pending=None;events=0
                        for i,(xx,yy,v) in enumerate(pts):
                            weak=0 if v>=.8 else weak+1
                            if pending is None and weak>=gap:
                                pending=i-weak+1
                            if pending is None or i+1-pending<gap+win:continue
                            block=np.asarray(pts[i-win+1:i+1])
                            if v<1 or np.minimum(4.,block[:,2]).mean()<1.05 or np.mean(block[:,2]>=1)<.8:continue
                            events+=1
                            left=(pts[pending][0]+org[0])/z
                            end=(xx+org[0])/z
                            if left<94+width and end>=94:
                                detail['injected_band_accepted']+=1
                                coords=block[:,:2]+org
                                wrong=np.mean(cKDTree(gt).query(coords)[0]/z<=2.5)<.8
                                detail['wrong_injected']+=int(wrong)
                            pending=None;weak=0
                        assert events==count
                        detail['accepted']=events
    write_csv(OUT/'synthetic_reconnections.csv',rows)

if __name__=='__main__':run()

