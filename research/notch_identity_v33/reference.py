"""Two-scale translation and local exposure-compensated crack evidence."""
import cv2
import numpy as np
from research.notch_identity_v3.detector import px


def align(current, fixed, box, search, center, noise, contrast, mask_fn):
    """Masked ZNCC. Translation maps current coordinates into fixed coordinates."""
    h,w=current.shape
    dx,dy=center
    x0,y0,x1,y1=box
    x0=max(x0,0,search-dx); y0=max(y0,0,search-dy)
    x1=min(x1,w,w-search-dx); y1=min(y1,h,h-search-dy)
    result=dict(status='INSUFFICIENT_CONTEXT',shift=None,ncc=None,margin=None)
    if x1-x0<2*search+1 or y1-y0<2*search+1:return result
    block=fixed[y0+dy-search:y1+dy+search,x0+dx-search:x1+dx+search].astype(np.float32)
    mask=mask_fn(np.arange(x0,x1)[None,:],np.arange(y0,y1)[:,None]).astype(np.float32)
    # Ignore missing reference support throughout the complete translation footprint.
    invalid=cv2.dilate((~np.isfinite(block)).astype('uint8'),np.ones((2*search+1,2*search+1),np.uint8))
    mask*=1-invalid[search:-search,search:-search]
    block=np.nan_to_num(block)
    n=mask.sum()
    if n<.35*mask.size:return result
    patch=current[y0:y1,x0:x1].astype(np.float32)
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
    def __init__(self,raw,fixed,sl,offset,start,scale,noise,contrast):
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
                          lambda xx,yy:(xx<x-px(scale,.05))|(abs(yy-y)>px(scale,.04)))

        self.coarse['anchor']='NOTCH'
        if self.coarse['status']!='OK':
            anchors=[]
            for sign in (-1,1):
                center_y=y+sign*px(scale,.22)
                area=(x-px(scale,.22),center_y-px(scale,.12),x+px(scale,.50),center_y+px(scale,.12))
                anchors.append(align(ta,tb,area,px(scale,.04),(0,0),noise,contrast,
                               lambda xx,yy:np.ones((yy.size,xx.size),bool)))
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
                         lambda xx,yy:np.broadcast_to(abs(yy-y)>p(.027),(yy.size,xx.size)))
            if status['status']!='OK':
                area=(x-p(.32),y-p(.24),x+p(.15),y+p(.24))
                wide=align(self.local_current,self.local_fixed,area,p(.015),self.coarse['shift'],self.noise,self.contrast,
                           lambda xx,yy:np.broadcast_to(abs(yy-y)>p(.05),(yy.size,xx.size)))
                if wide['status']=='OK':status={**wide,'anchor':'WIDE_TAIL'}
        self.cache[key]=status
        return status

    def measure(self,pts):
        pts=np.asarray(pts,int); x,y=pts.T
        reg=self.local(x[-1],y[-1])
        if reg['status']!='OK':return reg,None
        dx,dy=reg['shift'];r=px(self.s,.014);h,w=self.gray.shape
        if (x+dx).min()<0 or (x+dx).max()>=w or min(y.min(),(y+dy).min())<r or max(y.max(),(y+dy).max())+r>=h:
            return {**reg,'status':'EDGE'},None
        def profile(im,xx,yy):
            flank=np.minimum(im[yy-r,xx],im[yy+r,xx]).astype(float)
            return flank-im[yy,xx]
        a=profile(self.gray,x,y);b=profile(self.fixed,x+dx,y+dy)
        if not np.isfinite(b).all():return {**reg,'status':'MISSING'},None
        return reg,(a,b,a-b)

    def protect(self,x,y,i):
        span=px(self.s,.022)
        if i<span or i+span>=len(x):return False
        pts=np.column_stack((x[i-span:i+span+1],y[i-span:i+span+1]))
        _,data=self.measure(pts)
        if data is None:return False
        a,b,net=data
        changed=(net>max(2*self.noise,.022*self.contrast))&(a>self.noise)
        return bool(changed[:span].mean()>=.65 and changed[span:].mean()>=.65)

    def review(self,points):
        pts=np.asarray(points); x=pts[:,0];s=self.s
        pts=pts[x>=x[-1]-px(s,.15)]
        reg,data=self.measure(pts)
        audit=dict(**reg,decision='NO_ALIGNMENT',cut=None,net=None,fraction=None)
        if data is None:return audit
        a,b,net=data
        changed=(net>max(2*self.noise,.025*self.contrast))&(a>self.noise)
        window=px(s,.022)
        audit.update(net=float(np.mean(net[-window:])),fraction=float(changed[-window:].mean()),decision='RETAIN')
        static=(b>2*self.noise)&(abs(net)<=np.maximum(2*self.noise,.25*np.maximum(a,b)))
        weak=(a<max(2.5*self.noise,.035*self.contrast))&(~changed)
        last=np.flatnonzero(changed)
        if len(last):
            k=int(last[-1])+1
            if len(pts)-k>=window and (static|weak)[k:].mean()>=.75 and changed[max(0,k-2*window):k].mean()>=.45:
                audit.update(decision='TRIM_STATIC' if static[k:].mean()>=.5 else 'TRIM_WEAK',cut=int(pts[k,0]))
        elif static.mean()>=.75:audit['decision']='PERSISTENT_NO_BOUNDARY'
        return audit

    def rank(self,pts):
        pts=np.asarray(pts)
        pts=pts[pts[:,0]<=pts[0,0]+px(self.s,.25)]
        reg,data=self.measure(pts)
        if data is None:return dict(weight=0.,fraction=None,mean=None,status=reg['status'])
        a,b,net=data
        val=np.clip(net/self.contrast,0,.5)
        fraction=float((net>max(2*self.noise,.025*self.contrast)).mean())
        mean=float(val.mean())
        return dict(weight=.65*fraction*np.sqrt(mean),fraction=fraction,mean=mean,status='OK')
