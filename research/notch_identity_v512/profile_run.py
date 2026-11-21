"""Paired module timing with one worker, identical inputs and warmed JIT kernels."""
from contextlib import ExitStack
from time import perf_counter
from unittest.mock import patch

import cv2
import numpy as np
from research.notch_identity_v510 import batch as baseline
from research.notch_identity_v510 import terminal as previous
from research.v3_labelme_comparison.compare import write_csv
from . import batch, terminal
from .batch import OUT, OLD, SELECT, old, read, read_csv, sha, sources


def main():
    assert read(OUT/'freeze.json')['sources']==sources() and (OUT/'three_point_bend_seal.json').exists()
    g='three_point_bend'
    ids=[int(r['frame_id']) for r in read_csv(SELECT) if r['dataset_id']==g]
    old.warm();cv2.setNumThreads(1);records=[]
    for i in ids:
        folder=OLD/'evidence'/g/str(i);meta=read(folder/'metadata.json');info=meta['input']
        l,t,r,b=meta['evidence']['scene']['bounds'];pair,rpair=map(np.asarray,(meta['current_points'],meta['fixed_points']))
        with np.load(folder/'arrays.npz') as z:raw=z['raw'];aligned=z['fixed__aligned']
        fixed=old.read_fixed(info['reference'],info['ref_sha'])[t:b,l:r]
        for label,stage in [('S3','S3'),('S4','S4')]:
            def call():
                return batch.run_mode(raw,fixed,pair,rpair,np.array([l,t]),stage,'full',aligned=aligned)
            if i==ids[0]:call()
            hooks=[(terminal,'prepare','prepare'),(terminal.base,'lattice','lattice'),(terminal,'downstream_peak','peaks'),
                   (terminal.fields,'make','fields'),(terminal.fields,'registered','registration'),
                   (terminal.rules,'normal','normal'),(terminal.rules,'extend','bridge')]
            times={k:0. for k in ('prepare','registration','fields','normal','lattice','peaks','bridge')};stack=[]
            def timed(fn,key):
                def invoke(*a,**kw):
                    start=perf_counter();stack.append(0.)
                    try:return fn(*a,**kw)
                    finally:
                        dt=perf_counter()-start;times[key]+=dt-stack.pop()
                        if stack:stack[-1]+=dt
                return invoke
            with ExitStack() as ctx:
                for mod,attr,key in hooks:ctx.enter_context(patch.object(mod,attr,timed(getattr(mod,attr),key)))
                pred,total=call()
            times['other']=total-sum(times.values());times['total']=total
            records.append(dict(frame=i,model=label,tip=pred['tip'],**{k:1000*v for k,v in times.items()}))
    write_csv(OUT/'paired_tpb_profile_ms.csv',records)


if __name__=='__main__':main()
