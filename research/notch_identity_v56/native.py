"""Use P1/P2 only to define the coarse search corridor and its forward direction."""
from functools import lru_cache
import cv2
import numpy as np
from research.notch_identity_v51 import terminal as base
from research.v3_labelme_comparison.infer import current

@lru_cache(maxsize=2)
def reference(path,digest):
    return current(path,digest)

def find_body(gray,points):
    p=np.asarray(points,dtype=float)
    if p.shape!=(2,2) or not np.isfinite(p).all():return None
    p=p[np.argsort(p[:,1],kind='stable')]
    dx,dy=p[1]-p[0];span=np.hypot(dx,dy)
    if span<8:return None
    normal=np.array([dy,-dx])/span
    mid=p.mean(axis=0);h,w=gray.shape
    corners=np.array([mid+a*normal*span+b*(p[1]-p[0]) for a in (-1.,1.50) for b in (-.47,.47)])
    l,y=np.maximum(0,np.floor(corners.min(axis=0)).astype(int))
    r,b=np.minimum([w,h],np.ceil(corners.max(axis=0)).astype(int)+1)
    if r-l<9 or b-y<9:return None
    tile=gray[y:b,l:r]
    yy,xx=np.ogrid[y:b,l:r]
    axial=(xx-mid[0])*normal[0]+(yy-mid[1])*normal[1]
    side=(xx-mid[0])*(-normal[1])+(yy-mid[1])*normal[0]
    search=(abs(side)<.45*span)&(axial>-.96*span)&(axial<1.45*span)
    vals=tile[search]
    if not len(vals):return None
    low,bg=np.percentile(vals,[3,70])
    mask=(search&(tile<low+.30*max(bg-low,1))).astype('uint8')
    opened=cv2.morphologyEx(mask,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)))
    count,labels,stats,_=cv2.connectedComponentsWithStats(opened)
    choices=[]
    for j in range(1,count):
        bx,by,bw,bh,area=stats[j]
        if bw<12 or area<45 or bw<.75*bh:continue
        piece=labels[by:by+bh,bx:bx+bw]==j
        thick=np.flatnonzero(piece.sum(axis=0)>=4)
        if not len(thick):continue
        end=thick[-1];ys=np.flatnonzero(piece[:,end])
        tip=np.array([l+bx+end,y+by+np.median(ys)])
        if np.dot(tip-mid,normal)<-.55*span:continue
        # Choose a substantial dark notch body intersecting the rear of the corridor.
        extent=(l+bx-mid[0])*normal[0]+(y+by+bh/2-mid[1])*normal[1]
        if extent>-.05*span and bx>1:continue
        cols=piece[:,max(0,end-3):max(1,end)].sum(0)
        thickness=float(np.median(cols)) if len(cols) else len(ys)
        far=piece[:,max(0,end-22):max(1,end-17)].sum(0)
        if len(far) and np.median(far)>2.3*thickness:thickness=max(thickness,.60*float(np.median(far)))
        choices.append((area/(1+abs(np.dot(tip-mid,[-normal[1],normal[0]]))/span),tip,thickness))
    if not choices:return None
    _,tip,thickness=max(choices,key=lambda z:z[0])
    return np.rint(tip).astype(int),thickness,normal

def prepare(raw,points,stage):
    body=find_body(raw,points)
    if body is None:return None
    root,thickness,normal=body
    # Optical neighbourhood from observed mouth thickness, independent of point spacing.
    scale=float(np.clip(16*thickness,72,720))
    x,y=root;left=max(0,x-int(.58*scale));top=max(0,y-int(.50*scale))
    right=raw.shape[1];bottom=min(raw.shape[0],y+int(.50*scale)+1)
    crop=np.ascontiguousarray(raw[top:bottom,left:right])
    scene=base.prepare(crop,root-[left,top],scale)
    if scene is None:return None
    scene.front=min(scene.front,max(0,int(root[0]-left-scene.origin[0])))
    scene.stage=stage;scene.native_origin=np.array([left,top]);scene.native_bounds=(left,top,right,bottom)
    scene.body_root=root;scene.mouth_thickness=thickness;scene.normal=normal
    return scene

def fixed_crop(p,fixed):
    # Texture and the notch silhouette provide the initial integer translation in native pixels.
    l,t,r,b=p.native_bounds
    x,y=p.body_root;h,w=fixed.shape
    hx=int(np.clip(2*p.mouth_thickness,12,56));hy=int(np.clip(p.mouth_thickness,8,34))
    x0=max(l,x-hx);x1=min(r,x+hx+1);y0=max(t,y-hy);y1=min(b,y+hy+1)
    patch=p.raw[y0-t:y1-t,x0-l:x1-l]
    left=max(0,x0-56);top=max(0,y0-56)
    search=fixed[top:min(h,y1+56),left:min(w,x1+56)]
    if not patch.size or any(a<b for a,b in zip(search.shape,patch.shape)):return None,(0,0),0.
    match=cv2.matchTemplate(search.astype('float32'),patch.astype('float32'),cv2.TM_CCOEFF_NORMED)
    _,ncc,_,loc=cv2.minMaxLoc(match);dx=left+loc[0]-x0;dy=top+loc[1]-y0
    if ncc<.55:return None,(0,0),ncc
    result=cv2.warpAffine(fixed.astype('float32',copy=False),np.float32([[1,0,l+dx],[0,1,t+dy]]),
        (r-l,b-t),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
    return result,(dx,dy),float(ncc)
