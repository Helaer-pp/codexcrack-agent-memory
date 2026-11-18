"""Stages 2 and 3. The reference may support an already observed valley only."""
import cv2
import numpy as np
from numba import njit
from . import detector as identity
from .detector import px


def valley_image(raw,scale):
    gray=raw.astype(np.float32)
    response=np.zeros_like(gray)
    for fraction in (.007,.014,.024):
        r=px(scale,fraction)
        if 2*r>=len(gray):
            continue
        flanks=np.minimum(gray[:-2*r],gray[2*r:])
        response[r:-r]=np.maximum(response[r:-r],np.where(flanks>40,flanks-gray[r:-r],0))
    smooth=cv2.GaussianBlur(response,(0,0),max(.35,scale/288),max(.35,.65*scale/288))
    evidence=.55*response+.45*smooth
    residual=gray-cv2.medianBlur(raw,3)
    stride=px(scale,.014)
    sample=residual[::stride,::stride]
    noise=max(1.,1.4826*float(np.median(np.abs(sample-np.median(sample)))))
    col=np.percentile(evidence[::px(scale,.01)],85,axis=0).astype(np.float32)
    local=cv2.blur(col.reshape(1,-1),(2*px(scale,.05)+1,1)).ravel()
    background=np.maximum.reduce([col,local,np.full_like(col,np.median(col))])
    return np.ascontiguousarray(evidence/np.maximum(4.,background+1.8*noise)),response,noise


def prepare(raw,hint,scale,stage):
    found=identity.locate_root(raw,hint,scale)
    if found is None:
        return None
    starts,front=found
    top=max(0,front[1]-px(scale,.55))
    bottom=min(raw.shape[0],front[1]+px(scale,.55)+1)
    left=max(0,min(x for x,y in starts)-px(scale,.035))
    sl=np.s_[top:bottom,left:]
    signal,response,noise=valley_image(raw[sl],scale)
    return (sl,(left,top),[(x-left,y-top) for x,y in starts],signal,response,scale,
            front[0]-left,raw[sl],noise,stage)


@njit(cache=False)
def trace_windowed(signal,bonus,x,y,horizon_limit,band,commit,gap,window):
    h,w=signal.shape
    path=[]
    weak=0
    slope=0.
    while x+1<w:
        horizon=min(horizon_limit,w-1-x)
        low,high=max(0,y-band),min(h,y+band+1)
        height=high-low
        prev=np.full(height,-1e10)
        prev[y-low]=0.
        parent=np.zeros((horizon,height),np.int32)
        for t in range(horizon):
            nxt=np.full(height,-1e10)
            for i in range(height):
                best=-1e10
                for j in range(max(0,i-2),min(height,i+3)):
                    score=prev[j]-.48*abs(i-j)-.16*abs(i-j-slope)
                    if score>best:
                        best=score
                        parent[t,i]=j
                nxt[i]=best+min(4.,signal[low+i,x+t+1])-1.1+bonus[low+i,x+t+1]
            prev=nxt
        idx=np.argmax(prev)
        line=np.empty(horizon,np.int32)
        for t in range(horizon-1,-1,-1):
            line[t]=low+idx
            idx=parent[t,idx]
        for t in range(min(commit,horizon)):
            yy=line[t]
            x+=1
            slope=.7*slope+.3*(yy-y)
            y=yy
            v=signal[y,x]
            path.append((x,y,v))
            weak=0 if v>=1 else weak+1
            if weak>=gap:
                return path
        if len(path)>=window+2:
            if sum([path[j][2]>=1 for j in range(len(path)-window,len(path))])<.5*window:
                break
    return path


