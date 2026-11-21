"""Experimental causal gate adaptation. Coordinates in history are reference-image pixels."""
from collections import deque
import cv2
import numpy as np


def unit(v):
    return v / max(1e-9, np.linalg.norm(v))


def transform(points, matrix):
    return np.asarray(points) @ matrix[:, :2].T + matrix[:, 2]


class Strip:
    """Sample both frames at the same material coordinates, with transverse flanks."""
    def __init__(self, reference, current, matrix, origin, direction, xs, half):
        self.origin, self.direction = origin, unit(direction)
        self.normal = np.array([-self.direction[1], self.direction[0]])
        self.xs, self.half = xs, half
        grid = origin + xs[None,:,None]*self.direction + np.arange(-half,half+1)[:,None,None]*self.normal
        def sample(im, q):
            a=cv2.remap(im,q[:,:,0].astype('f'),q[:,:,1].astype('f'),cv2.INTER_LINEAR)
            return cv2.GaussianBlur(a.astype('f'),(3,3),.65)
        cur_grid=transform(grid,matrix)
        valid=np.ones(grid.shape[:2],bool)
        for im,q in [(reference,grid),(current,cur_grid)]:
            valid &= (q[:,:,0]>=3)&(q[:,:,0]<im.shape[1]-3)&(q[:,:,1]>=3)&(q[:,:,1]<im.shape[0]-3)
        self.ref=sample(reference,grid)
        self.cur=sample(current,cur_grid)
        band=np.abs(np.arange(-half,half+1))[:,None]>=half*.65
        noise=valid & band & (self.ref>140) & (self.cur>140)
        self.usable=noise.sum()>=32
        offset=np.median((self.cur-self.ref)[noise]) if self.usable else 0.
        def valley(a):
            return .5*(np.roll(a,3,axis=0)+np.roll(a,-3,axis=0))-a
        delta=np.minimum(self.ref-self.cur+offset,valley(self.cur)-valley(self.ref))
        self.score=np.minimum(delta,valley(self.cur))
        self.current_ridge=valley(self.cur)
        self.good=valid & (self.ref>130)
        self.good[:3]=False
        self.good[-3:]=False
        self.score[~self.good]=0
        self.threshold=max(3.,float(np.percentile(self.score[noise],95))) if self.usable else np.inf
        self.noise=noise

    def point(self,x,y):
        return self.origin+self.xs[x]*self.direction+(y-self.half)*self.normal

    def robust_suffix(self,line):
        # Check the same pixels against a ±1 px reference registration error.
        q=line-self.origin
        x=np.rint(q@self.direction-self.xs[0]).astype(int)
        y=np.rint(q@self.normal+self.half).astype(int)
        if min(x)<1 or max(x)+1>=self.ref.shape[1] or min(y)<1 or max(y)+1>=self.ref.shape[0]:return None
        ref_min=cv2.erode(self.ref,np.ones((3,3),np.uint8))[y,x]
        contrast=np.minimum(ref_min-self.cur[y,x],self.score[y,x])
        # Only the proximal two samples can overlap the edge under resampling.
        # A single-frame decision reports the actually supported distal suffix.
        k=0
        while k<2 and contrast[k]<self.threshold:k+=1
        tail=contrast[k:]
        if len(tail)>=4 and np.min(tail)>=self.threshold and np.median(tail)>=2.5*self.threshold:
            return line[k:]
        return None

    def include_current_ridge(self):
        # Only used on an already traced distal section. Require history and
        # new-image support as separate checks before accepting this refinement.
        self.score=np.maximum(self.score,.65*self.current_ridge)
        self.score[~self.good]=0
        self.threshold=max(self.threshold,float(np.percentile(self.score[self.noise],95)))

    def follow(self, first, y, last):
        """Bounded DP from one observed seed. Stop where cumulative support peaks."""
        field=np.clip(self.score[:,first:last+1]/self.threshold,0,3)-1
        h,w=field.shape
        prev=np.full(h,-np.inf);prev[y]=field[y,0]
        parents=np.zeros((w,h),dtype=np.int16)
        best=[prev.max()];ends=[y]
        for i in range(1,w):
            options=np.stack([np.r_[-np.inf,prev[:-1]]-.65,prev,np.r_[prev[1:],-np.inf]-.65])
            choice=options.argmax(axis=0)
            parents[i]=np.arange(h)+choice-1
            prev=options.max(axis=0)+field[:,i]
            ends.append(int(prev.argmax())); best.append(prev.max())
        n=int(np.argmax(best))
        ys=[ends[n]]
        for i in range(n,0,-1):ys.append(int(parents[i,ys[-1]]))
        ys.reverse()
        return np.arange(first,first+n+1),np.asarray(ys),best[n]

    def endpoint(self, xx, yy):
        if len(xx)<6 or xx[-1]+10>=len(self.xs):return False
        s=self.score[yy,xx]
        if np.mean(s[-min(8,len(s)):]>=self.threshold)<.6:return False
        # An endpoint needs a visible material patch ahead. Reject a sustained
        # continuation within the local cone, including a shallow turn.
        k=int(xx[-1]); y=int(yy[-1])
        for slope in [-.5,0.,.5]:
            ys=np.rint(y+slope*np.arange(1,11)).astype(int)
            xs=k+np.arange(1,11)
            if ys.min()<0 or ys.max()>=self.good.shape[0] or not self.good[ys,xs].all():return False
            hits=self.score[ys,xs]>=self.threshold*.7
            if np.convolve(hits[2:].astype(int),np.ones(4),mode='valid').max()>=4:return False
        return True


