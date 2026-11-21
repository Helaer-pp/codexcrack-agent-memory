"""Paired inference shares the V3.4 geometry runner; grayscale-only dispatches directly to V3.4."""
import numpy as np
from research.notch_identity_v31 import topology
from research.notch_identity_v31.detector import px
from research.notch_identity_v34 import guards, terminal as previous
from . import competition
from research.notch_identity_v34.terminal import follow
from .reference import Support

STAGES=('mouth','veto','v3_6')
def prepare(raw,hint,scale,stage='v3_6'):
    if stage not in STAGES:raise ValueError(stage)
    p=previous.prepare(raw,hint,scale)
    return (*p[:-3],stage,*p[-2:]) if p is not None else None

def predict(prepared,bonus,fixed=None):
    """fixed is the optional geometrically aligned reference in the input ROI."""
    if prepared is None:return competition.predict(None,None)
    if fixed is None:
        return previous.predict((*prepared[:-3],'v3_4',*prepared[-2:]),None)
    sl,(left,top),starts,sig,resp,scale,front,gray,noise,stage,raw,contrast=prepared
    support=None
    if fixed is not None:
        support=Support(raw,fixed,sl,(left,top),np.median(starts,axis=0),scale,noise,contrast,'v3_5')
        support.front=front
        support.patch='rollback' if stage=='v3_6' else stage
    protection=support
    if bonus is None:bonus=np.zeros_like(sig)
    bonus=np.where((sig>=.55)&(sig<1.),np.clip(bonus,0,.08),0).astype(np.float32)
    bonus[:,:front+px(scale,.2)+1]=0
    ridge=support.ridge
    original_starts=list(starts)
    fused=sig
    if ridge is not None:
        normalized=np.clip(ridge/max(3*noise,.08*contrast),0,1)
        extra=np.where(sig>.24,.35*normalized,0)
        extra[:,:front+px(scale,.20)]=0
        fused=(sig+extra).astype(np.float32) if support.coarse.get('anchor')=='CONTOUR' else sig
    red_seeds=set()
    closed_tips=[]
    audits=[]
    mid=float(np.median([p[1] for p in starts]))
    def candidate(s,rank_response,b,p):
        is_red=tuple(p) in red_seeds
        depth=resp
        if is_red:
            s=(s+np.minimum(.90,normalized)*np.clip(sig,0,1)).astype(np.float32)
            depth=resp+np.minimum(ridge,.10*contrast)
        rec=follow(s,depth,b,p,gray,scale,noise,stage,contrast,support=protection)
        a=rec['audit']
        if rec['tip'] and support is not None:
            extension=support.extend_clean(rec['points']) if a.get('geometry') in ('DISTAL_KINK','DISTAL_BRIGHT_GAP') else []
            if extension:
                rec['points']=rec['points']+extension
                rec['tip']=extension[-1]
                a['clean_extension']=len(extension)
            ref=support.review(rec['points'])
            if ref['cut'] is not None:
                oldtip=rec['tip']
                rec=follow(s,depth,b,p,gray,scale,noise,stage,contrast,ref['cut'],protection)
                a=rec['audit']
                ref['before_tip']=[oldtip[0]+left,oldtip[1]+top]
                ref['cut']+=left
                for key in ('prior_cut','break_x'):
                    if ref.get(key) is not None:ref[key]+=left
            a['reference']=ref
            if rec['tip']:
                rank=support.rank(rec['points']);a['increment_rank']=rank
                rec['rank_bonus']=rank['weight'];rec['tier']=rank.get('tier',0)
                if stage!='mouth' and ref.get('source')!='NONE':
                    body=ref.get('body_net')
                    static=ref['decision']=='NO_SUPPORTED_BOUNDARY' or body==0.
                    positive=(body or 0)>max(3*noise,.025*contrast) or ((rank.get('near_fraction') or 0)>.45 and (rank.get('mean') or 0)>3*noise)
                    rec['static_branch']=static
                    rec['positive_branch']=bool(positive and not static)
                    a.update(static_branch=static,positive_branch=rec['positive_branch'])
        if rec['tip']:
            reason=topology.check(gray,rec['points'],front,scale,True)
            if not reason and guards.open_rim(rec['points'],front,mid,scale,gray):
                reason='OUTWARD_OPEN_RIM'
            if reason=='CLOSED_RIM':closed_tips.append(np.asarray(rec['tip']))
            if is_red and any(np.linalg.norm(np.asarray(rec['tip'])-tip)<=px(scale,.030) for tip in closed_tips):
                reason='CLOSED_RIM'
            if reason and is_red and reason!='CLOSED_RIM':
                pts=np.asarray(rec['points'])
                near=pts[pts[:,0]<=p[0]+px(scale,.16)]
                _,evidence=support.evidence(near)
                if len(near)>=px(scale,.04) and evidence is not None and evidence['good'].mean()>=.85 and evidence['dup'].mean()<.1:
                    a['rescued_gate']=reason
                    reason=None
            if reason:rec.update(status=reason,points=[],tip=None)
        for name in ('first_loss','extinction_limit','geometry_cut','rebound_cut'):
            if a.get(name) is not None:a[name]+=left
        for event in a.get('events',[]):
            for j in range(3):event[j]+=left
        for key in ('waived','waived_lip'):a[key]=[v+left for v in a.get(key,[])]
        a['red_seed']=is_red
        audits.append(a)
        return rec
    def compete(roots):
        return competition.predict((sl,(left,top),roots,fused,np.clip(resp/contrast,0,1)*255,scale,front),bonus,candidate)
    result=compete(original_starts)
    choice=result['diagnostics'].get('selected')
    poor=choice is None or (audits[choice].get('increment_rank',{}).get('fraction') or 0)<.15
    whole=set()
    boundary=choice is not None and audits[choice].get('reference',{}).get('decision')=='NO_SUPPORTED_BOUNDARY'
    if ridge is not None and (poor or boundary):
        whole=set(support.mouth_seeds(original_starts,front))
        for x,y in original_starts:
            rad=px(scale,.025);width=px(scale,.055)
            y0=max(0,y-rad);y1=min(ridge.shape[0],y+rad+1)
            block=ridge[y0:y1,x:min(x+width,ridge.shape[1])]
            if block.shape[1]<width:continue
            # Probe along three plausible tangents within the original mouth corridor.
            for slope in (-.35,0,.35):
                cols=np.arange(width);ys=np.clip(np.arange(len(block))[:,None]+np.rint(slope*cols).astype(int),0,len(block)-1)
                strength=np.mean(block[ys,cols]>max(3*noise,.045*contrast),axis=1)
                j=int(np.argmax(strength))
                if strength[j]>=.68 and block[j,0]>max(2*noise,.035*contrast):
                    red_seeds.add((x,y0+j))
        red_seeds.update(whole)
        if red_seeds:
            audits.clear()
            roots=list(dict.fromkeys([*original_starts,*sorted(red_seeds)]))
            result=compete(roots)
    result['diagnostics']['added_ridge_seeds']=len(red_seeds)
    result['diagnostics']['whole_mouth_seeds']=len(whole)
    for c,a in zip(result['diagnostics']['candidates'],audits):c['trace']=a
    result['diagnostics']['coarse']=support.coarse if support else None
    return result
