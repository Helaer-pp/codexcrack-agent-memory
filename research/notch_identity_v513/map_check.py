"""Compare local reference pixels and NCC metadata before and after the S3 optimization."""
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from .run import frozen, jobs, load, workers
from . import batch as b,terminal
from .registration import registered
from research.v3_labelme_comparison.compare import write_csv


def compare(job):
    group,i,_,_,_=job
    meta,raw,aligned,fixed=load(group,i)
    x,y,r,bottom=meta['evidence']['scene']['bounds']
    bounds=[x,y,r,bottom]
    pairs=[('original',np.array(meta['current_points']),np.array(meta['fixed_points']))]
    if group=='group_c':
        geo=b.geometry(raw,[x,y],fixed,meta,b.read(b.POLICY))
        bounds=geo['box']
        pairs.append(('bright',np.array(geo['cur_points']),np.array(geo['ref_points'])))
    l,t,r,bottom=bounds
    origin=np.array([l,t])
    local=raw[t-y:bottom-y,l-x:r-x]
    mapping=aligned[t-y:bottom-y,l-x:r-x]
    rows=[]
    for label,cp,rp in pairs:
        prep=terminal.prepare(local,cp.mean(0)-origin,b.SCALE,'S2',fixed[t:bottom,l:r],rp.mean(0)-origin)
        pixels=0;equal=True;metadata=True
        if prep:
            p=prep[0]
            args=(p.sl,p.origin,p.starts,None,None,p.scale,p.front,p.local,p.noise,None,p.raw,p.span)
            a,u,first=registered(args,mapping,'S2')
            e,v,second=registered(args,mapping,'S3')
            metadata=(a==e and u==v)
            if first is not None and second is not None:
                pixels=first.size
                equal=np.array_equal(first,second,equal_nan=True)
            else:equal=first is second
        rows.append(dict(group=group,frame=i,placement=label,pixels=pixels,equal=equal,metadata=metadata))
    return rows


if __name__=='__main__':
    import sys
    frozen()
    for g in sys.argv[1:]:
        assert (b.OUT/(g+'_seal.json')).exists()
        with ProcessPoolExecutor(4,initializer=workers) as pool:
            rows=[r for batch in pool.map(compare,jobs(g,('S2','S3'),False),chunksize=2) for r in batch]
        write_csv(b.OUT/(g+'_reference_parity.csv'),rows)
        print(g,len(rows),sum(r['pixels'] for r in rows),flush=True)
