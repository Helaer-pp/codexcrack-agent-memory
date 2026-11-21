"""Measure a reference-notch aperture in native pixels after the silhouette is located."""
import cv2
import numpy as np
from dataclasses import dataclass
from research.notch_identity_v51.terminal import Scene


@dataclass
class PhysicalScene(Scene):
    aperture: float
    quiet: bool
    residual: float
    route_floor: float


def measure(ref,tip):
    x,y=tip
    roi=ref[max(0,y-64):y+65,max(0,x-8):x+33]
    low,high=np.percentile(roi,(8,85))
    cut=low+.30*(high-low)
    values=[]
    for back in (2,4,6):
        dark=ref[:,max(0,x-back)]<cut
        edges=np.flatnonzero(np.diff(np.r_[False,dark,False]))
        runs=[b-a for a,b in zip(edges[::2],edges[1::2]) if a-2<=y<b+2]
        if runs:values.append(max(runs))
    # Bounded aperture prevents the entire black clamp becoming a filter radius.
    aperture=float(np.clip(np.median(values) if values else 4.,4.,32.))
    return aperture,float(np.clip(aperture*15.,64.,384.))


def quiet_mouth(raw,ref,tip,rtip,scale):
    radius=max(5,round(.055*scale))
    half=min(radius,tip[1],rtip[1],len(raw)-1-tip[1],len(ref)-1-rtip[1])
    width=min(round(.13*scale),raw.shape[1]-tip[0],ref.shape[1]-rtip[0])
    if half<4 or width<8:return False,255.,0.
    def patch(im,pt):
        x,y=pt
        a=im[y-half:y+half+1,x:x+width].astype(np.float32)
        return cv2.GaussianBlur(a,(3,3),.75)
    a,b=patch(raw,tip),patch(ref,rtip)
    core=a[2:-2,2:-2]
    best=255.
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            diff=b[2+dy:2+dy+len(core),2+dx:2+dx+core.shape[1]]-core
            best=min(best,float(np.percentile(abs(diff-np.median(diff)),95)))
    floor=max(4.,.035*float(np.ptp(b)),3.*float(np.median(abs(a-cv2.medianBlur(a,3)))))
    return best<=floor,best,floor
