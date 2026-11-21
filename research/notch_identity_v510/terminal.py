"""Vertex-snap S1 field and valley search with independently evidenced branch competition."""
from dataclasses import replace
import numpy as np
from research.notch_identity_v58 import terminal as original
from research.notch_identity_v58.terminal import base,prior,entrances,downstream_peak,px
from research.notch_identity_v59 import terminal as vertex
from .ridge import prefer_active,middle_bridge,signed_difference
STAGES=('apex_only','red_priority','v5_10')


def prepare(raw,hint,scale,stage='v5_10',reference=None,reference_hint=None):
    if stage not in STAGES:raise ValueError(stage)
    prep=vertex.prepare(raw,hint,scale,'apex_only',reference,reference_hint)
    return (replace(prep[0],stage='valley_recovery'),prep[1],stage) if prep else None


def predict(prep,bonus=None,fixed=None,archive=None):
    if prep is None:return original.predict(None)
    scene,band,stage=prep
    if stage=='apex_only' or fixed is None:
        m=original.predict(scene,bonus,fixed,archive)
    else:m=search(scene,fixed,archive,stage,band)
    m['diagnostics']['dual']['material_band']=list(band)
    return m


def search(p,fixed,archive,stage,band):
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
        fine,core,dip,strength,bridge_fine=prior.normal_evidence(p,fixed,reg['shift'],score)
        delta=signed_difference(p,fixed,reg['shift'])
        threshold=max(1.,2.7*p.noise,.030*p.span)
        score[dip] = np.minimum(score[dip],-.70)
        profile = base.mouth_profile(p,fixed,reg,score)
    centres = np.asarray([np.median(g) for g in groups])
    owner = np.argmin(abs(np.arange(score.shape[1])[:,None]-centres),axis=1) if groups else []
    winner=None
    candidates=[]
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
            path,peak_evidence=downstream_peak(p,field,path,V,back,direction,bridge_fine,strength,contact)
            total=float(V[tuple(path[-1])])
            if stage=='v5_10':
                path,bridge=middle_bridge(p,field,path,bridge_fine,core,strength,(fine & ~bridge_fine)|dip,band)
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
                  original_merit=merit,reason=stop,value=float(total),net_length=net_length,joint_fraction=fraction,merit=merit,bridge=bridge)
        if len(groups)>1:field[:width,owner!=idx]=restore
        diag['branches'].append(item)
        if stop=='VALID':candidates.append((path,item))
    diag['priority_applied']=False
    if joint and len(candidates)>1:
        diag['priority_applied']=prefer_active(candidates,bridge_fine,delta,threshold)
    if candidates:winner=max(candidates,key=lambda pair:pair[1]['merit'])
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
