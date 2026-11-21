"""Signed ridge evidence and single-pass, free-endpoint maximum-score path."""
from dataclasses import dataclass
import cv2
import numpy as np
from numba import njit
from research.notch_identity_v31.detector import locate_root,px
from research.notch_identity_v31 import topology
from research.notch_identity_v40.evidence import registered

STAGES=('global_raw','joint_dp','v5_0')

@dataclass
class Scene:
    raw: np.ndarray
    local: np.ndarray
    sl: tuple
    origin: tuple
    starts: list
    front: int
    scale: float
    noise: float
    span: float
    black: float
    stage: str

def prepare(raw,hint,scale,stage='v5_0'):
    if stage not in STAGES:raise ValueError(stage)
    mouth,black,span=locate_root(raw,hint,scale,True)
    if mouth is None:return None
    starts,(fx,fy)=mouth
    top=max(0,fy-px(scale,.27));bottom=min(len(raw),fy+px(scale,.27)+1)
    left=max(0,fx-px(scale,.08));sl=np.s_[top:bottom,left:]
    local=raw[sl];res=local.astype(np.float32)-cv2.medianBlur(local,3)
    stride=px(scale,.012);sub=res[::stride,::stride]
    noise=max(.006*span,1.4826*float(np.median(abs(sub-np.median(sub)))),1e-6)
    return Scene(raw,local,sl,(left,top),[(x-left,y-top) for x,y in starts],fx-left,scale,noise,span,black,stage)

def bilateral(im,s):
    """Positive thin bright ridge on an already polarity-corrected image."""
    radii=sorted(set(px(s,r) for r in (.007,.014,.024)))
    pad=radii[-1];h=len(im);out=np.zeros_like(im)
    extended=cv2.copyMakeBorder(im,pad,pad,0,0,cv2.BORDER_REPLICATE)
    for r in radii:
        out=np.maximum(out,im-np.maximum(extended[pad-r:pad-r+h],extended[pad+r:pad+r+h]))
    return out

def fields(p,fixed):
    s=p.scale;g=p.local.astype(np.float32);sig=max(.45,.003*s)
    # Straight line openings attenuate isolated spots while preserving a sloping valley.
    reach=px(s,.011)
    kernels=[]
    for slope in (-.55,0.,.55):
        rise=round(slope*reach)
        k=np.zeros((2*abs(rise)+1,2*reach+1),np.uint8)
        cv2.line(k,(0,abs(rise)-rise),(2*reach,abs(rise)+rise),1)
        kernels.append(k)
    texture=np.abs(g-cv2.GaussianBlur(g,(0,0),sigmaX=max(.5,.017*s)))
    sample=texture[::px(s,.012),p.front+px(s,.035)::px(s,.012)]
    # Strong background texture makes short oblique ridges discontinuous in a line opening.
    uniform=np.clip((3.2*p.noise-np.quantile(sample,.925))/(1.1*p.noise),0,1) if sample.size else 0.
    def ridge(im):
        a=bilateral(im,s)
        sustained=np.maximum.reduce([cv2.morphologyEx(a,cv2.MORPH_OPEN,k) for k in kernels])
        clean=np.clip((.026*p.span-p.noise)/(.020*p.span),0,1)
        weak=np.clip((.19*p.span-a)/(.10*p.span),0,1)
        mix=.03+.87*uniform*clean*weak
        a=(1-mix)*a+mix*sustained
        return .60*a+.40*cv2.GaussianBlur(a,(0,0),sigmaX=sig,sigmaY=max(.35,sig*.52))
    depth=ridge(-g)
    size=2*px(s,.036)+1
    broad=cv2.blur(depth,(size,size))
    tau=np.maximum(2.25*p.noise+.007*p.span,1.9*broad)
    raw_score=2.1*np.tanh(depth/(2*tau))-.97
    score=raw_score.copy();coarse=reg=None;source='RAW_ONLY'
    if fixed is not None and p.stage!='global_raw':
        args=(p.sl,p.origin,p.starts,None,None,s,p.front,p.local,p.noise,None,p.raw,p.span)
        coarse,reg,aligned=registered(args,fixed)
        if aligned is not None:
            valid=np.isfinite(aligned);f=np.where(valid,aligned,g);d=f-g
            if np.any(valid) and np.quantile(np.abs(d[::4,::4]),.995)>.01*p.span:
                inc=ridge(d);fd=bilateral(-f,s);r=px(s,.014)
                smooth=cv2.GaussianBlur(d,(0,0),sigmaX=sig,sigmaY=max(.35,.5*sig))
                plus=np.maximum(smooth,0);minus=np.maximum(-smooth,0)
                pos=cv2.blur(plus,(1,2*r+1));neg=cv2.blur(minus,(1,2*r+1))
                inc*=np.clip(1-neg/np.maximum(pos,p.noise),0,1)
                reach=px(s,.025)
                # Require a sustained reference valley at a common local displacement.
                coherent=cv2.blur(fd,(2*px(s,.012)+1,1))
                prior=cv2.dilate(coherent,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*reach+1,2*reach+1)))
                risk=np.clip((prior/np.maximum(depth,tau)-.40)/.45,0,1)*np.clip((prior-2*p.noise)/tau,0,1)
                diff_tau=np.maximum(2.45*p.noise+.007*p.span,2*cv2.blur(inc,(size,size)))
                delta_score=2.1*np.tanh(inc/(2*diff_tau))-.97
                distance=np.maximum(0,np.arange(g.shape[1],dtype=np.float32)-p.front)
                # Reference valleys overlap the open notch at the birth; ramp to full strength in material.
                prior_weight=np.clip((distance-.04*s)/(.14*s),0.,1.)
                fused=(.90-.47*prior_weight)*raw_score+(.10+.47*prior_weight)*delta_score-1.38*risk*prior_weight
                fused=np.where(depth>=np.maximum(1.35*p.noise,.007*p.span),fused,np.minimum(fused,-.8))
                score=np.where(valid,fused,raw_score);source='JOINT'
            else:source='NO_INCREMENT_RAW'
        else:source='UNREGISTERED_RAW'
    # No legal seed behind the mouth or on a detached dark stroke.
    f=p.front;end=min(g.shape[1],f+px(s,.020)+1)
    seeds=np.zeros((len(g),end-f),np.uint8)
    mid=int(np.median(np.array(p.starts)[:,1]));pad=px(s,.16)
    patch=g[:,max(0,f-px(s,.055)):end]
    material=float(np.percentile(patch,70))
    _,cc=cv2.connectedComponents((patch<material-max(4*p.noise,.10*p.span)).astype('uint8'))
    left=f-max(0,f-px(s,.055));core=patch[:,:max(1,left-px(s,.025))]<p.black+.26*p.span
    counts=np.bincount(cc[:,:core.shape[1]][core],minlength=2);counts[0]=0
    if counts.max():
        connected=cc[:,left:]==counts.argmax()
        seeds[:]=connected&(depth[:,f:end]>tau[:,f:end])
        seeds[:max(0,mid-pad)]=0;seeds[mid+pad+1:]=0
        # A mouth-edge pixel with blank material immediately to its right is not a ridge birth.
        audit=cv2.dilate(depth,np.ones((2*px(s,.004)+1,1),np.uint8))
        for j in range(seeds.shape[1]):
            block=audit[:,f+j+1:min(g.shape[1],f+j+1+px(s,.010))]
            if block.shape[1]:seeds[:,j]&=(block>max(2*p.noise,.018*p.span)).mean(1)>=.65
    return np.ascontiguousarray(score[:,f:].T),np.ascontiguousarray(seeds.T),coarse,reg,source

