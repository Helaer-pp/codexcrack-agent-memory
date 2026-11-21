"""Cumulative weak-gap, taper, reference and adaptive presets with the V3 API."""
import cv2
import numpy as np
from numba import njit
from scipy.ndimage import median_filter
from research.notch_identity_v3 import detector as competition
from research.notch_identity_v3 import terminal as v3
from .detector import locate_root,px
from . import topology

STAGES=('gap','taper','weak_ref','v3_1')


def prepare(raw,hint,scale,stage='v3_1'):
    if stage not in STAGES:
        return v3.prepare(raw,hint,scale,stage)
    level=STAGES.index(stage)+1
    found,black,contrast=locate_root(raw,hint,scale,level==4)
    if found is None:
        return None
    starts,front=found
    top=max(0,front[1]-px(scale,.55));left=max(0,min(x for x,y in starts)-px(scale,.035))
    sl=np.s_[top:front[1]+px(scale,.55)+1,left:]
    raw_band=raw[sl]
    if level==1:
        signal,resp,noise=v3.valley_image(raw_band,scale)
    else:
        gray=raw_band.astype(np.float32);resp=np.zeros_like(gray)
        material=black+.17*contrast if level==4 else 40
        for frac in (.007,.014,.024):
            r=px(scale,frac)
            if 2*r<len(gray):
                side=np.minimum(gray[:-2*r],gray[2*r:])
                resp[r:-r]=np.maximum(resp[r:-r],np.where(side>material,side-gray[r:-r],0))
        smooth=cv2.GaussianBlur(resp,(0,0),max(.01,scale/288),max(.01,.65*scale/288))
        evidence=.55*resp+.45*smooth
        stride=px(scale,.014)
        residual=(gray-cv2.medianBlur(raw_band,3))[::stride,::stride]
        noise=max(contrast*.006 if level==4 else 1.,float(1.4826*np.median(abs(residual-np.median(residual)))),1e-6)
        col=np.percentile(evidence[::px(scale,.01)],85,axis=0).astype(np.float32)
        local=median_filter(col,size=2*px(scale,.05)+1,mode='nearest')
        floor=contrast*.023 if level==4 else 4.
        signal=np.ascontiguousarray(evidence/np.maximum(floor,np.maximum(col,local)+1.8*noise))
    return (sl,(left,top),[(x-left,y-top) for x,y in starts],signal,resp,scale,front[0]-left,raw_band,noise,stage,contrast)


@njit(cache=False)
def trace_windowed(sig,bonus,x,y,horizon,band,commit,gap,near_limit,max_gap,recover,soft):
    h,w=sig.shape
    start=x
    pts=[]
    slope=0.
    weak=0
    pending=-1
    first_loss=-1
    recovered=0
    stop=0
    while x+1<w:
        n=min(horizon,w-x-1); lo=max(0,y-band); hi=min(h,y+band+1); height=hi-lo
        prev=np.full(height,-1e10);prev[y-lo]=0.
        parents=np.zeros((n,height),np.int32)
        for t in range(n):
            nxt=np.full(height,-1e10)
            for i in range(height):
                best=-1e10
                for j in range(max(0,i-2),min(height,i+3)):
                    dy=i-j
                    score=prev[j]-.40*abs(dy)-.28*abs(dy-slope)
                    if score>best:
                        best=score;parents[t,i]=j
                v=sig[lo+i,x+t+1]
                drift=abs(lo+i-y-slope*(t+1))
                nxt[i]=best+min(v,4.)-1.1+bonus[lo+i,x+t+1]-.10*drift/max(1.,n*.3)
            prev=nxt
        idx=np.argmax(prev);line=np.empty(n,np.int32)
        for t in range(n-1,-1,-1):
            line[t]=lo+idx;idx=parents[t,idx]
        for t in range(min(n,commit)):
            yy=line[t];x+=1;v=sig[yy,x]
            if v>=1.:
                slope=.75*slope+.25*(yy-y)
            y=yy;pts.append((x,y,v))
            threshold=soft
            weak=0 if v>=threshold else weak+1
            if weak>=gap and pending<0:
                pending=len(pts)-weak
                if first_loss<0:first_loss=pts[pending][0]
                if x-start-weak>=near_limit:
                    # Retain measured taper samples in this terminal window only.
                    return pts if soft<1. else pts[:pending],first_loss,recovered,1
            if pending>=0:
                # Buffer the missing span and a complete support window. Roll back
                # all speculative observations if the budget or the evidence fails.
                if weak>max_gap or len(pts)-pending>max_gap+recover:
                    return pts[:pending],first_loss,recovered,2
                if len(pts)-pending>=gap+recover:
                    support=0.;count=0
                    for k in range(len(pts)-recover,len(pts)):
                        sv=pts[k][2];support+=min(4.,sv);count+=sv>=1.
                    if support/recover>=1.05 and count>=.8*recover and v>=1.:
                        pending=-1;recovered+=1;weak=0
    if pending>=0:
        return pts[:pending],first_loss,recovered,3
    return pts,first_loss,recovered,stop