def follow(signal,response,bonus,start,gray,scale,noise,stage):
    x,y=start
    r=px(scale,.014)
    seed=max(range(max(0,y-r),min(len(gray),y+r+1)),key=lambda j:min(4.,signal[j,x])-.35*abs(j-y)*288/scale)
    track=trace_windowed(signal,bonus,x,seed,px(scale,.07),px(scale,.076),px(scale,.017),
                         px(scale,.014),px(scale,.035))
    def reject(status):
        return dict(status=status,tip=None,points=[])
    if not track:
        return reject('NO_ROOT_ATTACHMENT')
    arr=np.asarray(track)
    xx,yy=arr[:,:2].astype(int).T
    depth=response[yy,xx]
    hit=(arr[:,2]>=1)&(depth>=3)
    idx=np.flatnonzero(hit)
    if not len(idx) or idx[0]>px(scale,.007):
        return reject('NO_ROOT_ATTACHMENT')
    body_end=max(1,round(.6*(idx[-1]+1)))
    supported_body=depth[:body_end][hit[:body_end]]
    body=float(np.median(supported_body)) if len(supported_body) else float(depth[idx[0]])
    win=px(scale,.021)
    for end in reversed(idx):
        if end+1<px(scale,.031):
            break
        inside=slice(max(0,end-win+1),end+1)
        if hit[inside].sum()<np.ceil(2*win/3):
            continue
        ex,ey=xx[end],yy[end]
        length=px(scale,.035)
        if ex+length>=gray.shape[1]:
            return reject('ROI_BOUNDARY')
        # Sample the observed continuation where it exists, then project the terminal
        # tangent into the material; side pixels quantify the local gray variability.
        forward=np.arange(ex+1,ex+length+1)
        slope=(ey-yy[max(0,end-win+1)])/max(1,min(end,win-1))
        forward_y=np.clip(np.rint(ey+slope*(forward-ex)).astype(int),0,len(gray)-1)
        available=min(length,len(xx)-end-1)
        forward_y[:available]=yy[end+1:end+1+available]
        after=float(np.median(response[forward_y,forward]))
        gray_values=gray[forward_y,forward].astype(float)
        after_mad=float(np.median(np.abs(gray_values-np.median(gray_values))))
        local=float(np.median(depth[inside]))
        support=float(np.mean(bonus[yy[inside],xx[inside]])) if stage in ('s3','s3t') else 0.
        required=max(.18*body,2*noise,after+.35*min(after_mad,noise*3))
        if local*(1+support)<required or local<=after:
            continue
        use=idx[idx<=end]
        pts=np.column_stack((xx[use],yy[use]))
        if stage in ('s3','s3t'):
            distance=np.linalg.norm(np.diff(np.vstack(([x,seed],pts)),axis=0),axis=1).sum()
            coherence=np.linalg.norm(pts[-1]-[x,seed])/max(1.,distance)
            early=min(len(xx),px(scale,.028))
            if hit[:early].mean()<.65 or coherence<.65:
                return reject('DETACHED_OR_FOLDED')
            # A bright gap between the segmented notch and a parallel crack-like stroke.
            bridge=gray[min(seed,y):max(seed,y)+1,x]
            if len(bridge)>px(scale,.007) and np.max(bridge)>np.median(gray[:,x]):
                return reject('BRIGHT_ROOT_GAP')
        points=pts.tolist()
        return dict(status='VALID',points=points,tip=points[-1],
                    terminal=dict(body_response_ref=body,local_response=local,after_response=after,
                                  material_mad=after_mad,noise=noise,required=required,
                                  bonus_mean=support,untrimmed_x=int(xx[idx[-1]])))
    return reject('NO_CERTIFIED_TAIL')


def predict(prepared,bonus):
    if prepared is None:
        return identity.predict(None,None)
    sl,origin,starts,signal,response,scale,front,gray,noise,stage=prepared
    if stage in ('s3','s3t'):
        bonus=bonus*np.clip(signal-1.,0,1)
        bonus[:,:front+px(scale,.2)+1]=0
    def candidate(s,r,b,p):
        record=follow(s,r,b,p,gray,scale,noise,stage)
        if stage=='s3t' and record['tip']:
            from .topology import check
            reason=check(gray,record['points'],front,scale)
            if reason:
                return dict(status=reason,tip=None,points=[])
        return record
    result=identity.predict(prepared[:7],bonus,candidate)
    terminal=result['diagnostics'].get('terminal')
    if terminal:
        terminal['untrimmed_x']+=origin[0]
    return result



