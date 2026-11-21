"""Known opposite translations and textureless fallback on generated native grids."""
from types import SimpleNamespace
import cv2
import numpy as np
from . import batch as b,domain


def run():
    rng=np.random.default_rng(60)
    fixed=rng.integers(60,205,(140,420),dtype=np.uint8)
    y,x=np.indices(fixed.shape)
    mid=70
    ux,uy=3,-2
    dx,dy=-4,1
    xx=x+np.where(y<mid,ux,dx);yy=y+np.where(y<mid,uy,dy)
    cur=fixed[np.clip(yy,0,139),np.clip(xx,0,419)]
    pts=np.array([[40.,35.],[40.,105.]])
    scene=SimpleNamespace(origin=(20,0),front=20,starts=[(20,mid)],scale=288.,
               local=cur,black=1.,span=200.,noise=1.)
    def check(a,f):
        mapping=domain.ReferenceMap(a,f,pts,pts,[0,0,420,140],(scene,[0,140],'S1'),'S1')
        mapping(420)
        return mapping
    m=check(cur,fixed)
    assert all((w['up'],w['down'])==([ux,uy],[dx,dy]) for w in m.info['windows'])
    flat=np.full_like(fixed,120)
    blank=check(flat,flat)
    assert all(w['up_mode']==w['down_mode']=='zero' for w in blank.info['windows'])
    fixed[mid+1:]=120
    cur[mid+1:]=120
    part=check(cur,fixed)
    assert all(w['up']==[ux,uy] and w['down_mode'] in ('single','zero') for w in part.info['windows'])
    b.save(b.OUT/'registration_check.json',dict(asymmetric=m.info,blank=blank.info,one_side=part.info))
    print('Opposite shifts recovered; flat material fell back; partial texture checked.')

if __name__=='__main__':run()
