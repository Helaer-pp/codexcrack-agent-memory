"""Local structural negatives for a tracked rim of an opening or closed bright island."""
import cv2
import numpy as np
from .detector import px


def check(raw,points,front,scale):
    pts=np.asarray(points,dtype=int)
    x,y=pts.T
    pad=px(scale,.10)
    left=max(0,min(x)-pad)
    right=min(raw.shape[1],max(x)+pad+1)
    top=max(0,min(y)-pad)
    bottom=min(raw.shape[0],max(y)+pad+1)
    patch=raw[top:bottom,left:right]
    material=float(np.percentile(patch,70))
    dark=float(np.median(raw[y,x]))
    # Segment at a relative intensity between the trace and adjacent material.
    mask=(patch<.5*(material+dark)).astype('uint8')
    contours,tree=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    if tree is not None:
        for contour,hierarchy in zip(contours,tree[0]):
            if hierarchy[3]<0:
                continue
            bx,by,bw,bh=cv2.boundingRect(contour)
            end_x=left+bx+bw-1
            if bw<.045*scale or bh<.018*scale or cv2.contourArea(contour)<.0005*scale**2:
                continue
            at_end=abs(x[-1]-end_x)<=.025*scale and top+by-.02*scale<=y[-1]<=top+by+bh+.02*scale
            if at_end and (x[0]<=end_x-bw/2):
                return 'CLOSED_RIM'
    # A short oblique taper of the thick body is not a distal thin valley.
    distance=cv2.distanceTransform(mask,cv2.DIST_L2,3)
    thickness=float(np.median(distance[y-top,x-left]))
    oblique=abs(y[-1]-y[0])>.55*max(1,x[-1]-x[0])
    if x[-1]-front<.055*scale and oblique and thickness>=.003*scale:
        return 'OPEN_BODY_RIM'
    return None

