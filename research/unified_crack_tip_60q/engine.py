"""Current-observation engine. No filesystem, sample identity or annotation interface."""
import copy,heapq,math
import numpy as np
from scipy.spatial import cKDTree
from .config import CONFIG,ARMS,validate
from .features import prepare,ordered_points,NORMALS
from .graph import build_graph

def initial_state():return dict(tracks=[],next_id=1,main_track=None,last_official=None,last_geometry=None,opening=None)
def trace(e,k,entry=0):
    p=e['xy'][e['ptr'][k]:e['ptr'][k+1]]
    return p if entry==0 else p[::-1]

def dynamic_mask(e,state,disabled,c):
    g=e['scene'];xa,ya,xb,yb=g['bounds'];shape=e['raw'].shape;mask=np.zeros(shape,bool);events=[]
    if 'dynamic_roi' in disabled:
        mask[:]=True;return mask,[dict(action='STATIC_SAFE_AREA',bounds=g['bounds'],reason='ABLATION')],False
    center=float((g['root'] or g['center'])[1]);half=max(12.,c['roi_initial_halfwidth']*g['scale']);maximum=max(half,.8*g['scale'])
    f=e['features'];scout=(f[:,0]>=c['roi_scout_min_pixels'])&(f[:,6]>=.65)
    if 'tracking' not in disabled and state['tracks']:
        hist=[t for t in state['tracks'] if t['missed']<=c['track_lost_ttl']]
        if hist:events.append(dict(action='HISTORY_SCOUT_HINT',bounds=g['bounds'],reason='PAST_EXTENT_ONLY',max_x=max(t['historical_max_x'] for t in hist)))
    count=0;budget=False
    for x in range(xa,xb,c['roi_step']):
        if count>=c['roi_max_expansions']:budget=True;events.append(dict(action='BUDGET_STOP',reason='ROI_EXPANSIONS',x=x));break
        end=min(x+c['roi_step'],xb);in_strip=scout&(f[:,11:15:2].max(1)>=x)&(f[:,11:15:2].min(1)<end)
        ymid=(f[:,12]+f[:,14])*.5;near=in_strip&(np.abs(ymid-center)<=half)
        old=(center,half);reason='FORWARD_SCOUT_NO_STRONG_SEGMENT'
        if near.any():
            next_center=float(np.median(ymid[near]));center=.5*center+.5*next_center;half=max(12.,half*.9);reason='CURRENT_STRUCTURED_SCOUT'
        else:half=min(maximum,half*1.3);reason='ROLLBACK_WIDEN_NO_CURRENT_SUPPORT'
        # Independent full-height scout may retain multiple disjoint lanes. No self-confirming endpoint extension.
        bands=[(center-half,center+half)]
        far=np.flatnonzero(in_strip&~near)
        for k in far:
            y=float(ymid[k]);bands.append((y-max(8.,.08*g['scale']),y+max(8.,.08*g['scale'])))
        if 'tracking' not in disabled:
            for t in state['tracks']:
                if t['missed']<=c['track_lost_ttl'] and x<=t['historical_max_x']+c['roi_step']:
                    y=t['last_tip'][1];bands.append((y-half,y+half))
        for lo,hi in bands:mask[max(0,int(lo-ya)):min(shape[0],int(math.ceil(hi-ya))+1),x-xa:end-xa]=True
        events.append(dict(action='INITIAL' if count<c['roi_initial_steps'] else 'ADVANCE',bounds=[x,max(ya,center-half),end,min(yb,center+half)],reason=reason,
                           center_before=old[0],halfwidth_before=old[1],center_after=center,halfwidth_after=half,independent_scout_segments=int(in_strip.sum()),lanes=len(bands)))
        count+=1
    return mask,events,budget

