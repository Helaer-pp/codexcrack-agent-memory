"""Observable bright-gap, tangent, cross-section and aperture tests in ROI coordinates."""
import math
import numpy as np
from numba import njit
from research.notch_identity_v31.detector import px

@njit(cache=False)
def width(gray,x,y,r):
    lo=max(0,y-r);hi=min(gray.shape[0]-1,y+r)
    center=float(gray[y,x])
    half=(center+min(float(gray[lo,x]),float(gray[hi,x])))/2
    a=y;b=y
    while a>lo and gray[a-1,x]<=half:a-=1
    while b<hi and gray[b+1,x]<=half:b+=1
    return b-a+1

@njit(cache=False)
def inspect_track(arr,gray,scale,start,distal,same_lip):
    """Replay V3.1 provisional events before any point is admitted to competition."""
    gap=max(1,round(.014*scale));recover=max(1,round(.05*scale))
    span=max(2,round(.027*scale));near=round(.35*scale)
    weak=0;pending=-1;dark_gap=0
    events=[]  # start, recovery window start/end, extrapolation residual, width ratio, accepted
    for i in range(len(arr)):
        x=int(arr[i,0]);v=arr[i,2]
        if distal and x-start>near:
            dark_gap=dark_gap+1 if v<.85 else 0
            if dark_gap>=gap:return i-dark_gap+1,1,events
            # Evaluate shorter weak intervals after downstream direction becomes measurable.
            if i>=3*span:
                k=i-span
                if arr[k,2]<.85 and arr[k-1,2]<1. and arr[k-span,0]-start>near:
                    m1=(arr[k-1,1]-arr[k-span,1])/max(1,span-1)
                    m2=(arr[i,1]-arr[k+1,1])/max(1,span-1)
                    if abs(math.atan(m2)-math.atan(m1))>math.radians(22):
                        return k-1,2,events
        weak=0 if v>=.8 else weak+1
        if weak>=gap and pending<0:pending=i-weak+1
        if pending<0 or i-pending+1<gap+recover:continue
        left=i-recover+1
        if v<1 or np.minimum(4.,arr[left:i+1,2]).mean()<1.05 or (arr[left:i+1,2]>=1).mean()<.8:continue
        good=True;residual=-1.;ratio=-1.
        if pending>=span+1:
            pre=arr[pending-span:pending]
            after=arr[left:i+1]
            xm=pre[:,0].mean();ym=pre[:,1].mean()
            slope=np.sum((pre[:,0]-xm)*(pre[:,1]-ym))/max(1.,np.sum((pre[:,0]-xm)**2))
            residual=np.median(np.abs(after[:,1]-(ym+slope*(after[:,0]-xm))))
            rad=max(1,round(.023*scale))
            wa=np.median(np.array([width(gray,int(vv[0]),int(vv[1]),rad) for vv in pre]))
            wb=np.median(np.array([width(gray,int(vv[0]),int(vv[1]),rad) for vv in after]))
            ratio=max(wa,wb)/max(1.,min(wa,wb))
            good=residual<=max(1.,.012*scale) and ratio<=2.
        else:
            good=False
        accepted=good or not same_lip
        events.append((int(arr[pending,0]),int(arr[left,0]),x,residual,ratio,int(accepted)))
        if not accepted:return pending,3,events
        weak=0;pending=-1
    return len(arr),0,events

def taper_evidence(xx,yy,depth,i,front,mad,noise,scale):
    win=px(scale,.021)
    if i+1<3*win:return False,{}
    blocks=np.median(depth[i-3*win+1:i+1].reshape(3,win),axis=1)
    tail=blocks[-1]
    # Tolerate shot noise, but exclude a robust secondary valley-depth peak.
    decay=blocks[0]>=tail and np.all(np.diff(blocks)<=max(noise,.10*blocks[0]))
    y=yy[i-3*win+1:i+1]
    angles=np.arctan((y[win-1::win]-y[::win])/max(1,win-1))
    turn=float(np.rad2deg(abs(angles[-1]-np.median(angles[:2]))))
    clear=front<=1.5*noise and tail>=3*max(front,noise) and mad<=2.5*noise
    return bool(clear and decay and turn<=18),dict(clear=bool(clear),decay=bool(decay),angle=turn)

def rebound_cut(depth,noise,scale):
    # Require a body-to-floor fade followed by a renewed and sustained dark segment.
    # Only operate in the terminal neighborhood; isolated weak texture is not decisive.
    win=px(scale,.017)
    if len(depth)<5*win:return len(depth)
    lo=max(3*win,len(depth)-px(scale,.18))
    for k in range(lo,len(depth)-2*win):
        if depth[k]>2*noise:continue
        valley=np.median(depth[k:k+win])
        before=np.median(depth[k-2*win:k-win]);after=np.median(depth[k+win:k+2*win])
        # A subpixel fade may have only one trough column after resampling.
        # Confirm the preceding trend and both subsequent blocks of resurgence.
        earlier=np.median(depth[k-3*win:k-2*win])
        next_block=np.median(depth[k:k+2])
        later=np.median(depth[k+win//2+1:k+win+2])
        if (win<=2 and earlier>before>2.5*max(depth[k],noise) and next_block<=2.5*noise and
            later>max(3*noise,2*depth[k]) and after>max(3*noise,2*depth[k])):
            return k
        if valley<=2*noise and before>max(4*noise,2.5*valley) and after>max(4*noise,2.5*valley):
            return k
    return len(depth)

def open_rim(points,front,mid_y,scale,gray):
    pts=np.asarray(points)
    if len(pts)<2:return False
    x,y=pts.T
    drift=y[-1]-y[0];offset=y[0]-mid_y
    return bool((x[-1]-front)/scale<.06 and abs(offset)>max(px(scale,.012),2*width(gray,x[0],y[0],px(scale,.02))) and
                drift*offset>0 and abs(drift)/max(1,x[-1]-x[0])>.45)
