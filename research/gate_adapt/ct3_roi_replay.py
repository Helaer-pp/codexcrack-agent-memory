"""CT3 paired anchor perturbations. Previous measured tips are comparison points, not labels."""
import ctypes as C
import itertools
from pathlib import Path
import os
import csv
import json
import hashlib
import cv2
import numpy as np
from all_groups import ROOT,inventory,api

RUN_ID=os.environ.get('CRACK_CT3_RUN','ct3_roi_tip_r01')
if Path(RUN_ID).name!=RUN_ID or not RUN_ID:
    raise ValueError('CRACK_CT3_RUN must be a simple run id')
OUT=ROOT/'output/runs'/RUN_ID
GOLD=ROOT/'output/runs/seven_groups_gate_locked_r01/ct3/paths.jsonl'
CASES={'measured':(0,0,1),'right5':(5,0,1),'right10':(10,0,1),'right20':(20,0,1),
       'left10':(-10,0,1),'up10':(0,-10,1),'shorter':(0,0,.75),'longer':(0,0,1.35)}

def contains(roi,p):
    return p is not None and roi[0]<=p[0]<roi[0]+roi[2] and roi[1]<=p[1]<roi[1]+roi[3]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    api.BASE=ROOT/'output/build/src/cpp/a/Release/CrackV4.dll'
    api.EXPECTED_BASE=api.sha(api.BASE)
    runtime=C.CDLL(str(api.BASE.with_name('opencv_world440.dll')))
    lib=api.base_library()
    lib.CrackV4LastDebugJson.argtypes=[C.c_void_p];lib.CrackV4LastDebugJson.restype=C.c_char_p
    ds=inventory()['ct3'][1]
    old={(int(r['frame']),r['case']):r for r in csv.DictReader((ROOT/'output/runs/ct3_anchor_sensitivity_01/per_frame.csv').open(encoding='utf-8-sig'))}
    rows=[]; comparisons=[]; pairs=[];det={}
    with (OUT/'paths.jsonl').open('w',encoding='utf8') as stream:
        try:
            for i,((file,points,_),gold) in enumerate(zip(ds,api.load(GOLD),strict=True)):
                raw=file.read_bytes()
                assert hashlib.sha256(raw).hexdigest()==gold['image_sha256']
                gray=cv2.imdecode(np.frombuffer(raw,np.uint8),0);ii=api.image(gray)
                frame=[]; records={}
                ref_tip=gold['tip']
                for name,(dx,dy,s) in CASES.items():
                    pp=np.asarray(points)
                    # One shared, correctly initialized reference coordinate
                    # system. Only CURRENT-frame points are perturbed: this is
                    # the production anchor-decoupling contract.
                    if i and name!='measured':pp=pp.mean(0)+(pp-pp.mean(0))*s+[dx,dy]
                    if i==0:det[name]=api.Baseline(gray,pp,mode='auto')
                    h=det[name].handle
                    r=api.Result();r.struct_size=C.sizeof(r)
                    code=lib.CrackV4Process(h,C.byref(ii),api.points(pp),C.byref(r)) if i else lib.CrackV4GetBaseline(h,C.byref(r))
                    assert not code
                    roi=json.loads(lib.CrackV4LastDebugJson(h))['tip_roi_xywh']
                    tip=[r.tip.x,r.tip.y] if r.tip_confirmed else None
                    if tip:assert contains(roi,tip)
                    n=lib.CrackV4CopyPath(h,0,None,0);p=(api.Point*n)()
                    assert lib.CrackV4CopyPath(h,0,p,n)==n
                    records[name]=dict(tip=tip,path=[[q.x,q.y] for q in p],roi=roi,anchors=pp.tolist())
                    before=old[(i+1,name)]
                    frame.append(dict(frame=i+1,image=file.name,case=name,anchors=pp.tolist(),roi=roi,
                        old_tip_valid=int(before['tip_valid']),old_tip_x=float(before['tip_x']) if int(before['tip_valid']) else None,
                        old_tip_y=float(before['tip_y']) if int(before['tip_valid']) else None,
                        new_tip_valid=r.tip_confirmed,new_tip_x=tip[0] if tip else None,new_tip_y=tip[1] if tip else None,
                        length_valid=r.length_confirmed,length_px=r.length_px if r.length_confirmed else None,
                        proxy_tip=ref_tip,proxy_in_roi=contains(roi,ref_tip) if ref_tip else None,
                        delta_proxy_px=np.linalg.norm(np.array(tip)-ref_tip) if tip and ref_tip else None,
                        detector_ms=r.detector_ms if i else None))
                shared=all(contains(z['roi'],ref_tip) for z in records.values()) if ref_tip else None
                count=sum(r['new_tip_valid'] for r in frame);distances=[]
                for a,b in itertools.combinations(CASES,2):
                    za,zb=records[a],records[b]
                    ta,tb=za['tip'],zb['tip']
                    shared_pair=contains(za['roi'],ref_tip) and contains(zb['roi'],ref_tip) if ref_tip else None
                    dist=float(np.linalg.norm(np.array(ta)-tb)) if ta and tb else None
                    if dist is not None:distances.append(dist)
                    pairs.append(dict(frame=i+1,image=file.name,a=a,b=b,both_cover_proxy=shared_pair,
                        a_valid=int(ta is not None),b_valid=int(tb is not None),delta_px=dist))
                for r in frame:r.update(all_cover_proxy=shared)
                rows.extend(frame)
                comparisons.append(dict(frame=i+1,image=file.name,proxy=ref_tip,all_cover_proxy=shared,confirmed=count,
                    missing=len(CASES)-count,pair_max_px=max(distances) if distances else None))
                stream.write(json.dumps(dict(frame=i+1,image=file.name,proxy=ref_tip,cases=records))+'\n')
        finally:
            for d in det.values():d.close()
    api.csvout(OUT/'per_frame.csv',rows);api.csvout(OUT/'frame_comparison.csv',comparisons)
    api.csvout(OUT/'pairwise.csv',pairs)
    summary=[]
    for name in CASES:
        rr=[r for r in rows if r['case']==name]
        shared=[r for r in rr if r['all_cover_proxy']]
        summary.append(dict(case=name,old=sum(r['old_tip_valid'] for r in rr),new=sum(r['new_tip_valid'] for r in rr),
            shared_n=len(shared),shared_miss=sum(not r['new_tip_valid'] for r in shared),full=sum(r['length_valid'] for r in rr),
            extra_without_proxy=sum(r['new_tip_valid'] and r['proxy_tip'] is None for r in rr),
            mean_ms=np.mean([r['detector_ms'] for r in rr[1:]])))
    api.csvout(OUT/'summary.csv',summary)
    api.save(OUT/'manifest.json',dict(dll=api.EXPECTED_BASE,cases=CASES,frames=len(ds),summary=summary))
    print(summary)
    print('statuses',[(i,sum(r['confirmed']==i for r in comparisons)) for i in range(9)])
    print('spread',max(r['pair_max_px'] or 0 for r in comparisons))
if __name__=='__main__':main()