def path_evidence(e,chain,disabled,opening,c):
    ids=[k for k,entry in chain];f=e['features'][ids];weights=np.maximum(f[:,0],1);obs=int(weights.sum());g=e['scene'];root=np.asarray(g['root'] or g['center'])
    start=trace(e,*chain[0])[0];end=trace(e,*chain[-1])[-1]
    distance=float(np.linalg.norm(start-root));root_support=float(math.exp(-distance/max(20,c['root_soft_scale']*g['scale'])))
    depth=float(np.average(f[:,2],weights=weights));continuity=float(np.average(f[:,6],weights=weights))
    refs={}
    for channel,col in [('fixed',7),('prev',9)]:
        fraction=0. if channel in disabled else float(np.average(f[:,col],weights=weights));valid=(f[:,col]>0)&np.isfinite(f[:,col+1])
        delta=float(np.average(f[valid,col+1],weights=weights[valid]*f[valid,col])) if fraction>0 and valid.any() else None
        refs[channel]=dict(available=fraction>0,coverage=fraction,signed_line_minus_background=delta,positive_support=delta is not None and delta>=e['threshold']*.5)
    agreement=0
    if 'opening' not in disabled and opening is not None and abs(opening)>.1:
        values=[v['signed_line_minus_background'] for v in refs.values() if v['available'] and v['signed_line_minus_background'] is not None]
        agreement=int(bool(values) and np.sign(np.median(values))==np.sign(opening))
    return dict(observed_pixels=obs,raw_depth=depth,raw_threshold=e['threshold'],coherence=continuity,origin_distance=distance,origin_support=root_support,
                fixed=refs['fixed'],prev=refs['prev'],opening_proxy=None if 'opening' in disabled else opening,opening_reference_agreement=agreement,observed_start=start.tolist(),observed_end=end.tolist())

