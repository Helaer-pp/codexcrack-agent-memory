"""Lazily register only the part of the native grid requested by the DP."""
from time import perf_counter
from research.notch_identity_v515.domain import align_frame,embed,replay

class ReferenceMap:
    def __init__(self,current,fixed,cp,rp,box,prep,stage):
        self.inputs=(current,fixed,cp,rp)
        self.box=box
        self.prep=prep
        self.stage=stage
        self.seconds=0.
        self.pixels=0
        self.bounds=[]
        self.info=dict(windows=[])
    def __call__(self,stop):
        tick=perf_counter()
        l,t,r,b=self.box
        box=[l,t,min(r,l+stop),b]
        tile,self.bounds,self.info=align_frame(*self.inputs,box,self.prep,self.stage)
        aligned=embed(tile,self.bounds,box)
        self.pixels+=tile.size
        self.seconds+=perf_counter()-tick
        return aligned
