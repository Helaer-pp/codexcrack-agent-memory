"""Scale-aware notch identity competition. The frozen r02 trace and stop are Stage 1 controls."""
import cv2
import numpy as np
from research.raw_notch_trace_v2b import detector as r02


def px(scale, fraction):
    return max(1, round(scale * fraction))


def locate_root(raw, hint, scale):
    x, y = np.rint(hint).astype(int)
    h, w = raw.shape
    radius = px(scale, .23)
    left, top = max(0, x-2*radius), max(0, y-radius)
    patch = raw[top:min(h,y+radius+1), left:min(w,x+radius+1)]
    k = 2*px(scale,.007)+1
    if min(patch.shape, default=0) < k:
        return None
    opened = cv2.morphologyEx((patch < 57).astype('uint8'), cv2.MORPH_OPEN,
                              cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k,k)))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(opened, 8)
    candidates = []
    for i in range(1,count):
        bx, by, width, height, area = stats[i]
        if bx > px(scale,.007) or width < px(scale,.035) or height < k or area < .0006*scale**2:
            continue
        end = int(bx+width-1)
        old_y = int(np.median(np.flatnonzero(labels[:, end]==i)))
        candidates.append((np.hypot(left+end-x,top+old_y-y), i, end, old_y))
    if not candidates:
        return None
    _, component, end, old_y = min(candidates)
    ys,xs = np.where(labels==component)
    frontier = np.full(labels.shape[0],-1)
    np.maximum.at(frontier,ys,xs)
    nose = np.flatnonzero(frontier >= max(0,end-px(scale,.04)))
    mid = int(np.median(nose))
    band = np.flatnonzero((frontier >= max(0,end-px(scale,.13))) &
                          (np.abs(np.arange(len(frontier))-mid)<=px(scale,.15)))
    # Two balanced halves, extremes and forward-most legacy tip. Bounded number of seeds.
    picks = [mid, old_y]
    for half in (band[band<=mid], band[band>=mid]):
        if len(half):
            picks.extend(half[np.rint(np.linspace(0,len(half)-1,7)).astype(int)])
    starts = [(left+int(frontier[v]), top+int(v)) for v in picks if frontier[v]>=0]
    return list(dict.fromkeys(starts)), (left+end,top+old_y)


def prepare(raw,hint,scale):
    found = locate_root(raw,hint,scale)
    if found is None:
        return None
    starts, front = found
    # Same vertical crop as r02 for the native Stage 1 evidence.
    radius = max(35,round(.55*scale))
    top = max(0,front[1]-radius)
    bottom = min(raw.shape[0],front[1]+radius+1)
    left = max(0,min(x for x,y in starts)-px(scale,.035))
    sl = np.s_[top:bottom,left:]
    signal,response = r02.valley_image(raw[sl])
    return sl, (left,top), [(x-left,y-top) for x,y in starts],signal,response,scale,front[0]-left


def features(pts, start, signal, response, scale, stop=None):
    if stop is not None:
        pts = pts[pts[:,0]<stop]
    if not len(pts):
        return dict(score=0.,density=0.,signal=0.,depth=0.,attachment=0.,roughness=0.)
    x,y=pts.T
    observed=signal[y,x]
    depth=response[y,x]
    density=np.count_nonzero(observed>=1.)/max(1,x[-1]-start[0])
    signal_score=float(np.median(np.minimum(4.,observed)))/4.
    depth_score=float(np.median(np.log1p(depth)))/np.log(256.)
    first=x<=start[0]+px(scale,.025)
    attachment=np.sum(np.minimum(observed[first],4.))/(4.*min(px(scale,.025),max(1,x[-1]-start[0])))
    rough=float(np.mean(np.maximum(0,np.abs(np.diff(y))/np.diff(x)-1))) if len(x)>1 else 0.
    score=float(density+signal_score+depth_score+attachment-.5*rough)
    return dict(score=score,density=float(density),signal=signal_score,depth=float(depth_score),
                attachment=float(attachment),roughness=rough)


def merger(a,b,scale):
    span=px(scale,.025)
    tolerance=px(scale,.007)
    tip_near=np.linalg.norm(a[-1]-b[-1]) <= .03*scale
    xs,ia,ib=np.intersect1d(a[:,0],b[:,0],assume_unique=True,return_indices=True)
    if not len(xs):
        return None
    close=np.abs(a[ia,1]-b[ib,1])<=tolerance
    breaks=np.flatnonzero(~close | (np.diff(xs,prepend=xs[0])>px(scale,.012)))
    begin=(int(breaks[-1])+1) if len(breaks) else 0
    if begin<len(xs) and len(xs)-begin>=span and min(a[-1,0],b[-1,0])-xs[-1]<=tolerance:
        return int(xs[begin])
    if tip_near:
        return int(min(a[-1,0],b[-1,0]))
    return None


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
            eligible.append(i)
    pairs=[]
    choice=None
    if eligible:
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
        choice=max(sorted(siblings),key=lambda i:(diagnostics[i]['near']['score'],diagnostics[i]['rank']))
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


