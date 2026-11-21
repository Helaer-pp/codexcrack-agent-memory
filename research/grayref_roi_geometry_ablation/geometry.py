"""Image-evidence-only search masks. No paths, filenames, identities or labels accepted."""
import ast
import copy
import inspect
import math
import time
import numpy as np
import cv2
from grayref_simplified_evidence_v0 import algorithm as frozen

MODES=['A_ORIGINAL_ROI','B_COMPACT_FIXED_BAND','C_DYNAMIC_CORRIDOR']
CONFIG=dict(version='roi_geometry_r01',band_half_fraction=.15,half_min=12,
            corridor_half_fraction=.06,corridor_half_min=8,corridor_max_fraction=.30,
            safe_height_cap=.4,step=8,branches=3,widen_factor=1.25,shrink_factor=.8,
            stable_deviation=2.,seed_span_fraction=.1,seed_span_min=16,
            branch_separation_fraction=.03,branch_separation_min=4,support_columns=2,
            boundary_margin=2,display_diff=40,surface_cols=100,surface_rows=55)

def safe_mask(a):
    g=a['roi'];m=np.zeros(a['gray'][0].shape,bool)
    m[g['upper']-g['ya']+2:g['lower']-g['ya']-1,g['xleft']-g['xa']:g['xr']-g['xa']]=True
    return m

def fusion(a):
    c=frozen.CONFIG;V=a['valley'][0]
    D=np.nan_to_num(a['diff']['aligned_local'],nan=0).astype(np.float32)-a['gray'][0].astype(np.float32)-a['diff']['local_bias']
    scale=3*a['noise']+c['valley_scale']
    E=np.clip(V/scale,0,4)+c['ref_bonus']*a['diff']['ref_quality_map']*np.clip(np.maximum(D,0)/scale,0,4)
    eligible=a['material']&(V>=a['threshold'])
    return E,eligible

