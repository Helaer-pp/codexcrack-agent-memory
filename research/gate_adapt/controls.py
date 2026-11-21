"""Gate-level fixtures. The supplied V1 rejection injects the branch under test."""
import json
import cv2
import numpy as np
from adapt import GateAdapter

IDENTITY=np.array([[1.,0.,0.],[0.,1.,0.]])
ANCHORS=np.array([[45.,54.],[45.,130.]])
def scene():
    noise=np.random.default_rng(1946).normal(0,1.2,(190,240))
    ref=np.uint8(np.clip(185+noise,0,255))
    cv2.fillPoly(ref,[np.int32([(0,85),(69,89),(69,95),(0,99)])],50)
    return ref

def draw(im,a,b,color):
    out=im.copy()
    cv2.line(out,a,b,color,1,cv2.LINE_AA)
    return out

def controls():
    ref=scene()
    cases={}
    def record(name,lines,action,gt):
        tip=lines[-1][-1] if lines else None
        cases[name]=dict(action=action,tip=tip,known_tip=gt,error_px=float(np.linalg.norm(np.array(gt)-tip)) if tip is not None and gt is not None else None)
    def seed(name,r,im,gt):
        adapter=GateAdapter(r,ANCHORS)
        adapter.apply(0,r,IDENTITY,[], 'no_seed',[],None)
        lines,reason=adapter.apply(1,im,IDENTITY,[],'no_seed',[],None)
        record(name,lines,reason,gt)
    crack=draw(ref,(70,92),(79,91),124)
    seed('short_new_line',ref,crack,[79,91])
    seed('static_feature',crack,crack,None)
    seed('identity',ref,ref,None)
    seed('exposure_step',ref,cv2.add(ref,12),None)
    seed('foreign_line_far_from_notch',ref,draw(ref,(90,92),(99,91),120),None)
    seed('single_dark_dot',ref,draw(ref,(71,92),(72,92),90),None)
    # Same pixels as positive fixture, different ownership cannot be inferred.
    seed('new_scratch_at_notch',ref,crack,None)
    for stop in ('terminal_strength','possible_forward_continuation'):
        for label,history,current,gt in (
            ('supported',[133,136],draw(ref,(85,92),(139,92),120),[139,92]),
            ('no_history',[],draw(ref,(85,92),(139,92),120),[139,92]),
            ('erased',[133,136],ref,None),
        ):
            adapter=GateAdapter(ref,ANCHORS)
            for i in range(3):
                known=[[list((float(x),92.)) for x in range(85,history[i-1]+1)]] if i and history else []
                adapter.apply(i,ref,IDENTITY,known,'evidence_ended',[],None)
            segment=[[[float(x),92.] for x in range(85,136)]]
            lines,reason=adapter.apply(3,current,IDENTITY,[],'gap_unresolved',segment,stop)
            record(stop+'_'+label,lines,reason,gt)
    return cases

