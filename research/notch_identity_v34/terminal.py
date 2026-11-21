"""V3.4 normal-profile evidence, measured on the frozen V3.2 candidate geometry."""
import time
import numpy as np
from scipy.ndimage import median_filter
from research.notch_identity_v31 import topology
from research.notch_identity_v31.detector import px
from research.notch_identity_v31.terminal import trace_windowed
from research.notch_identity_v32 import terminal as base, reference
from . import guards,competition
from .reference import Support

STAGES=('unlock','shield','branch','v3_4')

def prepare(raw,hint,scale,stage='v3_4'):
    if stage not in STAGES:raise ValueError(stage)
    prep=base.prepare(raw,hint,scale,'v3_2')
    return (*prep[:-2],stage,raw,prep[-1]) if prep is not None else None

def follow(sig,resp,bonus,start,gray,scale,noise,stage,contrast,hard_cut=None,support=None):
    x,y=start;r=px(scale,.014)
    seed=max(range(max(0,y-r),min(len(gray),y+r+1)),key=lambda j:min(4.,sig[j,x])-.35*abs(j-y)*288/scale)
    track,loss,reconnections,stop=trace_windowed(sig,bonus,x,seed,px(scale,.07),px(scale,.076),px(scale,.017),px(scale,.014),
                                                 px(scale,.35),px(scale,.045),px(scale,.05),.80)
    audit=dict(first_loss=int(loss) if loss>=0 else None,reconnections=int(reconnections),
               stop=('ROI_END','DISTAL_WEAK','GAP_NOT_REACQUIRED','GAP_AT_BOUNDARY')[stop],gate=None)
    def reject(reason):
        return dict(status=reason,tip=None,points=[],audit=audit)
    if not track:return reject('NO_ROOT_ATTACHMENT')
    arr=np.array(track);xx,yy=arr[:,:2].astype(int).T;score=arr[:,2];depth=resp[yy,xx]
    # The frozen DP returns the first distal weak interval immediately.  Obtain
    # bounded downstream observations for the bilateral test, never publish the
    # speculative suffix unless both sides pass independently.
    if stop==1 and support is not None and stage!='unlock' and support.coarse['status']=='OK':
        last_x,last_y=xx[-1],yy[-1]
        end=min(sig.shape[1],last_x+px(scale,.060)+1)
        if last_x+1<end:
            extra,_,_,_=trace_windowed(sig[:,:end],bonus[:,:end],last_x,last_y,px(scale,.07),px(scale,.076),
                px(scale,.017),end+1,end+1,end+1,px(scale,.05),.80)
            if extra:
                trial=np.vstack((arr,np.asarray(extra)))
                tx,ty=trial[:,:2].astype(int).T
                first=int(np.searchsorted(tx,xx[-1]-px(scale,.014)+1))
                if support.protect(tx,ty,first):
                    arr=trial;xx,yy=tx,ty;score=arr[:,2];depth=resp[yy,xx];audit['lookahead']=len(extra)
    skip=0;waived=[];allowed=np.empty(0,np.int64)
    while True:
        limit,why,events=guards.inspect_track(arr,gray,sig,scale,x,True,True,skip,allowed)
        if why==3 and support is not None and support.accept_lip(xx,yy,events[-1]):
            allowed=np.append(allowed,int(xx[limit]));waived.append(int(xx[limit]));continue
        if why not in (1,2) or support is None or not support.protect(xx,yy,limit):break
        waived.append(int(xx[limit]))
        skip=max(skip+1,limit+px(scale,.025))
    audit['waived_lip']=allowed.tolist()
    audit['waived']=waived
    audit.update(geometry=('CLEAR','DISTAL_BRIGHT_GAP','DISTAL_KINK','OTHER_LIP')[why],
                 geometry_cut=int(xx[limit]) if limit<len(xx) else None,events=[list(e) for e in events])
    if hard_cut is not None:limit=min(limit,int(np.searchsorted(xx,hard_cut)))
    if limit==0:return reject('GEOMETRY_CUT_AT_ROOT')
    xx,yy,score,depth=xx[:limit],yy[:limit],score[:limit],depth[:limit]
    floor=.016*contrast
    strong=(score>=1)&(depth>=floor)
    obs= (score>=.55)&(depth>=floor)
    idx=np.flatnonzero(obs); strong_ids=np.flatnonzero(strong)
    if not len(strong_ids) or strong_ids[0]>px(scale,.007):return reject('NO_ROOT_ATTACHMENT')
    be=max(1,round(.6*(strong_ids[-1]+1)));body_depth=depth[:be][strong[:be]]
    body=float(np.median(body_depth)) if len(body_depth) else float(depth[strong_ids[0]])
    win=px(scale,.021);ahead=px(scale,.035)
    ceiling=len(xx)-1
    if len(xx):
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
    trough=guards.rebound_cut(depth,noise,scale)
    if trough<len(depth) and support is not None and support.protect(xx,yy,trough):
        audit['waived'].append(int(xx[trough]))
        trough=len(depth)
    if trough<len(depth):
        ceiling=min(ceiling,trough-1)
        audit['rebound_cut']=int(xx[trough])
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
        strong_gate=(strong[end] and strong[sl].sum()>=np.ceil(2*win/3)
                     and local>=max(.18*body,2*noise,front+.35*min(mad,3*noise)) and local>front)
        smooth=float(np.mean(np.abs(np.diff(yy[sl])-slope))) if end>0 and len(yy[sl])>1 else 0.
        prior=depth[max(0,end-px(scale,.09)):max(1,end-win+1)]
        nearby_body=min(body,float(np.median(prior))) if len(prior) else body
        taper=(local>max(1.6*front,2.5*max(noise,mad),.25*nearby_body)
               and smooth<.85 and float(score[sl].mean())>=.80)
        if taper:
            allowed,evidence=guards.taper_evidence(xx,yy,depth,end,front,mad,noise,scale)
            taper=allowed
            if not allowed:audit['taper_rejections']=audit.get('taper_rejections',0)+1
        confirmed=False
        if (not strong_gate and not taper and support is not None and waived and ex>waived[0]
                and why in (1,2) and limit<len(arr) and end>=limit-px(scale,.014)
                and strong[end] and strong[sl].mean()>=.65):
            # A confirmed weak gap can lead to a new, lower-contrast trunk. The
            # original trunk-relative threshold may no longer represent this segment.
            left_pts=arr[max(0,end-win+1):end+1,:2].astype(int)
            right_pts=arr[limit:limit+ahead,:2].astype(int)
            if len(right_pts)>=px(scale,.014):
                _,lt=support.evidence(left_pts);_,rt=support.evidence(right_pts)
                confirmed=(lt is not None and rt is not None and lt['good'].mean()>=.75 and
                           rt['good'].mean()<=.25 and rt['dc'].mean()<.5*lt['dc'].mean())
        if not (strong_gate or taper or confirmed):continue
        # A soft sample is public only when the independent tapered-tail gate passes.
        use=np.union1d(strong_ids[strong_ids<=end],idx[(idx<=end)&(idx>end-win)]) if taper else strong_ids[strong_ids<=end]
        pts=np.column_stack((xx[use],yy[use]))
        dist=np.linalg.norm(np.diff(np.vstack(([x,seed],pts)),axis=0),axis=1).sum()
        if strong[:px(scale,.028)].mean()<.65 or np.linalg.norm(pts[-1]-[x,seed])/max(1.,dist)<.65:
            return reject('DETACHED_OR_FOLDED')
        bridge=gray[min(seed,y):max(seed,y)+1,x]
        if len(bridge)>px(scale,.007) and bridge.max()>np.median(gray[:,x]):return reject('BRIGHT_ROOT_GAP')
        audit['gate']='REF_REACQUIRED' if confirmed else 'STRONG' if strong_gate else 'TAPER'
        audit.update(body=float(body),nearby_body=nearby_body,tail=local,front=front,noise=noise,row_mad=mad)
        points=pts.tolist()
        return dict(status='VALID',points=points,tip=points[-1],audit=audit)
    return reject('NO_CERTIFIED_TAIL')