def masks(*,evidence,P_cur,config):
    if config!=CONFIG or set(config)!=set(CONFIG):raise ValueError('Frozen geometry schema only')
    a=evidence;g=a['roi'];P=np.asarray(P_cur,float)
    if P.shape!=(2,2) or not np.isfinite(P).all():raise ValueError('Invalid P')
    safe=safe_mask(a);h,w=safe.shape;d=float(np.linalg.norm(P[1]-P[0]));cy=float(P[:,1].mean()-g['ya'])
    sh=g['lower']-g['upper']-3;half=min(config['safe_height_cap']*sh,max(config['half_min'],config['band_half_fraction']*d))
    yy=np.arange(h)[:,None];band=safe&(np.abs(yy-cy)<=half)
    E,eligible=fusion(a);peak=eligible&(E>=np.roll(E,1,0))&(E>np.roll(E,-1,0))
    left=g['xleft']-g['xa'];right=g['xr']-g['xa'];span=max(config['seed_span_min'],round(config['seed_span_fraction']*d))
    hmin=max(config['corridor_half_min'],config['corridor_half_fraction']*d)
    hmax=max(hmin,min(config['safe_height_cap']*sh,config['corridor_max_fraction']*d))
    sep=max(config['branch_separation_min'],config['branch_separation_fraction']*d)
    # Same unverified geometric hypothesis in every image. Image notch may supply seed center,
    # but cannot replace physical identity certification or alter frozen ranking's notch.
    origin=a['notch']['point'];seedcy=origin[1]-g['ya'] if origin and abs(origin[1]-g['ya']-cy)<=half else cy
    seedx=max(left,min(right-1,round(origin[0]-g['xa']))) if origin and abs(origin[1]-g['ya']-cy)<=half else left
    window=peak[:,seedx:min(right,seedx+span)]&band[:,seedx:min(right,seedx+span)]
    support=window.sum(1);strength=np.where(window,E[:,seedx:min(right,seedx+span)],0).sum(1)
    options=sorted(np.flatnonzero(support>=config['support_columns']).tolist(),key=lambda y:(abs(y-seedcy),-float(strength[y]),y))
    centers=[]
    for y in options:
        if all(abs(y-v)>=sep for v in centers):centers.append(float(y))
        if len(centers)==config['branches']:break
    if not centers:centers=[seedcy]
    active=[dict(id=i,center=y,slope=0.,half=hmin,missing=0) for i,y in enumerate(centers)]
    planes=np.zeros((config['branches'],h,w),bool);events=[];nextid=len(active);expansions=0;contractions=0
    for b in active:planes[b['id'],:,left:seedx]=safe[:,left:seedx]&(np.abs(yy-b['center'])<=hmin)
    gap=int(np.clip(round(frozen.CONFIG['gap_fraction']*(right-left)),frozen.CONFIG['gap_min'],frozen.CONFIG['gap_max']))
    for x in range(seedx,right,config['step']):
        if not active:break
        xe=min(right,x+config['step']);proposed=[]
        for branch in active:
            center=branch['center'];hw=branch['half'];slot=branch['id']%config['branches']
            local=safe[:,x:xe]&(np.abs(yy-(center+branch['slope']*np.arange(xe-x)[None,:]))<=hw)
            planes[slot,:,x:xe]|=local
            ys,xs=np.where(peak[:,x:xe]&local);bins=[]
            # Cluster vertical alternatives; all supported branches compete only for the
            # explicit geometry-controller budget, never for the frozen path budget.
            for y in sorted(set(ys.tolist()),key=lambda y:(abs(y-center),y)):
                if any(abs(y-b['y'])<sep for b in bins):continue
                take=np.abs(ys-y)<max(2,sep*.5);n=len(set(xs[take].tolist()))
                if n>=config['support_columns']:
                    yfit=float(np.median(ys[take]));strength=float(np.mean(E[ys[take],xs[take]+x]))
                    bins.append(dict(y=yfit,n=n,strength=strength,deviation=float(np.std(ys[take]))))
            if bins:
                for b in bins[:config['branches']]:
                    stable=b['deviation']<=config['stable_deviation'] and abs(b['y']-center)<hw*.5
                    nh=max(hmin,hw*config['shrink_factor']) if stable else min(hmax,hw*config['widen_factor'])
                    reason='STABLE_SHRINK' if nh<hw else 'DISAGREEMENT_EXPAND' if nh>hw else 'STABLE_HOLD'
                    expansions+=nh>hw;contractions+=nh<hw
                    slope=float(np.clip((b['y']-center)/max(1,xe-x),-frozen.CONFIG['direction_limit'],frozen.CONFIG['direction_limit']))
                    proposed.append(dict(id=branch['id'],center=b['y']+slope*(xe-x)*.5,slope=slope,half=nh,missing=0,priority=b['strength'],parent=branch['id']))
                    events.append(dict(x0=x+g['xa'],x1=xe+g['xa'],branch=branch['id'],center_y=center+g['ya'],half_before=hw,half_after=nh,reason=reason,support_columns=b['n'],dispersion=b['deviation']))
            else:
                missing=branch['missing']+xe-x;nh=min(hmax,hw*config['widen_factor']);expansions+=nh>hw
                events.append(dict(x0=x+g['xa'],x1=xe+g['xa'],branch=branch['id'],center_y=center+g['ya'],half_before=hw,half_after=nh,reason='MISSING_EXPAND' if missing<=gap else 'GAP_BOUND_TERMINATE',support_columns=0,missing=missing))
                if missing<=gap:proposed.append({**branch,'center':center+branch['slope']*(xe-x),'half':nh,'missing':missing,'priority':-missing,'parent':branch['id']})
        chosen=[]
        for b in sorted(proposed,key=lambda b:(-b['priority'],b['center'],b['id'])):
            if any(abs(b['center']-v['center'])<sep for v in chosen):continue
            if len(chosen)<config['branches']:chosen.append(b)
            else:events.append(dict(x0=xe+g['xa'],reason='GEOMETRY_BRANCH_CAP',center_y=b['center']+g['ya'],parent=b['parent']))
        # Stable slot identities are geometry-display lanes, not physical branches.
        active=[{**b,'id':i} for i,b in enumerate(chosen)]
    corridor=planes.any(0)&safe
    return [safe,band,corridor],planes,dict(origin_status='ORIGIN_GEOMETRY_UNVERIFIED',P_scale=d,centerline_y=cy+g['ya'],band_half=half,corridor_half_min=hmin,corridor_half_max=hmax,seed_x=seedx+g['xa'],seed_centers=[y+g['ya'] for y in centers],events=events,expansions=expansions,contractions=contractions,branch_lanes=config['branches'],gap_bound=gap)