def outer_seed(strip):
    """Find the distal edge of the dark notch, then start only on bright material."""
    h,w=strip.ref.shape
    if not strip.usable:return None
    dark=(strip.ref<115).astype('uint8')
    dark=cv2.morphologyEx(dark,cv2.MORPH_CLOSE,np.ones((3,5),np.uint8))
    n,labels,stats,_=cv2.connectedComponentsWithStats(dark,8)
    candidates=[i for i in range(1,n) if stats[i,0]<=w*.22 and
                stats[i,1]<=strip.half+3 and stats[i,1]+stats[i,3]>strip.half-3 and stats[i,4]>=16]
    if not candidates:return None
    body=labels==max(candidates,key=lambda i:stats[i,4])
    cols=np.flatnonzero(body.sum(axis=0)>=3)
    if not cols.size:return None
    edge=int(cols[-1])
    ys=np.flatnonzero(body[:,edge])
    center=int(np.median(ys))
    best=None
    for x in range(edge+1,min(edge+9,w-15)):
        for y in range(max(3,center-6),min(h-3,center+7)):
            if not strip.good[y,x] or strip.score[y,x]<strip.threshold:continue
            xx,yy,gain=strip.follow(x,y,min(w-1,x+32))
            if len(xx)<6 or not strip.endpoint(xx,yy):continue
            if np.mean(strip.score[yy,xx]>=strip.threshold)<.8:continue
            merit=gain-.4*(x-edge)-.4*abs(y-center)
            if best is None or merit>best[0]:
                best=(merit,np.array([strip.point(i,j) for i,j in zip(xx,yy)]))
    return best[1] if best is not None else None


