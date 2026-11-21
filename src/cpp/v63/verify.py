"""Replay original Gray8 frames through the public DLL and compare unrounded coordinates."""
import hashlib
import argparse
import ctypes as C
import json
import math
import os
from pathlib import Path

import numpy as np
from src.cpp.v512.verify_abi import Image,Point,Config,Result,image,pair
from research.notch_identity_v63 import batch as b,inputs
from research.notch_identity_v63.run import frozen
from research.v3_labelme_comparison.compare import write_csv

BUILD=b.ROOT/'output/build/v63_release/src/cpp/v63/Release'
VERSION=(b.ROOT/'GrayDetectionV2/VERSION.txt').read_text(encoding='ascii').strip()
OUT=b.ROOT/'output/verification'/('v63_GrayDetectionV2_API2_'+VERSION+'_cmake')


def library(folder=BUILD):
    with os.add_dll_directory(str(b.ROOT/'third_party/opencv440/bin')):
        dll=C.CDLL(str((folder/'GrayDetectionV2.dll').resolve()))
    p=C.POINTER
    specs=[('DefaultConfig',[p(Config)],None),('Create',[p(Image),p(Point),p(Config),p(C.c_void_p),p(C.c_double),C.c_char_p,C.c_int],C.c_int),
           ('Process',[C.c_void_p,p(Image),p(Point),p(Result)],C.c_int),('GetBaseline',[C.c_void_p,p(Result)],C.c_int),
           ('CopyPath',[C.c_void_p,C.c_int,p(Point),C.c_int],C.c_int),('Destroy',[C.c_void_p],None),
           ('LastJson',[C.c_void_p],C.c_char_p),('BuildInfo',[],C.c_char_p),('SetNumThreads',[C.c_int],None)]
    for name,args,restype in specs:
        func=getattr(dll,'GrayDetectionV2'+name);func.argtypes=args;func.restype=restype
    assert dll.GrayDetectionV2BuildInfo().startswith(b'GrayDetectionV2 V6.3 S2')
    dll.GrayDetectionV2SetNumThreads(1)
    return dll


def create(lib, reference, points):
    handle = C.c_void_p()
    cfg = Config()
    lib.GrayDetectionV2DefaultConfig(C.byref(cfg))
    cfg.ratio = .025
    message = C.create_string_buffer(512)
    rc = lib.GrayDetectionV2Create(C.byref(image(reference)), pair(points), C.byref(cfg),
                                   C.byref(handle), None, message, len(message))
    if rc:
        raise RuntimeError(message.value.decode('utf8', errors='replace'))
    return handle


def copy_path(lib,h,observed=0):
    n=lib.GrayDetectionV2CopyPath(h,observed,None,0)
    assert n>=0
    data=(Point*n)()
    assert lib.GrayDetectionV2CopyPath(h,observed,data,n)==n
    return [[p.x,p.y] for p in data]


def replay(g,place,selected,dx=0,folder=BUILD):
    frozen()
    assert b.read(b.ROOT/'config/dataset_usage_policy.json')['groups'][g] in ('DEVELOPMENT','VALIDATION_ONLY')
    OUT.mkdir(parents=True,exist_ok=True)
    key='CRACKV4_V512_MATERIAL_POLICY'
    os.environ.pop(key,None)
    if g=='group_c':
        if place=='bright':os.environ[key]=str(b.POLICY)
        else:
            policy=OUT/'group_c_original.json'
            b.save(policy,{**b.read(b.POLICY),'material_mode':1})
            os.environ[key]=str(policy)
    lib=library(folder)
    ids={int(r['frame_id']) for r in b.read_csv(b.SELECT) if r['dataset_id']==g}
    file=b.OUT/(g+'.jsonl');assert b.read(b.OUT/(g+'_seal.json'))['predictions']==b.sha(file)
    rows=[];handle=None;framekey=None
    try:
        for rec in map(json.loads,file.open(encoding='utf8')):
            i=rec['frame']
            if selected and i not in ids:continue
            meta=inputs.metadata(g,i);src=meta['input']
            cur=b.old.current(src['current'],src['image_sha'])
            cp=np.asarray(meta['current_points'])+[dx,0]
            rp=np.asarray(meta['fixed_points'])+[dx,0]
            key=(src['ref_sha'],tuple(map(tuple,rp)))
            if key!=framekey:
                if handle:lib.GrayDetectionV2Destroy(handle);handle=None
                fixed=b.old.read_fixed(src['reference'],src['ref_sha'])
                handle=create(lib,fixed,rp);framekey=key
            out=Result(size=C.sizeof(Result))
            rc=lib.GrayDetectionV2Process(handle,C.byref(image(cur)),pair(cp),C.byref(out))
            if rc:raise RuntimeError((g,i,lib.GrayDetectionV2LastJson(handle)))
            points=copy_path(lib,handle);tip=[out.tip.x,out.tip.y] if out.tip_ok else None
            expected=rec['placements'][place]['S2']['full'];target=expected['tip']
            assert (points[-1] if points else None)==tip
            assert copy_path(lib,handle,1)==points and bool(out.tip_ok)==bool(out.length_ok)
            arc=sum(math.dist(a,b) for a,b in zip(points,points[1:]))
            assert math.isclose(out.length,arc,abs_tol=1e-8) and math.isclose(out.mm,arc*.025,abs_tol=1e-8)
            reference_path=expected['points']
            pmap=dict(reference_path)
            qmap=dict(points)
            common=pmap.keys() & qmap.keys()
            max_dy=max((abs(pmap[x]-qmap[x]) for x in common), default=0)
            rows.append(dict(path_sha=hashlib.sha256(np.asarray(points,dtype='<f8').tobytes()).hexdigest(),
                        max_dy_px=max_dy,nonshared_x=len(pmap.keys() ^ qmap.keys()),group=g,placement=place,frame=i,anchors_dx=dx,status_equal=bool(tip)==bool(target),
                        tip_equal=tip==target,path_equal=points==expected['points'],tip=tip,expected=target,
                        tip_delta=math.dist(tip,target) if tip and target else None,length=out.length,
                        length_delta=abs(out.length-(expected['path_length_px'] or 0)),ms=out.detector_ms))
    finally:
        if handle:lib.GrayDetectionV2Destroy(handle)
    name=f'{g}_{place}_{dx}_'+('sample' if selected else 'all')
    write_csv(OUT/(name+'.csv'),rows)
    print(name,len(rows),{k:sum(r[k] for r in rows) for k in ('status_equal','tip_equal','path_equal')},flush=True)

if __name__=='__main__':
    arg=argparse.ArgumentParser()
    arg.add_argument('group');arg.add_argument('placement',nargs='?',default='original')
    arg.add_argument('--sample',action='store_true');arg.add_argument('--dx',type=int,default=0)
    arg.add_argument('--folder',type=Path,default=BUILD)
    a=arg.parse_args();replay(a.group,a.placement,a.sample,a.dx,a.folder)
