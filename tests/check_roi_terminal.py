"""Exercise the A endpoint ABI without an entrance and in four ROI directions."""
from pathlib import Path
import sys
import ctypes as C
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/python'))
from crackv4 import frozen_a as api

def check():
    api.BASE=ROOT/'output/build/src/cpp/a/Release/CrackV4.dll'
    api.EXPECTED_BASE=api.sha(api.BASE)
    runtime=C.CDLL(str(api.BASE.with_name('opencv_world440.dll')))
    rng=np.random.default_rng(20261106)
    reference=np.uint8(np.clip(rng.normal(185,6,(288,384)),0,255))
    frame=reference.copy()
    cv2.line(frame,(135,149),(189,137),80,2,cv2.LINE_AA)
    for k in range(4):
        pp=np.array([[94.,104.],[94.,178.]])
        target=np.array([189.,137.])
        ref=reference.copy();im=frame.copy()
        for _ in range(k):
            h=ref.shape[0]
            pp=np.stack((h-1-pp[:,1],pp[:,0]),axis=1)
            target=np.array([h-1-target[1],target[0]])
            im=cv2.rotate(im,cv2.ROTATE_90_CLOCKWISE)
            ref=cv2.rotate(ref,cv2.ROTATE_90_CLOCKWISE)
        d=api.Baseline(ref,pp,mode='auto')
        def detect(image):
            r=api.Result();r.struct_size=C.sizeof(r)
            ok=d.lib.CrackV4Process(d.handle,C.byref(api.image(image)),api.points(pp),C.byref(r))
            assert ok==0
            return r
        try:
            assert not detect(ref).tip_confirmed
            r=detect(im)
            assert r.tip_confirmed and np.linalg.norm(target-[r.tip.x,r.tip.y])<4 and not r.length_confirmed,(k,r.tip.x,r.tip.y)
            assert not detect(ref).tip_confirmed
        finally:d.close()
    for mode in ['auto','cracked']:
        d=api.Baseline(frame,[[94.,104.],[94.,178.]],mode=mode)
        try:
            r=api.Result();r.struct_size=C.sizeof(r)
            assert d.lib.CrackV4GetBaseline(d.handle,C.byref(r))==0
            assert r.tip_confirmed and np.linalg.norm([r.tip.x-189,r.tip.y-137])<4
            assert d.lib.CrackV4ResetTemporal(d.handle)==0
            assert d.lib.CrackV4Process(d.handle,C.byref(api.image(frame)),api.points([[94.,104.],[94.,178.]]),C.byref(r))==0
            assert r.tip_confirmed and np.linalg.norm([r.tip.x-189,r.tip.y-137])<4
        finally:d.close()
    print('ROI terminal: four orientations, detached crack, clean controls, precracked reference and reset passed')
if __name__=='__main__': check()