class GateAdapter:
    def __init__(self, reference, anchors):
        self.reference=reference
        delta=np.diff(anchors,axis=0)[0]
        self.forward=unit(np.array([delta[1],-delta[0]]))
        self.spacing=np.linalg.norm(delta)
        self.origin=np.mean(anchors,axis=0)
        self.history=deque(maxlen=5)
        self.starts=deque(maxlen=3)
        self.last_frame=-1

    def apply(self, i, im, matrix, previous_segments, stop, blocked_segments, reason, eligible=True):
        if i!=self.last_frame+1:raise ValueError('One ordered stream per adapter')
        self.last_frame=i
        inv=cv2.invertAffineTransform(matrix)
        def ref(points):return transform(points,inv)
        if previous_segments:
            line=ref(previous_segments[-1])
            if len(line)>=6:
                self.history.append((i,line[-1],unit(line[-1]-line[-6])))
            return previous_segments,'previous'
        if not eligible or i==0:return [],'ineligible'
        if stop in ('no_seed','temporal_pending') or reason=='no_unique_restart':
            half=max(12,min(30,round(self.spacing*.24)))
            strip=Strip(self.reference,im,matrix,self.origin,self.forward,
                        np.arange(-round(self.spacing/5),round(self.spacing*.85)+1),half)
            line=outer_seed(strip)
            if line is None:return [],'no_exterior_seed'
            hits=sum(i-frame<=3 and np.linalg.norm(line[0]-old[0])<=4 and
                     np.linalg.norm(line[-1]-old[-1])<=5 and
                     np.dot(unit(line[-1]-line[0]),unit(old[-1]-old[0]))>.7
                     for frame,old in self.starts)
            self.starts.append((i,line))
            if hits==0:
                line=strip.robust_suffix(line)
                if line is None:return [],'short_seed_pending'
            return [transform(line,matrix).tolist()],'short_seed'
        if reason not in ('terminal_strength','possible_forward_continuation') or not blocked_segments:
            return [],reason or stop
        line=ref(blocked_segments[-1])
        if len(line)<36:return [],'short_tail'
        # Estimate direction upstream of the disputed end. Its last tangent
        # can already be following background, particularly after a weak gap.
        d=unit(line[-22]-line[-36])
        start=line[-36]
        projected=np.dot(line[-1]-start,d)
        strip=Strip(self.reference,im,matrix,start,d,np.arange(0,int(np.ceil(projected))+32),18)
        if not strip.usable:return [],'no_local_material'
        delta=strip.score.copy()
        strip.include_current_ridge()
        # Reacquire from a supported point on the last measured section. The
        # endpoint itself may be displaced, so do not use it as a new seed.
        y=int(np.argmax(strip.score[strip.half-3:strip.half+4,0]))+strip.half-3
        xx,yy,_=strip.follow(0,y,len(strip.xs)-1)
        if not strip.endpoint(xx,yy):return [],'local_endpoint_unresolved'
        tail=np.array([strip.point(x,y) for x,y in zip(xx,yy)])
        if (abs(strip.xs[xx[-1]]-projected)>16 or np.mean(strip.score[yy,xx]>=strip.threshold)<.7
                or np.mean(delta[yy[-8:],xx[-8:]]>=strip.threshold*.65)<.5):
            return [],'insufficient_local_tail'
        endpoint=tail[-1]
        direction=unit(endpoint-tail[-min(8,len(tail))])
        radius=np.clip(.1*self.spacing,4,10)
        hits=0
        near_end=False
        # A preceding endpoint may lie on the currently observed trailing
        # section. Require one recent endpoint near this end as well, to avoid
        # validating a long unrelated tail via a remote shared prefix.
        for frame,old,prior_dir in self.history:
            if not 0<i-frame<=4:continue
            dist=np.linalg.norm(tail-old,axis=1)
            k=int(np.argmin(dist))
            tangent=unit(tail[min(k+3,len(tail)-1)]-tail[max(k-3,0)])
            near=np.linalg.norm(endpoint-old)<=radius and np.dot(direction,prior_dir)>.5
            on_trailing=dist[k]<=max(3.,.025*self.spacing) and np.dot(tangent,prior_dir)>.5
            near_end |= near
            hits+=int(near or on_trailing)
        if hits<2 or not near_end:return [],'weak_tip_history'
        # Splice only if the new local line intersects the original measured segment.
        k=int(np.argmin(np.linalg.norm(line-tail[0],axis=1)))
        if np.linalg.norm(line[k]-tail[0])>3:return [],'tail_disconnected'
        pts=np.concatenate((line[:k],tail))
        return blocked_segments[:-1]+[transform(pts,matrix).tolist()],'verified_local_tail'

