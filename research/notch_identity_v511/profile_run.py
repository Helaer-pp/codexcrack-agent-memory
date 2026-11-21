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
        for label,runner,core,stage in [('V5.10',baseline,previous,'v5_10'),('S4',batch,terminal,'S4')]:
            def call():
                return runner.run_mode(raw,fixed,pair,rpair,np.array([l,t]),stage,'full',aligned=aligned)
            if i==ids[0]:call()
            hooks=[(core,'prepare','prepare'),(core.base,'lattice','lattice'),(core,'downstream_peak','peaks')]
            if label=='S4':hooks.extend([(runner,'material_reference','upstream'),(core.fields,'make','fields'),
                (core.rules,'normal','normal'),(core.rules,'extend','bridge')])
            else:hooks.extend([(core.base,'fields','fields'),(core.prior,'normal_evidence','normal'),(core,'middle_bridge','bridge')])
            times={k:0. for k in ('prepare','upstream','fields','normal','lattice','peaks','bridge')};stack=[]
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
