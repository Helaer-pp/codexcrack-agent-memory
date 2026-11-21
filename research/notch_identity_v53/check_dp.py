"""Exhaustive small-grid independent check of free endpoints, allowed births, and debt."""
import numpy as np
from .terminal import global_free_end_dp

def exhaustive(a,seed,s,neck):
    values=np.full(a.shape,-np.inf);w,h=a.shape
    def visit(x,y,d,v):
        values[x,y]=max(values[x,y],v)
        if x+1==w:return
        for u in range(max(0,y-2),min(h,y+3)):
            step=u-y
            score=v+a[x+1,u]-.13*abs(step)-.19*abs(step-d)
            if score>=-(.105 if neck and x+1<=.24*s else .025)*s:visit(x+1,u,step,score)
    for x,y in zip(*np.nonzero(seed)):
        visit(x,y,0,max(0.,float(a[x,y])))
    return values

def main():
    rng=np.random.default_rng(101)
    for i in range(24):
        a=rng.normal(size=(6,4)).astype(np.float32)
        seeds=np.zeros((2,4),np.uint8)
        if i:seeds[rng.integers(0,2),rng.integers(0,4)]=1
        if i%2:seeds[0,-1]=1
        scale=15.+i;neck=bool(i%3)
        path,best,v=global_free_end_dp(a,seeds,scale,neck)
        expected=exhaustive(a,seeds,scale,neck)
        np.testing.assert_allclose(v,expected,atol=1e-5)
        assert abs(best-max(0,expected.max()))<1e-5
        if len(path):
            assert seeds[tuple(path[0])] and np.all(np.diff(path[:,0])==1) and np.all(abs(np.diff(path[:,1]))<=2)
            assert abs(v[tuple(path[-1])]-best)<1e-5
            steps=np.diff(path[:,1],prepend=path[0,1])
            total=max(0,a[tuple(path[0])])+sum(a[tuple(pt)]-.13*abs(d)-.19*abs(d-prior) for pt,d,prior in zip(path[1:],steps[1:],steps[:-1]))
            assert abs(total-best)<1e-5
    from .terminal import lattice,qualified_peak,band_width
    from types import SimpleNamespace
    from .batch import lengths
    score=np.full((36,7),-.9,np.float32);score[:8,3]=2.;score[17:29,3]=1.
    seed=np.zeros((1,7),np.uint8);seed[0,3]=1
    p=SimpleNamespace(scale=50.,front=0,local=np.full((7,36),160,np.uint8))
    pg,vg,values,back,direction=lattice(score,seed,50.,True)
    pd,vd,_,_=qualified_peak(p,score,values,back,direction)
    assert pd[-1,0]==28
    assert band_width(np.uint8([[0,1],[1,1],[1,0],[0,1]])).tolist()==[[0,2],[2,2],[2,0],[0,1]]
    # A large carry-over on the upper lip must not win over the lower positive local maximum.
    score=np.full((46,32),-100.,np.float32);score[:17,4]=2.;score[17:,4]=-.60
    score[:10,27]=.80;score[10:21,27]=-.2;score[21:36,27]=1.
    seeds=np.zeros((1,32),np.uint8);seeds[0,[4,27]]=1
    p=SimpleNamespace(scale=100.,front=0,local=np.full((32,46),170,np.uint8))
    _,_,v,back,direction=lattice(score,seeds,100.,True)
    assert np.unravel_index(np.argmax(v[21:]),v[21:].shape)==(0,4)
    pd,_,_,_=qualified_peak(p,score,v,back,direction)
    assert tuple(pd[-1])==(35,27)
    score[:,27]=-100.
    _,_,v,back,direction=lattice(score,seeds,100.,True)
    pd,_,_,_=qualified_peak(p,score,v,back,direction)
    assert not len(pd)
    scene=dict(points_observed=True,points_geometry=[[0,3],[0,-3]])
    val=lengths(dict(points=[[1,1],[4,5]],tip=[4,5],root=[1,1]),scene)
    assert val==dict(path_length_px=5.,projected_length_px=4.)
    assert lengths(dict(tip=None),scene)==dict(path_length_px=None,projected_length_px=None)
    print('Verified 24 exhaustive grids, distal peak, width measurement and length contracts.')
if __name__=='__main__':main()
