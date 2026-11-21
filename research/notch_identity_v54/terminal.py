"""Valley-to-peak endpoint qualification and local mouth review on the frozen clean field."""
from dataclasses import replace
import cv2
import numpy as np
from research.notch_identity_v53 import terminal as previous
from research.notch_identity_v53.terminal import lattice, unwind, global_free_end_dp, baseline, topology, px

STAGES=('valley','v5_4')

def prepare(raw,hint,scale,stage='v5_4'):
    if stage not in STAGES:
        raise ValueError(stage)
    scene=previous.prepare(raw,hint,scale,'local_peaks')
    if scene is not None:
        scene.stage=stage
    return scene

def fields(p,fixed):
    return previous.fields(replace(p,stage='local_peaks'),fixed)

def increments(score,path):
    segment=score[path[:,0],path[:,1]].astype(float)
    slope=np.diff(path[:,1],prepend=path[0,1])
    segment-=.13*np.abs(slope)+.19*np.abs(np.diff(slope,prepend=0))
    segment[0]=max(0.,segment[0])
    return segment

def extension_evidence(score,path,s):
    result=dict(positive_extension=False,tail_length=0,net_mean=None,support=None,longest_run=0,
                valley_x=None,valley_value=None,valley_gain=None,peak_value=None,ending_mean=None)
    if not len(path):
        return result
    inside=np.flatnonzero(path[:,0]>.19*s)
    if not len(inside):
        return result
    gain=increments(score,path)
    curve=np.cumsum(gain)
    k=int(inside[np.argmin(curve[inside])])
    result.update(valley_x=int(path[k,0]),valley_value=float(curve[k]),valley_gain=float(curve[-1]-curve[k]),peak_value=float(curve[-1]))
    rising=path[k+1:]
    if not len(rising):
        return result
    strong=score[rising[:,0],rising[:,1]]>.08
    breaks=np.flatnonzero(np.diff(np.r_[False,strong,False]))
    run=max((b-a for a,b in zip(breaks[::2],breaks[1::2])),default=0)
    net=float(gain[k+1:].mean())
    ending=float(gain[max(k+1,len(path)-px(s,.014)):].mean())
    ok=(len(rising)>=px(s,.030) and result['valley_gain']>=max(1.,.010*s) and
        net>.075 and strong.mean()>=.54 and run>=px(s,.012) and ending>.06 and gain[-1]>0)
    result.update(positive_extension=bool(ok),tail_length=len(rising),net_mean=net,support=float(strong.mean()),longest_run=int(run),ending_mean=ending)
    return result

def qualified_peak(p,score,values,back,direction):
    maxima=(values>=cv2.dilate(values,np.ones((3,3),np.uint8))) & (values>.052*p.scale) & (score>.08)
    maxima[:int(.20*p.scale)+1]=False
    xs,ys=np.where(maxima)
    for n,j in enumerate(np.argsort(-values[xs,ys],kind='stable'),1):
        x,y=xs[j],ys[j]
        path=unwind(back,x,y,direction[x,y])
        if not extension_evidence(score,path,p.scale)['positive_extension']:
            continue
        if topology.check(p.local,path+[p.front,0],p.front,p.scale,True)!='CLOSED_RIM':
            return path,float(values[x,y]),n,len(xs)
    return np.empty((0,2),np.int32),0.,len(xs),len(xs)

