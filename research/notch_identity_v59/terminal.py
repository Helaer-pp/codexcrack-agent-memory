"""V5.4 evidence and registration, separate entrance lattices and a witnessed forward continuation."""
import cv2
import numpy as np
from research.notch_identity_v54 import terminal as base
from research.notch_identity_v57 import terminal as prior
from research.notch_identity_v58 import optics
from dataclasses import replace
from .geometry import material, apex
from research.notch_identity_v40.evidence import offset_image
from research.notch_identity_v53.terminal import band_width

STAGES = ('apex_only', 'v5_9')
global_free_end_dp = base.global_free_end_dp
px = base.px


def prepare(raw, hint, scale=288., stage='v5_9', reference=None, reference_hint=None):
    if stage not in STAGES:raise ValueError(stage)
    ref=raw if reference is None else reference
    ref_hint=np.asarray(hint if reference_hint is None else reference_hint)
    band=material(raw,ref,np.asarray(hint),ref_hint,scale)
    if band is None:return None
    top,bottom=band
    origin=np.array([0,top])
    fixed_tip=apex(ref[top:bottom],ref_hint-origin,scale)
    if fixed_tip is None:return None
    guess=np.asarray(fixed_tip)+np.asarray(hint)-ref_hint
    tip=apex(raw[top:bottom],guess,scale)
    if tip is None:return None
    p=base.prepare(raw[top:bottom],tip,scale)
    if p is None:return None
    ys,xs=p.sl
    return replace(p,raw=raw,origin=(p.origin[0],p.origin[1]+top),
        sl=(slice(ys.start+top,ys.stop+top),xs),stage=stage,
        starts=p.starts),band


def tangent_mask(path, xs, ys):
    # Limit departures from the prefix direction while allowing pixel noise and curvature.
    tail=path[-min(len(path),13):]
    slope=(tail[-1,1]-tail[0,1])/max(1,tail[-1,0]-tail[0,0])
    distance=xs-path[-1,0]
    return abs(ys-path[-1,1]-slope*distance)<=3.+.32*np.maximum(0,distance)


def normal_evidence(p, fixed, shift, score):
    # The sampling domain starts at the front. Replicated borders cannot read a left-side marker.
    gray = p.local[:, p.front:].astype(np.float32)
    dx, dy = shift
    reference = cv2.warpAffine(fixed[p.sl], np.float32([[1, 0, dx+p.front], [0, 1, dy]]),
        (gray.shape[1], len(gray)), flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_CONSTANT, borderValue=float('nan'))
    delta = np.where(np.isfinite(reference), reference-gray, 0.)
    threshold = max(1., 2.7*p.noise, .030*p.span)
    dark,ridge,dipole=optics.measure(gray,delta,threshold,optics.OFFSETS)
    def persistent(mask, n):
        spread = cv2.dilate(mask.astype('float32'), np.ones((3,1),np.uint8))
        return cv2.blur(spread,(n,1))>=.65
    core = dark > max(3*p.noise,.035*p.span)
    dipole &= ~(core & persistent(core,7))
    wide = (band_width(delta>threshold)>max(3,.035*p.scale)) & (ridge<1.6)
    fine = (ridge>1.) & persistent(ridge>1.,5) & ~dipole & ~wide
    # A shifted stroke can retain a sharp current valley and defeat the dipole veto.
    # Require new darkness for differential continuation, using the registered reference.
    ref_depth = base.baseline.bilateral(-np.where(np.isfinite(reference),reference,gray),p.scale)
    prior = cv2.dilate(ref_depth,np.ones((2*px(p.scale,.035)+1,3),np.uint8))
    bridge_fine = fine & (prior < np.maximum(4*p.noise,.52*np.maximum(delta,threshold)))
    return fine.T, core.T, dipole.T, ridge.T, bridge_fine.T


