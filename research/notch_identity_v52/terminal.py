"""Width-aware V5.1 net evidence and competing global/distal endpoints."""
from dataclasses import replace
import cv2
import numpy as np
from numba import njit
from research.notch_identity_v51 import terminal as baseline
from research.notch_identity_v31 import topology
from research.notch_identity_v31.detector import px

STAGES=('mouth_width','v5_2')

def prepare(raw,hint,scale,stage='v5_2'):
    if stage not in STAGES:raise ValueError(stage)
    scene=baseline.prepare(raw,hint,scale)
    if scene is not None:scene.stage=stage
    return scene

@njit
def band_width(mask):
    h,w=mask.shape
    result=np.zeros((h,w),np.int32)
    for x in range(w):
        y=0
        while y<h:
            if not mask[y,x]:
                y+=1
                continue
            start=y
            while y<h and mask[y,x]:y+=1
            result[start:y,x]=y-start
    return result

def fields(p,fixed):
    score,seeds,coarse,reg,source,stats=baseline.fields(replace(p,stage='v5_1'),fixed)
    if source!='JOINT':return score,seeds,coarse,reg,source,stats
    s=p.scale;front=p.front;n=min(len(score),px(s,.25)+1)
    g=p.local[:,front:front+n].astype(np.float32)
    dx,dy=reg['shift']
    # Inverse map into the same geometrically aligned reference used by V5.1.
    warped=cv2.warpAffine(fixed[p.sl],np.float32([[1,0,dx+front],[0,1,dy]]),(n,len(g)),
        flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
    d=np.where(np.isfinite(warped),warped-g,0.)
    d=cv2.GaussianBlur(d,(0,0),max(.40,.0025*s))
    floor=max(3*p.noise,.038*p.span)
    width=band_width(d>floor)
    radius=px(s,.012)
    def prominence(im):
        pad=cv2.copyMakeBorder(im,radius,radius,0,0,cv2.BORDER_REPLICATE)
        return np.maximum(0,im-np.maximum(pad[:-2*radius],pad[2*radius:]))
    crest=np.maximum(prominence(d),prominence(-g))/np.maximum(d,floor)
    wide=np.clip((width-.024*s)/(.015*s),0,1)
    flat=np.clip((.56-crest)/.36,0,1)
    taper=np.clip((.25-np.arange(n)/s)/.05,0,1)
    weight=wide*flat*taper
    original=score[:n].T
    reduction=weight*np.maximum(0,original-.015)
    original-=reduction
    stats.update(blob_pixels=int((weight>.5).sum()),max_blob_reduction=float(reduction.max()))
    return score,seeds,coarse,reg,source,stats

def extension_evidence(score,path,s):
    tail=path[path[:,0]>.19*s]
    if not len(tail):return dict(positive_extension=False,tail_length=0,net_mean=None,support=None,longest_run=0)
    slopes=np.diff(path[:,1],prepend=path[0,1])
    cost=.13*np.abs(slopes)+.19*np.abs(np.diff(slopes,prepend=0))
    evidence=score[tail[:,0],tail[:,1]]
    net=float((evidence-cost[-len(tail):]).mean())
    support=float(np.mean(evidence>.08))
    longest=run=0
    for v in evidence:
        run=run+1 if v>.08 else 0
        longest=max(longest,run)
    ok=len(tail)>=px(s,.035) and net>.075 and support>=.54 and longest>=px(s,.012)
    return dict(positive_extension=bool(ok),tail_length=len(tail),net_mean=net,support=support,longest_run=longest)

@njit
def two_peaks_dp(score,seeds,s,neck_credit=False):
    """Exact directional-state recurrence; no downstream restarts or terminal trimming."""
    w,h=score.shape;neg=-np.inf
    prev=np.full((h,5),neg,np.float32);back=np.full((w,h,5),-2,np.int8)
    values=np.full((w,h),neg,np.float32)
    best=0.;bx=by=bd=-1
    distant=0.;dx=dy=dd=-1
    low=h;high=-1
    for x in range(w):
        floor=-(.105 if neck_credit and x<=.24*s else .025)*s
        start=max(0,low-2);end=min(h,high+3)
        if x<seeds.shape[0]:
            for y in range(h):
                if seeds[x,y]:start=min(start,y);end=max(end,y+1)
        cur=np.full((h,5),neg,np.float32)
        # Precompute the best predecessor for each possible arrival slope.
        costs=np.full((h,5),neg,np.float64);args=np.full((h,5),-1,np.int8)
        for yy in range(low,high+1):
            for k in range(5):
                costs[yy,k]=prev[yy,k];args[yy,k]=k
            for d in range(1,5):
                k=args[yy,d-1]
                v=prev[yy,k]-.19*abs(d-k)
                if v>=costs[yy,d]:costs[yy,d]=v;args[yy,d]=k
            for d in range(3,-1,-1):
                k=args[yy,d+1]
                v=prev[yy,k]-.19*abs(d-k)
                if v>costs[yy,d]:costs[yy,d]=v;args[yy,d]=k
        low=h;high=-1
        for y in range(start,end):
            val=score[x,y]
            if x<seeds.shape[0] and seeds[x,y]:
                cur[y,2]=max(0.,val);back[x,y,2]=-1
            for d in range(5):
                yy=y-(d-2)
                if 0<=yy<h:
                    v=costs[yy,d]-.13*abs(d-2)+val
                    if v>cur[y,d] and v>=floor:
                        cur[y,d]=v;back[x,y,d]=args[yy,d]
                v=cur[y,d]
                if v>values[x,y]:values[x,y]=v
                if v>best:best=v;bx=x;by=y;bd=d
                if x>.20*s and v>distant:distant=v;dx=x;dy=y;dd=d
            if values[x,y]>neg:low=min(low,y);high=max(high,y)
        if high<0 and x+1>=seeds.shape[0]:break
        prev=cur
    return unwind(back,bx,by,bd),best,values,unwind(back,dx,dy,dd),distant

@njit
def unwind(back,bx,by,bd):
    path=np.empty((max(0,bx+1),2),np.int32);n=0
    while bx>=0:
        path[n,0]=bx;path[n,1]=by;n+=1
        k=back[bx,by,bd]
        if k<0:break
        by-=bd-2;bx-=1;bd=k
    return path[:n][::-1].copy()

def global_free_end_dp(score,seeds,s,neck_credit=False):
    path,total,values,_,_=two_peaks_dp(score,seeds,s,neck_credit)
    return path,total,values

def predict(p,bonus=None,fixed=None,archive=None):
    audit=dict(decision='NO_NOTCH',stop='NO_NOTCH',events=[],trials=[],rejections={})
    m=dict(status='NO_NOTCH_BODY',tip=None,root=None,points=[],diagnostics=dict(dual=audit,candidates=[],pairs=[],selected=None))
    if p is None:return m
    score,seeds,coarse,reg,source,stats=fields(p,fixed)
    path,total,values,distal,dscore=two_peaks_dp(score,seeds,p.scale,source=='JOINT')
    global_path=path;global_score=total
    diagnostics=extension_evidence(score,distal,p.scale)
    pick='GLOBAL'
    if (p.stage=='v5_2' and source=='JOINT' and len(path) and len(distal)
            and path[-1,0]<=.19*p.scale and distal[-1,0]-path[-1,0]>=.045*p.scale
            and total>.040*p.scale and dscore>.052*p.scale and diagnostics['positive_extension']):
        if topology.check(p.local,distal+[p.front,0],p.front,p.scale,True)!='CLOSED_RIM':
            path=distal;total=dscore;pick='DISTAL'
    org=np.asarray(p.origin)+[p.front,0]
    for label,track,value in [('global',global_path,global_score),('distal',distal,dscore)]:
        audit[label+'_tip']=(track[-1]+org).tolist() if len(track) else None
        audit[label+'_score']=float(value) if len(track) else None
    audit.update(pick=pick,**diagnostics)
    minimum=.040*p.scale
    stop='ACCEPTED_PEAK'
    if not len(path):stop='NO_REACHABLE_POSITIVE'
    elif total<=minimum:stop='INSUFFICIENT_TOTAL'
    elif path[-1,0]-path[0,0]<px(p.scale,.030):stop='SHORT_PATH'
    else:
        pts=path+[p.front,0]
        reject=topology.check(p.local,pts,p.front,p.scale,True)
        if reject=='CLOSED_RIM':stop=reject
    if source=='PREEXISTING_CHECK':
        streak=longest=0
        for x,y in path:
            if x>.20*p.scale:break
            streak=streak+1 if score[x,y]>.10 and x>.015*p.scale else 0
            longest=max(streak,longest)
        stats['strong_run']=longest
        if longest<px(p.scale,.035) or stop!='ACCEPTED_PEAK':stop='NO_CONFIRMED_PREEXISTING'
    peak=(path[-1]+org).tolist() if len(path) else None
    audit.update(decision=source,stop=stop,front=int(org[0]),registration=reg,peak=peak,score=float(total),minimum=float(minimum),seeds=int(seeds.sum()),**stats)
    m['diagnostics']['coarse']=coarse
    if archive is not None:
        archive.update(origin=org,score=score.astype('float16'),value=values,path=path)
    if stop!='ACCEPTED_PEAK':m['status']='no_tip' if stop=='NO_CONFIRMED_PREEXISTING' else stop;return m
    pts=(path+org).tolist();root=pts[0];tip=pts[-1]
    trace=dict(first_loss=None,stop=stop,gate=source,reference=reg or {})
    m.update(status='VALID',tip=tip,root=root,points=pts)
    m['diagnostics'].update(selected=0,candidates=[dict(start=root,tip=tip,status='VALID',trace=trace)])
    return m
