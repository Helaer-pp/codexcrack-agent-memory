"""Keep texture windows local to the notch and use continuous row-wise displacement."""
import cv2
import numpy as np
from research.notch_identity_v40.evidence import registered as legacy
from research.notch_identity_v31.detector import px


def align(current, fixed, box, search, center, noise, contrast, mask_fn, material):
    """Masked ZNCC. Translation maps current coordinates into fixed coordinates."""
    h,w=current.shape
    dx,dy=center
    x0,y0,x1,y1=box
    x0=max(x0,0,search-dx); y0=max(y0,0,search-dy)
    x1=min(x1,w,w-search-dx); y1=min(y1,h,h-search-dy)
    result=dict(status='INSUFFICIENT_CONTEXT',shift=None,ncc=None,margin=None)
    if x1-x0<2*search+1 or y1-y0<2*search+1:return result
    block=fixed[y0+dy-search:y1+dy+search,x0+dx-search:x1+dx+search].astype(np.float32,copy=False)
    mask=mask_fn(np.arange(x0,x1)[None,:],np.arange(y0,y1)[:,None]).astype(np.float32)
    mask*=material[y0:y1,x0:x1]
    # Ignore missing reference support throughout the complete translation footprint.
    if not np.isfinite(block).all():
        invalid=cv2.dilate((~np.isfinite(block)).astype('uint8'),np.ones((2*search+1,2*search+1),np.uint8))
        mask*=1-invalid[search:-search,search:-search]
        block=np.nan_to_num(block)
    n=mask.sum()
    if n<.35*mask.size:return result
    patch=current[y0:y1,x0:x1].astype(np.float32,copy=False)
    tpl=(patch-(patch*mask).sum()/n)*mask
    energy=np.sum(tpl**2)
    if energy/n<max(1.8*noise,.02*contrast)**2:
        result['status']='LOW_TEXTURE';return result
    def corr(a,b):return cv2.matchTemplate(a,b,cv2.TM_CCORR)
    var=np.maximum(1e-5,corr(block**2,mask)-corr(block,mask)**2/n)
    scores=corr(block,tpl)/np.sqrt(var*energy)
    by,bx=np.unravel_index(scores.argmax(),scores.shape)
    best=float(np.clip(scores[by,bx],-1,1));others=scores.copy()
    rad=max(1,round(.32*search))
    others[max(0,by-rad):by+rad+1,max(0,bx-rad):bx+rad+1]=-1
    gap=best-float(others.max())
    result.update(ncc=best,margin=gap,shift=[int(dx+bx-search),int(dy+by-search)],
                  status='OK' if best>=.75 and gap>=.012 else 'AMBIGUOUS')
    return result


class Support:
    def __init__(self,raw,fixed,sl,offset,start,scale,noise,contrast,material):
        self.material=material[sl]
        self.gray=raw[sl]
        self.fixed=fixed[sl]
        self.s=scale; self.noise=noise; self.contrast=contrast
        self.cache={}
        x,y=np.rint(np.asarray(start)+offset).astype(int)
        box=(x-px(scale,.40),y-px(scale,.23),x+px(scale,.52),y+px(scale,.23))
        def texture(im):
            return im-cv2.GaussianBlur(im,(0,0),max(.5,.018*scale))
        a=raw.astype(np.float32)
        b=np.where(np.isfinite(fixed),fixed,a).astype(np.float32)
        ta=texture(a);tb=texture(b);tb[~np.isfinite(fixed)]=np.nan
        self.local_current=ta[sl];self.local_fixed=tb[sl]
        self.coarse=align(ta,tb,box,px(scale,.04),(0,0),noise,contrast,
                          lambda xx,yy:(xx<x-px(scale,.05))|(abs(yy-y)>px(scale,.04)),material)

        self.coarse['anchor']='NOTCH'
        if self.coarse['status']!='OK':
            anchors=[]
            for sign in (-1,1):
                center_y=y+sign*px(scale,.22)
                area=(x-px(scale,.22),center_y-px(scale,.12),x+px(scale,.50),center_y+px(scale,.12))
                anchors.append(align(ta,tb,area,px(scale,.04),(0,0),noise,contrast,
                               lambda xx,yy:np.ones((yy.size,xx.size),bool),material))
            if all(r['status']=='OK' for r in anchors) and np.linalg.norm(np.subtract(anchors[0]['shift'],anchors[1]['shift']))<=px(scale,.01):
                self.coarse={**max(anchors,key=lambda r:r['margin']),'anchor':'TWO_FLANKS'}
        self.coarse['anchor_status']=self.coarse['status']

    def local(self,x,y):
        p=lambda f:px(self.s,f)
        key=(int(x),int(y))
        if key in self.cache:return self.cache[key]
        status=dict(status='COARSE_'+self.coarse['status'],shift=None,ncc=None,margin=None)
        if self.coarse['status']=='OK':
            box=(x-p(.21),y-p(.12),x+p(.11),y+p(.12))
            status=align(self.local_current,self.local_fixed,box,p(.015),self.coarse['shift'],self.noise,self.contrast,
                         lambda xx,yy:np.broadcast_to(abs(yy-y)>p(.027),(yy.size,xx.size)),self.material)
            if status['status']!='OK':
                area=(x-p(.32),y-p(.24),x+p(.15),y+p(.24))
                wide=align(self.local_current,self.local_fixed,area,p(.015),self.coarse['shift'],self.noise,self.contrast,
                           lambda xx,yy:np.broadcast_to(abs(yy-y)>p(.05),(yy.size,xx.size)),self.material)
                if wide['status']=='OK':status={**wide,'anchor':'WIDE_TAIL'}
        self.cache[key]=status
        return status



