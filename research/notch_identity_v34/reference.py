"""Residual-translation tolerant line measurements in the current ROI coordinate system."""
import numpy as np
from numba import njit
from research.notch_identity_v33.reference import Support as Previous
from research.notch_identity_v3.detector import px


@njit
def sample(im,x,y):
    i,j=int(np.floor(x)),int(np.floor(y))
    if i<0 or j<0 or i+1>=im.shape[1] or j+1>=im.shape[0]:return np.nan
    u=x-i;v=y-j
    return (1-v)*((1-u)*im[j,i]+u*im[j,i+1])+v*((1-u)*im[j+1,i]+u*im[j+1,i+1])


@njit
def along(im,x,y,tx,ty):
    return (sample(im,x-tx,y-ty)+2*sample(im,x,y)+sample(im,x+tx,y+ty))*.25

@njit
def profiles(cur,ref,pts,dx,dy,radius,search,tangent,noise):
    """Each row holds positive/negative energy, signed integral and the two depths."""
    result=np.full((len(pts),5),np.nan)
    for i in range(len(pts)):
        lo=max(0,i-tangent);hi=min(len(pts)-1,i+tangent)
        vx,vy=pts[hi]-pts[lo];norm=max(1.,np.hypot(vx,vy))
        nx=-vy/norm;ny=vx/norm if hi>lo else 1.
        x,y=pts[i];fx=x+dx;fy=y+dy
        tx=ny*max(1.,radius*.65);ty=-nx*max(1.,radius*.65)
        a=along(cur,x-radius*nx,y-radius*ny,tx,ty);b=along(cur,x+radius*nx,y+radius*ny,tx,ty)
        f1=along(ref,fx-radius*nx,fy-radius*ny,tx,ty);f2=along(ref,fx+radius*nx,fy+radius*ny,tx,ty)
        bias=.5*(f1+f2-a-b)
        pos=neg=net=0.
        for j in range(-radius,radius+1):
            v=along(ref,fx+j*nx,fy+j*ny,tx,ty)-along(cur,x+j*nx,y+j*ny,tx,ty)-bias
            net+=v;pos+=max(0.,v-.5*noise);neg+=max(0.,-v-.5*noise)
        peak=0.
        for u in range(-search,search+1):
            for v in range(-search,search+1):
                if u*u+v*v>search*search:continue
                cx=fx+u;cy=fy+v
                valley=min(along(ref,cx-radius*nx,cy-radius*ny,tx,ty),along(ref,cx+radius*nx,cy+radius*ny,tx,ty))-along(ref,cx,cy,tx,ty)
                if np.isfinite(valley):peak=max(peak,valley)
        result[i,0]=pos;result[i,1]=neg;result[i,2]=net
        result[i,3]=min(a,b)-along(cur,x,y,tx,ty);result[i,4]=peak
    return result


