"""Deterministic event proposals. No identity, filename, family or GT input."""
from common3 import *
from candidates import profile,propose as old_propose,PARAM as OLD_PARAM
PARAM=dict(K=12,max_samples=4096,window_width_factors=[2.,4.,6.],window_min=6.,window_max=32.,
    pre_snr=3.,drop_snr=2.5,merge_width=.75,peak_radius_width=.75,plateau_fraction=.9)

def legacy_trace(cur,path,tip,valid,width,tiles):
    pool,seq,cost=old_propose(cur,path,tip,valid,width,tiles)
    pr=profile(cur,path,width);raw=[];filters=[]
    if pr is None:return pool,raw,filters
    p,s,w=pr['xy'],pr['s'],pr['width'];sig=pr['peak']/pr['noise'];N=len(s)
    win=max(3,int(np.clip(4*w,8,24)/pr['step']));proposals=[]
    for j in range(N):
        inwindow=win<=j<N-win
        pre=float(np.median(sig[j-win:j])) if inwindow else None
        post=float(np.median(sig[j+1:j+win+1])) if inwindow else None
        turn=float(np.arccos(np.clip(pr['t'][j-win]@pr['t'][j+win],-1,1))) if inwindow else None
        observed=bool(pr['valid'][max(0,j-win):min(N,j+win+1)].mean()>=.9)
        for origin in ['SUSTAINED_SUPPORT_CHANGE','BRANCH_OR_GEOMETRY_CHANGE']:
            strength=(pre-post if origin=='SUSTAINED_SUPPORT_CHANGE' else turn*5) if inwindow else None
            eligible=bool(inwindow and observed and pre>3 and (pre-post>2.5 if origin=='SUSTAINED_SUPPORT_CHANGE' else turn>.35))
            event_id=f'{origin}:{j}'
            why='PASSED_EVENT_THRESHOLD' if eligible else 'WINDOW_END_MARGIN' if not inwindow else 'INVALID_SAMPLES' if not observed else 'PRE_SUPPORT_BELOW_THRESHOLD' if pre<=3 else 'CHANGE_BELOW_THRESHOLD'
            r=dict(event_id=event_id,raw_s=float(s[j]),raw_xy=p[j].tolist(),origin=origin,strength=strength,observable=observed,pre=pre,post=post,turn=turn,window=win,eligible=eligible,first_reason=why)
            raw.append(r)
            if eligible:proposals.append((strength,j,origin,event_id))
            else:filters.append(dict(event_id=event_id,stage='EVENT_GENERATION',kept=False,reason=why,competing_id=None))
    if len(tiles)>1:
        for k,(a,b) in enumerate(zip(tiles[:-1],tiles[1:])):
            if a[5]-b[5]>.25 or (a[4]>20 and b[4]<.4*a[4]):
                j=int(np.argmin(np.linalg.norm(p-np.asarray(b[:2]),axis=1)));eligible=win<=j<N-win;event_id=f'NATIVE_TILE_SUPPORT_CHANGE:{k}'
                strength=3+max(0.,a[5]-b[5])*5
                raw.append(dict(event_id=event_id,raw_s=float(s[j]),raw_xy=p[j].tolist(),origin='NATIVE_TILE_SUPPORT_CHANGE',strength=strength,observable=bool(pr['valid'][j]),eligible=eligible,first_reason='PASSED_EVENT_THRESHOLD' if eligible else 'WINDOW_END_MARGIN'))
                if eligible:proposals.append((strength,j,'NATIVE_TILE_SUPPORT_CHANGE',event_id))
                else:filters.append(dict(event_id=event_id,stage='EVENT_GENERATION',kept=False,reason='WINDOW_END_MARGIN',competing_id=None))
    chosen=[dict(xy=list(tip),event_id='A_ORIGINAL')] if valid else []
    raw.append(dict(event_id='A_PATH_TERMINAL',raw_s=float(s[-1]),raw_xy=p[-1].tolist(),origin='A_PATH_TERMINAL',strength=None,observable=bool(pr['valid'][-1]),eligible=valid,first_reason='OFFICIAL_VALID' if valid else 'OFFICIAL_TIP_NOT_CONFIRMED'))
    filters.append(dict(event_id='A_PATH_TERMINAL',stage='VALID_ONLY_ENDPOINT',kept=valid,reason='A_ORIGINAL_RETAINED' if valid else 'UNCONFIRMED_ENDPOINT_NOT_PROPOSED',competing_id=None))
    groups={origin:sorted([x for x in proposals if x[2]==origin],reverse=True) for origin in ['SUSTAINED_SUPPORT_CHANGE','BRANCH_OR_GEOMETRY_CHANGE','NATIVE_TILE_SUPPORT_CHANGE']}
    while len(chosen)<12 and any(groups.values()):
        for origin,q in groups.items():
            if not q or len(chosen)>=12:continue
            strength,j,_,eid=q.pop(0);xy=p[j]+float(pr['offsets'][pr['best'][j]])*pr['n'][j]
            near=next((c for c in chosen if np.linalg.norm(xy-c['xy'])<max(4.,3*w)),None)
            filters.append(dict(event_id=eid,stage='NORMAL_REFINEMENT_AND_MERGE',kept=near is None,reason='MERGED' if near else 'KEPT',competing_id=near['event_id'] if near else None,refined_xy=xy.tolist(),normal_offset=float(pr['offsets'][pr['best'][j]])))
            if near is None:chosen.append(dict(xy=xy.tolist(),event_id=eid))
    for q in groups.values():
        for _,j,_,eid in q:filters.append(dict(event_id=eid,stage='BUDGET',kept=False,reason='K_LIMIT',competing_id=None))
    assert len(chosen)==len(pool)
    for a,b in zip(chosen,pool):assert np.array_equal(a['xy'],b['xy']),'Legacy audit altered candidates'
    return pool,raw,filters