from research.notch_identity_v35.reference import contour

def fast_registration(p,fixed):
    sl,origin,starts,_,_,s,front,gray,noise,_,raw,span=p
    center=np.median(starts,axis=0)
    # The correlation slabs, their search radii and Gaussian halo lie inside this box.
    front_x=int(origin[0]+front)
    center_y=int(round(center[1]+origin[1]))
    left=max(0,front_x-px(s,.08));right=min(raw.shape[1],front_x+px(s,.70)+1)
    top=max(0,center_y-px(s,.45));bottom=min(raw.shape[0],center_y+px(s,.45)+1)
    roi=np.s_[top:bottom,left:right]
    current=raw[roi];ref=fixed[roi]
    inside=(slice(max(0,sl[0].start-top),max(0,sl[0].stop-top)),
            slice(max(0,sl[1].start-left),None))
    offset=np.array(origin)-[left,top]
    # Reject black fixture and missing reference support throughout the search footprint.
    radius=px(s,.04)
    material=(current>max(5,noise*2)) & (cv2.erode((np.isfinite(ref)&(ref>max(5,noise*2))).astype('uint8'),
                 np.ones((2*radius+1,2*radius+1),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=0)>0)
    reg=Support(current,ref,inside,offset,center,s,noise,span,material)
    if reg.coarse['status']!='OK':
        # Geometric fallback compares the finite notch silhouette, without intensity NCC on the fixture.
        radius=max(1,px(s,.021))
        cy=int(round(center[1]+origin[1]))-top
        cx=front_x-left
        y0=max(radius,cy-px(s,.065));y1=min(len(current)-radius,cy+px(s,.065)+1)
        x0=radius;x1=min(current.shape[1]-radius,cx+px(s,.04)+1)
        if y1>y0 and x1>x0:
            cut=float(np.percentile(current[y0:y1,x0:x1],8))+.20*span
            shape=(current[y0:y1,x0:x1]<cut).astype(np.float32)
            area=ref[y0-radius:y1+radius,x0-radius:x1+radius]
            if .05<shape.mean()<.94 and np.isfinite(area).all():
                mse=cv2.matchTemplate((area<cut).astype(np.float32),shape,cv2.TM_SQDIFF)/shape.size
                yi,xi=np.indices(mse.shape)
                by,bx=np.unravel_index(np.argmin(mse+.0002*((yi-radius)**2+(xi-radius)**2)),mse.shape)
                if mse[by,bx]<.13:
                    reg.coarse=dict(status='OK',anchor='BOUNDED_CONTOUR',shift=[int(bx-radius),int(by-radius)],
                                    loss=float(mse[by,bx]))
    if reg.coarse['status']!='OK':return reg.coarse,{},None
    # Use one off-crack flank measurement ahead of the mouth. Both stages map
    # from the current grid into the already geometrically remapped reference.
    local=reg.local(min(gray.shape[1]-1,front+px(s,.24)),round(center[1]))
    shift=local['shift'] if local['status']=='OK' else reg.coarse['shift']
    local=dict(local,shift=shift,source='FINE' if local['status']=='OK' else reg.coarse['anchor'])
    f=cv2.warpAffine(fixed[sl],np.float32([[1,0,shift[0]],[0,1,shift[1]]]),(gray.shape[1],gray.shape[0]),
        flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
    return reg.coarse,local,f


def registered(args,fixed,stage):
    sl,origin,starts,_,_,s,front,gray,noise,_,raw,span=args
    f=fixed
    # Preserve the footprint of all NCC windows and Gaussian filter support.
    # The returned shift is applied to the full original ROI below.
    coarse,reg,aligned=fast_registration(args,f)
    return coarse,reg,aligned
