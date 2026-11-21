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
    from .terminal import extension_evidence,two_peaks_dp,band_width
    from .batch import lengths
    scores=np.full((12,6),-.55,np.float32);scores[:3,2]=1.0;scores[7:,3]=.40
    seeds=np.zeros((1,6),np.uint8);seeds[0,2]=1
    pg,vg,values,pd,vd=two_peaks_dp(scores,seeds,20.,True)
    assert abs(vd-values[5:].max())<1e-5
    assert tuple(pd[-1])==tuple(np.unravel_index(np.argmax(values[5:]),values[5:].shape)+np.array([5,0]))
    assert extension_evidence(scores,np.empty((0,2),int),20)['positive_extension']==False
    assert band_width(np.uint8([[0,1],[1,1],[1,0],[0,1]])).tolist()==[[0,2],[2,2],[2,0],[0,1]]
    scene=dict(points_observed=True,points_geometry=[[0,3],[0,-3]])
    val=lengths(dict(points=[[1,1],[4,5]],tip=[4,5],root=[1,1]),scene)
    assert val==dict(path_length_px=5.,projected_length_px=4.)
    assert lengths(dict(tip=None),scene)==dict(path_length_px=None,projected_length_px=None)
    print('Verified 24 exhaustive grids, distal peak, width measurement and length contracts.')
if __name__=='__main__':main()
