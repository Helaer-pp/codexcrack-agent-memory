"""Vertex-snap S1 field and valley search with independently evidenced branch competition."""
from dataclasses import replace
import numpy as np
from research.notch_identity_v58 import terminal as original
from research.notch_identity_v58.terminal import base,prior,entrances,downstream_peak,px
from research.notch_identity_v59 import terminal as vertex
from research.notch_identity_v510.ridge import middle_bridge, prefer_active, longest
import hashlib
from research.notch_identity_v512 import rules
from research.notch_identity_v513 import curve
from . import fields, geometry
from research.notch_identity_v516.closure import proximal_scene, scratch_cut
from research.notch_identity_v516 import transition
from research.notch_identity_v515 import corridor
from time import perf_counter
STAGES=('S1','S2','S3')


def prepare(raw,hint,scale,stage='S1',reference=None,reference_hint=None):
    if stage not in STAGES:raise ValueError(stage)
    if stage=='S1':
        prep=vertex.prepare(raw,hint,scale,'apex_only',reference,reference_hint)
        return (replace(prep[0],stage='valley_recovery'),prep[1],stage) if prep else None
    ref=raw if reference is None else reference
    rh=np.asarray(hint if reference_hint is None else reference_hint)
    band=vertex.material(raw,ref,np.asarray(hint),rh,scale)
    if band is None:return None
    top,bottom=band
    offset=np.array([0,top])
    a,b=raw[top:bottom],ref[top:bottom]
    rt=vertex.apex(b,rh-offset,scale)
    if rt is None:return None
    tip=vertex.apex(a,np.asarray(rt)+hint-rh,scale)
    if tip is None:return None
    aperture,native_scale=geometry.measure(b,rt)
    scene=base.prepare(a,tip,native_scale)
    if scene is None:return None
    quiet,change,floor=geometry.quiet_mouth(a,b,tip,rt,native_scale)
    scene=geometry.PhysicalScene(**vars(scene),aperture=aperture,quiet=quiet,residual=change,route_floor=floor)
    ys,xs=scene.sl
    return replace(scene,raw=raw,origin=(scene.origin[0],scene.origin[1]+top),
                   sl=(slice(ys.start+top,ys.stop+top),xs),stage='valley_recovery'),band,stage


