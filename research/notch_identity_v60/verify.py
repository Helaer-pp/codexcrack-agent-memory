"""Check the delivered reports, frozen outputs, labels, lengths and media index."""
import json
import re
from collections import Counter
from pathlib import Path
from zipfile import ZipFile
import cv2
from . import batch as b
from .run import frozen

def main():
    frozen()
    out=b.OUT
    selection=b.read(out/'selection.json')
    stage=selection['stage']
    bench={}
    for s in b.ALGS:
        for count in (4,):
            name=f'bench_{s}_{count}'
            assert b.read(out/(name+'.json'))['n']==520
            rows=b.read_csv(out/(name+'.csv'))
            bench[s,count]={int(r['frame']):r for r in rows}
    compare={}
    for g,n in b.GROUPS.items():
        data=out/(g+'.jsonl');seal=b.read(out/(g+'_seal.json'))
        assert seal['predictions']==b.sha(data) and seal['sources']==b.sources()
        with data.open(encoding='utf8') as fp:
            for i,line in enumerate(fp,1):
                rec=json.loads(line)
                assert rec['frame']==i and rec['group']==g
                for placement,models in rec['placements'].items():
                    for s,entry in models.items():
                        m=entry['full']
                        assert (m['tip'] is None)==(not m['points'])
                        if m['tip'] is not None:assert m['tip']==m['points'][-1] and m['path_length_px']>=0
                        if g=='three_point_bend':
                            for count in (4,):
                                rr=bench[s,count][i]
                                assert m['status']==rr['status'] and m['tip']==(json.loads(rr['tip']) if rr['tip'] else None)
                        if s==stage:compare[g,placement,i]=m['path_length_px']
        assert i==n
    lengths=b.read_csv(out/'crack_lengths.csv')
    assert len(lengths)==len(compare)==2195
    for r in lengths:
        actual=compare[r['group'],r['placement'],int(r['frame'])]
        assert actual==(float(r['path_length_px']) if r['path_length_px'] else None)
    view=out/'difference_views'
    coordinates=b.read_csv(view/'coordinates.csv')
    assert len(coordinates)==1633
    videos={}
    for g,n in b.GROUPS.items():
        assert len(list((view/'frames'/g).glob('*.jpg')))==n
        assert len(list((view/'differences'/g).glob('*.png')))==n
        cap=cv2.VideoCapture(str(view/(g+'.mp4')))
        assert cap.isOpened() and int(cap.get(cv2.CAP_PROP_FRAME_COUNT))==n
        videos[g]=n
        cap.release()
    failures=b.read_csv(out/'failure_index.csv')
    for r in failures:
        pic=out/'audit_views'/f"{r['group']}_{r['placement']}_{int(r['frame']):04d}.jpg"
        assert pic.exists()
    with ZipFile(view/'failure_views.zip') as z:assert z.testzip() is None
    doc=b.ROOT/'evidence/v6_0'
    for name in ('REPORT.md','FAILURES_AUDIT.md'):
        body=(doc/name).read_text(encoding='utf8')
        assert all((doc/target).resolve().exists() for target in re.findall(r'\]\(([^)]+)\)',body))
    b.save(out/'verification.json',dict(stage=stage,frame_placements=len(compare),unique_frames=len(coordinates),
           bench_frame_comparisons=len(b.ALGS)*520,failed_frame_placements=len(failures),videos=videos,freeze_sha=b.sha(out/'freeze.json')))
    print(b.read(out/'verification.json'),flush=True)
if __name__=='__main__':main()
