"""Propagation of tangent and unsupported displacement for each direction state."""
import cv2
import numpy as np
from numba import njit
from research.notch_identity_v53.terminal import unwind


def displaced_trace(delta,scale,noise,span):
    # A nearby brightened ridge after registration is evidence for a displaced old line.
    radius=max(2,round(.065*scale))
    blue=cv2.blur(np.maximum(-delta.T,0),(2*max(1,round(.018*scale))+1,1))
    blue=cv2.dilate(blue,np.ones((2*radius+1,1),np.uint8)).T
    return np.ascontiguousarray(np.clip((blue-max(3*noise,.040*span))/max(.12*span,5*noise),0,1),dtype=np.float32)


@njit
def step(tangent,residual,gap,slope,dual,risk,scale):
    # Express duration and lateral excursion in units of the specimen feature scale.
    weak=not dual or risk>.28
    ds=1./max(1.,scale)
    if weak:
        gap+=1
        residual+=slope-tangent
    else:
        gap=max(0,gap-2)
        if not gap:residual=0.
        tangent+=(1.-np.exp(-ds/.04))*(slope-tangent)
    extent=gap*ds
    deviation=abs(residual)*ds
    bend=abs(np.arctan(slope)-np.arctan(tangent))
    # A missing observation alone is not positive evidence of a displaced scratch.
    cost=risk*min(1.,extent/.025)*(.8*bend+8.*max(0.,deviation/.010-1.))
    return tangent,residual,gap,cost


@njit
def lattice(field,seeds,scale,dual,risk,prune=False):
    w,h=field.shape
    future=np.zeros(w+1)
    if prune:
        for x in range(w-1,-1,-1):
            future[x]=max(0.,np.max(field[x])+future[x+1])
    prev=np.full((h,5),-np.inf,np.float32)
    back=np.full((w,h,5),-2,np.int8)
    state=np.zeros((h,5,3),np.float32)
    best=0.;bx=by=bd=-1
    low=h;high=-1
    reached=False
    for x in range(w):
        a=max(0,low-2);b=min(h,high+3)
        cur=np.full((h,5),-np.inf,np.float32)
        nxt=np.zeros_like(state)
        if x<seeds.shape[0]:
            for y in range(h):
                if seeds[x,y]:
                    a=min(a,y);b=max(b,y+1)
                    cur[y,2]=max(0.,field[x,y]);back[x,y,2]=-1
        low=h;high=-1
        floor=-(.105 if x<=.24*scale else .025)*scale
        for y in range(a,b):
            val=field[x,y]
            if not np.isfinite(val):continue
            for d in range(5):
                slope=d-2;py=y-slope
                if 0<=py<h:
                    for k in range(5):
                        if not np.isfinite(prev[py,k]):continue
                        estimate=prev[py,k]-.13*abs(slope)-.19*abs(d-k)+val
                        if estimate<=cur[y,d] or estimate<floor:continue
                        tan,res,gap,cost=step(state[py,k,0],state[py,k,1],int(state[py,k,2]),slope,dual[x,y],risk[x,y],scale)
                        value=estimate-cost
                        if value>cur[y,d] and value>=floor:
                            cur[y,d]=value;back[x,y,d]=k
                            nxt[y,d,0]=tan;nxt[y,d,1]=res;nxt[y,d,2]=gap
                if np.isfinite(cur[y,d]):
                    low=min(low,y);high=max(high,y)
                    if cur[y,d]>best:best=cur[y,d];bx=x;by=y;bd=d
                    if prune and cur[y,d]+future[x+1]+.001*(w-x)<best:
                        cur[y,d]=-np.inf
        if x>=w-48 and high>=0:reached=True
        prev=cur;state=nxt
        if high<0 and x+1>=seeds.shape[0]:break
    return unwind(back,bx,by,bd),best,reached


@njit
def transition_charges(path,dual,risk,scale):
    charges=np.zeros(len(path))
    tan=res=np.float32(0);gap=0
    for j in range(1,len(path)):
        x,y=path[j]
        tan1,res1,gap,cost=step(tan,res,gap,int(y-path[j-1,1]),dual[x,y],risk[x,y],scale)
        tan=np.float32(tan1);res=np.float32(res1);charges[j]=cost
    return charges
