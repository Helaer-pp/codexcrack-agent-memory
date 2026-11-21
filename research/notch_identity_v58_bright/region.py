"""A user-defined material window and paired, shadow-aware virtual measurement points."""
import cv2
import numpy as np


def band(view,origin,box):
    """Use illuminated row profiles across the specimen, preserving dark cracks inside it."""
    l,t,r,b=map(int,box)
    ox,oy=origin
    h,w=view.shape
    l=max(l,ox);r=min(r,ox+w);t=max(t,oy);b=min(b,oy+h)
    if r-l<50 or b-t<32:raise ValueError('material window out of view')
    margin=max(8,(b-t)//3)
    y0=max(oy,t-margin);y1=min(oy+h,b+margin)
    slab=view[y0-oy:y1-oy,l-ox:r-ox]
    # Avoid the V-notch at the left boundary when estimating the specimen's illuminated surface.
    material=slab[:,slab.shape[1]//8:]
    otsu=cv2.threshold(material,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[0]
    bright=float(np.percentile(material,85))
    floor=float(otsu+.35*(bright-otsu))
    profiles=[np.median(part,axis=1) for part in np.array_split(material,8,axis=1)]
    good=np.min(profiles,axis=0)>=floor
    good[:t-y0]=False;good[b-y0:]=False
    edges=np.flatnonzero(np.diff(np.r_[False,good,False]))
    runs=list(zip(edges[::2],edges[1::2]))
    if not runs:return None,floor
    a,c=max(runs,key=lambda run:run[1]-run[0])
    if c-a<32:return None,floor
    return [l,int(y0+a+2),r,int(y0+c-2)],floor


def safe_patches(view,origin,box,floor):
    l,t,r,b=box;ox,oy=origin
    crop=view[t-oy:b-oy,l-ox:r-ox]
    safe=cv2.erode((crop>=floor).astype(np.uint8),np.ones((9,9),np.uint8),
                   borderType=cv2.BORDER_CONSTANT,borderValue=0)
    return safe.astype(bool)


def paired_points(ref,cur,origin,box,floors,reference_targets,displacements):
    """A single relocation moves both frames' virtual point, preserving the tracked motion."""
    left,top,right,bottom=box
    sf=safe_patches(ref,[0,0],box,floors[0]);sc=safe_patches(cur,origin,box,floors[1])
    a=[];b=[]
    for i,(target,move) in enumerate(zip(reference_targets,displacements)):
        dx,dy=np.rint(move).astype(int)
        available=sf & np.roll(sc,(-dy,-dx),(0,1))
        yy,xx=np.indices(available.shape)
        available &= (xx+dx>=0)&(xx+dx<sf.shape[1])&(yy+dy>=0)&(yy+dy<sf.shape[0])
        limit=sf.shape[0]//2
        available &= (yy<limit-4) if i==0 else (yy>limit+4)
        ys,xs=np.nonzero(available)
        if not len(xs):return None,None
        xs+=left;ys+=top
        j=np.argmin((xs-target[0])**2+(ys-target[1])**2)
        a.append([int(xs[j]),int(ys[j])])
        b.append([int(xs[j]+dx),int(ys[j]+dy)])
    return np.asarray(a),np.asarray(b)


def geometry(raw,origin,fixed,meta,settings,delta=None):
    old=np.asarray(meta['current_points'],float)
    previous=np.asarray(meta['fixed_points'],float)
    motion=old-previous
    source=np.array(settings['reference_box'],int)
    dx=round(float(motion[:,0].mean()))
    moved=source+[dx,round(motion[0,1]),dx,round(motion[1,1])]
    current,cut=band(raw,origin,moved)
    ref_box=settings['fixed_band'];floor=settings['fixed_floor']
    if current is None:return None
    l,t=np.maximum(current[:2],ref_box[:2])
    r,b=np.minimum(current[2:],ref_box[2:])
    if r-l<50 or b-t<32:return None
    box=list(map(int,(l,t,r,b)))
    nominal=np.asarray(settings['reference_virtual_points'],float)
    requested=nominal if delta is None else nominal+delta
    rf,cp=paired_points(fixed,raw,origin,box,[floor,cut],requested,motion)
    if rf is None:return None
    return dict(box=box,ref_band=ref_box,cur_band=current,floors=[floor,cut],
                original_ref=previous.tolist(),original_cur=old.tolist(),requested_ref=requested.tolist(),
                ref_points=rf.tolist(),cur_points=cp.tolist())
