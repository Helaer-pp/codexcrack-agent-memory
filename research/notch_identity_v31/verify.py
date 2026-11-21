"""Check historical baseline parity and all published file links without new inference."""
import json,re
from .batch import ALGS,GROUPS,ROOT,V3,OUT,sources,read,sha,save
from research.v3_labelme_comparison.infer import read_csv

def verify():
    assert sources()==read(OUT/'freeze.json')['sources']
    new={}
    for g,n in GROUPS.items():
        path=OUT/(g+'.jsonl')
        assert sha(path)==read(OUT/(g+'_seal.json'))['predictions']
        for i,line in enumerate(path.open(),1):
            rec=json.loads(line)
            assert rec['frame']==i and rec['group']==g
            if len(rec['models'])>1:
                assert set(rec['models'])==set(ALGS)
                new[g,i]=rec
        assert i==n
    checks=0
    for stage,run in [('s3t',V3/'s3t'),('r02',ROOT/'output/experiments/raw_notch_trace_v2_20261118_r02')]:
        for split in ('dev','locked'):
            p=run/(split+'.jsonl')
            assert sha(p)==read(run/(split+'_seal.json'))['predictions']
            for line in p.open():
                old=json.loads(line)
                record=new.get((old['group'],old['frame']))
                if record is None:continue
                assert old['source_sha']==record['source_sha']
                for mode in ('full','raw_only'):
                    if mode not in old:continue
                    for k in ('root','points','tip','status'):
                        assert old[mode][k]==record['models'][stage][mode][k],(old['group'],old['frame'],stage,mode,k)
                    checks+=1
    assert checks==220 and len(new)==60
    for md in (OUT/'REPORT.md',ROOT/'evidence/v3_1/REPORT.md'):
        for href in re.findall(r'\[[^]]*\]\(([^)]+)\)',md.read_text(encoding='utf-8-sig')):
            assert (md.parent/href).is_file(),href
    frames=read_csv(OUT/'frames.csv')
    assert len(frames)==1633 and len({(r['group'],r['frame']) for r in frames})==1633
    for r in frames:
        assert (OUT/r['image']).is_file()
        if r['manual_comparison']:assert (OUT/r['manual_comparison']).is_file()
    save(OUT/'final_check.json',dict(historical_frame_mode_matches=checks,annotated=len(new),frames=len(frames),
         metrics_sha=sha(OUT/'metrics.json'),report_sha=sha(OUT/'REPORT.md'),sources_match_freeze=True))
    print('Verified',checks,'historical frame/mode results, all frame links and reports.')

if __name__=='__main__':verify()

