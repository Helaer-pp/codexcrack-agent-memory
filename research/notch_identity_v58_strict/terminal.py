"""V5.4 evidence and registration, separate entrance lattices and a witnessed forward continuation."""
import cv2
import numpy as np
from research.notch_identity_v54 import terminal as base
from research.notch_identity_v57 import terminal as prior
from research.notch_identity_v58 import optics
from dataclasses import replace
from research.notch_identity_v40.evidence import offset_image
from research.notch_identity_v53.terminal import band_width

STAGES = ('valley_recovery', 'v5_8')
global_free_end_dp = base.global_free_end_dp
px = base.px


def prepare(raw, hint, scale, stage='v5_8'):
    if stage not in STAGES:
        raise ValueError(stage)
    scene = optics.prepare_optical(raw,hint) if stage=='v5_8' else base.prepare(raw, hint, scale)
    if scene is not None:
        scene.stage = stage
    return scene


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


def predict(p,bonus=None,fixed=None,archive=None):
    if p is None or p.stage!='v5_8':
        return search(p,bonus,fixed,archive)
    shift=[0,0];quality=None;mapping=None
    if fixed is not None:
        fixed,shift,quality,mapping=optics.align(p,fixed)
    width=p.local.shape[1]
    end=width if width<1450 else min(width,p.front+800)
    while True:
        ys,xs=p.sl
        part=replace(p,local=p.local[:,:end],sl=(ys,slice(xs.start,xs.start+end)))
        m=search(part,bonus,fixed,archive)
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
    return m


def search(p, bonus=None, fixed=None, archive=None):
    diag = dict(decision='NO_NOTCH',stop='NO_NOTCH',pick='NONE',branches=[],trials=[],events=[])
    m = dict(status='NO_NOTCH_BODY',root=None,tip=None,points=[],diagnostics=dict(dual=diag,candidates=[],selected=None,pairs=[]))
    if p is None:
        return m
    score,seeds,coarse,reg,source,stats = base.fields(p,fixed)
    origin = np.asarray(p.origin)+[p.front,0]
    groups = entrances(seeds,p.scale)
    diag.update(roi_y=[int(p.origin[1]),int(p.origin[1]+len(p.local)-1)],front=int(origin[0]),registration=reg,decision=source,seed_band=len(seeds),**stats)
    m['diagnostics']['coarse']=coarse
    diag['right_active']=False
    joint = source=='JOINT'
    if joint:
        profiles=normal_evidence if p.stage=='v5_8' else prior.normal_evidence
        fine,core,dip,strength,bridge_fine = profiles(p,fixed,reg['shift'],score)
        score[dip] = np.minimum(score[dip],-.70)
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
            path,peak_evidence=downstream_peak(p,field,path,V,back,direction,bridge_fine,strength,contact,fine & ~bridge_fine)
            total=float(V[tuple(path[-1])])
            if p.stage=='v5_8':
                path,bridge=continue_ridge(p,field,path,bridge_fine,core,strength,fine & ~bridge_fine)
            else:
                path,bridge=prior.continue_ridge(p,field,path,bridge_fine,core,strength)
            bridge['downstream_peak']=peak_evidence
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