def predict(prepared,bonus,fixed=None):
    """fixed is the optional geometrically aligned reference in the input ROI."""
    if prepared is None:return competition.predict(None,None)
    sl,(left,top),starts,sig,resp,scale,front,gray,noise,stage,raw,contrast=prepared
    support=None
    if fixed is not None:
        support=Support(raw,fixed,sl,(left,top),np.median(starts,axis=0),scale,noise,contrast)
        support.stage=stage
    protection=support
    if bonus is None:bonus=np.zeros_like(sig)
    bonus=np.where((sig>=.55)&(sig<1.),np.clip(bonus,0,.08),0).astype(np.float32)
    bonus[:,:front+px(scale,.2)+1]=0
    ref_time=[];audits=[];cache={};mid=float(np.median([p[1] for p in starts]))
    def candidate(s,rank_response,b,p):
        rec=follow(s,resp,b,p,gray,scale,noise,stage,contrast,support=protection)
        a=rec['audit']
        if rec['tip'] and support is not None:
            ref=support.review(rec['points'])
            if ref['cut'] is not None:
                oldtip=rec['tip']
                rec=follow(s,resp,b,p,gray,scale,noise,stage,contrast,ref['cut'],protection)
                a=rec['audit']
                ref['before_tip']=[oldtip[0]+left,oldtip[1]+top]
                ref['cut']+=left
            a['reference']=ref
            if rec['tip']:
                rank=support.rank(rec['points']);a['increment_rank']=rank
                rec['rank_bonus']=rank['weight'];rec['tier']=rank.get('tier',0)
        if rec['tip']:
            reason=topology.check(gray,rec['points'],front,scale,True)
            if not reason and guards.open_rim(rec['points'],front,mid,scale,gray):
                reason='OUTWARD_OPEN_RIM'
            if reason:rec.update(status=reason,points=[],tip=None)
        for name in ('first_loss','extinction_limit','geometry_cut','rebound_cut'):
            if a.get(name) is not None:a[name]+=left
        for event in a.get('events',[]):
            for j in range(3):event[j]+=left
        for key in ('waived','waived_lip'):a[key]=[v+left for v in a.get(key,[])]
        audits.append(a)
        return rec
    result=competition.predict((sl,(left,top),starts,sig,np.clip(resp/contrast,0,1)*255,scale,front),bonus,candidate)
    for c,a in zip(result['diagnostics']['candidates'],audits):c['trace']=a
    result['diagnostics']['coarse']=support.coarse if support else None
    return result
