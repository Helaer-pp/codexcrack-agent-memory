"""V5.4 evidence and registration, separate entrance lattices and a witnessed forward continuation."""
import cv2
import numpy as np
from research.notch_identity_v54 import terminal as base
from research.notch_identity_v40.evidence import offset_image
from research.notch_identity_v53.terminal import band_width

STAGES = ('branch_dipole', 'v5_7')
global_free_end_dp = base.global_free_end_dp
px = base.px


def prepare(raw, hint, scale, stage='v5_7'):
    if stage not in STAGES:
        raise ValueError(stage)
    scene = base.prepare(raw, hint, scale)
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
    ridge = np.zeros_like(gray)
    dark = np.zeros_like(gray)
    dipole = np.zeros(gray.shape, bool)
    for slope in (-.70, -.34, 0., .34, .70):
        step = px(p.scale, .009)
        rise = round(step*slope)
        sm = .25*(2*delta + offset_image(delta, step, rise) + offset_image(delta, -step, -rise))
        for radius in sorted({px(p.scale, .008), px(p.scale, .016)}):
            x = round(-radius*slope/np.hypot(1,slope))
            y = max(1, round(radius/np.hypot(1,slope)))
            prominence = sm-np.maximum(offset_image(sm,x,y), offset_image(sm,-x,-y))
            eligible = (sm>1.25*threshold) & (prominence>.28*sm)
            ridge = np.maximum(ridge, np.where(eligible, prominence/threshold, 0.))
            dark = np.maximum(dark, np.minimum(offset_image(gray,x,y),offset_image(gray,-x,-y))-gray)
            blue = np.minimum(offset_image(sm,2*x,2*y), offset_image(sm,-2*x,-2*y))
            dipole |= (sm>threshold) & (blue < -threshold) & (-blue>.48*sm)
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


def continue_ridge(p, field, path, fine, core, strength):
    x,y = path.T
    near = x<=x[0]+max(5,px(p.scale,.10))
    record = dict(accepted=False, witness=int((fine[x[near],y[near]] & core[x[near],y[near]]).sum()))
    if record['witness']<2 or x[-1]+2>=len(field):
        return path,record
    # Fix the entire prefix; new paths can start only at its observed end.
    start_x, start_y = map(int,path[-1])
    span = min(len(field)-start_x, max(12,px(p.scale,.52)))
    radius = max(5,px(p.scale,.11))
    lo,hi = max(0,start_y-radius),min(field.shape[1],start_y+radius+1)
    sl = np.s_[start_x:start_x+span,lo:hi]
    valid = fine[sl]
    extra_score = np.where(valid,np.maximum(field[sl],np.minimum(.94,.16+.22*strength[sl])),
                           np.minimum(field[sl],-.38)).astype(np.float32)
    extra_score[0,:]=0
    start = np.zeros((1,hi-lo),np.uint8)
    start[0,start_y-lo]=1
    tail,_,_,_,_ = base.lattice(extra_score,start,p.scale,False)
    if len(tail)<max(4,px(p.scale,.017)):
        return path,record
    tx,ty = tail[1:].T
    hit = valid[tx,ty]
    slope = np.diff(tail[:,1])
    prev = path[-1,1]-path[-2,1] if len(path)>1 else 0
    net = extra_score[tx,ty]-.13*abs(slope)-.19*abs(np.diff(slope,prepend=prev))
    original_net = field[start_x+tx,lo+ty]-.13*abs(slope)-.19*abs(np.diff(slope,prepend=prev))
    record.update(columns=len(tx),fine_fraction=float(hit.mean()),mean_net=float(net.mean()),original_net=float(original_net.mean()))
    if hit.mean()<.30 or net.mean()<=0 or original_net.mean()<=0 or not hit[-1] or not hit[:min(4,len(hit))].any():
        return path,record
    record['accepted']=True
    return np.vstack((path,tail[1:]+[start_x,lo])),record