def predict(prep,bonus=None,fixed=None,archive=None):
    if prep is None:return original.predict(None)
    scene,band,stage=prep
    if fixed is None:
        m=original.predict(scene,bonus,fixed,archive)
    else:
        reduced=corridor.narrow(scene,'S2')
        height,width=reduced.local.shape
        budget_width=min(width,max(reduced.front+round(.75*scene.scale),180000//height)) if reduced is not scene else width
        visits=[]
        while True:
            ys,xs=reduced.sl
            cut=reduced if budget_width==width else replace(reduced,local=reduced.local[:,:budget_width],
                    sl=(ys,slice(xs.start,xs.start+budget_width)))
            aligned=fixed(xs.start+budget_width) if callable(fixed) else fixed
            m=search(cut,aligned,archive,stage,band)
            visits.append(height*budget_width)
            if budget_width==width or not m['diagnostics']['dual']['right_active']:break
            # Continue only when a reachable DP state entered the right-hand overlap.
            budget_width=min(width,2*budget_width)
        attempted=False
        if reduced is not scene:
            attempted=(stage!='S1' and m['tip'] is None and
                       any(v['reason']=='MOUTH_DEAD_END' for v in m['diagnostics']['dual']['branches']))
            if attempted:
                near=proximal_scene(scene,reduced)
                trial=search(near,aligned,archive,stage,band)
                visits.append(near.local.size)
                if trial['tip'] is not None and trial['tip'][0]-near.origin[0]-near.front<.20*scene.scale:
                    m=trial
            corridor.refine(m,cut,aligned)
        m['diagnostics']['dual'].update(proximal_replay=attempted,scale=scene.scale,
                aperture=getattr(scene,'aperture',None),native_change=getattr(scene,'residual',None),
                route_floor=getattr(scene,'route_floor',None))
        m['diagnostics']['dual'].update(field_pixels=sum(visits),original_pixels=scene.local.size,field_visits=visits)
    m['diagnostics']['dual']['material_band']=list(band)
    return m


def search(p,fixed,archive,stage,band):
    diag = dict(decision='NO_NOTCH',stop='NO_NOTCH',pick='NONE',branches=[],trials=[],events=[])
    m = dict(status='NO_NOTCH_BODY',root=None,tip=None,points=[],diagnostics=dict(dual=diag,candidates=[],selected=None,pairs=[]))
    if p is None:
        return m
    start=perf_counter()
    # One material search band for every stage; S4 skips inactive pointwise rows.
    lo,hi=fields.active_rows(p)
    score,seeds,coarse,reg,source,stats = fields.make(p,fixed,'S4')
    seeds[:,:lo]=0;seeds[:,hi:]=0
    score[:,:lo]=-np.inf;score[:,hi:]=-np.inf
    profile_ms=dict(fields=(perf_counter()-start)*1000, normal=0., lattice=0., peaks=0., bridge=0.)
    diag["timing_ms"]=profile_ms
    origin = np.asarray(p.origin)+[p.front,0]
    groups = entrances(seeds,p.scale)
    diag.update(roi_y=[int(p.origin[1]),int(p.origin[1]+len(p.local)-1)],front=int(origin[0]),registration=reg,decision=source,seed_band=len(seeds),**stats)
    m['diagnostics']['coarse']=coarse
    diag['right_active']=False
    joint = source=='JOINT'
    if joint:
        tick=perf_counter()
        fine,core,dip,strength,bridge_fine,delta,dual,_,_=rules.normal(p,fixed,reg['shift'],'S4')
        profile_ms['normal']=(perf_counter()-tick)*1000
        threshold=max(1.,2.7*p.noise,.030*p.span)
        if (coarse or {}).get('anchor')=='MATERIAL_NOTCH':
            raw_field=base.fields(p,None)[0]
            yy=np.arange(score.shape[1])+p.origin[1]
            margin=max(3,round(.035*p.scale))
            interior=(yy>=band[0]+margin)&(yy<band[1]-margin)
            measured=bridge_fine&interior
            score=np.where(measured,np.maximum(raw_field,np.minimum(1.3,.30+.35*strength)),raw_field)
            score[:,~interior]=-np.inf
        physical,red,blue,reflection=curve.evidence(p,score,strength,dual,core,delta,dip,band)
        diag['field_sha']=hashlib.sha256(np.ascontiguousarray(physical)).hexdigest()
        physical[:,:lo]=-np.inf;physical[:,hi:]=-np.inf
        if stage=='S3':
            risk=transition.displaced_trace(delta,p.scale,p.noise,p.span)
            # Establish a stem direction before testing a displaced old line against it.
            risk*=np.clip((np.arange(len(risk))[:,None]/p.scale-.18)/.12,0,1)
        profile = base.mouth_profile(p,fixed,reg,score)
    if not joint:diag['field_sha']=hashlib.sha256(np.ascontiguousarray(score)).hexdigest()
    centres = np.asarray([np.median(g) for g in groups])
    owner = np.argmin(abs(np.arange(score.shape[1])[:,None]-centres),axis=1) if groups else []
    winner=None
    candidates=[]
    curves=[]
    contact=int(np.ptp(np.flatnonzero(seeds.any(axis=0))))+len(seeds) if groups else 0
    for idx,rows in enumerate(groups):
        entry=np.zeros_like(seeds)
        entry[:,rows]=seeds[:,rows]
        entry_field=score
        field=physical if joint else score
        if len(groups)>1:
            width=max(len(seeds),round(3.*np.min(np.diff(centres))))
            field=field.copy()
            field[:width,owner!=idx]=-np.inf
            entry[:,owner!=idx]=0
        tick=perf_counter()
        if joint and stage=='S3':
            path,total,reached=transition.lattice(field,entry,p.scale,dual,risk,True)
        else:
            path,total,V,back,direction=base.lattice(field,entry,p.scale,joint)
            reached=bool(np.isfinite(V[-48:]).any())
        profile_ms['lattice']+=(perf_counter()-tick)*1000
        diag['right_active'] |= reached
        if not len(path):
            diag['branches'].append(dict(id=idx,reason='EMPTY',merit=0.,root=None,tip=None,base_tip=None))
            continue
        old_tip=(path[-1]+origin).tolist()
        info={}
        if joint:
            proposal=path
            path,info,values=curve.trace(proposal,field,dual,red,blue,reflection,p.scale)
            if stage=='S3':
                charges=transition.transition_charges(proposal,dual,risk,p.scale)
                values-=np.cumsum(charges)
                cut=scratch_cut(proposal,delta,p)
                if cut is not None:values[cut:]=min(0.,values[:cut].min())-1.
                info['scratch_cut']=cut
                end=int(np.argmax(values))+1
                path=proposal[:end]
                xx,yy=path.T
                info.update(peak=float(values[end-1]),geometry_cost=float(charges[:end].sum()),
                            dual_columns=int(dual[xx,yy].sum()),red=float(red[xx,yy].sum()),
                            blue=float(blue[xx,yy].sum()))
            total=info['peak']
        else:
            values=np.cumsum(base.increments(field,path))
        if archive is not None:
            curves.append(np.asarray(values,dtype=np.float32))
        initial_total=float(base.increments(entry_field,path).sum())
        supported=joint and stage in STAGES and info['dual_columns']>=8 and total>0
        x,y=path.T
        stop='VALID'
        if initial_total<=.040*p.scale and not supported:stop='INSUFFICIENT_TOTAL'
        elif x[-1]-x[0]<px(p.scale,.030):stop='SHORT_PATH'
        elif base.topology.check(p.local[:,p.front:],path,0,p.scale,True)=='CLOSED_RIM':stop='CLOSED_RIM'
        if joint:
            if x[-1]<len(profile[0])-px(p.scale,.018) and base.mouth_test(path,p,field,profile)['dead']:
                stop='MOUTH_DEAD_END'
            thin=fine[x,y];agreement=thin & core[x,y]
            net_length=int(thin.sum());fraction=float(agreement.mean())
        else:
            net_length=int((field[x,y]>.08).sum());fraction=0.
        if joint:
            run=longest(dual[x,y])
            info['longest_dual_run']=run
            contour_only=(coarse or {}).get('anchor')=='BOUNDED_CONTOUR' and reg.get('status')!='OK'
            if contour_only and x[-1]-x[0]<=.25*p.scale and run<8 and stop=='VALID':
                stop='CONTOUR_SHORT_DUAL_RUN'
        if source=='PREEXISTING_CHECK':
            near=(x<=px(p.scale,.20)) & (x>px(p.scale,.015)) & (field[x,y]>.10)
            edges=np.flatnonzero(np.diff(np.r_[False,near,False]))
            if max((b-a for a,b in zip(edges[::2],edges[1::2])),default=0)<px(p.scale,.035):
                stop='NO_CONFIRMED_PREEXISTING'
        merit=float(total+.65*net_length+.70*fraction*len(path))
        if joint and stage in STAGES:
            merit=float(total)
        item=dict(id=idx,root=(path[0]+origin).tolist(),tip=(path[-1]+origin).tolist(),base_tip=old_tip,
                  initial_total=initial_total,reason=stop,value=float(total),net_length=net_length,
                  joint_fraction=fraction,merit=merit,curve=info,bridge=dict(accepted=False))
        if archive is not None:item['V']=np.round(values,3).tolist()
        diag['branches'].append(item)
        if stop=='VALID':candidates.append((path,item))
    diag['priority_applied']=joint and stage in STAGES and len(candidates)>1
    if candidates:winner=max(candidates,key=lambda pair:pair[1]['merit'])
    if archive is not None:
        archive.update(origin=origin,branch_ids=np.arange(len(curves)),curves=[c.tolist() for c in curves])
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
