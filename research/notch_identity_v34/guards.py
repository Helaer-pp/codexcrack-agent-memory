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
def inspect_track(arr,gray,sig,scale,start,distal,same_lip,skip_to,allowed):
    """Replay V3.1 provisional events before any point is admitted to competition."""
    gap=max(1,round(.014*scale));recover=max(1,round(.05*scale))
    span=max(2,round(.027*scale));near=round(.35*scale)
    weak=0;pending=-1;dark_gap=0
    events=[]  # start, recovery window start/end, extrapolation residual, width ratio, accepted
    for i in range(len(arr)):
        x=int(arr[i,0]);v=arr[i,2]
        if distal and x-start>near and i>=skip_to:
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
            good=ratio<=2.
            # Require a distinct, already visible rival line beside the original lip.
            # Curvature or a large tangent residual alone never vetoes a recovery.
            if good:
                xa=after[:,0].mean();ya=after[:,1].mean()
                ma=np.sum((after[:,0]-xa)*(after[:,1]-ya))/max(1.,np.sum((after[:,0]-xa)**2))
                rival=0
                for old in pre:
                    xx=int(old[0]);yc=int(round(ya+ma*(xx-xa)))
                    pad=max(1,round(.007*scale))
                    lo=max(0,yc-pad);hi=min(gray.shape[0],yc+pad+1)
                    if lo<hi and abs(yc-old[1])>max(wa,pad)*2:
                        peak=lo+np.argmax(sig[lo:hi,xx])
                        if sig[peak,xx]>=1.0 and abs(peak-old[1])>max(wa,pad)*2:
                            rival+=1
                # The far end of the recovery window may already merge with
                # the opposite lip. Check the entry level across the gap itself.
                level=int(round(np.median(after[:max(1,len(after)//2),1])))
                entry=0
                for j in range(pending-span,left+1):
                    xx=int(arr[j,0]);lo=max(0,level-pad);hi=min(gray.shape[0],level+pad+1)
                    if lo<hi and sig[lo:hi,xx].max()>=1.:
                        entry+=1
                distinct=abs(level-pre[:,1].mean())>2*max(wa,pad)
                existing=distinct and entry>=.85*(left+1-pending+span)
                good=rival<.70*len(pre) and not existing
        else:
            good=False
        accepted=good or not same_lip or int(arr[pending,0]) in allowed
        events.append((int(arr[pending,0]),int(arr[left,0]),x,residual,ratio,int(accepted)))
        if not accepted:return pending,3,events
        weak=0;pending=-1
    return len(arr),0,events


from research.notch_identity_v32.guards import open_rim, rebound_cut, taper_evidence
