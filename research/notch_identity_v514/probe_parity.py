"""Compare every synthetic S3/S4 path and effective score field, before annotation scoring."""
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from . import batch as b,probes,terminal
from .run import frozen,workers
from research.v3_labelme_comparison.compare import write_csv


def trial(job):
    a,f,h,s,gt=probes.images(job)
    rows=[]
    for photo,g,bias in [('nominal',1.,0),('dim',.65,9),('bright',1.16,15)]:
        raw=np.clip(g*a+bias,0,255).astype('uint8')
        fixed=np.clip(g*f+bias,0,255).astype('float32')
        pair=[terminal.predict(terminal.prepare(raw,h,s,stage,reference=fixed),fixed=fixed) for stage in ('S3','S4')]
        m,n=pair
        d,e=[x['diagnostics']['dual'] for x in pair]
        rows.append(dict(case=job[0],width=job[1],contrast=job[2],zoom=job[3],noise=job[4],seed=job[5],photo=photo,
            field=d.get('field_sha')==e.get('field_sha'),path=m['points']==n['points'],status=m['status']==n['status'],tip=m['tip']==n['tip']))
    return rows


if __name__=='__main__':
    frozen()
    cases=list(dict.fromkeys((r['case'],int(r['width']),float(r['contrast']),float(r['zoom']),int(r['noise']),int(r['seed'])) for r in b.read_csv(b.OUT/'paired_probes.csv')))
    with ProcessPoolExecutor(4,initializer=workers) as pool:
        rows=[r for chunk in pool.map(trial,cases,chunksize=2) for r in chunk]
    write_csv(b.OUT/'synthetic_parity.csv',rows)
