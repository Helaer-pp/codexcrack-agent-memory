import numpy as np
from research.notch_identity_v3.detector import px,features,merger,r02

def filter_static(eligible,trials):
    if any(trials[i][0].get('positive_branch') for i in eligible):
        return [i for i in eligible if not trials[i][0].get('static_branch')]
    return eligible

def predict(prep,bonus,follow=r02.follow):
    if prep is None:
        return dict(status='NO_NOTCH_BODY',root=None,tip=None,points=[],diagnostics=dict(candidates=[],pairs=[]))
    _,(left,top),starts,signal,response,scale,front=prep
    trials=[]
    diagnostics=[]
    eligible=[]
    for i,start in enumerate(starts):
        result=follow(signal,response,bonus,start)
        pts=np.asarray(result['points'],dtype=int).reshape(-1,2)
        trials.append((result,pts))
        tip=result['tip']
        diag=dict(start=list(start),tip=tip,status=result['status'])
        diagnostics.append(diag)
        if tip and tip[0]>=front+px(scale,.03):
            whole=features(pts,start,signal,response,scale)
            length=(tip[0]-front)/scale
            diag['whole']=whole
            # Integrated support discounts tiny fragments with few independent observations.
            diag['rank']=float((.5+whole['density']+.25*whole['signal'])*np.log1p(length/.03))
            diag['rank']+=result.get('rank_bonus',0.)
            eligible.append(i)
    kept=filter_static(eligible,trials)
    for i in set(eligible)-set(kept):diagnostics[i]['static_veto']=True
    eligible=kept
    pairs=[]
    choice=None
    if eligible:
        top_tier=max(trials[i][0].get('tier',0) for i in eligible)
        eligible=[i for i in eligible if trials[i][0].get('tier',0)==top_tier]
        leader=max(eligible,key=lambda i:diagnostics[i]['rank'])
        siblings={leader}
        for ai,i in enumerate(eligible):
            for j in eligible[ai+1:]:
                x=merger(trials[i][1],trials[j][1],scale)
                if x is not None:
                    pairs.append([i,j,x])
                    if leader in (i,j):
                        siblings.update([i,j])
        # Use the same comparison span for both members; near-duplicate seeds merging
        # immediately are evaluated over the first quarter-scale of measured support.
        for i in siblings:
            start=starts[i]
            stop=start[0]+px(scale,.25)+1
            distinct=[x for a,b,x in pairs if i in (a,b) and a in siblings and b in siblings
                      and x>=start[0]+px(scale,.025)]
            if distinct:
                stop=min(stop,max(distinct))
            diagnostics[i]['near']=features(trials[i][1],start,signal,response,scale,stop)
            diagnostics[i]['near_end']=stop-1
        choice=max(sorted(siblings),key=lambda i:(diagnostics[i]['near']['score']+trials[i][0].get('rank_bonus',0.),diagnostics[i]['rank']))
    if choice is None:
        result=dict(status='NO_ELIGIBLE_ROOT_TRACE',tip=None,points=[])
        root=starts[0]
    else:
        result=dict(trials[choice][0])
        root=starts[choice]
    def xy(p):
        return [int(p[0]+left),int(p[1]+top)] if p is not None else None
    for d in diagnostics:
        d['start']=xy(d['start'])
        d['tip']=xy(d['tip'])
        if 'near_end' in d:
            d['near_end']+=left
    return dict(status=result['status'],root=xy(root),tip=xy(result['tip']),points=[xy(p) for p in result['points']],
                diagnostics=dict(terminal=result.get('terminal'),selected=choice,candidates=diagnostics,pairs=[[a,b,x+left] for a,b,x in pairs]))
