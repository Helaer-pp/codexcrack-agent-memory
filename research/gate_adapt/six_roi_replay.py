"""Independent, time-ordered streams using the shipping DLL and locked inputs."""
import argparse
import ctypes as C
import hashlib
import json
import itertools
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np
from all_groups import ROOT, api, inventory
from ct3_roi_replay import CASES, contains

RUN_ID=os.environ.get('CRACK_SIX_ROI_RUN','six_roi_anchor_replay_r01')
if Path(RUN_ID).name!=RUN_ID or not RUN_ID:raise ValueError('CRACK_SIX_ROI_RUN')
OUT=ROOT/'output/runs'/RUN_ID
PROXY=ROOT/'output/runs/seven_groups_gate_locked_r01'
DLL=Path(os.environ.get('CRACK_SIX_ROI_DLL',ROOT/'output/releases/A_Win64_OpenCV440/bin/CrackV4.dll')).resolve()
HASH=api.sha(DLL)
NAMES={'group_a':'开发组A','group_c':'验证组C','ct2':'CT2','group_h':'开发组H MT','three_point_bend':'三点弯','ct3':'CT3 白色喷漆','group_x':'排除组X白板（历史回放）'}
DISPLAY=['原实测点','右移 5 px','右移 10 px','右移 20 px','左移 10 px','上移 10 px','间距 × 0.75','间距 × 1.35']

def setup():
    api.BASE=DLL
    api.EXPECTED_BASE=HASH
    runtime=C.CDLL(str(api.BASE.with_name('opencv_world440.dll')))
    lib=api.base_library()
    lib.CrackV4LastDebugJson.argtypes=[C.c_void_p];lib.CrackV4LastDebugJson.restype=C.c_char_p
    lib.CrackV4SegmentCount.argtypes=[C.c_void_p]
    lib.CrackV4CopySegment.argtypes=[C.c_void_p,C.c_int,C.POINTER(api.Point),C.c_int]
    return lib,runtime

def run_case(lib,det,name,perturb,i,gray,points,mode):
    dx,dy,scale=perturb
    # Initialize every stream from the same valid reference coordinate system;
    # vary only current-frame tracking points.
    pp=points if i==0 or name=='measured' else points.mean(0)+(points-points.mean(0))*scale+[dx,dy]
    if i==0:det[name]=api.Baseline(gray,pp,mode=mode)
    h=det[name].handle
    r=api.Result();r.struct_size=C.sizeof(r)
    code=lib.CrackV4Process(h,C.byref(api.image(gray)),api.points(pp),C.byref(r)) if i else lib.CrackV4GetBaseline(h,C.byref(r))
    if code:raise RuntimeError((i,name,lib.CrackV4LastJson(h)))
    debug=json.loads(lib.CrackV4LastDebugJson(h))
    roi=debug['tip_roi_xywh']
    tip=[r.tip.x,r.tip.y] if r.tip_confirmed else None
    tip_in_roi=contains(roi,tip) if tip else None
    n=lib.CrackV4SegmentCount(h);assert n>=0
    segments=[]
    for j in range(n):
        k=lib.CrackV4CopySegment(h,j,None,0);assert k>0
        pts=(api.Point*k)();assert lib.CrackV4CopySegment(h,j,pts,k)==k
        segments.append([[p.x,p.y] for p in pts])
    assert bool(segments)==bool(tip)
    return dict(tip=tip,tip_in_roi=tip_in_roi,segments=segments,roi=roi,anchors=pp.tolist(),
                tip_measure_reason=debug.get('tip_measure_reason'),
                status=debug.get('result',{}).get('status'))

def run(group,workers=8):
    folder=OUT/group;folder.mkdir(parents=True,exist_ok=True)
    dest=folder/'records.jsonl'
    if dest.exists(): raise FileExistsError(dest)
    lib,runtime=setup()
    mode,ds=inventory()[group]
    layout=dict(CASES)
    # group_h has 1406 rows; 1.35 places P2 outside the sensor.
    if group=='group_h':layout['longer']=(0,0,1.2)
    ref=api.load(PROXY/group/'paths.jsonl')
    det={}
    with dest.with_suffix('.partial').open('w',encoding='utf8') as f,ThreadPoolExecutor(workers) as pool:
        try:
            for i,((path,points,digest),e) in enumerate(zip(ds,ref,strict=True)):
                raw=path.read_bytes()
                assert e['frame']==i+1 and e['image']==path.name and e['anchors']==points
                actual_hash=hashlib.sha256(raw).hexdigest()
                # CT3 is a historical inventory whose replay-side source
                # hashes were recorded from a different path. Keep the
                # ordered filename/frame checks, while requiring hashes for
                # the six sealed groups.
                if digest is not None:
                    assert actual_hash==digest==e['image_sha256']
                gray=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_GRAYSCALE)
                assert gray is not None
                points=np.array(points)
                futures={name:pool.submit(run_case,lib,det,name,perturb,i,gray,points,mode) for name,perturb in layout.items()}
                cases={k:v.result() for k,v in futures.items()}
                eligible='unknown' if e['tip'] is None else 'shared' if all(contains(c['roi'],e['tip']) for c in cases.values()) else 'outside'
                f.write(json.dumps(dict(frame=i+1,image=path.name,proxy=e['tip'],coverage=eligible,cases=cases),separators=(',',':'))+'\n')
                if (i+1)%25==0:
                    f.flush();print(group,i+1,'/',len(ds),flush=True)
        finally:
            for d in det.values():d.close()
    dest.with_suffix('.partial').replace(dest)
    with (folder/'manifest.json').open('w') as f:json.dump(dict(group=group,mode=mode,frames=len(ds),dll=HASH,anchor_cases=layout,proxy_sha256=api.sha(PROXY/group/'paths.jsonl')),f)
    print('done',group,len(ds),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('groups',nargs='+',choices=NAMES);parser.add_argument('--workers',type=int,default=8)
    args=parser.parse_args()
    for group in args.groups:run(group,args.workers)
