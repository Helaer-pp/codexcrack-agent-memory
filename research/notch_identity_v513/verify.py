"""Check released artifacts against the frozen sequence and evaluation denominators."""
import json
from zipfile import ZipFile
from .report import DOC, DATA, STAGES
from .run import frozen
from .batch import OUT,read,read_csv,sha,GROUPS,save


def main():
    frozen()
    checks={}
    for g,n in GROUPS.items():
        records=read_csv(OUT/(g+'_scores.csv'))
        assert len(records)==60*(2 if g=='group_c' else 1)
        for group,pl,name in DATA:
            if group==g:
                assert all(sum(r['state']=='VISIBLE' and r['placement']==pl and r['stage']==s for r in records)=={'group_a':19,'three_point_bend':15,'group_c':20}[g] for s in STAGES)
        p=OUT/(g+'.jsonl')
        assert sha(p)==read(OUT/(g+'_seal.json'))['predictions']
        with p.open() as stream:
            for i,rec in enumerate(map(json.loads,stream),1):
                assert rec['frame']==i
                for place,models in rec['placements'].items():
                    assert set(models)==set(STAGES)
                    for m in (item['full'] for item in models.values()):
                        assert m['points'][-1:]==([m['tip']] if m['tip'] else [])
        assert i==n
        for f in ['jitter','native_jitter']:
            r=read_csv(OUT/(g+'_'+f+'.csv'))
            assert len([x for x in r if float(x['delta'])!=0])==3*20*10
        view=read(OUT/'difference_views'/(g+'_views.json'))
        assert len(view['rows'])==n and view['sha']==sha(p)
        checks[g]=dict(frames=n,score_rows=len(records),placements=2 if g=='group_c' else 1)
    syn=read_csv(OUT/'paired_probes.csv')
    assert len(syn)==4212
    assert all(sum(r['stage']==s and r['negative']=='True' for r in syn)==468 for s in STAGES)
    for s in STAGES:
        for n in [1,4]:
            assert len(read_csv(OUT/f'bench_{s}_{n}.csv'))==520
    for n in [1,4]:
        assert len(read_csv(OUT/f'synthetic_speed_{n}.csv'))==len(syn)
    assert len(read_csv(OUT/'crack_lengths.csv'))==2195
    with ZipFile(OUT/'difference_views/failure_views.zip') as z:assert z.testzip() is None
    assert (OUT/'difference_views/index.html').is_file()
    save(OUT/'delivery_check.json',dict(groups=checks,synthetic=len(syn),length_rows=2195,
        reports={f:sha(DOC/f) for f in ('REPORT.md','FAILURES_AUDIT.md')}))
    print(checks)


if __name__=='__main__':main()
