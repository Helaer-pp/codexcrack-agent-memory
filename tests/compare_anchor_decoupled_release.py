"""Compare the anchor-decoupled DLL with the last shipped ROI-tip DLL."""
from pathlib import Path
import csv
import ctypes as C
import json
import os
import sys

import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/gate_adapt'))
from all_groups import inventory,api

OLD=ROOT/'output/releases/A_Win64_OpenCV440/bin/CrackV4.dll'
NEW=ROOT/'output/build/src/cpp/a/Release/CrackV4.dll'
RUN_ID=os.environ.get('CRACK_COMPARE_RUN','anchor_decoupling_release_compare_20261109_r01')
if Path(RUN_ID).name!=RUN_ID or not RUN_ID:raise ValueError('CRACK_COMPARE_RUN')
OUT=ROOT/'output/runs'/RUN_ID
if OUT.exists():raise FileExistsError(OUT)
OUT.mkdir(parents=True)
os.add_dll_directory(str(ROOT/'third_party/opencv440/bin'))

def configure(path):
    lib=C.CDLL(str(path))
    lib.CrackV4SetNumThreads.argtypes=[C.c_int]
    lib.CrackV4CreateExtended.argtypes=[C.POINTER(api.Image),C.POINTER(api.Point),C.POINTER(api.Config),C.POINTER(api.Experiment),C.POINTER(C.c_void_p),C.POINTER(C.c_double),C.c_char_p,C.c_int]
    lib.CrackV4SetOptionsV2.argtypes=[C.c_void_p,C.POINTER(api.Options)]
    lib.CrackV4GetBaseline.argtypes=[C.c_void_p,C.POINTER(api.Result)]
    lib.CrackV4Process.argtypes=[C.c_void_p,C.POINTER(api.Image),C.POINTER(api.Point),C.POINTER(api.Result)]
    lib.CrackV4CopyPath.argtypes=[C.c_void_p,C.c_int,C.POINTER(api.Point),C.c_int]
    lib.CrackV4Destroy.argtypes=[C.c_void_p]
    lib.CrackV4SetNumThreads(4)
    return lib

class Engine:
    def __init__(self,lib,reference,points,mode):
        self.lib=lib;self.handle=C.c_void_p()
        cfg=api.Config(C.sizeof(api.Config),{'clean':0,'cracked':1,'auto':2}[mode],1.,1)
        exp=api.Experiment(C.sizeof(api.Experiment),1,3572,0)
        error=C.create_string_buffer(4096);ms=C.c_double();im=api.image(reference)
        code=lib.CrackV4CreateExtended(C.byref(im),api.points(points),C.byref(cfg),C.byref(exp),C.byref(self.handle),C.byref(ms),error,len(error))
        if code:raise RuntimeError(error.value.decode())
        options=api.Options(C.sizeof(api.Options),2,1,1)
        if lib.CrackV4SetOptionsV2(self.handle,C.byref(options)):raise RuntimeError('options')
    def run(self,image,points,is_reference):
        result=api.Result();result.struct_size=C.sizeof(result);im=api.image(image)
        code=self.lib.CrackV4GetBaseline(self.handle,C.byref(result)) if is_reference else self.lib.CrackV4Process(self.handle,C.byref(im),api.points(points),C.byref(result))
        if code:raise RuntimeError('process')
        n=self.lib.CrackV4CopyPath(self.handle,0,None,0);data=(api.Point*max(0,n))()
        if self.lib.CrackV4CopyPath(self.handle,0,data,n)!=n:raise RuntimeError('path')
        path=np.asarray([(p.x,p.y) for p in data],dtype='<f8').reshape(-1,2)
        return result,path
    def close(self):
        if self.handle:self.lib.CrackV4Destroy(self.handle);self.handle=None

old_lib=configure(OLD);new_lib=configure(NEW)
rows=[];summary=[]
for group,(mode,sequence) in inventory().items():
    old=new=None
    try:
        for index,(file,points,digest) in enumerate(sequence):
            image=api.read(file)
            if index==0:
                old=Engine(old_lib,image,points,mode);new=Engine(new_lib,image,points,mode)
            a,pa=old.run(image,points,index==0);b,pb=new.run(image,points,index==0)
            state=(a.tip_confirmed,a.length_confirmed,a.root_confirmed,a.has_candidate)==(b.tip_confirmed,b.length_confirmed,b.root_confirmed,b.has_candidate)
            tip_equal=(a.tip.x,a.tip.y)==(b.tip.x,b.tip.y)
            length_equal=(a.length_px,a.observed_length_px)==(b.length_px,b.observed_length_px)
            path_equal=pa.shape==pb.shape and np.array_equal(pa,pb)
            rows.append(dict(group=group,frame=index+1,image=file.name,state_equal=state,tip_equal=tip_equal,length_equal=length_equal,path_equal=path_equal,
                old_tip_valid=a.tip_confirmed,new_tip_valid=b.tip_confirmed,old_tip_x=a.tip.x,old_tip_y=a.tip.y,new_tip_x=b.tip.x,new_tip_y=b.tip.y,
                old_points=len(pa),new_points=len(pb),new_detector_ms=None if index==0 else b.detector_ms))
    finally:
        if old:old.close()
        if new:new.close()
    rr=[r for r in rows if r['group']==group]
    times=[r['new_detector_ms'] for r in rr if r['new_detector_ms'] is not None]
    summary.append(dict(group=group,frames=len(rr),changed=sum(not (r['state_equal'] and r['tip_equal'] and r['length_equal'] and r['path_equal']) for r in rr),
        state_changed=sum(not r['state_equal'] for r in rr),tip_changed=sum(not r['tip_equal'] for r in rr),path_changed=sum(not r['path_equal'] for r in rr),
        mean_ms=float(np.mean(times)),p95_ms=float(np.percentile(times,95)),max_ms=max(times),over_15hz=sum(t>1000/15 for t in times)))
    print(summary[-1],flush=True)

api.csvout(OUT/'per_frame.csv',rows);api.csvout(OUT/'summary.csv',summary)
(OUT/'manifest.json').write_text(json.dumps(dict(old_sha256=api.sha(OLD),new_sha256=api.sha(NEW),groups=summary),ensure_ascii=False,indent=2),encoding='utf8')
if any(r['changed'] for r in summary):raise SystemExit('SHIPPED RESULT CHANGED')
print('FULL RELEASE COMPARISON PASSED',flush=True)