def build_candidates(e,mask,state,disabled,c):
    f=e['features'];n=len(f);xy=e['xy'];ptr=e['ptr'];g=e['scene'];xa,ya,_,_=g['bounds']
    ins=mask[xy[:,1]-ya,xy[:,0]-xa] if len(xy) else np.array([],bool)
    sums=np.add.reduceat(ins.astype(np.int32),ptr[:-1]) if n else np.array([],int)
    inside=sums==np.diff(ptr);eligible=e['graph_eligible']&inside
    reason=np.where(~e['graph_eligible'],1,np.where(~inside,2,0)).astype(np.uint8)
    adjacency={};edge_records=[];edges=e['edges'];edge_budget=e['graph_info']['budget_exhausted'];global_budget=e['counts']['budget_exhausted'] or edge_budget
    for i in np.flatnonzero(edges[:,7]==0):
        row=edges[i]
        u,v=int(row[0]),int(row[1]);a,b=u//2,v//2
        if row[7]!=0 or not eligible[a] or not eligible[b]:continue
        if 'gap' in disabled and row[2]>1.5:continue
        adjacency.setdefault(u,[]).append((v,i));adjacency.setdefault(v,[]).append((u,i))
    for v in adjacency.values():v.sort(key=lambda z:(float(edges[z[1],2]),z[0]))
    root=np.asarray(g['root'] or g['center'],float);zone=g['origin_zone'];seeds=[];entry_choices={}
    history_tips=[t['last_tip'] for t in state['tracks'] if t['missed']<=c['track_lost_ttl']] if 'tracking' not in disabled else []
    history_near=cKDTree(np.asarray(history_tips)).query(f[:,11:15].reshape(-1,2),k=1)[0].reshape(-1,2) if history_tips else np.full((n,2),np.inf)
    for k in np.flatnonzero(eligible):
        p=f[k,11:15].reshape(2,2);dist=np.linalg.norm(p-root,axis=1);entry=int(np.argmin(dist));start=p[entry]
        near=zone[0]<=start[0]<=zone[2] and zone[1]<=start[1]<=zone[3]
        historical=False
        if 'tracking' not in disabled:
            historical=history_near[k,entry]<max(20,.2*g['scale'])
        if not near and not historical:reason[k]=3;continue
        if not e['component_structure'][e['component_ids'][k]] and not historical:continue
        # Lexicographic comparison: geometry association, current structure, then weak opening tie context.
        priority=(float(dist[entry]),-float(f[k,2]),-float(f[k,0]),int(k))
        entry_choices.setdefault(int(e['component_ids'][k]),[]).append((priority,int(k),entry))
    for component,choices in entry_choices.items():
        # One entry per observed connected component; all outgoing terminal branches are still explored.
        seeds.append(min(choices))
    seeds.sort()
    if len(seeds)>c['max_roots']:global_budget=True
    roots=seeds[:c['max_roots']];front=[];best={};predecessor={};settled=set();alternatives=[];states=0
    for priority,k,entry in roots:
        key=2*k+entry;cost=(priority[0],0.,float(f[k,0]/(1+f[k,2])))
        if key not in best or cost<best[key]:
            best[key]=cost;predecessor[key]=None;heapq.heappush(front,(cost,key))
    while front and states<c['max_route_states']:
        cost,key=heapq.heappop(front)
        if key in settled or cost!=best[key]:continue
        settled.add(key);states+=1;k,entry=key//2,key%2;endpoint=2*k+(1-entry)
        for other,edge in adjacency.get(endpoint,[]):
            kk=other//2
            if kk==k:continue
            nxt=(cost[0],cost[1]+float(edges[edge,3]),cost[2]+float(f[kk,0]/(1+f[kk,2])))
            if other not in best or nxt<best[other]:
                if other in best:alternatives.append(dict(destination=other,previous=predecessor[other],cost=best[other],reason='LEXICOGRAPHIC_DOMINATED_SAME_ORIENTED_SEGMENT'))
                best[other]=nxt;predecessor[other]=(key,edge);heapq.heappush(front,(nxt,other))
            else:alternatives.append(dict(destination=other,previous=[key,edge],cost=nxt,reason='LEXICOGRAPHIC_DOMINATED_SAME_ORIENTED_SEGMENT'))
    if front:global_budget=True
    candidates=[];prefixes=[];seen_endpoints={};route_records=[]
    for key in sorted(settled):
        k,entry=key//2,key%2;endpoint=2*k+(1-entry)
        onward=adjacency.get(endpoint,[])
        route_records.append(dict(state=key,predecessor=predecessor[key],cost=best[key],segment=k,entry=entry))
        # Retain distinct real ends before gaps as diagnostics, but connected observed continuation is not a tip.
        observed_onward=any(edges[i,2]<=1.5 for other,i in onward if other//2!=k)
        if observed_onward:
            prefixes.append(dict(state=key,endpoint=trace(e,k,entry)[-1].tolist(),reason='OBSERVED_CONTINUATION_NOT_TERMINAL'));continue
        chain=[];used_edges=[];at=key;seen=set()
        while at is not None:
            if at in seen:raise AssertionError('Positive-cost predecessor graph cycle')
            seen.add(at);chain.append((at//2,at%2));prior=predecessor[at]
            if prior is None:break
            at,edge=prior;used_edges.append(edge)
        chain.reverse();used_edges.reverse();evidence=path_evidence(e,chain,disabled,e['opening_proxy'],c)
        if evidence['observed_pixels']<c['min_path_observed']:continue
        # Loopy texture paths are compared at path level, not discarded as weak RAW pixels.
        displacement=float(np.linalg.norm(np.asarray(evidence['observed_end'])-np.asarray(evidence['observed_start'])))
        coherence=displacement/max(1,evidence['observed_pixels']+best[key][1]);evidence['path_straightness']=coherence
        candidate=dict(id=len(candidates),chain=chain,edges=used_edges,inferred_gap_distance=best[key][1],evidence=evidence,
                       terminal=not onward,endpoint=trace(e,k,entry)[-1].tolist(),branch_id='branch-'+str(key),rejected_reasons=[],verified=False)
        if coherence<.3:candidate['rejected_reasons'].append('LOOPY_PATH_GEOMETRY')
        # Exact end identity is the directed terminal segment, not prefix containment.
        end_key=(*candidate['endpoint'],k,entry)
        if end_key in seen_endpoints:continue
        seen_endpoints[end_key]=candidate['id'];candidates.append(candidate)
    candidates.sort(key=lambda p:(not p['terminal'],-p['evidence']['origin_support'],-p['evidence']['raw_depth'],p['id']))
    omitted=candidates[c['max_candidates']:]
    if omitted:global_budget=True
    selected=candidates[:c['max_candidates']]
    return selected,dict(segment_outcomes=reason,segment_outcome_codes={'0':'SEARCHED','1':'NOT_STRUCTURED_FOR_CONNECTION','2':'OUTSIDE_WORKING_MASK','3':'NO_ORIGIN_OR_HISTORY_SEED'},
                         roots_total=len(seeds),roots_explored=len(roots),route_states=states,unvisited_states=len(front),
                         pruned=alternatives,deduplicated=prefixes,predecessor_states=route_records,
                         omitted_candidates=[dict(id=p['id'],endpoint=p['endpoint'],chain=p['chain'],reason='CANDIDATE_BUDGET') for p in omitted],
                         candidate_count=len(selected),budget_exhausted=global_budget)


def verify_candidate(p,e,disabled,state,c):
    v=p['evidence'];g=e['scene'];pts=np.concatenate([trace(e,k,side) for k,side in p['chain']])
    # Each route ends on a current observed segment; internal bend extrema are not branch tips.
    tip=trace(e,*p['chain'][-1])[-1];p['endpoint']=tip.tolist()
    xa,ya,xb,yb=g['bounds'];x,y=int(tip[0]-xa),int(tip[1]-ya)
    tail=trace(e,*p['chain'][-1]);p['tip_observation']='CURRENT_OBSERVED';p['raw_tail_points']=tail[-min(len(tail),8):].tolist()
    current_ok=v['observed_pixels']>=c['min_path_observed'] and v['raw_depth']>=c['strong_factor']*e['threshold'] and v['coherence']>=.55
    continuity=v['observed_pixels']/max(1,v['observed_pixels']+p['inferred_gap_distance']);p['evidence']['observed_fraction']=continuity
    root_support=v['origin_support'];has_ref=v['fixed']['positive_support'] or v['prev']['positive_support']
    # No reference veto: strong current geometry connection is independently sufficient.
    identity=(root_support>=.5 and continuity>=.8 and v['raw_depth']>=2*e['threshold'] and v['observed_pixels']>=12) or (root_support>=.08 and has_ref and continuity>=.85)
    # A historical link is supportive only when independently corroborated by current structure/context.
    history_support=False
    if 'tracking' not in disabled:
        for t in state['tracks']:
            old=np.asarray(t['signature'],float)
            if len(old) and t['missed']<=c['track_lost_ttl']:
                near,_=state['_signature_trees'][t['id']].query(pts[::max(1,len(pts)//32)],k=1)
                if float(np.mean(near<max(5,.04*g['scale'])))>=.45:history_support=True
    identity=identity or (history_support and root_support>=.1 and current_ok and continuity>=.9)
    p['evidence']['history_support']=history_support
    context=e['raw'][max(0,y-3):min(e['raw'].shape[0],y+4),x+1:min(e['raw'].shape[1],x+1+c['tip_context'])]
    material=float(np.mean(context>=c['material_min'])) if context.size else 0.
    boundary=x<2 or y<2 or x>=e['raw'].shape[1]-c['tip_context'] or y>=e['raw'].shape[0]-2
    p['evidence']['after_material_fraction']=material;p['evidence']['near_safe_boundary']=boundary
    if not current_ok:p['rejected_reasons'].append('CURRENT_SEGMENT_NOT_RELIABLE')
    if not identity:p['rejected_reasons'].append('CRACK_IDENTITY_UNCERTAIN')
    if not p['terminal']:p['rejected_reasons'].append('OBSERVED_OR_SUPPORTED_CONTINUATION')
    if continuity<.7:p['rejected_reasons'].append('INFERRED_GAP_DOMINATES')
    if boundary or material<c['tip_material_fraction']:p['rejected_reasons'].append('INSUFFICIENT_CURRENT_TIP_CONTEXT')
    # Extremely dark isolated strokes need structural origin support, not simply a large x.
    gray=float(e['raw'][y,x]);p['evidence']['tip_gray']=gray
    if gray<25 and root_support<.5 and not has_ref:p['rejected_reasons'].append('DARK_STROKE_IDENTITY_UNRESOLVED')
    p['verified']=not p['rejected_reasons']
    return p

def motion_recheck(p,e,previous,c):
    if previous is None:return None
    tip=np.asarray(p['endpoint'],float);delta=float(np.linalg.norm(tip-np.asarray(previous,float)))
    if delta<=max(8.,c['jump_scale']*e['scene']['scale']):return None
    xa,ya,_,_=e['scene']['bounds'];x,y=np.rint(tip-[xa,ya]).astype(int);raw=e['raw'].astype(np.float32)
    samples=[]
    for nx,ny in NORMALS:
        for k in c['normal_offsets']:
            if 0<=y+k*ny<raw.shape[0] and 0<=y-k*ny<raw.shape[0] and 0<=x+k*nx<raw.shape[1] and 0<=x-k*nx<raw.shape[1]:
                samples.append(float(min(raw[y+k*ny,x+k*nx],raw[y-k*ny,x-k*nx])-raw[y,x]))
    direct_raw=max(samples,default=0.)
    passed=direct_raw>=e['threshold'] and p['evidence']['observed_fraction']>=.7 and not p['evidence']['near_safe_boundary']
    if not passed:p['verified']=False;p['rejected_reasons'].append('ANOMALY_RAW_OR_CONNECTIVITY_RECHECK_FAILED')
    return dict(flag='MOTION_ANOMALY_RECHECK',distance=delta,direct_raw_depth=direct_raw,current_threshold=e['threshold'],
                references={k:p['evidence'][k] for k in ['fixed','prev']},observed_fraction=p['evidence']['observed_fraction'],passed=passed,
                decision_basis='CURRENT_RAW_CONTEXT_CONNECTION; distance triggers review only',no_displacement_rejection=True)

def update_tracks(candidates,state,disabled,g,c):
    old=state['tracks'] if 'tracking' not in disabled else [];updated=[];transitions=[];assigned=set();next_id=state['next_id']
    reliable=[p for p in candidates if p['verified']]
    if 'multitrack' in disabled and reliable:
        chosen=max(reliable,key=lambda p:(p['evidence']['origin_support'],p['evidence']['raw_depth']));
        for p in reliable:
            if p is not chosen:p['verified']=False;p['rejected_reasons'].append('SINGLE_TRACK_ABLATION_NOT_PURSUED')
        reliable=[chosen]
    for p in sorted(reliable,key=lambda p:(p['endpoint'][0],p['endpoint'][1],p['id'])):
        tip=np.asarray(p['endpoint']);signature=p.pop('_signature');matches=[]
        for t in old:
            if t['id'] in assigned or t['missed']>c['track_lost_ttl']:continue
            # Distance ranks identity association; it never vetoes a verified current branch.
            d=float(np.linalg.norm(tip-np.asarray(t['last_tip'])))/max(1,g['scale'])
            tree=state['_signature_trees'][t['id']];ds,_=tree.query(signature,k=1);overlap=float((ds<max(5,.04*g['scale'])).mean())
            matches.append((1-overlap+d,t,overlap))
        match=min(matches,key=lambda a:(a[0],a[1]['id'])) if matches else None
        if match is not None and (match[2]>.2 or match[0]<c['track_match_scale']):
            prior=match[1];tid=prior['id'];assigned.add(tid);status='REACQUIRING' if prior['missed'] else 'ACTIVE';extent=max(prior['historical_max_x'],float(tip[0]));parent=prior['parent']
        else:
            tid=next_id;next_id+=1;status='ACTIVE';extent=float(tip[0]);parent=state['main_track'] if old else None
        p['track_id']=tid;p['track_state']=status
        updated.append(dict(id=tid,parent=parent,branch_id=p['branch_id'],state='ACTIVE',missed=0,last_tip=tip.tolist(),signature=signature.tolist(),historical_max_x=extent))
        transitions.append(dict(track_id=tid,parent=parent,transition=status,current_verified=True))
    for t in old:
        if any(v['id']==t['id'] for v in updated):continue
        missed=t['missed']+1
        if missed<=c['track_lost_ttl']:
            updated.append({**t,'state':'LOST','missed':missed});transitions.append(dict(track_id=t['id'],transition='LOST',current_verified=False))
        else:transitions.append(dict(track_id=t['id'],transition='EXPIRED_REINITIALIZE',current_verified=False))
    exhausted=len(updated)>c['max_tracks'];updated=sorted(updated,key=lambda t:(t['missed'],t['id']))[:c['max_tracks']]
    main=state['main_track'] if any(t['id']==state['main_track'] and t['missed']==0 for t in updated) else None
    if main is None and reliable:main=max(reliable,key=lambda p:(p['evidence']['origin_support'],p['evidence']['raw_depth']))['track_id']
    if main is not None and reliable:
        old_main=next((p for p in reliable if p['track_id']==main),None)
        challenger=max(reliable,key=lambda p:(p['evidence']['origin_support'],p['evidence']['raw_depth']))
        if old_main is not None and challenger['evidence']['origin_support']>old_main['evidence']['origin_support']+c['main_hysteresis'] and challenger['evidence']['raw_depth']>1.2*old_main['evidence']['raw_depth']:
            transitions.append(dict(transition='MAIN_IDENTITY_CORRECTED_BY_CURRENT_DOMINANCE',old=main,new=challenger['track_id']))
            main=challenger['track_id']
    # Hysteresis concerns identity only. Official output selection below ignores this main ID.
    return updated,transitions,next_id,main,exhausted

def select_official(candidates,budget=False):
    valid=[p for p in candidates if p['verified']]
    if budget:return None,'BUDGET_EXHAUSTED'
    if not valid:return None,'IDENTITY_UNCERTAIN' if candidates else 'NO_VISIBLE_TRACK'
    best_x=max(p['endpoint'][0] for p in valid);ties=[p for p in valid if p['endpoint'][0]==best_x]
    ties.sort(key=lambda p:(-p['evidence']['origin_support'],-p['evidence']['raw_depth'],p['id']))
    if len(ties)>1 and ties[0]['endpoint'][1]!=ties[1]['endpoint'][1]:
        a,b=ties[:2]
        if abs(a['evidence']['origin_support']-b['evidence']['origin_support'])<.1 and abs(a['evidence']['raw_depth']-b['evidence']['raw_depth'])<2:return None,'IDENTITY_UNCERTAIN'
    return ties[0],'VALID'

class Engine:
    def __init__(self,config=None,arm='FULL'):
        self.config=copy.deepcopy(CONFIG if config is None else config);validate(self.config)
        if arm not in ARMS:raise ValueError('Unknown ablation arm')
        self.arm=arm;self.disabled=set(ARMS[arm]);self.state=initial_state()
    def process(self,current,current_points,fixed,fixed_points,previous=None,previous_points=None):
        try:e=prepare(current,current_points,fixed,fixed_points,previous,previous_points,self.state['last_geometry'],self.config)
        except ValueError as exc:
            budget=str(exc).startswith('BUDGET:')
            return dict(status='BUDGET_EXHAUSTED' if budget else 'PROCESSING_ERROR',tip=None,failure_reason='BUDGET' if budget else 'INPUT',error=str(exc),candidates=[],budget=dict(exhausted=budget)),{}
        e['edges'],e['graph_eligible'],e['graph_info']=build_graph(e,self.config)
        return self.process_evidence(e)
    def process_evidence(self,e):
        c=self.config;state={**self.state,'_signature_trees':{t['id']:cKDTree(np.asarray(t['signature'])) for t in self.state['tracks']}};disabled=self.disabled;g=e['scene'];mask,roi_events,roi_budget=dynamic_mask(e,state,disabled,c)
        candidates,lineage=build_candidates(e,mask,state,disabled,c);rechecks=[];recheck_budget=False
        for p in candidates:
            verify_candidate(p,e,disabled,state,c)
            anomaly=None
            if p['verified']:
                needs_recheck='tracking' not in disabled and state['last_official'] is not None and np.linalg.norm(np.asarray(p['endpoint'])-np.asarray(state['last_official']))>max(8.,c['jump_scale']*g['scale'])
                if needs_recheck and len(rechecks)>=c['max_rechecks']:
                    recheck_budget=True;p['verified']=False;p['rejected_reasons'].append('RECHECK_BUDGET')
                else:anomaly=motion_recheck(p,e,state['last_official'] if 'tracking' not in disabled else None,c)
            if anomaly is not None:
                rechecks.append(dict(candidate_id=p['id'],**anomaly))
                if len(rechecks)>c['max_rechecks']:recheck_budget=True
            pts=np.concatenate([trace(e,k,s) for k,s in p['chain']]);p['_signature']=pts[::max(1,len(pts)//32)].astype(float)
        tracks,transitions,next_id,main,track_budget=update_tracks(candidates,state,disabled,g,c)
        for p in candidates:p.pop('_signature',None)
        exhausted=roi_budget or lineage['budget_exhausted'] or recheck_budget or track_budget
        chosen,status=select_official(candidates,exhausted)
        if not exhausted and chosen is None and not candidates and any(t['state']=='LOST' for t in tracks):status='TRACK_LOST'
        preferred=max(candidates,key=lambda p:(int(p['evidence']['origin_support']*10),int(p['evidence']['raw_depth']/5),p['evidence']['opening_reference_agreement'],p['evidence']['origin_support'],p['evidence']['raw_depth'])) if candidates and chosen is None else None
        flags=[]
        if not g['points_observed']:flags.append('P1P2_DEGRADED')
        if not g['root']:flags.append('NOTCH_ROOT_UNCERTAIN')
        if rechecks:flags.append('MOTION_ANOMALY_RECHECK')
        for channel in ['fixed','prev']:
            if channel in disabled or e['reference_info'][channel]['status']=='UNAVAILABLE':flags.append(channel.upper()+'_REF_UNAVAILABLE')
        if exhausted:failure='BUDGET'
        elif chosen is not None:failure=None
        elif not candidates:failure='CONNECTIVITY' if e['counts']['segments'] else 'GRAY_SEGMENT'
        elif all('CRACK_IDENTITY_UNCERTAIN' in p['rejected_reasons'] for p in candidates):failure='TRACK_IDENTITY'
        else:failure='TIP_VERIFICATION'
        result=dict(schema_version='UCTIP-1.0',status=status,tip=None if chosen is None else chosen['endpoint'],selected_track_id=None if chosen is None else chosen['track_id'],
                    selection_rule='MAX_VALID_IMAGE_X',main_track_id=main,preferred_uncertain_tip=None if preferred is None else preferred['endpoint'],
                    candidates=candidates,flags=flags,failure_reason=failure,reference_info=e['reference_info'],
                    channels={**{k:('UNAVAILABLE' if k in disabled else e['reference_info'][k]['status']) for k in ['fixed','prev']},'p1p2':'OBSERVED' if g['points_observed'] else 'HISTORICAL_GEOMETRY_ONLY'},
                    tracks=tracks,track_transitions=transitions,rechecks=rechecks,roi_events=roi_events,scene=g,
                    budget=dict(exhausted=exhausted,roi=roi_budget,graph=lineage['budget_exhausted'],rechecks=recheck_budget,tracks=track_budget,
                                raw=e['counts'],graph_counts=e['graph_info'],route_states=lineage['route_states'],working_pixels=int(mask.sum()),scout_pixels=e['raw'].size),
                    counts={k:lineage[k] for k in ['roots_total','roots_explored','route_states','unvisited_states','candidate_count']},opening_proxy=None if 'opening' in disabled else e['opening_proxy'],arm=self.arm)
        self.state=dict(tracks=tracks,next_id=next_id,main_track=main,last_official=state['last_official'] if chosen is None else chosen['endpoint'],
                        last_geometry=g['points_geometry'] if g['points_observed'] else state['last_geometry'],opening=e['opening_proxy'])
        return result,dict(mask=mask,segment_outcomes=lineage.pop('segment_outcomes'),lineage=lineage)