def follow(sig,resp,bonus,start,gray,scale,noise,level,contrast):
    x,y=start;r=px(scale,.014)
    seed=max(range(max(0,y-r),min(len(gray),y+r+1)),key=lambda j:min(4.,sig[j,x])-.35*abs(j-y)*288/scale)
    track,loss,reconnections,stop=trace_windowed(sig,bonus,x,seed,px(scale,.07),px(scale,.076),px(scale,.017),px(scale,.014),
                                                 px(scale,.35),px(scale,.045),px(scale,.05),.80 if level>=2 else 1.)
    audit=dict(first_loss=int(loss) if loss>=0 else None,reconnections=int(reconnections),
               stop=('ROI_END','DISTAL_WEAK','GAP_NOT_REACQUIRED','GAP_AT_BOUNDARY')[stop],gate=None)
    def reject(reason):
        return dict(status=reason,tip=None,points=[],audit=audit)
    if not track:return reject('NO_ROOT_ATTACHMENT')
    arr=np.array(track);xx,yy=arr[:,:2].astype(int).T;score=arr[:,2];depth=resp[yy,xx]
    floor=.016*contrast if level==4 else 3.
    strong=(score>=1)&(depth>=floor)
    obs=strong if level==1 else (score>=.55)&(depth>=floor)
    idx=np.flatnonzero(obs); strong_ids=np.flatnonzero(strong)
    if not len(strong_ids) or strong_ids[0]>px(scale,.007):return reject('NO_ROOT_ATTACHMENT')
    be=max(1,round(.6*(strong_ids[-1]+1)));body_depth=depth[:be][strong[:be]]
    body=float(np.median(body_depth)) if len(body_depth) else float(depth[strong_ids[0]])
    win=px(scale,.021);ahead=px(scale,.035)
    ceiling=len(xx)-1
    if level>=2:
        # Look for extinction followed by a contrast rebound after a sustained fade.
        # Require two distinct scales of decay, so one isolated weak pixel cannot cut a trace.
        sm=median_filter(depth,size=max(3,2*px(scale,.006)+1),mode='nearest')
        separation=px(scale,.04)
        j=np.arange(max(2*separation,px(scale,.15)),len(sm)-separation)
        if len(j):
            low=depth[j]<np.maximum(2*noise,.14*body)
            decline=(sm[j-2*separation]>np.maximum(2.5*depth[j],.35*body)) & (sm[j-separation]>1.3*depth[j])
            for cut in j[low & decline]:
                # A true body can resume after a weak local minimum. A periodic,
                # low-amplitude suffix lasting several correlation lengths is
                # stronger evidence of a switch into substrate texture.
                tail=depth[cut+1:]
                if len(tail)<px(scale,.12):continue
                before=sm[cut-2*separation]
                if np.percentile(tail,85)>.80*before:continue
                samples=tail[:px(scale,.22)].astype(float)
                samples-=median_filter(samples,size=2*px(scale,.018)+1,mode="nearest")
                corr=0.
                for lag in range(px(scale,.009),px(scale,.035)+1):
                    a=samples[:-lag];b=samples[lag:]
                    den=np.linalg.norm(a)*np.linalg.norm(b)
                    if den and len(samples)>3*lag:
                        a2=samples[:-2*lag];b2=samples[2*lag:]
                        d2=np.linalg.norm(a2)*np.linalg.norm(b2)
                        if d2:
                            corr=max(corr,min(float(a@b/den),float(a2@b2/d2)))
                if corr>.60:
                    ceiling=int(cut);audit['extinction_limit']=int(xx[ceiling]);break
    for end in reversed(idx[idx<=ceiling]):
        if end+1<px(scale,.031):break
        sl=slice(max(0,end-win+1),end+1)
        if obs[sl].sum()<np.ceil(2*win/3):continue
        ex,ey=xx[end],yy[end]
        if ex+ahead>=gray.shape[1]:return reject('ROI_BOUNDARY')
        slope=(ey-yy[max(0,end-win+1)])/max(1,min(end,win-1))
        fx=np.arange(ex+1,ex+ahead+1)
        fy=np.clip(np.rint(ey+slope*(fx-ex)).astype(int),0,len(gray)-1)
        n=min(ahead,len(xx)-end-1);fy[:n]=yy[end+1:end+1+n]
        front=float(np.median(resp[fy,fx]));local=float(np.median(depth[sl]))
        front_gray=gray[fy,fx].astype(float);mad=float(np.median(abs(front_gray-np.median(front_gray))))
        assist=float(bonus[yy[sl],xx[sl]].mean())
        strong_gate=(strong[end] and strong[sl].sum()>=np.ceil(2*win/3)
                     and local*(1+assist if level<3 else 1)>=max(.18*body,2*noise,front+.35*min(mad,3*noise)) and local>front)
        smooth=float(np.mean(np.abs(np.diff(yy[sl])-slope))) if end>0 and len(yy[sl])>1 else 0.
        prior=depth[max(0,end-px(scale,.09)):max(1,end-win+1)]
        nearby_body=min(body,float(np.median(prior))) if len(prior) else body
        taper=(level>=2 and local>max(1.6*front,2.5*max(noise,mad),.25*nearby_body)
               and smooth<.85 and float(score[sl].mean())>=.80)
        if not (strong_gate or taper):continue
        # A soft sample is public only when the independent tapered-tail gate passes.
        use=np.union1d(strong_ids[strong_ids<=end],idx[(idx<=end)&(idx>end-win)]) if taper else strong_ids[strong_ids<=end]
        pts=np.column_stack((xx[use],yy[use]))
        dist=np.linalg.norm(np.diff(np.vstack(([x,seed],pts)),axis=0),axis=1).sum()
        if strong[:px(scale,.028)].mean()<.65 or np.linalg.norm(pts[-1]-[x,seed])/max(1.,dist)<.65:
            return reject('DETACHED_OR_FOLDED')
        bridge=gray[min(seed,y):max(seed,y)+1,x]
        if len(bridge)>px(scale,.007) and bridge.max()>np.median(gray[:,x]):return reject('BRIGHT_ROOT_GAP')
        audit['gate']='STRONG' if strong_gate else 'TAPER'
        audit.update(body=float(body),nearby_body=nearby_body,tail=local,front=front,noise=noise,row_mad=mad)
        points=pts.tolist()
        return dict(status='VALID',points=points,tip=points[-1],audit=audit)
    return reject('NO_CERTIFIED_TAIL')