def make_runner():
    """Exact frozen run_mode body plus one eligibility-mask intersection."""
    source=inspect.getsource(frozen.run_mode);tree=ast.parse(source);fn=tree.body[0]
    fn.name='masked_run_mode';fn.args.args.append(ast.arg(arg='search_mask'))
    at=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='eligible' for t in n.targets))
    fn.body.insert(at+1,ast.parse('eligible = eligible & search_mask').body[0]);ast.fix_missing_locations(tree)
    ns=dict(vars(frozen));exec(compile(tree,'<audited-single-mask-adapter>','exec'),ns)
    stripped=copy.deepcopy(tree);f=stripped.body[0];f.name='run_mode';f.args.args.pop();f.body.pop(at+1)
    assert ast.dump(stripped,include_attributes=False)==ast.dump(ast.parse(source),include_attributes=False)
    return ns['masked_run_mode']

MASKED_RUN=make_runner()

def boundary(result,mask,a):
    g=a['roi'];p=result['paths'][0] if result['paths'] else None;tip=result['candidate_tip'];point=tip or result['last_observed_pixel']
    edge=mask & ~cv2.erode(mask.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
    touch=False;safe_touch=False;context=False;window=None
    if point:
        x,y=round(point[0]-g['xa']),round(point[1]-g['ya']);touch=bool(0<=y<mask.shape[0] and 0<=x<mask.shape[1] and edge[y,x])
        safe_touch=point[0]>=g['xr']-2 or point[1]<=g['upper']+3 or point[1]>=g['lower']-3
        trace=p['observed_trace'] if p else []
        idx=next((s['trace_index'] for s in p['stop_candidates'] if s['point']==point),len(trace)-1) if p else -1
        recent=[v for j,v in enumerate(trace) if v[2] and max(0,idx-12)<=j<=idx]
        direction=frozen.slope(recent) if recent else 0.
        endy=point[1]+direction*frozen.CONFIG['stop_lookahead']
        context=point[0]+frozen.CONFIG['stop_lookahead']>=g['xr'] or min(point[1],endy)-2<g['upper']+2 or max(point[1],endy)+2>=g['lower']-1
        window=dict(point=point,forward_dx=24,half_y=2,direction=direction,uses_full_safe_evidence=True,insufficient_geometric_context=context)
    return dict(corridor_touch=touch,safe_roi_touch=safe_touch,insufficient_context=context,tip_validation_window=window)

def detect(*,evidence,P_cur,config):
    if set(evidence)!={'gray','valley','background','material','roi','noise','threshold','diff','reference_windows','reference_status','notch'}:raise ValueError('Evidence schema rejects identity/GT/unknown fields')
    ms,branches,control=masks(evidence=evidence,P_cur=P_cur,config=config);results=[];graphs={};timing=[]
    for name,m in zip(MODES,ms):
        t=time.perf_counter()
        r,graph=(frozen.run_mode(evidence,'C_FUSION_RAW',frozen.CONFIG) if name==MODES[0] else MASKED_RUN(evidence,'C_FUSION_RAW',frozen.CONFIG,m))
        elapsed=(time.perf_counter()-t)*1000;native=copy.deepcopy(r);b=boundary(r,m,evidence)
        if name!=MODES[0] and (b['corridor_touch'] or b['insufficient_context']) and r['paths']:
            r['tip']=None;r['output_state']='ROI_LIMITED';r['tip_status']='ROI_LIMITED'
        r.update(mode=name,native_output_state=native['output_state'],native_tip=native['tip'],geometry_boundary=b)
        results.append(r);graphs[name]=graph;timing.append(dict(mode=name,inference_ms=elapsed))
    return results,graphs,ms,branches,control,timing
