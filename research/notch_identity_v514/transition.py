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
    weak=not dual or risk>.28
    if weak:
        gap+=1
        residual+=slope-tangent
    else:
        gap=max(0,gap-2)
        residual=.7*(residual+slope-tangent) if gap else 0.
    angle=abs(slope-tangent)
    weight=min(1.,gap/max(2.,.025*scale))
    cost=weight*(.22*angle + (1.1+5.*risk)*max(0.,abs(residual)-.009*scale)/max(1.,.014*scale))
    # Geometrically displaced, reference-supported strokes cannot buy back large transverse jumps.
    if risk>.4 and abs(residual)>.032*scale and gap>.028*scale:cost=np.inf
    if not weak:tangent=.85*tangent+.15*slope
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
        prev=cur;state=nxt
        if high<0 and x+1>=seeds.shape[0]:break
    return unwind(back,bx,by,bd),best,bx>=w-48


def tail_cost(scene,path):
    gray=scene.local[:,scene.front:]
    x,y=path.T
    radius=max(2,round(.018*scene.scale))
    def valley(r):
        return np.maximum(0,np.minimum(gray[np.clip(y-r,0,len(gray)-1),x].astype(float),
                       gray[np.clip(y+r,0,len(gray)-1),x])-gray[y,x])
    narrow=valley(max(1,radius//2));broad=valley(radius)
    depth=np.minimum(narrow,broad)
    # A causal peak in the preceding stem gives a photometrically local reference.
    span=max(4,round(.085*scene.scale))
    past=cv2.dilate(depth.reshape(1,-1),np.ones((1,span),np.uint8),anchor=(span-1,0)).ravel()
    sharp=narrow/np.maximum(broad,2*scene.noise)
    fade=np.clip((.58-depth/np.maximum(past,4*scene.noise))/.38,0,1)
    shallow=np.clip((.70-sharp)/.42,0,1)
    weak=np.clip(1-depth/max(.25*scene.span,9*scene.noise),0,1)
    return 2.65*fade*np.maximum(shallow,weak)*np.clip(x/(.20*scene.scale)-.35,0,1)


def entry_arc(scene,path):
    x,y=path.T
    if len(x)<5:return False
    slope=np.diff(y)
    half=max(2,len(y)//3)
    tangent_change=abs(slope[:half].mean()-slope[-half:].mean())
    g=scene.local[:,scene.front:].astype(np.float32,copy=False)
    r=max(2,round(.016*scene.scale))
    flank=np.maximum(g[np.maximum(0,y-r),x],g[np.minimum(len(g)-1,y+r),x])
    lit=np.mean(flank>=scene.black+.85*scene.span)
    return x[-1]<.22*scene.scale and lit>.45 and (tangent_change>.19 or np.ptp(y)>.025*scene.scale)

@njit
def transition_charges(path,dual,risk,scale):
    charges=np.zeros(len(path))
    tan=res=np.float32(0);gap=0
    for j in range(1,len(path)):
        x,y=path[j]
        tan1,res1,gap,cost=step(tan,res,gap,int(y-path[j-1,1]),dual[x,y],risk[x,y],scale)
        tan=np.float32(tan1);res=np.float32(res1);charges[j]=cost
    return charges