def predict(prepared,bonus):
    if prepared is None:return competition.predict(None,None)
    if len(prepared)==10:return v3.predict(prepared,bonus)
    sl,(left,top),starts,sig,resp,scale,front,gray,noise,stage,contrast=prepared
    level=STAGES.index(stage)+1
    if bonus is None:bonus=np.zeros_like(sig)
    if level<3:
        bonus=bonus*np.clip(sig-1.,0,1)
    else:
        bonus=np.where((sig>=.55)&(sig<1.),np.clip(bonus,0,.08),0).astype(np.float32)
    bonus[:,:front+px(scale,.2)+1]=0
    audits=[]
    def candidate(s,rank_response,b,p):
        rec=follow(s,resp,b,p,gray,scale,noise,level,contrast)
        if rec['tip']:
            reason=topology.check(gray,rec['points'],front,scale,level==4)
            if reason:rec.update(status=reason,points=[],tip=None)
        info=rec['audit']
        if info['first_loss'] is not None:info['first_loss']+=left
        if 'extinction_limit' in info:info['extinction_limit']+=left
        audits.append(info)
        return rec
    # V3 already normalizes length by anchor spacing. Normalize the gray depth
    # used by its prefix-ranking statistic as well, before applying its log score.
    rank_resp=np.clip(resp/contrast,0,1)*255 if level==4 else resp
    result=competition.predict((sl,(left,top),starts,sig,rank_resp,scale,front),bonus,candidate)
    for d,a in zip(result['diagnostics']['candidates'],audits):d['trace']=a
    return result