class Support(Previous):
    stage='v3_4'

    def evidence(self,pts):
        pts=np.asarray(pts,dtype=np.int64)
        reg=self.local(*pts[-1])
        if reg['status']=='OK':used='FINE'
        elif reg['status'] in ('AMBIGUOUS','LOW_TEXTURE','INSUFFICIENT_CONTEXT') and self.coarse['status']=='OK':used='COARSE'
        else:return dict(**reg,source='NONE'),None
        shift=reg['shift'] if used=='FINE' else self.coarse['shift']
        info={**reg,'local_status':reg['status'],'local_shift':reg['shift'],'source':used,'shift':shift}
        floor=max(self.noise,.008*self.contrast)
        raw=profiles(self.gray,self.fixed,pts,*shift,px(self.s,.014),px(self.s,.010),px(self.s,.010),floor)
        if not np.isfinite(raw).all():return {**info,'source':'NONE','status':'MISSING'},None
        pos,neg,net,dc,df=raw.T
        # Poisson/read-noise excursions in a search disk must not count as a line.
        duplicate=(df>=.55*np.maximum(dc,floor))&(df>=max(3.5*floor,.04*self.contrast))
        bipolar=(neg>=.65*np.maximum(pos,floor))&(np.minimum(neg,pos)>3*floor)
        good=(net>max(2.5*floor,.022*self.contrast))&(neg<.60*np.maximum(pos,floor))&(~duplicate)
        return info,dict(pos=pos,neg=neg,net=net,dc=dc,df=df,dup=duplicate,bipolar=bipolar,good=good)

    def review(self,points):
        pts=np.asarray(points)
        tail=pts[pts[:,0]>=pts[-1,0]-px(self.s,.15)]
        reg,data=self.evidence(tail)
        audit=dict(**reg,decision='NO_ALIGNMENT',cut=None,net=None,fraction=None)
        if data is None:return audit
        w=min(len(tail),px(self.s,.022));end=slice(-w,None)
        pos=data['pos'][end].sum();neg=data['neg'][end].sum()
        good=data['good'];bad=data['dup']|data['bipolar']
        audit.update(decision='RETAIN',net=float(data['net'][end].mean()),fraction=float(good[end].mean()),
                     pos_energy=float(pos/w),neg_energy=float(neg/w),ratio=float(neg/max(pos,self.noise)),
                     duplicate=float(data['dup'][end].mean()),bipolar=float(data['bipolar'][end].mean()),
                     fixed_peak=float(data['df'][end].mean()),current_depth=float(data['dc'][end].mean()))
        # A sustained transition rejects the entire disconnected suffix, even if
        # isolated positive pixels appear farther along the scratch.
        for k in range(1,len(tail)-w+1):
            if good[end].mean()<.45 and bad[k] and bad[k:k+w].mean()>=.75 and good[max(0,k-w):k].mean()>=.6 and bad[k:].mean()>=.55:
                audit.update(decision='TRIM_DUPLICATE' if data['dup'][k:k+w].mean()>=.5 else 'TRIM_BIPOLAR',cut=int(tail[k,0]))
                return audit
        strict=self.stage=='v3_4' and (audit['fraction']<.45 or audit['net']<=0 or audit['ratio']>=.65)
        if strict or bad[end].mean()>=.6:
            # Include the preceding trunk if the full terminal neighborhood has already lost support.
            if not good.any() and len(pts)>len(tail):
                earlier=pts[pts[:,0]<tail[0,0]]
                _,more=self.evidence(earlier)
                if more is not None:
                    tail=pts;good=np.concatenate((more['good'],good))
            for k in range(len(good)-1,0,-1):
                sub=good[max(0,k-w+1):k+1]
                if good[k] and len(sub)==w and sub.mean()>=.65 and k+1<len(tail):
                    audit.update(decision='TRIM_LOW_FRACTION' if strict else 'TRIM_STATIC',cut=int(tail[k+1,0]));return audit
            audit['decision']='NO_SUPPORTED_BOUNDARY'
        return audit

    def protect(self,x,y,i):
        if self.stage=='unlock':return super().protect(x,y,i)
        w=px(self.s,.022)
        if i<w or i+w>=len(x):return False
        _,d=self.evidence(np.column_stack((x[i-w:i+w+1],y[i-w:i+w+1])))
        if d is None:return False
        return all(d['good'][sl].mean()>=.50 and d['net'][sl].mean()>max(5*self.noise,.06*self.contrast) for sl in (slice(0,w),slice(w,None)))

    def accept_lip(self,x,y,event):
        a,b,c=event[:3]
        if self.stage not in ('branch','v3_4') or event[4]<0 or event[4]>2:return False
        _,d=self.evidence(np.column_stack((x[(x>=b)&(x<=c)],y[(x>=b)&(x<=c)])))
        # Do not resurrect a second line independently visible before the loss:
        # the gap as well as the recovered segment must carry positive increments.
        ids=(x>=a)&(x<b)
        if d is None or not ids.any():return False
        _,gap=self.evidence(np.column_stack((x[ids],y[ids])))
        return gap is not None and gap['good'].mean()>=.5 and d['good'].mean()>=.8

    def rank(self,pts):
        if self.stage not in ('branch','v3_4'):return super().rank(pts)
        pts=np.asarray(pts); near=pts[:,0]<=pts[0,0]+px(self.s,.25)
        _,d=self.evidence(pts)
        if d is None:return dict(weight=0.,tier=0,status='UNAVAILABLE',fraction=None,mean=None)
        frac=float(d['good'].mean());short=float(d['good'][near].mean())
        mean=float(d['net'].mean());static=frac<.15 and mean<=2*self.noise
        tier=-1 if static else int(frac>=.40)
        weight=super().rank(pts)['weight']+.10*min(short,frac)
        return dict(weight=weight,tier=tier,fraction=frac,near_fraction=short,mean=mean,status='OK')
