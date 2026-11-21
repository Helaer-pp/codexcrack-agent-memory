"""Locate the upstream notch inside a reference-defined material strip, in sensor pixels."""
import cv2
import numpy as np


def material(raw, fixed, current_hint, reference_hint, scale):
    """The supplied image domain may already be an operator-defined specimen window."""
    h,w=raw.shape
    x,y=np.rint(reference_hint).astype(int)
    l=max(0,min(w-8,x+round(.45*scale)))
    r=max(l+1,min(w,x+round(1.8*scale)))
    sample=fixed[:,l:r:3]
    profile=np.median(sample,axis=1)
    lo,hi=np.percentile(fixed[::3,::5],(3,85))
    illuminated=profile>lo+.43*(hi-lo)
    edges=np.flatnonzero(np.diff(np.r_[False,illuminated,False]))
    runs=[(a,b) for a,b in zip(edges[::2],edges[1::2]) if b-a>=16]
    if not runs:return None
    a,b=min(runs,key=lambda v:max(v[0]-y,y-v[1]+1,0))
    dy=int(round(current_hint[1]-reference_hint[1]))
    top=max(0,a,a+dy);bottom=min(h,b,b+dy)
    if bottom-top<12:return None
    return int(top),int(bottom)


def apex(raw,hint,scale):
    h,w=raw.shape
    x,y=np.rint(hint).astype(int)
    l=max(0,x-round(.85*scale));r=min(w,x+round(1.0*scale))
    if r-l<10:return None
    view=raw[:,l:r]
    low,high=np.percentile(view[::2,::2],(3,84))
    mask=(view<low+.29*(high-low)).astype('uint8')
    opened=cv2.morphologyEx(mask,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
    n,cc,stats,_=cv2.connectedComponentsWithStats(opened)
    candidates=[]
    for k in range(1,n):
        xx,yy,width,height,area=stats[k]
        if xx>2 or width<8 or xx+width>=view.shape[1]-1 or area<40:continue
        right=xx+width-1;ys=np.flatnonzero(cc[:,right]==k)
        cy=float(np.median(ys))
        if min(cy,h-1-cy)<3:continue
        candidates.append((abs(cy-y),[int(l+right),int(round(cy))]))
    return min(candidates)[1] if candidates else None
