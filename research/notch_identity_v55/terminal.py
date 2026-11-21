"""Conditional fine differential ridge floor and conservative downstream branch selection."""
import cv2
import numpy as np
from research.notch_identity_v54 import terminal as prior
from research.notch_identity_v54.terminal import (
    lattice, unwind, global_free_end_dp, continuous_lip, topology, px, qualified_peak,
    extension_evidence, increments, mouth_profile, mouth_test, other_lip,
)

STAGES=('ridge','v5_5')

def prepare(raw,hint,scale,stage='v5_5'):
    if stage not in STAGES:
        raise ValueError(stage)
    scene=prior.prepare(raw,hint,scale)
    if scene is not None:
        scene.stage=stage
    return scene

def fields(p,fixed):
    score,seeds,coarse,reg,source,stats=prior.fields(p,fixed)
    if source!='JOINT':
        return score,seeds,coarse,reg,source,stats
    s=p.scale
    gray=p.local[:,p.front:].astype(np.float32)
    dx,dy=reg['shift']
    ref=cv2.warpAffine(fixed[p.sl],np.float32([[1,0,p.front+dx],[0,1,dy]]),(gray.shape[1],len(gray)),
        flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
    valid=np.isfinite(ref)
    ref=np.where(valid,ref,gray)
    diff=ref-gray
    radius=max(1,px(s,.0065))
    def prominence(im):
        pad=cv2.copyMakeBorder(im,radius,radius,0,0,cv2.BORDER_REPLICATE)
        return np.maximum(0,im-np.maximum(pad[2*radius:],pad[:-2*radius]))
    floor=max(3*p.noise,.035*p.span)
    red=prominence(diff)
    contrast=red/np.maximum(diff,floor)
    amplitude=red/floor
    raw_depth=prominence(-gray)
    old_depth=cv2.dilate(cv2.blur(prominence(-ref),(2*px(s,.009)+1,1)),
                         np.ones((2*radius+1,1),np.uint8))
    # Reference scratches can shift sideways. Inspect the reference within a small displacement envelope.
    ref_band=cv2.dilate(old_depth,np.ones((2*px(s,.038)+1,2*px(s,.009)+1),np.uint8))
    static=ref_band/np.maximum(floor,red)
    # A near-mouth broad red band with a textured centre must not receive the uplift.
    n=min(gray.shape[1],px(s,.25)+1)
    broad=prior.previous.band_width(diff[:,:n]>floor)>.024*s
    supported=valid & (diff>1.15*floor) & (amplitude>1.0) & (contrast>.27) & (static<.55)
    supported[:,:n]&=~broad
    # Retain locally elongated signals, allowing the thin centreline to move between columns.
    nearby=cv2.dilate(supported.astype('float32'),np.ones((2*px(s,.0035)+1,1),np.uint8))
    along=cv2.blur(nearby,(2*px(s,.012)+1,1))
    ridge=supported & (along>=.69)
    ridge[:,:px(s,.19)]=False
    weak=raw_depth<np.maximum(1.4*floor,.42*red)
    strength=np.clip((amplitude-1)/2,0,1)*np.clip((contrast-.27)/.45,0,1)
    proposed=.10+.92*strength
    # A bridge must return to an observed joint core. Never reward an unbounded diffuse tail.
    core=((raw_depth>floor)&(contrast>.27)&(diff>floor)&(static<.55)).astype('uint8')
    window=px(s,.11)
    core=cv2.dilate(core,np.ones((2*px(s,.025)+1,1),np.uint8))
    right=cv2.dilate(core,np.ones((1,window+1),np.uint8),anchor=(0,0),borderType=cv2.BORDER_CONSTANT,borderValue=0)
    left=cv2.dilate(core,np.ones((1,window+1),np.uint8),anchor=(window,0),borderType=cv2.BORDER_CONSTANT,borderValue=0)
    chosen=ridge & weak & (left!=0) & (right!=0) & (score.T<proposed)
    score.T[chosen]=proposed[chosen]
    stats.update(ridge_pixels=int(ridge.sum()),lift_pixels=int(chosen.sum()),_ridge=ridge.T)
    return score,seeds,coarse,reg,source,stats

def link_evidence(early,late,score,ridge,s,early_score,late_score):
    x,y=early[-1];offset=x-late[0,0]
    if offset<0 or offset>=len(late)-1:
        return dict(ok=False,reason='NO_OVERLAP')
    overlap=min(offset+1,len(early),px(s,.032))
    separation=np.abs(early[-overlap:,1]-late[offset+1-overlap:offset+1,1])
    tail=late[offset+1:]
    net=increments(score,late)[offset+1:]
    fine=ridge[tail[:,0],tail[:,1]]
    support=(net>.05)|fine
    edges=np.flatnonzero(np.diff(np.r_[False,~support,False]))
    longest=max((b-a for a,b in zip(edges[::2],edges[1::2])),default=0)
    checks={'SAME_BRANCH':separation.max()<=max(2,.014*s),
            'FINE_OR_FUSED':support.mean()>=.50 and (fine.mean()>=.16 or (net>.08).mean()>=.58),
            'GAP':longest<=max(2,.045*s),'MEAN':net.mean()>-.29,'RATIO':late_score>=.64*early_score}
    return dict(ok=all(checks.values()),reason=','.join(k for k,v in checks.items() if not v) or 'PASS',
                span=len(net),separation=int(separation.max()),fine=float(fine.mean()),support=float(support.mean()),
                deepest_gap=int(longest),mean=float(net.mean()),ratio=float(late_score/early_score))

def downstream(p,score,values,back,direction,ridge,early,best):
    # Baseline eligibility checks still apply to each prospective downstream endpoint.
    x0,y0=early[-1];s=p.scale
    lo=x0+px(s,.023)+1
    hi=min(len(score),x0+px(s,.24)+1)
    audit=dict(early=early[-1].tolist(),early_score=best,replaced=False,links=[])
    if lo>=hi:
        return early,best,audit
    bound=values[lo-1:min(len(score),hi+1)]
    maxima=cv2.dilate(bound,np.ones((3,3),np.uint8))[1:1+hi-lo]
    region=values[lo:hi]
    xs,ys=np.where((region>=maxima)&(region>max(.052*s,.64*best))&(score[lo:hi]>.08))
    order=np.lexsort((-region[xs,ys],-xs))
    for j in order:
        x,y=xs[j]+lo,ys[j]
        if abs(y-y0)>2*(x-x0)+max(2,.014*s):
            continue
        path=unwind(back,x,y,direction[x,y])
        if not extension_evidence(score,path,s)['positive_extension']:
            continue
        if topology.check(p.local,path+[p.front,0],p.front,s,True)=='CLOSED_RIM':
            continue
        value=float(values[x,y])
        item=link_evidence(early,path,score,ridge,s,best,value)
        audit['links'].append(dict(point=[int(x),int(y)],value=value,**item))
        if item['ok']:
            audit['replaced']=True
            return path,value,audit
    return early,best,audit

def predict(p,bonus=None,fixed=None,archive=None):
    audit=dict(decision='NO_NOTCH',stop='NO_NOTCH',events=[],trials=[],rejections={})
    m=dict(status='NO_NOTCH_BODY',tip=None,root=None,points=[],diagnostics=dict(dual=audit,candidates=[],pairs=[],selected=None))
    if p is None:return m
    score,seeds,coarse,reg,source,stats=fields(p,fixed)
    ridge=stats.pop('_ridge',None)
    path,total,values,back,direction=lattice(score,seeds,p.scale,source=='JOINT')
    distal=np.empty((0,2),np.int32);dscore=0.
    if source=='JOINT':
        distal,dscore,checked,candidates=qualified_peak(p,score,values,back,direction)
        if p.stage=='v5_5' and len(distal) and len(path) and (path[-1,0]<=.19*p.scale or np.array_equal(distal[-1],path[-1])):
            distal,dscore,details=downstream(p,score,values,back,direction,ridge,distal,dscore)
            stats['branch_review']=details
        stats.update(local_maxima=candidates,candidates_checked=checked)
    global_path=path;global_score=total
    diagnostics=extension_evidence(score,distal,p.scale)
    pick='GLOBAL'
    if (source=='JOINT' and len(path) and len(distal)
            and path[-1,0]<=.19*p.scale and distal[-1,0]-path[-1,0]>=.045*p.scale
            and total>.040*p.scale and dscore>.052*p.scale and diagnostics['positive_extension']):
        if topology.check(p.local,distal+[p.front,0],p.front,p.scale,True)!='CLOSED_RIM':
            path=distal;total=dscore;pick='DISTAL'
    if (pick=='GLOBAL' and stats.get('branch_review',{}).get('replaced') and
            np.array_equal(global_path[-1],stats['branch_review']['early'])):
        path,total,pick=distal,dscore,'DISTAL'
    veto=False
    if source=='JOINT' and len(global_path) and global_path[-1,0]<=.19*p.scale:
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


