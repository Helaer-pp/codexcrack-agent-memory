"""Native notch routing, a proximal recovery window, and absolute terminal cross sections."""
from dataclasses import dataclass, replace
import cv2
import numpy as np
from research.notch_identity_v51.terminal import Scene
from research.notch_identity_v510.ridge import longest

@dataclass
class NotchScene(Scene):
    quiet_notch: bool
    mouth_extent: int
    change_quantile: float

def notch_observation(raw,ref,tip,rtip):
    x,y=map(int,tip);rx,ry=map(int,rtip)
    # Measure the physical silhouette just behind its vertex, in native pixels.
    back=raw[max(0,y-28):y+29,max(0,x-6):x+1]
    cut=float(np.percentile(back,15))+.28*float(np.ptp(back))
    opening=int(np.count_nonzero(np.mean(back<cut,axis=1)>.5))
    extent=int(np.clip(3*opening,16,64))
    half=max(6,extent//2)
    half=min(half,y,ry,len(raw)-1-y,len(ref)-1-ry)
    width=min(extent,raw.shape[1]-x,ref.shape[1]-rx)
    if half<3 or width<8:return False,extent,255.
    a=raw[y-half:y+half+1,x:x+width].astype(np.float32)
    b=ref[ry-half:ry+half+1,rx:rx+width].astype(np.float32)
    # Bias removal and small shifts tolerate a one-pixel difference in silhouette localization.
    smooth=lambda im:cv2.GaussianBlur(im,(3,3),.65)
    a=smooth(a)[2:-2,2:-2];b=smooth(b)
    best=255.
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            d=b[2+dy:2+dy+a.shape[0],2+dx:2+dx+a.shape[1]]-a
            d-=np.median(d)
            best=min(best,float(np.percentile(abs(d),97)))
    noise=float(np.median(abs(a-cv2.medianBlur(a,3))))
    return best<=max(3.,3.5*noise),extent,best

def proximal_scene(scene,narrow):
    # The distal strip already encloses all entrance rows. Add the radius difference
    # outside both lips only on the first fifth-scale and a small filter halo.
    halo=round(.055*scene.scale)
    low=max(0,narrow.origin[1]-scene.origin[1]-halo)
    high=min(len(scene.local),narrow.origin[1]-scene.origin[1]+len(narrow.local)+halo)
    ys,xs=scene.sl
    end=min(scene.local.shape[1],scene.front+round(.20*scene.scale)+1+max(12,round(.08*scene.scale)))
    return replace(scene,sl=(slice(ys.start+low,ys.start+high),slice(xs.start,xs.start+end)),
                   local=scene.local[low:high,:end],origin=(scene.origin[0],scene.origin[1]+low),
                   starts=[(x,y-low) for x,y in scene.starts])

def valley(p,path):
    x,y=path.T
    g=p.local[:,p.front:]
    def sample(d):return g[np.clip(y+d,0,len(g)-1),x].astype(np.float32)
    center=np.minimum(sample(0),.5*(sample(-1)+sample(1)))
    def shoulders(radii):
        left=np.mean([sample(-r) for r in radii],axis=0)
        right=np.mean([sample(r) for r in radii],axis=0)
        return np.minimum(left,right)-center
    return shoulders((1,2)),shoulders((4,5,6))

def tail_charge(p,path,red):
    x,y=path.T
    near,far=valley(p,path)
    noise=max(1.,p.noise)
    shallow=(near<max(2.5*noise,3.)) & (far<max(7*noise,.13*p.span))
    # Detect an additive contrast step between adjacent three-column neighborhoods.
    sm=np.convolve(np.pad(far,(1,1),mode='edge'),np.ones(3)/3,mode='valid')
    step=np.r_[np.repeat(sm[0],3),sm][:-3]-sm>max(1.4*noise,2.)
    recent=cv2.dilate(step.astype('uint8')[None,:],np.ones((1,13),np.uint8),anchor=(12,0)).ravel().astype(bool)
    weak=(red[x,y]>.02)&(red[x,y]<.82)
    broad=shallow & (far-near>noise)
    # Isolated flat pixels routinely alternate with sharp hairline minima.
    persistent=cv2.morphologyEx(broad.astype('uint8')[None,:],cv2.MORPH_OPEN,np.ones((1,3),np.uint8)).ravel()
    return 2.8*(x>.22*p.scale)*persistent*recent*weak

def scratch_cut(path,delta,p):
    # A brightened copy beside the newly dark stroke must follow a sustained,
    # coherent offset as the path turns away from its incoming tangent.
    x,y=path.T
    span=max(4,round(.040*p.scale))
    if len(x)<3*span:return None
    offsets=np.r_[np.arange(-max(3,round(.044*p.scale)),-1),np.arange(2,max(3,round(.044*p.scale))+1)]
    side=-delta[x[:,None],np.clip(y[:,None]+offsets,0,delta.shape[1]-1)]
    blue=side.max(axis=1)
    witness=(blue>max(4*p.noise,.09*p.span)) & (delta[x,y]>max(3*p.noise,.05*p.span))
    edges=np.flatnonzero(np.diff(np.r_[False,witness,False]))
    for first,last in zip(edges[::2],edges[1::2]):
        if first<2*span or last-first<span:continue
        reach=min(last-first,2*span)
        incoming=(y[first]-y[first-2*span])/(2*span)
        outgoing=(y[first+reach-1]-y[first])/max(1,reach-1)
        # Permit geometric curvature when the opposite-sign trace has no stable displacement.
        shift=offsets[side[first:first+reach].argmax(axis=1)]
        if abs(outgoing-incoming)>.16 and np.ptp(shift)<=max(2,.012*p.scale):
            return first
    return None
