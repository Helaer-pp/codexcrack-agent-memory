"""Regression checks for exact directional path scores and the valley boundary."""
import numpy as np
from . import terminal as t
from research.notch_identity_v40.probes import original

def main():
    # A strong mouth, a falling transition, then an independently supported distal rise.
    s=100.
    score=np.full((47,1),.8,np.float32)
    score[21:34]=-1.3
    seeds=np.ones((1,1),np.uint8)
    _,_,values,back,direction=t.lattice(score,seeds,s,True)
    tr=t.unwind(back,46,0,direction[46,0])
    info=t.extension_evidence(score,tr,s)
    assert info['valley_x']==33 and info['tail_length']==13
    assert info['positive_extension'] and abs(info['valley_gain']-13*.8)<1e-5
    assert abs(info['peak_value']-values[-1,0])<1e-4
    only_fall=t.extension_evidence(score,tr[:34],s)
    assert not only_fall['positive_extension'] and only_fall['tail_length']==0
    rising=t.extension_evidence(np.ones_like(score),tr,s)
    assert rising['valley_x']==20 and rising['tail_length']==26
    rng=np.random.default_rng(54)
    for _ in range(16):
        grid=rng.uniform(-1,1.5,(35,11)).astype('float32')
        seed=np.zeros((3,11),np.uint8);seed[:,4:7]=1
        _,_,V,B,D=t.lattice(grid,seed,s,True)
        for x,y in zip(*np.where(np.isfinite(V))):
            track=t.unwind(B,x,y,D[x,y])
            assert abs(t.increments(grid,track).sum()-V[x,y])<2e-5
    raw,h,s,_=original.scene('UNLOADED',1.,1,17)
    ref=original.scene('UNLOADED',1.,1,31)[0].astype('float32')
    old=t.previous.prepare(raw,h,s,'local_peaks')
    for fixed in (ref,None):
        old_score,old_seeds,*_=t.previous.fields(old,fixed)
        for stage in t.STAGES:
            score,seeds,*_=t.fields(t.prepare(raw,h,s,stage),fixed)
            assert np.array_equal(score,old_score) and np.array_equal(seeds,old_seeds)
    print('Passed valley and boundary cases, 16 exact directional-state grids, and clean field equality.')
if __name__=='__main__':
    main()
