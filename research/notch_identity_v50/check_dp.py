"""Exhaustive small-grid independent check of free endpoints, allowed births, and debt."""
import numpy as np
from .terminal import global_free_end_dp

def exhaustive(a,seed,s):
    values=np.full(a.shape,-np.inf);w,h=a.shape
    def visit(x,y,d,v):
        values[x,y]=max(values[x,y],v)
        if x+1==w:return
        for u in range(max(0,y-2),min(h,y+3)):
            step=u-y
            score=v+a[x+1,u]-.13*abs(step)-.19*abs(step-d)
            if score>=-.025*s:visit(x+1,u,step,score)
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
        path,best,v=global_free_end_dp(a,seeds,55.)
        expected=exhaustive(a,seeds,55.)
        np.testing.assert_allclose(v,expected,atol=1e-5)
        assert abs(best-max(0,expected.max()))<1e-5
        if len(path):
            assert seeds[tuple(path[0])] and np.all(np.diff(path[:,0])==1) and np.all(abs(np.diff(path[:,1]))<=2)
            assert abs(v[tuple(path[-1])]-best)<1e-5
            steps=np.diff(path[:,1],prepend=path[0,1])
            total=max(0,a[tuple(path[0])])+sum(a[tuple(pt)]-.13*abs(d)-.19*abs(d-prior) for pt,d,prior in zip(path[1:],steps[1:],steps[:-1]))
            assert abs(total-best)<1e-5
    print('24 exhaustive checks passed.')
if __name__=='__main__':main()
