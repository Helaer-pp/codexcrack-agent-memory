"""A and B have separate evidence, optimization and terminal tests."""
import cv2
import numpy as np
from research.notch_identity_v34 import terminal as gray_tracker
from . import evidence,tracking

STAGES=('track_a','evidence','track_b','v4_0')

def prepare(raw,hint,scale,stage='v4_0'):
    if stage not in STAGES:raise ValueError(stage)
    p=gray_tracker.prepare(raw,hint,scale)
    return (*p[:-3],stage,*p[-2:]) if p is not None else None

def refine(path,p,ev):
    pts=np.asarray(path,dtype=np.float32);s=p[5];raw=p[4]
    tangent=np.gradient(pts,axis=0)
    normal=np.column_stack((-tangent[:,1],tangent[:,0]))
    normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-5)
    radius=min(2.,max(.75,.007*s))
    t=np.linspace(-radius,radius,9,dtype=np.float32)
    xy=pts[:,None,:]+normal[:,None,:]*t[None,:,None]
    values=cv2.remap(raw,xy[:,:,0],xy[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    j=values.argmax(axis=1);i=np.arange(len(j))
    peaks=(values[:,1:-1]>values[:,:-2])&(values[:,1:-1]>=values[:,2:])
    good=(j>0)&(j<8)&(peaks.sum(axis=1)==1)&(values[i,j]-np.maximum(values[:,0],values[:,-1])>p[8])
    x,y=pts.astype(int).T;good&=ev['clear'][y-ev['top'],x]>.75
    j=np.clip(j,1,7)
    a,b,c=values[i,j-1],values[i,j],values[i,j+1]
    fraction=np.clip(.5*(a-c)/np.minimum(a-2*b+c,-1e-6),-.5,.5)
    offset=np.where(good,t[j]+fraction*(t[1]-t[0]),0)
    return (pts+normal*offset[:,None]).tolist(),int(good.sum())

def predict(p,bonus=None,fixed=None):
    base=(*p[:-3],'v3_4',*p[-2:]) if p is not None else None
    a=gray_tracker.predict(base,None)
    if fixed is None:return a
    stage=p[-3] if p is not None else 'track_a'
    ev=coarse=local=None
    if p is not None and stage!='track_a':
        ev,coarse,local=evidence.make(p,fixed)
    decision='NO_NOTCH' if p is None else 'TRACK_A_ONLY' if stage=='track_a' else 'REFERENCE_UNAVAILABLE'
    b=None;count=0;rejected={};candidates=[]
    if ev is not None:
        if stage=='evidence':
            decision='EVIDENCE_ONLY'
        else:
            candidates,count=tracking.trace(ev,p)
            b,rejected=tracking.admissible(candidates,p)
            decision='INCREMENT_CERTIFIED' if b else 'NO_CERTIFIED_INCREMENT'
    origin=np.asarray(p[1]) if p is not None else np.zeros(2)
    diag=dict(track_a_tip=a['tip'],track_a_root=a['root'],track_b_tip=None,track_b_root=None,decision=decision,
              seeds=count,certified=len(candidates),rejections=rejected,coarse=coarse,registration=local,
              noise_floor=ev['floor'] if ev is not None else None,refined=0,events=[])
    if b:
        path=b['points'];root=(np.array(b['root'])+origin).tolist()
        diag.update(track_b_tip=(path[-1]+origin).tolist(),track_b_root=root,
                    events=[[int(col+origin[0]) for col in event] for event in b['events']])
        if stage=='v4_0':path,diag['refined']=refine(path,p,ev)
        path=(np.array(path)+origin).tolist();tip=path[-1]
        trace=dict(reference=local,gate='B_SNR',stop='INCREMENT_END',first_loss=None)
        result=dict(status='VALID',root=root,points=path,tip=tip,diagnostics=dict(candidates=[dict(start=root,tip=tip,status='VALID',trace=trace)],pairs=[],selected=0))
    else:result=a
    result['diagnostics'].update(dual=diag,coarse=coarse)
    return result