def mouth_profile(p,fixed,reg,score):
    n=min(len(score),px(p.scale,.27)+1)
    gray=p.local[:,p.front:p.front+n].astype(np.float32)
    dx,dy=reg['shift']
    ref=cv2.warpAffine(fixed[p.sl],np.float32([[1,0,p.front+dx],[0,1,dy]]),(n,len(gray)),
        flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
    diff=np.where(np.isfinite(ref),ref-gray,0.)
    radius=max(2,px(p.scale,.008))
    def contrast(im):
        pad=cv2.copyMakeBorder(im,radius,radius,0,0,cv2.BORDER_REPLICATE)
        return np.maximum(0,im-np.maximum(pad[2*radius:],pad[:-2*radius]))
    floor=max(2.8*p.noise,.028*p.span)
    dark=contrast(-gray)/np.maximum(floor,np.maximum(diff,0.))
    ref_valley=contrast(-np.where(np.isfinite(ref),ref,gray))
    added=np.maximum(0,contrast(-gray)-ref_valley)/floor
    ridge=contrast(diff)/floor
    bright=cv2.dilate(gray,np.ones((2*px(p.scale,.030)+1,1),np.uint8))-gray
    return dark.T,ridge.T,(bright/p.span).T,(diff/floor).T,added.T

def mouth_test(track,p,score,profile):
    dark,ridge,bright,delta,added=profile
    x,y=track[-max(3,px(p.scale,.025)):].T
    core=float(np.mean(dark[x,y]>.22))
    glare=float(np.mean(bright[x,y]>.12))
    incremental=float(np.mean(delta[x,y]>1))
    ahead=score[x[-1]+1:x[-1]+1+px(p.scale,.018),max(0,y[-1]-1):y[-1]+2]
    cliff=bool(len(ahead) and np.mean(np.max(ahead,axis=1)<-.15)>=.60)
    new_core=float(np.mean((dark[x,y]>.22)&(added[x,y]>.5)))
    static_toe=(new_core<.36 and glare>=.70 and cliff)
    # A very short dark toe may finish on the bright-to-gray boundary of a displaced reflection.
    # At the terminal pixel and immediately downstream compare the fine valley to residual difference.
    end_x,end_y=int(x[-1]),int(y[-1])
    ahead_x=slice(end_x,min(len(dark),end_x+1+px(p.scale,.015)))
    band=slice(max(0,end_y-1),end_y+2)
    flat_red=np.mean((np.max(dark[ahead_x,band],axis=1)<.22)&(np.max(delta[ahead_x,band],axis=1)>1))
    toe_edge=(track[-1,0]-track[0,0]<=.055*p.scale and glare>=.70 and cliff and flat_red>=1/3)
    dead=incremental>=.48 and ((core<.36 and (glare>=.35 or cliff)) or static_toe or toe_edge)
    return dict(dead=bool(dead),dark_fraction=core,new_dark_fraction=new_core,glare_fraction=glare,diff_fraction=incremental,flat_red=float(flat_red),cliff=cliff)

def other_lip(p,global_path,score,values,back,direction,profile):
    dark,ridge,_,delta,_=profile
    ok=(values>=cv2.dilate(values,np.ones((3,3),np.uint8))) & (values>.04*p.scale)
    ok[:int(.10*p.scale)]=False
    ok[int(.22*p.scale)+1:]=False
    xs,ys=np.where(ok)
    for j in np.argsort(-values[xs,ys],kind='stable'):
        x,y=xs[j],ys[j]
        if abs(y-global_path[-1,1])<.025*p.scale:
            continue
        tr=unwind(back,x,y,direction[x,y])
        if abs(tr[0,1]-global_path[0,1])<.018*p.scale:
            continue
        xx,yy=tr[-max(3,px(p.scale,.025)):].T
        if np.mean((dark[xx,yy]>.22)&(ridge[xx,yy]>.40)&(delta[xx,yy]>.55))<.60:
            continue
        if topology.check(p.local,tr+[p.front,0],p.front,p.scale,True)!='CLOSED_RIM':
            return tr,float(values[x,y])
    return np.empty((0,2),np.int32),0.

def continuous_lip(path,score,seeds,p,fixed,reg):
    """Replace an unsupported cross-lip traverse only when both ends support the other lip."""
    s=p.scale
    def unchanged():
        return path,None
    if len(path)<.14*s:return unchanged()
    rows=np.flatnonzero(seeds.any(axis=0))
    lips=np.split(rows,np.flatnonzero(np.diff(rows)>px(s,.012))+1)
    if len(lips)<2:return unchanged()
    values=score[path[:,0],path[:,1]]
    smooth=np.convolve(values,np.ones(3)/3,'same')
    weak=np.flatnonzero(smooth<.02)
    for run in np.split(weak,np.flatnonzero(np.diff(weak)>1)+1):
        if len(run)<px(s,.024):continue
        lo,hi=run[0],run[-1]+1
        if lo<2 or hi+px(s,.018)>=len(path) or path[hi,0]>.30*s:continue
        before=path[lo-1];after=path[hi]
        if abs(after[1]-before[1])<.032*s:continue
        window=path[hi:hi+px(s,.025)]
        if (score[window[:,0],window[:,1]]>.08).mean()<.65:continue
        for lip in sorted(lips,key=lambda a:abs(np.median(a)-after[1])):
            height=np.median(lip)
            if abs(height-path[0,1])<.026*s or abs(height-after[1])+.018*s>=abs(before[1]-after[1]):continue
            length=min(int(after[0]),px(s,.082))
            if length<3:continue
            # Evaluate the alternative root directly on mutually observed current and incremental valleys.
            # Its short physical prefix can be visible even when the global score suppresses the mouth.
            cur=p.local[:,p.front:p.front+length].astype(np.float32)
            dx,dy=reg['shift']
            ref=cv2.warpAffine(fixed[p.sl],np.float32([[1,0,dx+p.front],[0,1,dy]]),(length,len(cur)),
                flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
            diff=np.where(np.isfinite(ref),ref-cur,0.)
            prefix_signal=np.minimum(baseline.bilateral(-cur,s),baseline.bilateral(diff,s))
            limited=np.clip(prefix_signal/max(2.8*p.noise,.024*p.span)-1.,-1.,1.4)
            band=np.ascontiguousarray(limited.T,np.float32)
            band[:,np.abs(np.arange(score.shape[1])-height)>.032*s]=-100.
            start=np.zeros_like(seeds);start[:,lip]=seeds[:,lip]
            prefix,quality,_,_,_=lattice(band,start,s,True)
            if len(prefix)<px(s,.018) or quality<.014*s:continue
            x0,y0=prefix[-1];x1,y1=after;span=x1-x0
            if not .014*s<span<.21*s:continue
            if abs(y1-y0)+.012*s>=abs(after[1]-before[1]):continue
            # Cubic interpolation ties the measured prefix and distal tangent, clamped to avoid overshoot.
            n=min(len(prefix)-1,px(s,.024));slope=(y0-prefix[-n-1,1])/n
            distal_window=path[hi:hi+px(s,.032)]
            lag=max(1,len(distal_window)//2)
            end_slope=float(np.median((distal_window[lag:,1]-distal_window[:-lag,1])/lag)) if len(distal_window)>lag else 0.
            chord=(y1-y0)/span
            def bounded(v):
                return np.sign(chord)*np.clip(np.sign(chord)*v,0,3*abs(chord))
            x=np.arange(x0+1,x1);u=(x-x0)/span
            y=(2*u**3-3*u**2+1)*y0+(u**3-2*u**2+u)*span*bounded(slope)+(-2*u**3+3*u**2)*y1+(u**3-u**2)*span*bounded(end_slope)
            gap=np.column_stack((x,np.rint(y))).astype(np.int32)
            proposed=np.vstack((prefix,gap,path[hi:]))
            if np.max(np.abs(np.diff(proposed[:,1])))>2:continue
            return proposed,dict(start=int(x0),end=int(x1),inferred_columns=len(gap),prefix_score=float(quality))
    return unchanged()

def predict(p,bonus=None,fixed=None,archive=None):
    audit=dict(decision='NO_NOTCH',stop='NO_NOTCH',events=[],trials=[],rejections={})
    m=dict(status='NO_NOTCH_BODY',tip=None,root=None,points=[],diagnostics=dict(dual=audit,candidates=[],pairs=[],selected=None))
    if p is None:return m
    score,seeds,coarse,reg,source,stats=fields(p,fixed)
    path,total,values,back,direction=lattice(score,seeds,p.scale,source=='JOINT')
    distal=np.empty((0,2),np.int32);dscore=0.
    if source=='JOINT':
        distal,dscore,checked,candidates=qualified_peak(p,score,values,back,direction)
        stats.update(local_maxima=candidates,candidates_checked=checked)
    global_path=path;global_score=total
    diagnostics=extension_evidence(score,distal,p.scale)
    pick='GLOBAL'
    if (source=='JOINT' and len(path) and len(distal)
            and path[-1,0]<=.19*p.scale and distal[-1,0]-path[-1,0]>=.045*p.scale
            and total>.040*p.scale and dscore>.052*p.scale and diagnostics['positive_extension']):
        if topology.check(p.local,distal+[p.front,0],p.front,p.scale,True)!='CLOSED_RIM':
            path=distal;total=dscore;pick='DISTAL'
    veto=False
    if source=='JOINT' and p.stage=='v5_4' and len(global_path) and global_path[-1,0]<=.19*p.scale:
        profile=mouth_profile(p,fixed,reg,score)
        post=mouth_test(global_path,p,score,profile)
        stats['mouth_review']=post
        if post['dead'] and pick=='GLOBAL':
            if len(distal) and distal[-1,0]>global_path[-1,0] and diagnostics['positive_extension']:
                path,total,pick=distal,dscore,'DISTAL'
            else:
                alt,alt_score=other_lip(p,global_path,score,values,back,direction,profile)
                if len(alt):
                    path,total,pick=alt,alt_score,'OTHER_LIP'
                else:
                    veto=True
    bridge=None
    if source=='JOINT' and len(path) and total>.040*p.scale:
        revised,details=continuous_lip(path,score,seeds,p,fixed,reg)
        if details and topology.check(p.local,revised+[p.front,0],p.front,p.scale,True)!='CLOSED_RIM':
            path=revised;bridge=details
    stats['lip_bridge']=bridge
    org=np.asarray(p.origin)+[p.front,0]
    for label,track,value in [('global',global_path,global_score),('distal',distal,dscore)]:
        audit[label+'_tip']=(track[-1]+org).tolist() if len(track) else None
        audit[label+'_score']=float(value) if len(track) else None
    audit.update(pick=pick,**diagnostics)
    minimum=.040*p.scale
    stop='ACCEPTED_PEAK'
    if not len(path):stop='NO_REACHABLE_POSITIVE'
    elif total<=minimum:stop='INSUFFICIENT_TOTAL'
    elif path[-1,0]-path[0,0]<px(p.scale,.030):stop='SHORT_PATH'
    else:
        pts=path+[p.front,0]
        reject=topology.check(p.local,pts,p.front,p.scale,True)
        if reject=='CLOSED_RIM':stop=reject
    if veto:stop='MOUTH_DEAD_END'
    if source=='PREEXISTING_CHECK':
        streak=longest=0
        for x,y in path:
            if x>.20*p.scale:break
            streak=streak+1 if score[x,y]>.10 and x>.015*p.scale else 0
            longest=max(streak,longest)
        stats['strong_run']=longest
        if longest<px(p.scale,.035) or stop!='ACCEPTED_PEAK':stop='NO_CONFIRMED_PREEXISTING'
    peak=(path[-1]+org).tolist() if len(path) else None
    audit.update(decision=source,stop=stop,front=int(org[0]),registration=reg,peak=peak,score=float(total),minimum=float(minimum),seeds=int(seeds.sum()),**stats)
    m['diagnostics']['coarse']=coarse
    if archive is not None:
        archive.update(origin=org,score=score.astype('float16'),value=values,path=path)
    if stop!='ACCEPTED_PEAK':m['status']='no_tip' if stop in ('NO_CONFIRMED_PREEXISTING','MOUTH_DEAD_END') else stop;return m
    pts=(path+org).tolist();root=pts[0];tip=pts[-1]
    trace=dict(first_loss=None,stop=stop,gate=source,reference=reg or {})
    m.update(status='VALID',tip=tip,root=root,points=pts)
    m['diagnostics'].update(selected=0,candidates=[dict(start=root,tip=tip,status='VALID',trace=trace)])
    return m