def entrances(seeds, scale):
    rows = np.flatnonzero(seeds.any(axis=0))
    if not len(rows):
        return []
    groups = list(np.split(rows,np.flatnonzero(np.diff(rows)>px(scale,.008))+1))
    while len(groups)>3:
        k = int(np.argmin([b[0]-a[-1] for a,b in zip(groups,groups[1:])]))
        groups[k:k+2] = [np.r_[groups[k],groups[k+1]]]
    if len(groups)==1 and len(rows)>=max(8,.038*scale):
        groups = list(np.array_split(rows, 2))
    return groups


def continue_ridge(p, field, path, fine, core, strength, static):
    x,y = path.T
    near = x<=x[0]+max(5,px(p.scale,.10))
    record = dict(accepted=False, witness=int((fine[x[near],y[near]] & core[x[near],y[near]]).sum()))
    if record['witness']<2 or x[-1]+1>=len(field):
        return path,record
    # Fix the entire prefix; new paths can start only at its observed end.
    start_x, start_y = map(int,path[-1])
    span = min(len(field)-start_x, max(12,px(p.scale,.52)))
    radius = max(5,px(p.scale,.11))
    lo,hi = max(0,start_y-radius),min(field.shape[1],start_y+radius+1)
    sl = np.s_[start_x:start_x+span,lo:hi]
    valid = fine[sl]
    observed=np.where(valid,np.maximum(field[sl],np.minimum(1.3,.30+.35*strength[sl])),
                      np.where(core[sl],np.clip(field[sl],-.14,.12),np.minimum(field[sl],-.38)))
    extra_score=np.where(np.isfinite(field[sl]) & ~static[sl],observed,-np.inf).astype(np.float32)
    xx,yy=np.ogrid[start_x:start_x+span,lo:hi]
    extra_score[~tangent_mask(path,xx,yy)]=-np.inf
    extra_score[0,:]=0
    start = np.zeros((1,hi-lo),np.uint8)
    start[0,start_y-lo]=1
    tail,_,_,_,_ = base.lattice(extra_score,start,p.scale,False)
    if len(tail)<2:
        return path,record
    tx,ty = tail[1:].T
    hit = valid[tx,ty]
    slope = np.diff(tail[:,1])
    prev = path[-1,1]-path[-2,1] if len(path)>1 else 0
    net = extra_score[tx,ty]-.13*abs(slope)-.19*abs(np.diff(slope,prepend=prev))
    original_net = field[start_x+tx,lo+ty]-.13*abs(slope)-.19*abs(np.diff(slope,prepend=prev))
    record.update(columns=len(tx),fine_fraction=float(hit.mean()),mean_net=float(net.mean()),original_net=float(original_net.mean()))
    if hit.mean()<.30 or net.mean()<=0:
        return path,record
    record['accepted']=True
    return np.vstack((path,tail[1:]+[start_x,lo])),record


def raw_continuation(p, fixed, reg, path, fine, core, strength, band):
    """Check a short raw-supported terminal extension against the registered material."""
    if len(path)<16:return path,None
    x,y=map(int,path[-1])
    raw_score=base.fields(p,None)[0]
    limit=min(len(raw_score)-x,max(9,round(.14*p.scale)))
    if limit<5:return path,None
    radius=min(20,limit);lo=max(0,y-radius);hi=min(raw_score.shape[1],y+radius+1)
    field=raw_score[x:x+limit,lo:hi].copy()
    xx,yy=np.ogrid[x:x+limit,lo:hi]
    margin=max(3,round(.035*p.scale))
    inside=(yy+p.origin[1]>=band[0]+margin)&(yy+p.origin[1]<band[1]-margin)
    field[~(tangent_mask(path,xx,yy)&inside)]=-np.inf
    start=np.zeros((1,hi-lo),np.uint8);start[0,y-lo]=1
    tail,*_=base.lattice(field,start,p.scale,False)
    if len(tail)<5:return path,None
    tail=tail[1:]+[x,lo];tx,ty=tail.T
    dx,dy=reg['shift']
    rx=tx+p.origin[0]+p.front+dx;ry=ty+p.origin[1]+dy
    if min(ry)<2 or max(ry)>=len(fixed)-2 or min(rx)<0 or max(rx)>=fixed.shape[1]:return path,None
    ref_depth=np.minimum(fixed[ry-2,rx],fixed[ry+2,rx])-fixed[ry,rx]
    cur=p.local.astype('float32')
    cx=tx+p.front
    if min(ty)<2 or max(ty)>=len(cur)-2:return path,None
    depth=np.minimum(cur[ty-2,cx],cur[ty+2,cx])-cur[ty,cx]
    corroborated=core[tx,ty] & (depth>np.maximum(3*p.noise,ref_depth+2*p.noise))
    supported=fine[tx,ty] | corroborated
    if supported.mean()<.60 or corroborated.mean()<.33 or fine[tx,ty].mean()<.15:return path,None
    if np.mean(raw_score[tx,ty])<.10:return path,None
    return np.vstack((path,tail)),dict(columns=len(tail),raw_fraction=float(corroborated.mean()),fine_fraction=float(fine[tx,ty].mean()))


