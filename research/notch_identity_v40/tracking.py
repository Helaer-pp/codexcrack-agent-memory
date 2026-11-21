"""Independent incremental tracks in current-grid coordinates (before input ROI offset)."""
import cv2
import numpy as np
from research.notch_identity_v31.detector import px
from research.notch_identity_v31.terminal import trace_windowed
from research.notch_identity_v31 import topology
from research.notch_identity_v32.guards import open_rim

def roots(sig,front,mid,s):
    pad=px(s,.16);length=px(s,.026)
    lo=max(0,front-px(s,.14));hi=min(sig.shape[1]-length-1,front+px(s,.10))
    a=max(0,mid-pad);b=min(len(sig),mid+pad+1)
    if hi<lo or a>=b:return []
    patch=sig[a:b,lo:hi+length+1]
    # Favor the first visible column of a coherent ridge. Retain both mouth lips.
    score=np.zeros((len(patch),hi-lo+1),np.float32)
    for slope in (-.45,0,.45):
        mass=np.zeros_like(score)
        for j in range(length):
            yy=np.clip(np.arange(len(patch))+round(slope*j),0,len(patch)-1)
            mass+=np.log1p(patch[yy,j:j+score.shape[1]])
        score=np.maximum(score,mass/length)
    score*=patch[:,:score.shape[1]]>=1.0
    score/=1+np.maximum(np.arange(lo,hi+1)-front,0)/max(1,.10*s)
    picks=[]
    for _ in range(10):
        y,x=np.unravel_index(score.argmax(),score.shape)
        if score[y,x]<.75:break
        picks.append((lo+int(x),a+int(y)))
        dx,dy=px(s,.035),px(s,.014)
        score[max(0,y-dy):y+dy+1,max(0,x-dx):x+dx+1]=0
    return picks

