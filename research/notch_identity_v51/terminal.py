"""Signed ridge evidence and single-pass, free-endpoint maximum-score path."""
from dataclasses import dataclass
import cv2
import numpy as np
from numba import njit
from research.notch_identity_v31.detector import locate_root,px
from research.notch_identity_v31 import topology
from research.notch_identity_v40.evidence import registered

STAGES=('neck_fusion','zero_gate','v5_1')

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

def prepare(raw,hint,scale,stage='v5_1'):
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
    uniform=float(uniform)
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
    if p.stage=='v5_1':
        # Clip the background floor, raise the zero crossing and retain dynamic range for deep lines.
        base=np.maximum(tau, np.maximum(.033*p.span,3.8*p.noise))
        raw_score=np.maximum(-.56,2.45*np.tanh(depth/(2*base))-1.46)
    lateral=abs(np.arange(len(g))-int(np.median(np.array(p.starts)[:,1])))>.12*s
    sample=raw_score[lateral,p.front+px(s,.04)::4]
    stats={'background_raw':float(sample.mean()) if sample.size else None}
    score=raw_score.copy();coarse=reg=None;source='RAW_ONLY'
    if fixed is not None:
        args=(p.sl,p.origin,p.starts,None,None,s,p.front,p.local,p.noise,None,p.raw,p.span)
        coarse,reg,aligned=registered(args,fixed)
        if aligned is not None:
            valid=np.isfinite(aligned);f=np.where(valid,aligned,g);d=f-g
            adequate=valid.mean()>.65 and (reg.get('status')=='OK' or (coarse or {}).get('status')=='OK')
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
                # A neighbouring static valley may start several columns beyond the active crack.
                # Retain displacement tolerance but require column overlap for a full static penalty.
                column_prior=cv2.dilate(coherent,np.ones((2*reach+1,3),np.uint8))
                overlap=np.clip(column_prior/np.maximum(prior,p.noise),0,1)
                risk*=.30+.70*overlap
                diff_tau=np.maximum(2.45*p.noise+.007*p.span,2*cv2.blur(inc,(size,size)))
                delta_score=2.1*np.tanh(inc/(2*diff_tau))-.97
                distance=np.maximum(0,np.arange(g.shape[1],dtype=np.float32)-p.front)
                # Reference valleys overlap the open notch at the birth; ramp to full strength in material.
                prior_weight=np.clip((distance-.04*s)/(.14*s),0.,1.)
                background=delta_score[lateral,p.front+px(s,.04)::4]
                stats['background_diff']=float(background.mean()) if background.size else None
                fused=(.90-.47*prior_weight)*raw_score+(.10+.47*prior_weight)*delta_score-1.38*risk*prior_weight
                neck=(1-prior_weight)
                strong=np.clip((delta_score-.32)/.42,0,1)*(1-risk*prior_weight)
                # Preserve the original distal joint score where there is visible current-image evidence.
                visible=depth>=np.maximum(1.35*p.noise,.007*p.span)
                legacy_raw=2.1*np.tanh(depth/(2*tau))-.97
                if p.stage=='v5_1':
                    fused+=.43*prior_weight*np.maximum(0,legacy_raw-raw_score)*np.clip((delta_score+.2)/.65,0,1)
                fused=np.maximum(fused,neck*np.maximum(raw_score,.93*delta_score)-.16-1.38*risk*prior_weight-(1-neck)*2.5)
                # Disconnected point texture in the far field has a strong instantaneous peak but little longitudinal support.
                line=cv2.morphologyEx(inc,cv2.MORPH_OPEN,np.ones((1,2*px(s,.011)+1),np.uint8))
                corr=np.clip(line/np.maximum(inc,p.noise),0,1)
                far=np.clip((distance-.25*s)/(.12*s),0,1)
                fused=np.maximum(fused,np.where(strong>.55,.90*delta_score-1.2*risk,-2.5))
                middle=cv2.blur(g,(2*px(s,.026)+1,2*px(s,.026)+1))
                broad_gray=cv2.blur(g,(2*px(s,.085)+1,2*px(s,.085)+1))
                flank=np.abs(middle[lateral,p.front+px(s,.06)::5]-broad_gray[lateral,p.front+px(s,.06)::5])
                rough=float(np.quantile(flank,.90))/p.span if flank.size else 1.
                smooth_material=float(np.clip((.0080-rough)/.0025,0,1))
                clean=float(np.clip((.028*p.span-p.noise)/(.015*p.span),0,1))
                # Measure relative valley depth before the lip responses saturate in tanh.
                birth=np.clip(1-distance/(.24*s),0,1)
                prominence=np.clip((depth/np.maximum(.16*p.span,6*p.noise)-.85),-.50,1.6)
                fused+=1.15*birth*prominence
                near_raw=raw_score-(2.2+1.2*risk)*np.clip((distance-.15*s)/(.12*s),0,1)
                fused=np.maximum(fused,near_raw)
                reach=px(s,.032)
                # Join strong observations on both sides of a short gap along the same local tangent.
                neck_end=min(g.shape[1],p.front+px(s,.26))
                stem=np.minimum(depth[:,:neck_end],inc[:,:neck_end])*(1-risk[:,:neck_end]*prior_weight[:neck_end])
                stem=cv2.dilate(stem,np.ones((2*px(s,.003)+1,1),np.uint8))
                bridged=np.zeros_like(stem)
                for slope in (-.16,0.,.16):
                    dy=round(reach*slope);k=np.zeros((2*abs(dy)+1,2*reach+1),np.uint8)
                    cv2.line(k,(0,abs(dy)-dy),(2*reach,abs(dy)+dy),1)
                    bridged=np.maximum(bridged,cv2.morphologyEx(stem,cv2.MORPH_CLOSE,k))
                bridge=np.zeros_like(depth,dtype=bool)
                bridge[:,:neck_end]=(bridged>max(.17*p.span,7*p.noise))&(stem<.6*bridged)
                fused=np.maximum(fused,np.where(bridge,.66,-2.5))
                # On smooth material, disconnected spots can mimic a weak fade after the true tip.
                ink=bilateral(d,s)
                continuous=np.maximum.reduce([cv2.morphologyEx(ink,cv2.MORPH_OPEN,k) for k in kernels])
                strength=np.clip((.21*p.span-inc)/(.10*p.span),0,1)
                width=2*px(s,.013)+1
                averaged=cv2.blur(d,(width,1))
                slow=bilateral(averaged,s)*np.clip(1-neg/np.maximum(pos,p.noise),0,1)
                slow_base=max(2.4*p.noise/np.sqrt(width),.025*p.span)
                sustained=(slow>slow_base)&(averaged>slow_base)&(risk<.35)&(depth>.55*p.noise)
                lift=np.clip(slow/slow_base-1,0,.75)*(1-clean)
                fused=np.maximum(fused,np.where(sustained & (far>.5),lift-.14,-2.5))
                penalty=1.65*far*clean*smooth_material*strength*np.clip(1-continuous/np.maximum(inc,p.noise),0,1)
                fused-=penalty+.40*far*clean*smooth_material*strength*(1-corr)
                if smooth_material>.05:
                    # A taper keeps a transverse gradient; repeated dots also vary along the axis.
                    sm=cv2.GaussianBlur(d,(0,0),sigmaX=max(.65,.0045*s))
                    gx=cv2.Sobel(sm,-1,1,0);gy=cv2.Sobel(sm,-1,0,1)
                    box=(2*px(s,.020)+1,2*px(s,.009)+1)
                    ratio=cv2.blur(gx*gx,box)/np.maximum(cv2.blur(gy*gy,box),.01*p.noise**2)
                    dot=np.clip((ratio-.20)/.40,0,1)
                    faded=np.clip(1-ratio/.60,0,1)*np.clip(slow/(.60*slow_base),0,1)
                    supported=(averaged>p.noise)&(depth>.4*p.noise)&(risk<.40)&(far>.5)
                    fused=np.maximum(fused,np.where(supported,.9*faded-.34,-2.5))
                    fused-=1.55*smooth_material*far*strength*dot
                    # A displaced scratch can remain unipolar locally, even in smooth material.
                    fused-=.45*smooth_material*far*risk*overlap
                    # An existing displaced line redistributes darkness across the normal;
                    # a superposed new crack adds integrated darkness even beside that line.
                    radius=px(s,.045);box_mass=(2*px(s,.012)+1,2*radius+1)
                    residual=d-cv2.blur(d,(2*px(s,.08)+1,2*px(s,.08)+1))
                    mass=cv2.blur(residual,box_mass)
                    strength_sum=cv2.blur(np.abs(residual),box_mass)
                    imbalance=np.clip(mass/np.maximum(strength_sum,.50*p.noise),0,1)
                    added=np.clip((imbalance-.07)/.26,0,1)
                    joined=np.minimum(raw_score,delta_score)+.26*added-.62*(1-added)
                    recover=(risk>.20)&(far>.5)&(added>.30)&(slow>.7*slow_base)&(ratio<.55)
                    fused=np.maximum(fused,np.where(recover,joined,-2.5))
                fused=np.where(visible|(strong>.55)|bridge|(sustained & (far>.5)),fused,np.minimum(fused,-.8))
                # Contiguous new dark ridges are needed when the registered views differ only by sensor noise.
                if adequate and np.quantile(np.abs(d[valid][::8]),.95)<max(4*p.noise,.025*p.span):
                    width=max(1,px(s,.035))
                    near=strong[:,p.front:p.front+px(s,.30)]
                    if near.size and cv2.blur(near,(width,1)).max()<.40:
                        source='NO_INCREMENT'
                if source!='NO_INCREMENT':score=np.where(valid,fused,raw_score);source='JOINT'
            else:source='NO_INCREMENT' if adequate else 'UNREGISTERED_RAW'
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
    if source=='NO_INCREMENT' and p.stage!='neck_fusion':
        strong_depth=np.maximum(5.5*p.noise,.105*p.span)
        score=np.where(depth>=strong_depth,raw_score,np.minimum(raw_score,-.55))
        stats['strong_floor']=float(strong_depth)
        source='PREEXISTING_CHECK'
    return np.ascontiguousarray(score[:,f:].T,dtype=np.float32),np.ascontiguousarray(seeds.T),coarse,reg,source,stats