def propose(cur,path,tip,valid,width=2.,tiles=None,mode='FULL'):
    start=time.perf_counter();tiles=[] if tiles is None else tiles
    old,seq,_=old_propose(cur,path,tip,valid,width,tiles)
    pool=[dict(c,origin=c['origin'],source_version='AP2_RETAINED',event_id=f'OLD:{c["candidate_id"]}') for c in old]
    trace=[];pr=profile(cur,path,width)
    if pr is None:return pool,seq,trace,dict(ms=(time.perf_counter()-start)*1000,K=len(pool),reason='NO_SEED_UNRESOLVED')
    p,s,w=pr['xy'],pr['s'],pr['width'];sig=pr['peak']/pr['noise'];N=len(s)
    def add(c):
        near=next((q for q in pool if np.linalg.norm(np.asarray(c['xy'])-q['xy'])<max(3.,PARAM['merge_width']*w)),None)
        why='MERGED' if near else 'K_LIMIT' if len(pool)>=12 else 'KEPT'
        trace.append(dict(**c,stage='UNION',kept=why=='KEPT',filter_reason=why,competing_id=near['event_id'] if near else None))
        if why=='KEPT':pool.append(c)
    if not valid and mode in ['FULL','ENDPOINT_ONLY']:
        add(dict(origin='A_TRACKING_ENDPOINT_UNCONFIRMED',xy=p[-1].tolist(),raw_xy=p[-1].tolist(),s=float(s[-1]),normal_offset=0.,
            A_original_bitwise=False,event_id='TRACKING_END',source_version='AP3',strength=0.,reason='DP_TERMINAL_EVENT_NOT_OFFICIAL_CONFIRMATION',
            pre_support=float(np.median(sig[max(0,N-12):])),post_support=None,local_W=w))
    if mode in ['FULL','MULTISCALE_ONLY']:
        proposals=[]
        for scale in PARAM['window_width_factors']:
            win=max(3,int(np.clip(scale*w,PARAM['window_min'],PARAM['window_max'])/pr['step']))
            score=np.full(N,-np.inf);pre=np.zeros(N);post=np.zeros(N)
            for j in range(win,N-win):
                pre[j]=np.median(sig[j-win:j]);post[j]=np.median(sig[j+1:j+win+1])
                if pr['valid'][j-win:j+win+1].mean()>=.9 and pre[j]>PARAM['pre_snr']:score[j]=pre[j]-post[j]
            radius=max(2,int(PARAM['peak_radius_width']*w/pr['step']));used=set()
            for j in range(win,N-win):
                if score[j]<=PARAM['drop_snr'] or j in used:continue
                local=score[max(win,j-radius):min(N-win,j+radius+1)]
                if score[j]<np.max(local):continue
                lo=hi=j
                while lo>win and score[lo-1]>=score[j]*PARAM['plateau_fraction'] and j-lo<win:lo-=1
                while hi<N-win-1 and score[hi+1]>=score[j]*PARAM['plateau_fraction'] and hi-j<win:hi+=1
                used.update(range(lo,hi+1));refined=(lo+hi)/2
                xy=np.array([np.interp(refined,np.arange(N),p[:,k]) for k in [0,1]])
                jj=int(round(refined));offset=float(pr['offsets'][pr['best'][jj]]);xy+=offset*pr['n'][jj]
                c=dict(origin='MULTISCALE_SUPPORT_CHANGE',xy=xy.tolist(),raw_xy=p[j].tolist(),s=float(np.interp(refined,np.arange(N),s)),
                    raw_s=float(s[j]),normal_offset=offset,longitudinal_refinement=float((refined-j)*pr['step']),
                    A_original_bitwise=False,event_id=f'MULTI:{scale}:{j}',source_version='AP3',strength=float(score[j]),
                    pre_support=float(pre[jj]),post_support=float(post[jj]),local_R=float(sig[jj]),local_W=w,
                    reason='LOCAL_MAXIMUM_SUSTAINED_DROP_WITH_PLATEAU_CENTER',window_px=win*pr['step'],plateau=[lo,hi])
                proposals.append(c);trace.append(dict(**c,stage='RAW_EVENT',kept=True,filter_reason='EVENT_LOCAL_MAXIMUM',competing_id=None))
        for c in sorted(proposals,key=lambda c:(-c['strength'],c['s'],c['event_id'])):add(c)
    for k,c in enumerate(pool):c['candidate_id']=k
    assert len(pool)<=12
    return pool,seq,trace,dict(ms=(time.perf_counter()-start)*1000,K=len(pool),profile_samples=N,A_original_retained=valid,old_pool_preserved=True)
