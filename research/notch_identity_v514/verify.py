"""Verify sealed inference, per-frame views, timing runs and published file links."""
import csv
import json
import re
from zipfile import ZipFile
from pathlib import Path
from . import batch as b
from .run import frozen
from .report import DOC


def main():
    frozen()
    out=b.OUT; info={}
    synth=b.read_csv(out/'paired_probes.csv')
    assert len(synth)==5616
    for s in b.ALGS:
        assert sum(r['stage']==s and r['negative']=='True' for r in synth)==468
    for g,n in b.GROUPS.items():
        src=out/(g+'.jsonl');seal=b.read(out/(g+'_seal.json'))
        assert seal['predictions']==b.sha(src)
        vals=b.read_csv(out/(g+'_scores.csv'))
        places=('original','bright') if g=='group_c' else ('original',)
        for pl in places:
            for st in b.ALGS:
                rs=[r for r in vals if r['placement']==pl and r['stage']==st]
                assert len(rs)==20 and sum(r['state']=='VISIBLE' for r in rs)=={'group_a':19,'three_point_bend':15,'group_c':20}[g]
        with src.open() as stream:
            for i,rec in enumerate(map(json.loads,stream),1):
                assert rec['frame']==i
                for pl,models in rec['placements'].items():
                    assert set(models)==set(b.ALGS)
                    for m in (v['full'] for v in models.values()):
                        assert m['points'][-1:]==([m['tip']] if m['tip'] else [])
                    bounds=rec['mappings'][pl]['bounds']
                    if bounds:assert bounds[0]>=rec['box'][0]
        assert i==n
        views=b.read(out/'difference_views'/(g+'_views.json'))
        assert len(views['rows'])==n and views['sha']==b.sha(src)
        pressure=b.read_csv(out/(g+'_stress.csv'))
        for st in b.ALGS:
            for dx in ('0','-50','-100','-150'):
                assert len({r['frame'] for r in pressure if r['stage']==st and r['direction']=='left' and r['delta']==dx})==20
        info[g]=dict(images=n,placements=len(places),score_rows=len(vals),pressure_rows=len(pressure))
    for st in b.ALGS:
        for n in (1,4):assert len(b.read_csv(out/f'bench_{st}_{n}.csv'))==520
    assert len(b.read_csv(out/'synthetic_parity.csv'))==1404 and len(b.read_csv(out/'crack_lengths.csv'))==2195
    with ZipFile(out/'difference_views/failure_views.zip') as z:assert z.testzip() is None
    for path in (DOC/'REPORT.md',DOC/'FAILURES_AUDIT.md'):
        s=path.read_text(encoding='utf8')
        for t in re.findall(r'\[[^\]]+\]\(([^)]+)\)',s):assert (DOC/t).is_file(),t
    assert (out/'difference_views/index.html').exists()
    import sys,platform,cv2,numpy as np
    environment=dict(python=sys.version.split()[0],opencv=cv2.__version__,numpy=np.__version__,platform=platform.platform())
    evaluators={p.name:b.sha(p) for p in Path(__file__).parent.glob('*.py')}
    b.save(out/'delivery_check.json',dict(groups=info,synthetic=len(synth),environment=environment,source_hashes=evaluators,
        reports={p.name:b.sha(p) for p in DOC.glob('*.md')},release_dll=b.sha(b.ROOT/'output/releases/V5_12_CrackV4_minimal/CrackV4.dll')))
    print(info)

if __name__=='__main__':main()