def downstream_peak(p, field, path, values, back, direction, fine, strength, contact, static):
    early=int(path[-1,0])
    near_mouth=early-path[0,0]<=max(18,4*contact)
    maxima=(values>=cv2.dilate(values,np.ones((3,3),np.uint8))) & (field>.08)
    maxima[:early+4]=False
    xs,ys=np.where(maxima & (values>1.))
    for j in np.argsort(-values[xs,ys],kind='stable'):
        x,y=xs[j],ys[j]
        alt=base.unwind(back,x,y,direction[x,y])
        ax,ay=alt.T
        first=np.searchsorted(ax,early)
        if first>=len(ax)-4:continue
        if not near_mouth:
            if abs(ay[first]-path[-1,1])>2 or not np.array_equal(alt[:first],path[:-1]):continue
            extension=alt[first+1:];ex,ey=extension.T
            paired=fine[ex,ey]
            if paired.mean()<.30:continue
            if np.mean(base.increments(field,alt)[first+1:]+np.where(paired,np.maximum(0,np.minimum(.94,.16+.22*strength[ex,ey])-field[ex,ey]),0))<=0:continue
        steps=base.increments(field,alt)
        cumulative=np.cumsum(steps)
        bottom=first+np.argmin(cumulative[first:])
        gain=float(cumulative[-1]-cumulative[bottom])
        tail=alt[bottom+1:]
        if len(tail)<5 or gain<2.5:continue
        tx,ty=tail.T
        if static[tx,ty].any():continue
        if p.stage=='v5_9' and (static[ax[first+1:],ay[first+1:]].any() or not tangent_mask(path,ax[first+1:],ay[first+1:]).all()):continue
        measured=fine[tx,ty];positive=field[tx,ty]>.08
        edges=np.flatnonzero(np.diff(np.r_[False,positive,False]))
        if max((b-a for a,b in zip(edges[::2],edges[1::2])),default=0)<3:continue
        if positive.mean()<.52 or steps[-min(4,len(tail)):].mean()<=.06:continue
        # Judge the observed rising segment after the valley; the intervening fall is permitted.
        lifted=steps[bottom+1:]+np.where(measured,np.maximum(0,np.minimum(.94,.16+.22*strength[tx,ty])-field[tx,ty]),0)
        if measured.mean()<.30 or lifted.mean()<=0:continue
        if base.topology.check(p.local[:,p.front:],alt,0,p.scale,True)=='CLOSED_RIM':continue
        return alt,dict(valley_x=int(ax[bottom]),late_x=int(x),gain=gain,columns=len(tx),
                        fine_fraction=float(measured.mean()),mean_net=float(lifted.mean()))
    return path,None