@njit
def global_free_end_dp(score,seeds,s):
    """Exact directional-state recurrence; no downstream restarts or terminal trimming."""
    w,h=score.shape;neg=-np.inf
    prev=np.full((h,5),neg,np.float32);back=np.full((w,h,5),-2,np.int8)
    values=np.full((w,h),neg,np.float32)
    best=0.;bx=by=bd=-1
    for x in range(w):
        cur=np.full((h,5),neg,np.float32)
        for y in range(h):
            val=score[x,y]
            if x<seeds.shape[0] and seeds[x,y]:
                cur[y,2]=max(0.,val);back[x,y,2]=-1
            for d in range(5):
                yy=y-(d-2)
                if yy<0 or yy>=h:continue
                vmax=neg;arg=-1
                for k in range(5):
                    v=prev[yy,k]-.13*abs(d-2)-.19*abs(d-k)
                    if v>vmax:vmax=v;arg=k
                v=vmax+val
                if v>cur[y,d] and v>=-.025*s:
                    cur[y,d]=v;back[x,y,d]=arg
            for d in range(5):
                v=cur[y,d]
                if v>values[x,y]:values[x,y]=v
                if v>best:best=v;bx=x;by=y;bd=d
        prev=cur
    path=np.empty((max(0,bx+1),2),np.int32);n=0
    while bx>=0:
        path[n,0]=bx;path[n,1]=by;n+=1
        k=back[bx,by,bd]
        if k<0:break
        by-=bd-2;bx-=1;bd=k
    return path[:n][::-1].copy(),best,values

def predict(p,bonus=None,fixed=None,archive=None):
    audit=dict(decision='NO_NOTCH',stop='NO_NOTCH',events=[],trials=[],rejections={})
    m=dict(status='NO_NOTCH_BODY',tip=None,root=None,points=[],diagnostics=dict(dual=audit,candidates=[],pairs=[],selected=None))
    if p is None:return m
    score,seeds,coarse,reg,source=fields(p,fixed)
    path,total,values=global_free_end_dp(score,seeds,p.scale)
    org=np.asarray(p.origin)+[p.front,0]
    minimum=.040*p.scale
    stop='GLOBAL_MAX'
    if not len(path):stop='NO_REACHABLE_POSITIVE'
    elif total<=minimum:stop='INSUFFICIENT_TOTAL'
    elif path[-1,0]-path[0,0]<px(p.scale,.030):stop='SHORT_PATH'
    elif p.stage!='joint_dp':
        pts=path+[p.front,0]
        reject=topology.check(p.local,pts,p.front,p.scale,True)
        if reject=='CLOSED_RIM':stop=reject
    peak=(path[-1]+org).tolist() if len(path) else None
    audit.update(decision=source,stop=stop,front=int(org[0]),registration=reg,peak=peak,score=float(total),minimum=float(minimum),seeds=int(seeds.sum()))
    m['diagnostics']['coarse']=coarse
    if archive is not None:
        archive.update(origin=org,score=score.astype('float16'),value=values,path=path)
    if stop!='GLOBAL_MAX':m['status']=stop;return m
    pts=(path+org).tolist();root=pts[0];tip=pts[-1]
    trace=dict(first_loss=None,stop=stop,gate=source,reference=reg or {})
    m.update(status='VALID',tip=tip,root=root,points=pts)
    m['diagnostics'].update(selected=0,candidates=[dict(start=root,tip=tip,status='VALID',trace=trace)])
    return m
