"""Independent contour registration, signed ridge fusion and distal shape evidence."""
import cv2
import numpy as np
from research.notch_identity_v34.reference import Support as Baseline
from research.notch_identity_v31.detector import px

def contour(raw,fixed,start,s,noise,contrast):
    x,y=np.rint(start).astype(int)
    r=px(s,.24);bound=px(s,.025)
    xs=np.arange(x-px(s,.30),x+1)
    if xs[0]<bound or xs[-1]+bound>=raw.shape[1] or y-r<0 or y+r>=raw.shape[0]:return None
    def edges(im,cols):
        a=im[y-r:y+r+1,cols]
        if not np.isfinite(a).all():return None
        lo,hi=np.percentile(a,[12,85])
        if hi-lo<max(8*noise,.28*contrast):return None
        dark=a<lo+.40*(hi-lo)
        first=dark.argmax(0);last=2*r-dark[::-1].argmax(0)
        usable=(last-first>px(s,.035))&(first>0)&(last<2*r)&dark[r]
        return first,last,usable
    cur=edges(raw,xs)
    if cur is None:return None
    results=[]
    for dx in range(-bound,bound+1):
        fixed_edges=edges(fixed,xs+dx)
        if fixed_edges is None:continue
        valid=cur[2]&fixed_edges[2]
        if valid.mean()<.75:continue
        a,b=cur[0][valid],cur[1][valid]
        if np.ptp(b-a)<px(s,.04):continue
        top=fixed_edges[0][valid]-a;bot=fixed_edges[1][valid]-b
        dy=int(round(np.median((top+bot)*.5)))
        loss=np.median(abs((top+bot)*.5-dy))+.3*np.mean(abs(np.r_[top-dy,bot-dy]))+.08*(abs(dx)+abs(dy))
        if abs(dy)<=bound and np.quantile(abs(np.r_[top-dy,bot-dy]),.85)<=px(s,.022):
            results.append((loss,dx,dy))
    if not results:return None
    loss,dx,dy=min(results)
    return dict(status='OK',anchor='CONTOUR',anchor_status='OK',shift=[dx,dy],ncc=None,margin=None,contour_loss=float(loss))