@njit
def global_free_end_dp(score,seeds,s,neck_credit=False):
    """Exact directional-state recurrence; no downstream restarts or terminal trimming."""
    w,h=score.shape;neg=-np.inf
    prev=np.full((h,5),neg,np.float32);back=np.full((w,h,5),-2,np.int8)
    values=np.full((w,h),neg,np.float32)
    best=0.;bx=by=bd=-1
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
            if values[x,y]>neg:low=min(low,y);high=max(high,y)
        if high<0 and x+1>=seeds.shape[0]:break
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
    score,seeds,coarse,reg,source,stats=fields(p,fixed)
    path,total,values=global_free_end_dp(score,seeds,p.scale,source=='JOINT')
    org=np.asarray(p.origin)+[p.front,0]
    minimum=.040*p.scale
    stop='GLOBAL_MAX'
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
        if longest<px(p.scale,.035) or stop!='GLOBAL_MAX':stop='NO_CONFIRMED_PREEXISTING'
    peak=(path[-1]+org).tolist() if len(path) else None
    audit.update(decision=source,stop=stop,front=int(org[0]),registration=reg,peak=peak,score=float(total),minimum=float(minimum),seeds=int(seeds.sum()),**stats)
    m['diagnostics']['coarse']=coarse
    if archive is not None:
        archive.update(origin=org,score=score.astype('float16'),value=values,path=path)
    if stop!='GLOBAL_MAX':m['status']='no_tip' if stop=='NO_CONFIRMED_PREEXISTING' else stop;return m
    pts=(path+org).tolist();root=pts[0];tip=pts[-1]
    trace=dict(first_loss=None,stop=stop,gate=source,reference=reg or {})
    m.update(status='VALID',tip=tip,root=root,points=pts)
    m['diagnostics'].update(selected=0,candidates=[dict(start=root,tip=tip,status='VALID',trace=trace)])
    return m