def trace(e,p):
    sig=np.ascontiguousarray(e['signal']);zero=np.zeros_like(sig)
    s=p[5];front=p[6];top=e['top'];mid=int(np.median(np.array(p[2])[:,1]))-top
    candidates=[];starts=roots(sig,front,mid,s)
    for x,y in starts:
        track,_,_,_=trace_windowed(sig,zero,x,y,px(s,.065),px(s,.055),px(s,.016),
            px(s,.016),px(s,.34),px(s,.05),px(s,.040),.78)
        if len(track)<px(s,.026):continue
        arr=np.vstack(([x,y,sig[y,x]],np.array(track)))
        xx,yy=arr[:,:2].astype(int).T;val=arr[:,2]
        # Trim a reconnection that lands on a different pre-existing increment ridge.
        weak=val<.78;segments=np.flatnonzero(np.diff(np.r_[False,weak,False])).reshape(-1,2)
        end=len(val);events=[]
        for a,b in segments:
            if b-a<px(s,.014) or b>=len(val):continue
            w=px(s,.025);prev=max(0,a-w)
            slope=(yy[a-1]-yy[prev])/max(1,a-1-prev) if a else 0
            residual=abs(yy[b]-(yy[max(0,a-1)]+slope*(b-a+1)))
            ahead=min(len(yy)-1,b+w)
            exit_slope=(yy[ahead]-yy[b])/max(1,ahead-b)
            orientation=e['orientation'][yy[b:ahead+1],xx[b:ahead+1]]
            # A reconnection must be sustained, directionally resolved increment.
            if np.median(orientation)<.15 or np.mean(val[b:ahead+1]>=1.15)<.5:
                end=a;break
            if residual>max(1,.006*s) or abs(slope-exit_slope)>.36:
                end=a;break
            # Measure both edges of the bridge against the extrapolated incoming ridge.
            if b-a>=px(s,.025) and np.max(np.abs(yy[b:ahead+1]-(yy[a-1]+slope*(np.arange(b,ahead+1)-a+1))))>max(1,.006*s):
                end=a;break
            events.append([int(xx[a]),int(xx[b]),int(xx[min(len(xx)-1,b+w-1)])])
        val=val[:end];xx=xx[:end];yy=yy[:end]
        if not len(val):continue
        # Off-axis measurements estimate the clutter a ridge-seeking DP can collect.
        offsets=np.arange(px(s,.035),px(s,.10)+1,2)
        side=sig[np.clip(yy[:,None]+np.r_[-offsets,offsets],0,len(sig)-1),xx[:,None]]
        background=max(1.15,float(np.percentile(side,97)))
        w=px(s,.033)
        strength=np.convolve(val,np.ones(w)/w,'valid') if len(val)>=w else np.empty(0)
        dense=np.convolve((val>=background).astype(float),np.ones(w)/w,'valid') if len(val)>=w else []
        supported=np.flatnonzero((np.asarray(dense)>=.66)&(strength>=1.20*background))
        if not len(supported):continue
        end=int(supported[-1]+w//2+1)
        # A fading oriented line can give way to a long isotropic spot field.
        # Demand a persistent loss of direction relative to the preceding trunk.
        orientation=e['orientation'][yy,xx]
        block=px(s,.065)
        eligible=[]
        if end>2*block:
            # Count gates are necessary conditions for the exact order statistics.
            above=np.convolve((orientation[:end]>.72).astype(int),np.ones(block,int),'valid')
            below=np.cumsum((orientation[:end]<.28)[::-1],dtype=int)[::-1]
            js=np.arange(block,end-block)
            eligible=js[(above[js-block]>=block//2)&(below[js]>=np.floor(.8*(end-js-1))+1)]
        for j in eligible:
            if (np.median(orientation[j-block:j])>.72 and
                np.quantile(orientation[j:end],.80)<.28 and
                np.median(val[j:end])<.4*np.median(val[j-block:j])):
                end=j+1;break
        val=val[:end];xx=xx[:end];yy=yy[:end]
        ids=np.flatnonzero(val>=.85)
        if not len(ids):continue
        w=px(s,.022)
        last=next((int(j) for j in ids[::-1] if j>=w and (val[j-w+1:j+1]>=.8).mean()>=.60),None)
        if last is None or xx[last]<front+px(s,.027) or xx[last]-x<px(s,.026):continue
        obs=ids[ids<=last]
        if len(obs)/(last+1)<.58:continue
        path=np.c_[xx[obs],yy[obs]+top]
        # Recover the observed mouth-side prefix omitted by a seed inside a ridge.
        prefix=[];row=y
        for col in range(x-1,max(front-1,x-px(s,.035)-1),-1):
            window=np.arange(max(0,row-1),min(len(sig),row+2))
            row=int(window[np.argmax(sig[window,col])])
            if sig[row,col]<background:break
            prefix.append([col,row+top])
        if prefix:path=np.vstack((prefix[::-1],path))
        # A terminal observation at the image edge has no measured forward background.
        if path[-1,0]+w>=sig.shape[1]:continue
        near=val[:min(last+1,px(s,.18))]
        rank=float(np.mean(np.log1p(near))*min(1.,len(obs)/max(1,.12*s))/(1+max(0,x-front)/max(1,.12*s)))
        candidates.append(dict(root=path[0].tolist(),points=path,rank=rank,events=[ev for ev in events if ev[2]<=xx[last]]))
    return candidates,len(starts)

def admissible(candidates,p):
    if not candidates:return None,{}
    gray=p[7];scale=p[5];front=p[6];mid=float(np.median(np.array(p[2])[:,1]))
    # Check the published root is connected to the original mouth (gray geometry
    # only). Track B's seeds, DP scores and terminal certification use E_diff.
    area=gray[:,:min(gray.shape[1],front+px(scale,.12)+1)]
    material=float(np.percentile(area,85))
    _,cc=cv2.connectedComponents((area<material-max(3.5*p[8],.07*p[-1])).astype('uint8'),connectivity=8)
    l=max(1,min(x for x,y in p[2])+1)
    core=area[:,:l]<material-.45*p[-1]
    counts=np.bincount(cc[:,:l][core],minlength=2);counts[0]=0
    body=counts.argmax();rejected={}
    # A path ending on the boundary of a resolved dark closed loop is ineligible,
    # including short candidates that never reach the loop's rightmost pixel.
    mask=(gray<material-max(4*p[8],.12*p[-1])).astype('uint8')
    rad=px(scale,.005)
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*rad+1,2*rad+1)))
    contours,tree=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    holes=[h for h,t in zip(contours,tree[0] if tree is not None else []) if t[3]>=0 and cv2.contourArea(h)>.00045*scale**2]
    for c in sorted(candidates,key=lambda r:-r['rank']):
        x,y=c['root'];path=c['points'];xs,ys=path.T
        why=None
        if not body or cc[y,x]!=body:why='DETACHED_ROOT'
        elif any(abs(cv2.pointPolygonTest(h,tuple(map(float,path[-1])),True))<max(2,.018*scale) for h in holes):why='CLOSED_RIM'
        elif np.median(gray[ys,xs])>=material:why='BRIGHT_NOISE'
        else:
            why=topology.check(gray,path,front,scale,True)
            if not why and open_rim(path,front,mid,scale,gray):why='OPEN_RIM'
        if not why:return c,rejected
        rejected[why]=rejected.get(why,0)+1
    return None,rejected