def predict(prepared,bonus=None,fixed=None,archive=None):
    if prepared is None:return search(None,bonus,fixed,archive)
    p,band=prepared
    shift=[0,0];quality=None;mapping=None
    if fixed is not None:
        fixed,shift,quality,mapping=optics.align(p,fixed)
    width=p.local.shape[1]
    end=width if width<1450 else min(width,p.front+800)
    while True:
        ys,xs=p.sl
        part=replace(p,local=p.local[:,:end],sl=(ys,slice(xs.start,xs.start+end)))
        m=search(part,bonus,fixed,archive,band,quality)
        d=m['diagnostics']['dual']
        if end==width or not d['right_active']:break
        end=min(width,2*end)
    local=d.get('registration') or {}
    local_shift=local.get('shift') or [0,0]
    d['registration']=dict(local,shift=[a+b for a,b in zip(shift,local_shift)],
                           ncc=local.get('ncc') if local.get('ncc') is not None else quality)
    d['material_map']=mapping
    d['local_shift']=local_shift
    d['initial_shift']=shift
    d['optical_scale']=p.scale
    d['material_band']=list(band)
    return m


def search(p, bonus=None, fixed=None, archive=None, band=None, quality=None):
    diag = dict(decision='NO_NOTCH',stop='NO_NOTCH',pick='NONE',branches=[],trials=[],events=[])
    m = dict(status='NO_NOTCH_BODY',root=None,tip=None,points=[],diagnostics=dict(dual=diag,candidates=[],selected=None,pairs=[]))
    if p is None:
        return m
    score,seeds,coarse,reg,source,stats = base.fields(p,fixed)
    if p.stage=='v5_9' and source=='UNREGISTERED_RAW' and quality is not None and quality>=.95:
        # The optical alignment has independently matched the notch. A failed
        # flank re-registration need not hide an attached narrow differential ridge.
        fine,core,dip,strength,usable=normal_evidence(p,fixed,[0,0],score)
        near=usable[:max(6,px(p.scale,.10))] & core[:max(6,px(p.scale,.10))]
        if near.any(1).sum()>=4:
            score=np.where(usable,np.maximum(score,np.minimum(1.3,.30+.35*strength)),score)
            reg=dict(status='OK',shift=[0,0],ncc=quality,source='OPTICAL_NOTCH')
            source='JOINT'
    origin = np.asarray(p.origin)+[p.front,0]
    groups = entrances(seeds,p.scale)
    diag.update(roi_y=[int(p.origin[1]),int(p.origin[1]+len(p.local)-1)],front=int(origin[0]),registration=reg,decision=source,seed_band=len(seeds),**stats)
    m['diagnostics']['coarse']=coarse
    diag['right_active']=False
    joint = source=='JOINT'
    if joint:
        profiles=normal_evidence if p.stage=='v5_9' else prior.normal_evidence
        fine,core,dip,strength,bridge_fine = profiles(p,fixed,reg['shift'],score)
        score[dip] = np.minimum(score[dip],-.70)
        static=fine & ~bridge_fine
        if p.stage=='v5_9':
            margin=max(3,round(.035*p.scale))
            row=np.arange(score.shape[1])+p.origin[1]
            edge=(row-band[0]<margin)|(band[1]-1-row<margin)
            score[:,edge]=-np.inf
            seeds[:,edge]=0
            static=static|edge[None,:]
            bridge_fine=bridge_fine&~edge[None,:]
        profile = base.mouth_profile(p,fixed,reg,score)
    centres = np.asarray([np.median(g) for g in groups])
    owner = np.argmin(abs(np.arange(score.shape[1])[:,None]-centres),axis=1) if groups else []
    winner=None
    merits=[]
    curves=[]
    contact=int(np.ptp(np.flatnonzero(seeds.any(axis=0))))+len(seeds) if groups else 0
    for idx,rows in enumerate(groups):
        entry=np.zeros_like(seeds)
        entry[:,rows]=seeds[:,rows]
        field=score
        if len(groups)>1:
            width = max(len(seeds),round(3.*np.min(np.diff(centres))))
            restore=field[:width,owner!=idx].copy()
            field[:width,owner!=idx]=-np.inf
            entry[:,owner!=idx]=0
        path,total,V,back,direction=base.lattice(field,entry,p.scale,joint)
        if archive is not None:
            curves.append(V.max(axis=1))
        diag['right_active'] |= bool(np.isfinite(V[max(0,len(V)-48):]).any())
        if not len(path):
            if len(groups)>1:field[:width,owner!=idx]=restore
            continue
        old_tip=(path[-1]+origin).tolist()
        bridge=dict(accepted=False)
        if joint and total>.040*p.scale:
            path,peak_evidence=downstream_peak(p,field,path,V,back,direction,bridge_fine,strength,contact,static)
            total=float(V[tuple(path[-1])])
            if p.stage=='v5_9':
                path,bridge=continue_ridge(p,field,path,bridge_fine,core,strength,static)
            else:
                path,bridge=prior.continue_ridge(p,field,path,bridge_fine,core,strength)
            bridge['downstream_peak']=peak_evidence
            if p.stage=='v5_9' and not bridge['accepted'] and bridge.get('witness',0)>=2:
                path,bridge['raw_extension']=raw_continuation(p,fixed,reg,path,bridge_fine,core,strength,band)
        x,y=path.T
        stop='VALID'
        if total<=.040*p.scale:stop='INSUFFICIENT_TOTAL'
        elif x[-1]-x[0]<px(p.scale,.030):stop='SHORT_PATH'
        elif base.topology.check(p.local[:,p.front:],path,0,p.scale,True)=='CLOSED_RIM':stop='CLOSED_RIM'
        if joint:
            if x[-1]<len(profile[0])-px(p.scale,.018) and base.mouth_test(path,p,field,profile)['dead']:
                stop='MOUTH_DEAD_END'
            thin=fine[x,y];agreement=thin & core[x,y]
            net_length=int(thin.sum());fraction=float(agreement.mean())
        else:
            net_length=int((field[x,y]>.08).sum());fraction=0.
        if source=='PREEXISTING_CHECK':
            near=(x<=px(p.scale,.20)) & (x>px(p.scale,.015)) & (field[x,y]>.10)
            edges=np.flatnonzero(np.diff(np.r_[False,near,False]))
            if max((b-a for a,b in zip(edges[::2],edges[1::2])),default=0)<px(p.scale,.035):
                stop='NO_CONFIRMED_PREEXISTING'
        merit=float(total+.65*net_length+.70*fraction*len(path))
        item=dict(id=idx,root=(path[0]+origin).tolist(),tip=(path[-1]+origin).tolist(),base_tip=old_tip,
                  reason=stop,value=float(total),net_length=net_length,joint_fraction=fraction,merit=merit,bridge=bridge)
        if len(groups)>1:field[:width,owner!=idx]=restore
        diag['branches'].append(item)
        if stop=='VALID' and (not merits or merit>max(merits)):
            winner=(path,item)
            merits.append(merit)
    if archive is not None:
        archive.update(origin=origin,branch_ids=np.arange(len(curves)),curves=np.asarray(curves,dtype=np.float32))
    if winner is None:
        diag['stop']=max(diag['branches'],key=lambda a:a['merit'])['reason'] if diag['branches'] else 'NO_REACHABLE_POSITIVE'
        m['status']='no_tip'
        return m
    path,item=winner
    pts=(path+origin).tolist()
    diag.update(stop='ACCEPTED_PEAK',pick='BRANCH_'+str(item['id']),peak=pts[-1],score=item['value'])
    m.update(points=pts,root=pts[0],tip=pts[-1],status='VALID')
    m['diagnostics'].update(selected=0,candidates=[dict(start=pts[0],tip=pts[-1],status='VALID',
        trace=dict(first_loss=None,stop=diag['stop'],gate=source,reference=reg or {}))])
    return m
