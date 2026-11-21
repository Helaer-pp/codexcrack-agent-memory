"""Replay the public V4 entry point. Labels are not inference inputs."""
import csv
import ctypes as C
import json
import math
import os
import sys
from pathlib import Path

import cv2

from research.notch_identity_v512 import batch

BUILD=batch.ROOT/'output/build/v512_release/src/cpp/v512/Release'
DEST=batch.ROOT/'output/verification/v512_release'

class Point(C.Structure):
    _fields_=[('x',C.c_double),('y',C.c_double)]
class Image(C.Structure):
    _fields_=[('data',C.c_void_p),('width',C.c_int),('height',C.c_int),('stride',C.c_int64)]
class Config(C.Structure):
    _fields_=[('size',C.c_uint32),('mode',C.c_int),('ratio',C.c_double),('refine',C.c_int)]
class Result(C.Structure):
    _fields_=[('size',C.c_uint32),*[(k,C.c_int) for k in ('tip_ok','length_ok','root_ok','candidate')],
              ('tip',Point),*[(k,C.c_double) for k in ('length','observed','mm','detector_ms','api_ms')],
              ('hits',C.c_int),('tiles',C.c_int)]
def image(a):return Image(a.ctypes.data,a.shape[1],a.shape[0],a.strides[0])
def pair(pts):return (Point*2)(*(Point(*p) for p in pts))
def load():
    lib=C.CDLL(str(BUILD/'CrackV4.dll'))
    P=C.POINTER
    for name,args,ret in [('Create',[P(Image),P(Point),P(Config),P(C.c_void_p),P(C.c_double),C.c_char_p,C.c_int],C.c_int),
        ('Process',[C.c_void_p,P(Image),P(Point),P(Result)],C.c_int),('GetBaseline',[C.c_void_p,P(Result)],C.c_int),
        ('DefaultConfig',[P(Config)],None),('CopyPath',[C.c_void_p,C.c_int,P(Point),C.c_int],C.c_int),
        ('LastJson',[C.c_void_p],C.c_char_p),('Destroy',[C.c_void_p],None),('BuildInfo',[],C.c_char_p),
        ('SetNumThreads',[C.c_int],None)]:
        f=getattr(lib,'CrackV4'+name);f.argtypes=args;f.restype=ret
    assert b'V5.12' in lib.CrackV4BuildInfo()
    lib.CrackV4SetNumThreads(1)
    return lib
def create(lib,ref,rp):
    h=C.c_void_p();cfg=Config();lib.CrackV4DefaultConfig(C.byref(cfg))
    assert cfg.size==C.sizeof(Config) and cfg.refine==1
    cfg.ratio=.025
    err=C.create_string_buffer(512);ms=C.c_double()
    assert not lib.CrackV4Create(C.byref(image(ref)),pair(rp),C.byref(cfg),C.byref(h),C.byref(ms),err,len(err)),err.value
    return h
def pathof(lib,h,observed):
    n=lib.CrackV4CopyPath(h,observed,None,0);assert n>=0
    buf=(Point*n)()
    assert lib.CrackV4CopyPath(h,observed,buf,n)==n
    return [[int(p.x),int(p.y)] for p in buf]
def main(g,selected):
    assert batch.read(batch.ROOT/'config/dataset_usage_policy.json')['groups'][g] in ('DEVELOPMENT','VALIDATION_ONLY')
    if g=='group_c':os.environ['CRACKV4_V512_MATERIAL_POLICY']=str(batch.POLICY)
    else:os.environ.pop('CRACKV4_V512_MATERIAL_POLICY',None)
    lib=load();cv2.setNumThreads(1);DEST.mkdir(parents=True,exist_ok=True)
    digest=batch.sha(BUILD/'CrackV4.dll')
    assert batch.read(DEST/'freeze.json')['dll']==digest
    rows=[];ref=None;key=();h=None
    try:
        for rec in map(json.loads,(batch.OUT/(g+'.jsonl')).open()):
            marked='S3' in rec['placements']['original']
            if selected and not marked:continue
            i=rec['frame'];meta=batch.read(batch.OLD/'evidence'/g/str(i)/'metadata.json');info=meta['input']
            place='bright' if g=='group_c' else 'original'
            rp,cp=meta['fixed_points'],meta['current_points']
            newkey=(info['ref_sha'],tuple(map(tuple,rp)))
            if newkey!=key:
                if h:lib.CrackV4Destroy(h);h=None
                ref=batch.old.read_fixed(info['reference'],info['ref_sha']);h=create(lib,ref,rp);key=newkey
            cur=batch.old.current(info['current'],info['image_sha'])
            o=Result(size=C.sizeof(Result))
            assert not lib.CrackV4Process(h,C.byref(image(cur)),pair(cp),C.byref(o)),lib.CrackV4LastJson(h)
            path=pathof(lib,h,0);obs=pathof(lib,h,1)
            tip=[int(o.tip.x),int(o.tip.y)] if o.tip_ok else None
            assert (path[-1] if path else None)==tip and path[:len(obs)]==obs
            assert math.isclose(o.length,sum(math.dist(x,y) for x,y in zip(path,path[1:])),abs_tol=1e-7)
            assert math.isclose(o.mm,o.length*.025,abs_tol=1e-8)
            assert math.isclose(o.observed,sum(math.dist(x,y) for x,y in zip(obs,obs[1:])),abs_tol=1e-7)
            old=rec['placements'][place]['S4']['full']
            expected=old
            rows.append(dict(frame=i,marked=marked,tip=tip,expected=expected['tip'],historical=old['tip'],
                same_tip=tip==expected['tip'],same_path=path==expected['points'],historical_tip=tip==old['tip'],
                historical_path=path==old['points'],length=o.length,ms=o.detector_ms))
            if i%100==0:print(g,i,flush=True)
    finally:
        if h:lib.CrackV4Destroy(h)
    fn=DEST/(g+('_selected' if selected else '_all')+'.csv')
    with fn.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,rows[0]);writer.writeheader();writer.writerows(rows)
    print(g,len(rows),{k:sum(r[k] for r in rows) for k in ('same_tip','same_path','historical_tip')})
if __name__=='__main__':main(sys.argv[1],'--selected' in sys.argv)
