"""Replay original BMPs through the shipped C ABI; compare against the sealed V5.10 paths."""
import argparse
import csv
import ctypes as C
import json
import math
import os
from pathlib import Path
import time
from research.notch_identity_v510.batch import ROOT,OUT,OLD,POLICY,old,sha

BUILD=ROOT/'output/build/v510_native/src/cpp/v510/Release'
RESULTS=ROOT/'output/verification/v510_native'
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double)]
class Image(C.Structure):_fields_=[('data',C.c_void_p),('width',C.c_int),('height',C.c_int),('stride',C.c_int64)]
class Box(C.Structure):_fields_=[(k,C.c_int) for k in ('l','t','r','b')]
Pair=Point*2
class Config(C.Structure):_fields_=[('size',C.c_uint),('raw_only',C.c_int),('material_mode',C.c_int),('request',Box),('band',Box),('floor',C.c_double),('virtual',Pair),('mm_per_pixel',C.c_double)]
class Result(C.Structure):_fields_=[('size',C.c_uint),('status',C.c_int),('root',Point),('tip',Point),('arc',C.c_double),('proj',C.c_double),('count',C.c_int),('bridge',C.c_int),('ref',Pair),('cur',Pair),('mm',C.c_double),('ms',C.c_double)]
def read(p):return json.loads(p.read_text('utf-8-sig'))
def image(a):return Image(a.ctypes.data,a.shape[1],a.shape[0],a.strides[0])
def pair(pts):return Pair(*(Point(*p) for p in pts))
def libs():
    dll=C.CDLL(str(BUILD/'CrackV510.dll'))
    for name,args,typ in [
        ('Create',[C.POINTER(Image),C.POINTER(Point),C.POINTER(Config),C.POINTER(C.c_void_p)],C.c_int),
        ('Process',[C.c_void_p,C.POINTER(Image),C.POINTER(Point),C.POINTER(Result)],C.c_int),
        ('CopyPath',[C.c_void_p,C.POINTER(Point),C.c_int],C.c_int),
        ('GetBaseline',[C.c_void_p,C.POINTER(Result)],C.c_int),('Destroy',[C.c_void_p],None),
        ('LastError',[],C.c_char_p),('SetNumThreads',[C.c_int],None)]:
        fn=getattr(dll,'Crack510'+name);fn.argtypes=args;fn.restype=typ
    return dll
def main(g,selected=False):
    policy=read(ROOT/'config/dataset_usage_policy.json')['groups']
    assert g in ('group_a','three_point_bend','group_c') and policy[g] in ('DEVELOPMENT','VALIDATION_ONLY')
    RESULTS.mkdir(parents=True,exist_ok=True);identity=sha(BUILD/'CrackV510.dll')
    if policy[g]=='VALIDATION_ONLY':assert identity==read(RESULTS/'freeze.json')['dll_sha256']
    dll=libs();dll.Crack510SetNumThreads(4)
    run=OUT/(g+'.jsonl');assert sha(run)==read(OUT/(g+'_seal.json'))['predictions']
    rows=[];handles={}
    try:
        for line in run.open():
            rec=json.loads(line);i=rec['frame']
            if selected and 'apex_only' not in rec['placements']['original']:continue
            meta=read(OLD/'evidence'/g/str(i)/'metadata.json');info=meta['input']
            cur=old.current(info['current'],info['image_sha']);im=image(cur)
            for place,bundle in rec['placements'].items():
                for mode in ('full','raw_only'):
                    key=place,mode
                    if key not in handles:
                        cfg=Config(size=C.sizeof(Config),mm_per_pixel=.025,raw_only=int(mode=='raw_only'))
                        if g=='group_c':
                            policy_window=read(POLICY);cfg.material_mode=1+(place=='bright')
                            cfg.request=Box(*policy_window['reference_box']);cfg.band=Box(*policy_window['fixed_band'])
                            cfg.floor=policy_window['fixed_floor'];cfg.virtual=pair(policy_window['reference_virtual_points'])
                        ref=old.current(info['reference'],info['ref_sha']);ri=image(ref);h=C.c_void_p()
                        assert dll.Crack510Create(C.byref(ri),pair(meta['fixed_points']),C.byref(cfg),C.byref(h))==0,dll.Crack510LastError()
                        handles[key]=h,info['ref_sha']
                    h,ref_hash=handles[key];assert info['ref_sha']==ref_hash
                    m=bundle['v5_10'][mode];o=Result(size=C.sizeof(Result));start=time.perf_counter()
                    assert not dll.Crack510Process(h,C.byref(im),pair(meta['current_points']),C.byref(o)),dll.Crack510LastError()
                    ms=(time.perf_counter()-start)*1000
                    pts=(Point*o.count)();assert dll.Crack510CopyPath(h,pts,o.count)==o.count
                    path=[[p.x,p.y] for p in pts];end=path[-1] if path else None
                    status=['NO_NOTCH_BODY','no_tip','VALID'][o.status]
                    assert (not path and math.isnan(o.arc) and math.isnan(o.tip.x)) or end==[o.tip.x,o.tip.y]
                    assert (not path or math.isclose(math.fsum(math.dist(a,b) for a,b in zip(path,path[1:])),o.arc,abs_tol=1e-8))
                    assert o.ms>=0 and (math.isclose(o.arc*.025,o.mm,abs_tol=1e-10) if path else math.isnan(o.mm))
                    if place=='bright':
                        assert [[p.x,p.y] for p in o.cur]==rec['geometry']['cur_points']
                        assert [[p.x,p.y] for p in o.ref]==rec['geometry']['ref_points']
                    rows.append(dict(group=g,frame=i,place=place,mode=mode,status_equal=status==m['status'],tip_equal=end==m['tip'],path_equal=path==m['points'],
                        max_column_y_delta=max((abs(a[1]-b[1]) for a,b in zip(path,m['points'])),default=0) if len(path)==len(m['points']) and all(a[0]==b[0] for a,b in zip(path,m['points'])) else None,
                        expected=m['tip'],actual=end,error=math.dist(end,m['tip']) if end and m['tip'] else None,
                        arc_delta=o.arc-m['path_length_px'] if path and m['points'] else None,
                        proj_delta=o.proj-m['projected_length_px'] if path and m['points'] else None,native_ms=ms,dll=identity))
            if i%100==0:print(g,i,flush=True)
    finally:
        for h,_ in handles.values():dll.Crack510Destroy(h)
    dest=RESULTS/(g+('_selected' if selected else '_all')+'.csv')
    with dest.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,rows[0]);w.writeheader();w.writerows(rows)
    print(g,len(rows),sum(r['path_equal'] for r in rows),'exact paths')
    print([r for r in rows if not r['tip_equal']][:2])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('group');ap.add_argument('--selected',action='store_true')
    a=ap.parse_args();main(a.group,a.selected)
