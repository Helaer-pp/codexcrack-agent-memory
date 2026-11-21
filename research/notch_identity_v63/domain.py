"""One coarse translation and texture-validated bounded residuals on native material."""
from time import perf_counter
import cv2
import numpy as np
from research.notch_identity_v515.domain import embed
from research.notch_identity_v514.registration import align

from research.notch_identity_v60.domain import RADIUS, GAP, native_point, replay, residual_stats

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
        floor=max(5.,2*p.noise)
        allowed=np.isfinite(cur)&(cur>floor)
        good=(np.isfinite(base)&(base>floor)).astype(np.uint8)
        allowed &= cv2.erode(good,np.ones((11,11),np.uint8),borderType=cv2.BORDER_CONSTANT,borderValue=0)>0
        # Keep flat white reference patches exactly zero in the NCC variance calculation.
        # ZNCC is invariant to this constant offset. Material tests use original gray values.
        current_ncc=cur-255.
        reference_ncc=base-255.
        windows=[]
        stride=max(48,min(160,round(.45*p.scale)))
        for start_x in range(front,r,stride):
            end=min(r,start_x+stride)
            left=max(front-x,start_x-x)
            right=end-x
            def estimate(lo,hi,mask_fn):
                # Texture and NCC are checked over the same masked material pixels.
                res=align(current_ncc,reference_ncc,(left,lo,right,hi),RADIUS,(0,0),p.noise,p.span,mask_fn,allowed)
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
                                white_fraction=float(np.mean(base[:,left:right]>=250)),
                                up_status=up['status'],down_status=dn['status'],single_status=single['status'] if single else None,
                                up_ncc=up['ncc'],down_ncc=dn['ncc'],single_ncc=single['ncc'] if single else None))
        info=dict(windows=windows)
        tile=replay(self.fixed,self.cp,self.rp,bounds,info)
        info.update(before=residual_stats(cur,base,cy,front-x),after=residual_stats(cur,tile,cy,front-x))
        self.bounds,self.info=bounds,info
        self.pixels+=tile.size
        result=embed(tile,bounds,[l,t,r,b])
        self.seconds+=perf_counter()-start
        return result