def downstream_peak(p, field, path, values, back, direction, fine, core):
    """Compete reachable local peaks of this same entrance without a mouth-distance cutoff."""
    old_x, old_y = path.T
    if not (fine[old_x,old_y] & core[old_x,old_y] & (old_x<=old_x[0]+px(p.scale,.10))).any():
        return path, None
    maxima=(values>=cv2.dilate(values,np.ones((3,3),np.uint8))) & fine & (field>.08)
    maxima[:old_x[-1]+max(2,px(p.scale,.012))]=False
    xs,ys=np.where(maxima & (values>.040*p.scale))
    if not len(xs):
        return path,None
    best=float(values[old_x[-1],old_y[-1]]+.65*fine[old_x,old_y].sum()+.70*(fine[old_x,old_y]&core[old_x,old_y]).sum())
    chosen=path
    evidence=None
    examined=set()
    for i in np.argsort(-values[xs,ys],kind='stable'):
        x,y=int(xs[i]),int(ys[i])
        cell=(x//px(p.scale,.018),y//px(p.scale,.010))
        if cell in examined:
            continue
        examined.add(cell)
        alt=base.unwind(back,x,y,direction[x,y])
        ax,ay=alt.T
        # A revised prefix must still belong to the same physical entrance.
        if abs(ay[0]-old_y[0])>px(p.scale,.010):
            continue
        extra=ax>old_x[-1]
        fine_fraction=float(fine[ax[extra],ay[extra]].mean())
        net=float(base.increments(field,alt)[extra].mean())
        if fine_fraction<.30 or net<=0:
            continue
        supported=fine[ax,ay]
        merit=float(values[x,y]+.65*supported.sum()+.70*(supported&core[ax,ay]).sum())
        if merit>best and base.topology.check(p.local[:,p.front:],alt,0,p.scale,True)!='CLOSED_RIM':
            chosen,best=alt,merit
            evidence=dict(columns=int(extra.sum()),fine_fraction=fine_fraction,mean_net=net)
    return chosen,evidence


def predict(p, bonus=None, fixed=None, archive=None):
    diag = dict(decision='NO_NOTCH',stop='NO_NOTCH',pick='NONE',branches=[],trials=[],events=[])
    m = dict(status='NO_NOTCH_BODY',root=None,tip=None,points=[],diagnostics=dict(dual=diag,candidates=[],selected=None,pairs=[]))
    if p is None:
        return m
    score,seeds,coarse,reg,source,stats = base.fields(p,fixed)
    origin = np.asarray(p.origin)+[p.front,0]
    groups = entrances(seeds,p.scale)
    diag.update(roi_y=[int(p.origin[1]),int(p.origin[1]+len(p.local)-1)],front=int(origin[0]),registration=reg,decision=source,seed_band=len(seeds),**stats)
    m['diagnostics']['coarse']=coarse
    joint = source=='JOINT'
    if joint:
        fine,core,dip,strength,bridge_fine = normal_evidence(p,fixed,reg['shift'],score)
        score[dip] = np.minimum(score[dip],-.70)
        profile = base.mouth_profile(p,fixed,reg,score)
    centres = np.asarray([np.median(g) for g in groups])
    owner = np.argmin(abs(np.arange(score.shape[1])[:,None]-centres),axis=1) if groups else []
    winner=None
    merits=[]
    curves=[]
    for idx,rows in enumerate(groups):
        entry=np.zeros_like(seeds)
        entry[:,rows]=seeds[:,rows]
        field=score.copy() if len(groups)>1 else score
        if len(groups)>1:
            width = max(len(seeds),round(3.*np.min(np.diff(centres))))
            field[:width,owner!=idx]=-np.inf
            entry[:,owner!=idx]=0
        path,total,V,back,direction=base.lattice(field,entry,p.scale,joint)
        if archive is not None:
            curves.append(V.max(axis=1))
        if not len(path):
            continue
        old_tip=(path[-1]+origin).tolist()
        bridge=dict(accepted=False)
        if joint and p.stage=='v5_7' and total>.040*p.scale:
            path,peak_evidence=downstream_peak(p,field,path,V,back,direction,bridge_fine,core)
            total=float(V[tuple(path[-1])])
            path,bridge=continue_ridge(p,field,path,bridge_fine,core,strength)
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
