"""Single/four-worker paired speeds for the labeled comparison and synthetic matrix."""
from concurrent.futures import ProcessPoolExecutor
from itertools import product
from .run import frame, jobs, workers, frozen
from . import batch as b, probes
from research.v3_labelme_comparison.compare import write_csv


def sample(job):
    group,i,sel,stages,locked=job
    rec=frame((group,i,False,stages,False))
    return [dict(group=group,frame=i,placement=pl,stage=s,seconds=bundle['seconds'])
            for pl,models in rec['placements'].items() for s,bundle in models.items()]


def simulated(job):
    rows=probes.trial(job)
    return [{k:r[k] for k in ('case','negative','stage','seconds')} for r in rows]


def main():
    frozen()
    for n in (1,4):
        synthetic=b.read_csv(b.OUT/'paired_probes.csv')
        cases=list(dict.fromkeys((r['case'],int(r['width']),float(r['contrast']),float(r['zoom']),int(r['noise']),int(r['seed'])) for r in synthetic))
        inputs=[job for g in b.GROUPS for job in jobs(g,('S1','S2','S3'),False) if job[2]]
        with ProcessPoolExecutor(n,initializer=workers) as pool:
            selected=sum(pool.map(sample,inputs,chunksize=2),[])
            data=sum(pool.map(simulated,cases,chunksize=2),[])
        write_csv(b.OUT/f'labeled_speed_{n}.csv',selected)
        write_csv(b.OUT/f'synthetic_speed_{n}.csv',data)


if __name__=='__main__':main()