class Support(Baseline):
    def __init__(self,raw,fixed,sl,offset,start,s,noise,contrast,phase):
        super().__init__(raw,fixed,sl,offset,start,s,noise,contrast)
        self.phase=phase
        if self.coarse['status']=='AMBIGUOUS':
            reg=contour(raw,fixed,np.asarray(start)+offset,s,noise,contrast)
            if reg:self.coarse={**reg,'original_status':'AMBIGUOUS'}
        self.ridge=None
        if self.coarse['status']=='OK':
            dx,dy=self.coarse['shift'];h,w=self.gray.shape
            self.aligned=cv2.warpAffine(self.fixed,np.float32([[1,0,dx],[0,1,dy]]),(w,h),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
            valid=np.isfinite(self.aligned)
            f=np.where(valid,self.aligned,self.gray).astype('float32')
            self.ridge=self.ridge_map(f,valid)

    def ridge_map(self,f,valid):
        span=px(self.s,.018)
        def shoulders(im):
            return np.minimum(np.roll(im,span,axis=0),np.roll(im,-span,axis=0))
        gray=self.gray.astype('float32')
        delta=f-gray
        ridge=np.maximum(delta-shoulders(delta),0)
        flat=np.maximum(shoulders(f)-f,0)<max(2.5*self.noise,.035*self.contrast)
        ridge=np.minimum(ridge,np.maximum(delta,0))*flat*valid
        ridge[:span]=0;ridge[-span:]=0
        return cv2.GaussianBlur(ridge,(3,1),0)

    def accept_lip(self,x,y,event):
        if not super().accept_lip(x,y,event):return False
        if self.phase!='v3_5':return True
        a,b,c=event[:3];span=px(self.s,.031)
        old=(x>=a-span)&(x<a)
        entry=(x>=b)&(x<=c)
        if old.sum()<3 or entry.sum()<3:return False
        slope,intercept=np.polyfit(x[old],y[old],1)
        slope2=np.polyfit(x[entry],y[entry],1)[0]
        err=abs(y[entry]-(slope*x[entry]+intercept))
        if abs(np.arctan(slope)-np.arctan(slope2))>.25 or np.median(err)>max(.6,.004*self.s):return False
        _,before=self.evidence(np.column_stack((x[old],y[old])))
        return before is not None and before['good'].mean()>=.8 and event[3]<=.006*self.s

    def shape_match(self,pts,shift):
        # Search a single common translation of an oriented, high-pass strip.
        if len(pts)<4:return None
        r=px(self.s,.013);search=px(self.s,.030)
        p=np.asarray(pts,int)
        x,y=p.T
        angle=np.arctan2(y[-1]-y[0],max(1,x[-1]-x[0]))
        offsets=np.arange(-r,r+1)
        xx=x[:,None]-np.sin(angle)*offsets
        yy=y[:,None]+np.cos(angle)*offsets
        xx=np.rint(xx).astype(int);yy=np.rint(yy).astype(int)
        dx,dy=shift;h,w=self.gray.shape
        if min(xx.min(),yy.min())<0 or xx.max()>=w or yy.max()>=h:return None
        if xx.min()+dx<search or yy.min()+dy<search or xx.max()+dx+search>=w or yy.max()+dy+search>=h:return None
        target=self.gray[yy,xx].astype(float)
        def center(a):return a-(a[:,0:1]+a[:,-1:])*.5
        a=center(target);depth=-np.median(a[:,r])
        if depth<max(2.5*self.noise,.025*self.contrast):return None
        # A common displacement normal to the observed orientation preserves the tangent.
        best=None
        for d in range(-search,search+1):
            fx=xx+dx-round(np.sin(angle)*d);fy=yy+dy+round(np.cos(angle)*d)
            b=center(self.fixed[fy,fx])
            if not np.isfinite(b).all():continue
            ratio=-np.median(b[:,r])/depth
            if not .53<=ratio<=1.8:continue
            ncc=float((a*b).sum()/max(1.,np.linalg.norm(a)*np.linalg.norm(b)))
            if ncc>=.80 and (best is None or ncc>best['correlation']):
                best=dict(correlation=ncc,normal_shift=d,depth_ratio=float(ratio))
        return best

    def review(self,points):
        rev=super().review(points)
        if self.phase not in ('shape','v3_5') or rev['source']=='NONE':return rev
        pts=np.asarray(points,int);_,d=self.evidence(pts)
        if d is None:return rev
        w=px(self.s,.028);n=len(pts);body_slice=slice(0,max(1,int(.65*n)))
        strong=d['good'][body_slice]
        body=float(np.mean(d['net'][body_slice][strong])) if strong.any() else 0.
        tail=float(np.mean(d['net'][-w:]))
        rev.update(body_net=body,tail_body_ratio=tail/body if body>0 else None)
        if n<2*w or rev.get('shift') is None:return rev
        match=self.shape_match(pts[-w:],rev['shift'])
        rev['shape_match']=match
        floor=max(2.5*self.noise,.022*self.contrast)
        if match:
            # Locate the beginning of the same line, keeping the normal displacement
            # consistent between adjacent windows. A single matching cap is insufficient.
            onset=n-w
            step=max(1,w//2)
            for end in range(n-step,w-1,-step):
                earlier=self.shape_match(pts[end-w:end],rev['shift'])
                if earlier is None or abs(earlier['normal_shift']-match['normal_shift'])>px(self.s,.012):break
                onset=end-w
            if n-onset>=w+step and onset>=w and d['good'][:onset].any():
                cut=int(pts[onset,0])
                if rev['cut'] is None or cut<rev['cut']:
                    rev.update(decision='TRIM_MATCHED_SHAPE',cut=cut)
                return rev
        if body<=2*floor or rev['cut'] is not None:return rev
        supported=d['good']&(d['net']>=max(floor,.20*body))
        if supported[-w:].mean()>.45 and not match:return rev
        static=rev['decision']=='NO_SUPPORTED_BOUNDARY' and rev['fraction']==0 and rev.get('duplicate',0)>=.5
        start=max(0,n-2*w)
        slope=np.arctan2(pts[-1,1]-pts[start,1],max(1,pts[-1,0]-pts[start,0]))
        k=max(0,start-2*w)
        prior=np.arctan2(pts[start,1]-pts[k,1],max(1,pts[start,0]-pts[k,0]))
        broken=np.convolve((d['net']<floor).astype(int),np.ones(max(2,w//2),int),'valid')
        relative=tail<.2*body and np.any(broken[-3*w:]>=max(2,w//2)) and (abs(slope-prior)>.20 or d['bipolar'][-w:].mean()>=.3)
        if not (match or static or relative):return rev
        for j in range(n-2,w-2,-1):
            if supported[j] and supported[j-w+1:j+1].mean()>=.65:
                cut=int(pts[j+1,0])
                if rev['cut'] is None or cut<=rev['cut']:
                    rev.update(cut=cut,decision='TRIM_MATCHED_SHAPE' if match else 'TRIM_STATIC_BODY' if static else 'TRIM_RELATIVE')
                return rev
        if static or match:
            rev.update(decision='REJECT_UNLOCATED_STATIC_BOUNDARY',cut=int(pts[0,0]))
        return rev
    def extend_clean(self,points):
        """Follow a faint, attached dark ridge only across a quiet, flat reference patch."""
        if self.ridge is None or len(points)<px(self.s,.15):return []
        x,y=points[-1];pts=np.asarray(points)
        length=px(self.s,.065);pad=px(self.s,.022)
        if x+length+1>=self.gray.shape[1] or y<2*pad or y+2*pad>=self.gray.shape[0]:return []
        block=self.aligned[y-2*pad:y+2*pad+1,x-pad:x+length+1]
        if not np.isfinite(block).all() or np.ptp(np.percentile(block,[2,98]))>max(3*self.noise,.025*self.contrast):return []
        start=pts[pts[:,0]>=x-px(self.s,.025)]
        if len(start)<3:return []
        slope=np.clip(np.polyfit(start[:,0]-x,start[:,1],1)[0],-.5,.5)
        floor=max(2*self.noise,.012*self.contrast)
        last=float(y);result=[];empty=0;support=[]
        for j in range(1,length+1):
            center=last+slope
            ys=np.arange(round(center)-1,round(center)+2)
            col=self.ridge[ys,x+j]
            k=int(np.argmax(col-.15*floor*abs(ys-center)))
            if col[k]<floor:
                empty+=1
                if empty>=px(self.s,.012):break
                continue
            empty=0
            last=float(ys[k])
            result.append([x+j,int(last)])
            support.append(float(col[k]))
        if len(result)<px(self.s,.018) or len(result)/(result[-1][0]-x)<.58 or np.median(support)<1.5*floor:return []
        if result[-1][0]-x>=length-1:return []
        return result
