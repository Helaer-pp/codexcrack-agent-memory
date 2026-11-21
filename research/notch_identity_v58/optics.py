"""Pixel measurements in the notch neighbourhood, independent of the anchor separation."""
import cv2
import numpy as np
from numba import njit
from research.notch_identity_v54 import terminal as base


def prepare_optical(raw,hint):
    initial=base.prepare(raw,hint,288.)
    if initial is None:
        return None
    x,y=np.asarray(initial.starts[0])+initial.origin
    widths=[]
    for dx in (22,24,26):
        side=raw[max(0,y-72):y+73,max(0,x-dx)]
        edges=np.flatnonzero(np.diff(np.r_[False,side<initial.black+.28*initial.span,False]))
        mid=min(72,y)
        runs=[b-a for a,b in zip(edges[::2],edges[1::2]) if a<=mid+3 and b>=mid-3]
        widths.append(max(runs,default=0))
    width=np.median(widths)
    unit=144. if 0<width<26 else 576. if width>44 else 288.
    return initial if unit==288. else base.prepare(raw,hint,unit)


def align(p,fixed):
    x,y=np.asarray(p.starts[0])+p.origin
    l,r=max(0,x-46),min(p.raw.shape[1],x+19)
    t,b=max(0,y-26),min(len(p.raw),y+27)
    patch=p.raw[t:b,l:r].astype('float32')
    x0,y0=max(0,l-64),max(0,t-64)
    search=fixed[y0:b+64,x0:r+64].astype('float32')
    if min(patch.shape)<4 or np.std(patch)<1. or not np.isfinite(search).all():
        return fixed.astype('float32'),[0,0],None,dict(rows=[0,1],offsets=[[0,0],[0,0]])
    corr=cv2.matchTemplate(search,patch,cv2.TM_CCOEFF_NORMED)
    _,quality,_,pos=cv2.minMaxLoc(corr)
    dx,dy=(x0+pos[0]-l,y0+pos[1]-t) if quality>=.65 else (0,0)
    # Observe remote material on both sides. The opening silhouette itself may move with load.
    flanks=[]
    step=max(18,min(90,round(.25*p.scale)))
    rad=max(9,min(30,round(.095*p.scale)))
    for side in (-1,1):
        cy=y+side*step
        estimates=[]
        for offset in (-rad,2*rad,6*rad):
            cx=x+offset
            if (cy-rad<0 or cx-rad<0 or cy+rad>=len(p.raw) or cx+rad>=p.raw.shape[1]
                or cy+dy-rad-8<0 or cx+dx-rad-8<0 or cy+dy+rad+8>=len(fixed) or cx+dx+rad+8>=fixed.shape[1]):continue
            tile=p.raw[cy-rad:cy+rad+1,cx-rad:cx+rad+1].astype('float32')
            if np.std(tile)<2.:continue
            bank=fixed[cy+dy-rad-8:cy+dy+rad+9,cx+dx-rad-8:cx+dx+rad+9].astype('float32')
            response=cv2.matchTemplate(bank,tile,cv2.TM_CCOEFF_NORMED)
            _,q,_,(ix,iy)=cv2.minMaxLoc(response)
            if q<.34 or min(ix,iy)<1 or max(ix,iy)>=16:continue
            def sub(a,b,c):
                return float(np.clip(.5*(a-c)/min(-1e-5,a-2*b+c),-.5,.5))
            estimates.append([dx+ix-8+sub(response[iy,ix-1],q,response[iy,ix+1]),
                              dy+iy-8+sub(response[iy-1,ix],q,response[iy+1,ix])])
        if len(estimates)>=2 and np.max(np.ptp(estimates,axis=0))<4:
            flanks.append(np.median(estimates,axis=0))
    mapping=dict(rows=[int(y-step),int(y+step)],offsets=[list(v) for v in flanks] if len(flanks)==2 else [[dx,dy],[dx,dy]])
    result=remap(fixed,mapping)
    return result,[dx,dy],quality,mapping


def remap(image,mapping):
    h,w=image.shape
    rows=mapping['rows'];off=np.asarray(mapping['offsets'])
    y=np.arange(h,dtype='float32')
    dx=np.interp(y,rows,off[:,0]).astype('float32')
    dy=np.interp(y,rows,off[:,1]).astype('float32')
    mx=np.arange(w,dtype='float32')[None,:]+dx[:,None]
    my=np.broadcast_to((y+dy)[:,None],(h,w))
    return cv2.remap(image.astype('float32'),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)


@njit
def measure(gray,delta,threshold,offsets):
    h,w=gray.shape
    dark=np.zeros((h,w),np.float32)
    ridge=np.zeros_like(dark)
    dipole=np.zeros((h,w),np.bool_)
    for y in range(h):
        for x in range(w):
            center=delta[y,x]
            if center<=.60*threshold:continue
            for tangent,dx,dy in offsets:
                front=delta[min(h-1,max(0,y+tangent)),min(w-1,x+2)]
                rear=delta[min(h-1,max(0,y-tangent)),max(0,x-2)]
                signal=.25*(2*center+front+rear)
                if signal<=threshold:continue
                yp,ym=min(h-1,y+dy),max(0,y-dy)
                xp,xm=min(w-1,max(0,x+dx)),min(w-1,max(0,x-dx))
                side=-1e9
                blue=1e9
                for sign in (-1,1):
                    for factor in (1,2):
                        sy=max(0,min(h-1,y+sign*dy*factor))
                        sx=max(0,min(w-1,x+sign*dx*factor))
                        flank=.25*(2*delta[sy,sx]+delta[min(h-1,max(0,sy+tangent)),min(w-1,sx+2)]+delta[min(h-1,max(0,sy-tangent)),max(0,sx-2)])
                        if factor==1:side=max(side,flank)
                        else:blue=min(blue,flank)
                raw=min(gray[yp,xp],gray[ym,xm])-gray[y,x]
                dark[y,x]=max(dark[y,x],raw)
                prom=signal-side
                if signal>1.25*threshold and prom>.28*signal:
                    ridge[y,x]=max(ridge[y,x],prom/threshold)
                if blue < -threshold and -blue>.48*signal:dipole[y,x]=True
    return dark,ridge,dipole


OFFSETS=np.array([(round(2*s),round(-r*s/np.hypot(1,s)),max(1,round(r/np.hypot(1,s))))
                  for s in (-.70,-.34,0.,.34,.70) for r in (1,2,4,7)],np.int32)
