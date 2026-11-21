"""Replay the identical probe grid for V3.6 and the first V4.2 ablation."""
from concurrent.futures import ProcessPoolExecutor
from itertools import product
import cv2
from . import probes,terminal
from .batch import OUT
from research.notch_identity_v36 import terminal as v36

class ProbeModel:
    def __init__(self,stage):self.stage=stage
    def prepare(self,a,h,s):
        return v36.prepare(a,h,s) if self.stage=='v3_6' else terminal.prepare(a,h,s,'no_break')
    def predict(self,p,b,f):
        m=v36.predict(p,b,f) if self.stage=='v3_6' else terminal.predict(p,b,f)
        m['diagnostics'].setdefault('dual',dict(decision=self.stage))
        return m

def initialize(stage):
    cv2.setNumThreads(1);probes.terminal=ProbeModel(stage)

def run():
    from research.v3_labelme_comparison.infer import read_csv
    rows=read_csv(OUT/'paired_probes.csv')
    jobs=[(r['case'],int(r['width']),float(r['contrast']),float(r['zoom']),int(r['noise']),int(r['seed'])) for r in rows if r['photo']=='nominal']
    for stage in ('v3_6','no_break'):
        with ProcessPoolExecutor(6,initializer=initialize,initargs=(stage,)) as pool:result=sum(pool.map(probes.trial,jobs,chunksize=2),[])
        probes.write_csv(OUT/(stage+'_probes.csv'),result)
if __name__=='__main__':run()
