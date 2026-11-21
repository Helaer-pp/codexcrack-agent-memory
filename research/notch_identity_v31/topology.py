import cv2
import numpy as np
from research.notch_identity_v3.topology import check as original
from .detector import px


def check(raw,points,front,scale,adaptive):
    reason=original(raw,points,front,scale)
    if reason or not adaptive:
        return reason
    x,y=np.asarray(points,int).T
    pad=px(scale,.1)
    left=max(0,x[0]-pad);top=max(0,y.min()-pad)
    patch=raw[top:y.max()+pad+1,left:x[-1]+pad+1]
    background=float(np.percentile(patch,75))
    ink=float(np.median(raw[y,x]))
    mask=(patch<background-.30*(background-ink)).astype(np.uint8)
    # Close resampling holes before measuring the enclosed island.
    r=px(scale,.004)
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel)
    contours,tree=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    for c,h in zip(contours,tree[0] if tree is not None else []):
        if h[3]<0 or cv2.contourArea(c)/scale**2<.00045:
            continue
        bx,by,bw,bh=cv2.boundingRect(c)
        if bw/scale>.045 and bh/scale>.014 and abs(left+bx+bw-1-x[-1])<.033*scale and top+by-.025*scale<=y[-1]<=top+by+bh+.025*scale:
            return 'CLOSED_RIM'
    dx=max(1,x[-1]-x[0])
    if (x[-1]-front)/scale<.06 and abs(y[-1]-y[0])/dx>.65:
        if np.mean(raw[y,x]<background-.65*(background-ink))>.8:
            return 'OPEN_TAPER_RIM'
    return None

