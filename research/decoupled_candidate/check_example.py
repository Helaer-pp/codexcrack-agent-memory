"""Exercise the linked public C++ SDK on CT3, including early and disconnected tips."""
import json
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[3]
def check(exe, seq, files, mode, *, legacy=False):
    cmd=[str(Path(exe).resolve()),str(mode),'0.01']
    for row, path in zip(seq,files,strict=True):
        cmd.extend([str(path),*(str(v) for p in row['anchors'] for v in p)])
    output=subprocess.check_output(cmd,text=True).splitlines()
    assert len(output)==len(seq)
    for index,(row,text) in enumerate(zip(seq,output)):
        values=iter(map(float,text.split()))
        i,tip_ok,length_ok,x,y,length,mm,ms,count=[next(values) for _ in range(9)]
        assert i==index and bool(tip_ok)==(row['tip'] is not None) and bool(length_ok)==(row['length_px'] is not None)
        for a,b in zip((x,y),row['tip'] or (0,0)): assert abs(a-b)<=1e-8
        assert abs(length-(row['length_px'] or 0))<=1e-8
        segments=row['segments']
        assert count==(sum(len(p) for p in segments) if legacy else len(segments))
        for segment in segments:
            if not legacy: assert next(values)==len(segment)
            for point in segment:
                for expected in point: assert abs(next(values)-expected)<=1e-8
        assert next(values,None) is None

if __name__=='__main__':
    import csv
    folder_out=root/'output/runs/ct3_roi_tip_r01'
    with (folder_out/'per_frame.csv').open(encoding='utf-8-sig',newline='') as f:
        measured=[r for r in csv.DictReader(f) if r['case']=='measured']
    seq=[]
    for row,text in zip(measured,(folder_out/'paths.jsonl').read_text(encoding='utf8').splitlines(),strict=True):
        z=json.loads(text); c=z['cases']['measured']
        seq.append(dict(image=z['image'],anchors=c['anchors'],tip=c['tip'],segments=[c['path']] if c['path'] else [],
                        length_px=float(row['length_px']) if row['length_px'] else None))
    folder=Path(r'D:/datasets\1-引伸计\1-裂纹\2.裂纹扩展\白色喷漆')
    check(sys.argv[1],seq,[folder/r["image"] for r in seq],2,legacy="--legacy" in sys.argv[2:])
    print(f"Public C++ SDK: {len(seq)} CT3 frames passed")
