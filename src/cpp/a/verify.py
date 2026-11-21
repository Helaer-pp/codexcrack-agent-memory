"""Compare the shipping C ABI against immutable seven-group path/endpoint results."""
import argparse
import ctypes as C
import hashlib
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'research/gate_adapt'))
from all_groups import inventory, api

GOLD = ROOT/'output/runs/seven_groups_gate_locked_r01'
TOL = 1e-8

def segments(det):
    lib=det.lib
    count=lib.CrackV4SegmentCount(det.handle)
    assert count>=0
    result=[]
    for index in range(count):
        n=lib.CrackV4CopySegment(det.handle,index,None,0)
        assert n>0
        p=(api.Point*n)()
        assert lib.CrackV4CopySegment(det.handle,index,p,n)==n
        result.append(np.array([(q.x,q.y) for q in p]))
    return result

def verify(group, sequence, out):
    mode, files=sequence
    expected=api.load(GOLD/group/'paths.jsonl')
    assert len(files)==len(expected) and files
    rows=[]
    det=None
    try:
        for i,((path,points,digest),e) in enumerate(zip(files,expected)):
            assert e['frame']==i+1 and e['image']==path.name and points==e['anchors']
            data=path.read_bytes()
            assert hashlib.sha256(data).hexdigest()==e['image_sha256']
            assert not digest or digest==e['image_sha256']
            gray=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_GRAYSCALE)
            if i==0:
                det=api.Baseline(gray,points,mode)
            im=api.image(gray)
            anchors=api.points(points)
            r=api.Result()
            r.struct_size=C.sizeof(r)
            then=time.perf_counter_ns()
            if i:
                rc=det.lib.CrackV4Process(det.handle,C.byref(im),anchors,C.byref(r))
            else:
                rc=det.lib.CrackV4GetBaseline(det.handle,C.byref(r))
            wall=(time.perf_counter_ns()-then)/1e6
            if rc: raise RuntimeError((group,i+1,det.lib.CrackV4LastJson(det.handle)))
            v=api.V2()
            v.struct_size=C.sizeof(v);v.api_version=2
            assert det.lib.CrackV4GetResultV2(det.handle,C.byref(v))==0
            assert (v.frame_index,v.tip_confirmed,v.complete_length_valid,v.tip_px.x,v.tip_px.y)==(
                i,r.tip_confirmed,r.length_confirmed,r.tip.x,r.tip.y)
            seg=segments(det)
            gold=[np.asarray(p) for p in e['segments']]
            topology=[len(p) for p in gold]==[len(p) for p in seg]
            path_error=max((float(np.max(np.abs(p-q))) for p,q in zip(seg,gold)),default=0.) if topology else None
            tip=[r.tip.x,r.tip.y] if r.tip_confirmed else None
            tip_error=max((abs(x-y) for x,y in zip(tip,e['tip'])),default=0.) if tip and e['tip'] else 0. if tip==e['tip'] else None
            length=r.length_px if r.length_confirmed else None
            le=abs(length-e['length_px']) if length is not None and e['length_px'] is not None else 0. if length==e['length_px'] else None
            # Check the original flat-path entry point too.
            flat=np.concatenate(seg) if seg else np.empty((0,2))
            n=det.lib.CrackV4CopyPath(det.handle,0,None,0)
            assert n==len(flat)
            if n:
                raw=(api.Point*n)()
                assert det.lib.CrackV4CopyPath(det.handle,0,raw,n)==n
                assert np.array_equal(flat,[(q.x,q.y) for q in raw])
            if not r.tip_confirmed: assert (r.tip.x,r.tip.y)==(0.,0.)
            if not r.length_confirmed: assert r.length_px==r.length_mm==0.
            ok=all(x is not None and x<=TOL for x in [tip_error,path_error,le])
            rows.append(dict(group=group,frame=i+1,image=path.name,reference=int(i==0),
                tip_confirmed=r.tip_confirmed,tip_x=r.tip.x,tip_y=r.tip.y,length_confirmed=r.length_confirmed,
                length_px=length,segments=len(seg),points=n,matched=int(ok),tip_max_abs_px=tip_error,
                path_max_abs_px=path_error,length_abs_px=le,detector_ms=r.detector_ms if i else None,
                api_ms=r.api_ms if i else None,call_wall_ms=wall,init_ms=det.init_ms.value if not i else None))
            if not ok: print('DIFF',group,i+1,tip,e['tip'],[len(p) for p in seg],[len(p) for p in gold],flush=True)
    finally:
        if det:det.close()
    api.csvout(out/(group+'.csv'),rows)
    print(group,'frames',len(rows),'mismatches',sum(not r['matched'] for r in rows),flush=True)
    return rows

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('dll',type=Path)
    parser.add_argument('dest',type=Path)
    parser.add_argument('groups',nargs='*')
    args=parser.parse_args()
    args.dest.mkdir(parents=True,exist_ok=True)
    api.BASE=args.dll.resolve();api.EXPECTED_BASE=api.sha(api.BASE)
    # Load the distribution's OpenCV before resolving dependent modules.
    runtime=C.CDLL(str(api.BASE.with_name('opencv_world440.dll')))
    lib=api.base_library()
    lib.CrackV4SegmentCount.argtypes=[C.c_void_p]
    lib.CrackV4CopySegment.argtypes=[C.c_void_p,C.c_int,C.POINTER(api.Point),C.c_int]
    sequences=inventory()
    rows=[]
    groups=args.groups or ['ct3','group_a','group_c','ct2','group_h','three_point_bend','group_x']
    for group in groups: rows.extend(verify(group,sequences[group],args.dest))
    api.csvout(args.dest/'per_frame.csv',rows)
    summary=[]
    for group in groups:
        seq=[r for r in rows if r['group']==group]
        timings=np.array([r['detector_ms'] for r in seq[1:]])
        summary.append(dict(group=group,frames=len(seq),confirmed=sum(r['tip_confirmed'] for r in seq),
            mismatches=sum(not r['matched'] for r in seq),init_ms=seq[0]['init_ms'],
            exact=sum(all(r[k]==0. for k in ['tip_max_abs_px','path_max_abs_px','length_abs_px']) for r in seq),
            max_tip_px=max((r['tip_max_abs_px'] or 0) for r in seq),max_path_px=max((r['path_max_abs_px'] or 0) for r in seq),
            mean_ms=timings.mean(),p95_ms=np.percentile(timings,95),max_ms=timings.max(),
            over_15hz=int((timings>1000/15).sum()),api_mean_ms=np.mean([r['api_ms'] for r in seq[1:]])))
    api.csvout(args.dest/'summary.csv',summary)
    api.save(args.dest/'manifest.json',dict(dll=str(api.BASE),sha256=api.EXPECTED_BASE,opencv_sha256=api.sha(api.BASE.with_name('opencv_world440.dll')),
        gold=str(GOLD),coord_tolerance_px=TOL,threads=4,groups=summary))
    if any(r['mismatches'] for r in summary):raise SystemExit(1)

if __name__=='__main__':
    main()
