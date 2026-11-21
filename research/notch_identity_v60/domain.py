"""One coarse translation and texture-validated bounded residuals on native material."""
from time import perf_counter
import cv2
import numpy as np
from research.notch_identity_v515.domain import embed
from research.notch_identity_v514.registration import align

RADIUS = 5
GAP = 3


def native_point(q, meta, shape, refshape):
    x, y = q
    offset = np.mean(np.asarray(meta['fixed_points']) - meta['current_points'], axis=0)
    for win in meta['evidence']['reference_info']['fixed']['windows']:
        if win['x0'] <= x < win['x1']:
            offset += correction(y, win)
            break
    return np.array([x, y]) + offset


def correction(y, win):
    t = np.clip((y-win['mid']+GAP)/(2*GAP), 0, 1)
    t = t*t*(3-2*t)
    up, dn = np.asarray(win['up']), np.asarray(win['down'])
    return up + np.asarray(t)[...,None]*(dn-up)


def replay(fixed, cp, rp, bounds, info):
    x,y,r,b=bounds
    dx,dy=np.mean(np.asarray(rp)-cp,axis=0)
    yy,xx=np.mgrid[y:b,x:r].astype(np.float32)
    xx+=dx
    yy+=dy
    rows=np.arange(y,b)
    for win in info['windows']:
        sl=slice(win['x0']-x,win['x1']-x)
        shift=correction(rows,win)
        xx[:,sl]+=shift[:,0,None]
        yy[:,sl]+=shift[:,1,None]
    valid=(xx>=0)&(yy>=0)&(xx<fixed.shape[1]-1)&(yy<fixed.shape[0]-1)
    tile=cv2.remap(fixed,xx,yy,cv2.INTER_LINEAR).astype(np.float32)
    tile[~valid]=np.nan
    return tile


def residual_stats(cur, base, mid, front):
    # Count adjacent opposite signs on the same material mask before and after alignment.
    a=base[:,front:]-cur[:,front:]
    material=np.isfinite(a)&(cur[:,front:]>12)&(cur[:,front:]<249)
    side=np.abs(np.arange(len(a))-mid)>GAP
    material &= side[:,None]
    valid=material[2:]&material[:-2]
    pair=(a[2:]*a[:-2]<0)&(np.minimum(abs(a[2:]),abs(a[:-2]))>=5)
    return [int((valid & pair).sum()),int(valid.sum())]


class ReferenceMap:
    def __init__(self,current,fixed,cp,rp,box,prep,stage):
        self.current,self.fixed,self.cp,self.rp=current,fixed,cp,rp
        self.box,self.prep=box,prep
        self.bounds=[]
        self.info={'windows':[]}
        self.seconds=0.
        self.pixels=0

    def __call__(self,stop):
        start=perf_counter()
        l,t,r,b=self.box
        r=min(r,l+stop)
        p,band,_=self.prep
        front=l+p.origin[0]+p.front
        mid=t+p.origin[1]+int(np.median(np.asarray(p.starts)[:,1]))
        half=round((.23 if p.local.size>250000 else .51)*p.scale)
        x=max(l,front-round(.08*p.scale))
        y=max(t+band[0],mid-half)
        bottom=min(t+band[1],mid+half+1)
        bounds=[int(v) for v in (x,y,r,bottom)]
        cur=self.current[y:bottom,x:r].astype(np.float32)
        base=replay(self.fixed,self.cp,self.rp,bounds,{'windows':[]})
        cy=mid-y
        depth=max(12,min(48,round(.16*p.scale)))
        allowed=(cur>max(8,p.black+.08*p.span))&(cur<250)
        good=(np.isfinite(base)&(base>max(8,p.black+.08*p.span))&(base<250)).astype(np.uint8)
        allowed &= cv2.erode(good,np.ones((11,11),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=0)>0
        windows=[]
        stride=max(48,min(160,round(.45*p.scale)))
        for start_x in range(front,r,stride):
            end=min(r,start_x+stride)
            left=max(front-x,start_x-x)
            right=end-x
            def estimate(lo,hi,mask_fn):
                # Texture and NCC are checked over the same masked material pixels.
                res=align(cur,base,(left,lo,right,hi),RADIUS,(0,0),p.noise,p.span,mask_fn,allowed)
                if res['status']=='OK' and res['ncc']<.84:res['status']='LOW_NCC'
                return res
            full=lambda xx,yy:np.ones((yy.size,xx.size),bool)
            up=estimate(cy-depth,cy-GAP,full)
            dn=estimate(cy+GAP+1,cy+depth+1,full)
            single=None
            if any(a['status']!='OK' for a in (up,dn)):
                single=estimate(cy-depth,cy+depth+1,lambda xx,yy:np.broadcast_to(abs(yy-cy)>GAP,(yy.size,xx.size)))
            def pick(a):
                if a['status']=='OK':return a['shift'],'side'
                if single and single['status']=='OK':return single['shift'],'single'
                return [0,0],'zero'
            su,mu=pick(up)
            sd,md=pick(dn)
            windows.append(dict(x0=start_x,x1=end,mid=mid,up=su,down=sd,up_mode=mu,down_mode=md,
                                up_ncc=up['ncc'],down_ncc=dn['ncc'],single_ncc=single['ncc'] if single else None))
        info=dict(windows=windows)
        tile=replay(self.fixed,self.cp,self.rp,bounds,info)
        info.update(before=residual_stats(cur,base,cy,front-x),after=residual_stats(cur,tile,cy,front-x))
        self.bounds,self.info=bounds,info
        self.pixels+=tile.size
        result=embed(tile,bounds,[l,t,r,b])
        self.seconds+=perf_counter()-start
        return result
