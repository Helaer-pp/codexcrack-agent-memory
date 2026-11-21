"""Image-only stateless detector: no file/identity/label imports or inputs."""
import math,copy
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter1d

CONFIG=dict(version='simplified_v0_r01',temporal='OFF',material=100.,offsets=[3,6,10],gaussian_sigma=.6,
    valley_scale=6.,noise_multiple=2.,weak_min=2.,weak_max=8.,column_cap=12,peak_separation=3,adjacent_dy=3,
    gap_fraction=.02,gap_min=8,gap_max=24,direction_limit=.45,bridge_tolerance=3.,incoming_cap=4,paths_cap=6,
    ref_tile=64,ref_std=2.,ref_ncc=.8,ref_radius=4,ref_brightness=.5,ref_bonus=.35,ref_bias_max=20.,
    ambiguity=.04,stop_lookahead=24,stop_material=.65,stop_negative=.8,stop_ambiguity=.08,
    display_diff=40.,surface_cols=70,surface_rows=40)
FILTERS=['RAW','MEDIAN3','GAUSSIAN_LIGHT']
MODES=[f'{e}_{f}' for f in FILTERS for e in ['A_VALLEY_ONLY','B_DIFF_ONLY','C_FUSION']]

def validate_config(c):
    if not isinstance(c,dict) or set(c)!=set(CONFIG) or c!=CONFIG:raise ValueError('Strict frozen schema; identity/GT/unknown keys forbidden')

def geometry(C,P):
    h,w=C.shape;p1,p2=np.asarray(P,float);upper=math.ceil(p1[1]);lower=math.floor(p2[1]);xl=math.ceil(max(p1[0],p2[0]))
    if lower-upper<25 or not(0<=xl+50<w and 15<=upper<lower<h-15):raise ValueError('INPUT_INVALID P geometry')
    mid=round((p1[1]+p2[1])/2);line=gaussian_filter1d(C[mid-8:mid+9].astype(np.float32).mean(0),25);xr=w-25
    for x in range(xl+300,w-120):
        if line[x]<95 and line[x:x+95].mean()<95:xr=x;break
    return dict(xleft=xl,xr=xr,upper=upper,lower=lower,xa=max(0,xl-30),xb=min(w,xr+24),ya=max(0,upper-24),yb=min(h,lower+24))

def valley(I,c):
    I=I.astype(np.float32);V=np.zeros_like(I);bg=I.copy()
    for k in c['offsets']:
        z=(np.roll(I,k,0)+np.roll(I,-k,0))*.5;better=z-I>V;bg[better]=z[better];V=np.maximum(V,z-I)
    V[:10]=0;V[-10:]=0
    return V,bg,np.minimum(np.roll(I,10,0),np.roll(I,-10,0))

def ncc(a,b):
    a=a.astype(np.float64).ravel();b=b.astype(np.float64).ravel();a-=a.mean();b-=b.mean();den=np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.dot(a,b)/den) if den>1e-8 else 0.

def reference_evidence(R,C,rp,cp,g,cur,c):
    Y,X=np.mgrid[g['ya']:g['yb'],g['xa']:g['xb']].astype(np.float32)
    alpha=np.clip((Y-cp[0][1])/(cp[1][1]-cp[0][1]),0,1);delta=np.asarray(cp,np.float32)-np.asarray(rp,np.float32)
    mx=X-((1-alpha)*delta[0,0]+alpha*delta[1,0]);my=Y-((1-alpha)*delta[0,1]+alpha*delta[1,1])
    mask=(mx>=0)&(mx<R.shape[1]-1)&(my>=0)&(my<R.shape[0]-1)
    aligned=cv2.remap(R,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT).astype(np.float32);aligned[~mask]=np.nan
    q=np.zeros(cur.shape,np.float32);sx=np.zeros_like(q);sy=np.zeros_like(q);bias=np.zeros_like(q)
    records=[];same=bool(np.array_equal(R,C));radius=c['ref_radius'];safe=np.nan_to_num(aligned,nan=0)
    for x in range(g['xleft'],g['xr'],c['ref_tile']):
        xe=min(g['xr'],x+c['ref_tile']);sides=[]
        for y0 in [g['upper']+14,g['lower']-30]:
            a=y0-g['ya'];b=x-g['xa'];hh=16;ww=xe-x
            curwin=cur[a:a+hh,b:b+ww];base=safe[a:a+hh,b:b+ww]
            available=(curwin.size>=64 and curwin.std()>=c['ref_std'] and base.std()>=c['ref_std'] and np.mean((curwin>c['material'])&(base>c['material']))>=c['ref_brightness'] and mask[a-radius:a+hh+radius,b-radius:b+ww+radius].all() and not same)
            initial=ncc(curwin,base);dx=dy=0;best=initial
            if available:
                search=safe[a-radius:a+hh+radius,b-radius:b+ww+radius]
                corr=cv2.matchTemplate(search.astype(np.float32),curwin.astype(np.float32),cv2.TM_CCOEFF_NORMED)
                _,score,_,loc=cv2.minMaxLoc(corr)
                if score>initial+.02:best=float(score);dx=loc[0]-radius;dy=loc[1]-radius
            offset=float(np.median(safe[a+dy:a+dy+hh,b+dx:b+dx+ww]-curwin))
            trusted=bool(available and best>=c['ref_ncc'] and abs(offset)<=c['ref_bias_max'])
            sides.append(dict(bounds=[x,y0,xe,y0+16],ncc_initial=initial,ncc_corrected=best,std_current=float(curwin.std()),std_reference=float(base.std()),shift=[dx,dy],bias=offset,trusted=trusted,reason='SAME_IMAGE_NO_INCREMENT' if same else 'TRUSTED_TEXTURE_PROXY' if trusted else 'UNTRUSTED_TEXTURE_OR_MOTION'))
        trusted=all(s['trusted'] for s in sides)
        if trusted:
            sl=np.s_[:,x-g['xa']:xe-g['xa']];fraction=np.clip((Y[sl]-(g['upper']+22))/max(1,g['lower']-g['upper']-44),0,1)
            sx[sl]=(1-fraction)*sides[0]['shift'][0]+fraction*sides[1]['shift'][0];sy[sl]=(1-fraction)*sides[0]['shift'][1]+fraction*sides[1]['shift'][1]
            bias[sl]=(1-fraction)*sides[0]['bias']+fraction*sides[1]['bias'];q[sl]=min(s['ncc_corrected'] for s in sides)
        records.append(dict(x0=x,x1=xe,trusted=trusted,sides=sides))
    lmx=mx+sx;lmy=my+sy;localmask=(lmx>=0)&(lmx<R.shape[1]-1)&(lmy>=0)&(lmy<R.shape[0]-1)
    local=cv2.remap(R,lmx,lmy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT).astype(np.float32);local[~localmask]=np.nan;q[~localmask]=0
    signed=aligned-cur.astype(np.float32);corrected=local-cur.astype(np.float32)-bias
    return dict(aligned_reference=aligned,signed_raw=signed,positive=np.maximum(signed,0),absolute=np.abs(signed),valid_warp_mask=mask,local_warp_mask=localmask,ref_quality_map=q,aligned_local=local,signed_corrected=corrected,local_bias=bias,map_x=mx,map_y=my,local_map_x=lmx,local_map_y=lmy),records,('SAME_IMAGE_NO_INCREMENT' if same else 'LOCAL_TEXTURE_PROXY_TRUSTED' if q.any() else 'NOT_TRUSTED_FOR_INFERENCE')

def notch_hypothesis(I,g,c):
    left=max(0,g['xleft']-g['xa']);width=min(I.shape[1]-left,max(80,min(400,round(.5*(g['lower']-g['upper'])))))
    slab=(I[:,left:left+width]<80).astype(np.uint8);n,l,stats,cent=cv2.connectedComponentsWithStats(slab,8)
    options=[];cy=(g['upper']+g['lower'])/2-g['ya'];scale=max(12,(g['lower']-g['upper'])*.23)
    for k in range(1,n):
        x,y,w,h,area=stats[k]
        if x>2 or w<8 or area<20:continue
        score=area*math.exp(-.5*((cent[k,1]-cy)/scale)**2);yy,xx=np.where(l==k);right=xx.max();endy=float(np.median(yy[xx>=right-2]))
        options.append((score,[int(right+g['xleft']),float(endy+g['ya'])]))
    return dict(status='NOTCH_HYPOTHESIS' if options else 'NOT_EVALUABLE',point=max(options,key=lambda v:v[0])[1] if options else None,physical_identity_confirmed=False)

def evidence(current_uint8,reference_uint8,P_ref,P_cur,config):
    validate_config(config);C=current_uint8;R=reference_uint8
    if C.dtype!=np.uint8 or R.dtype!=np.uint8 or C.ndim!=2 or C.shape!=R.shape:raise ValueError('INPUT_INVALID image type/shape')
    pts=np.asarray([P_ref,P_cur],float)
    if pts.shape!=(2,2,2) or not np.isfinite(pts).all():raise ValueError('INPUT_INVALID P')
    if (pts[:,:,0]<0).any() or (pts[:,:,0]>=C.shape[1]).any() or (pts[:,:,1]<0).any() or (pts[:,:,1]>=C.shape[0]).any() or (pts[:,0,1]>=pts[:,1,1]).any():raise ValueError('INPUT_INVALID P bounds/order')
    g=geometry(C,P_cur);raw=C[g['ya']:g['yb'],g['xa']:g['xb']].copy()
    images=[raw,cv2.medianBlur(raw,3),cv2.GaussianBlur(raw.astype(np.float32),(3,3),config['gaussian_sigma'])];vals=[valley(i,config) for i in images]
    mask=np.zeros(raw.shape,bool);mask[g['upper']-g['ya']+2:g['lower']-g['ya']-1,g['xleft']-g['xa']:g['xr']-g['xa']]=True
    material=mask&(vals[0][2]>config['material']);resid=raw.astype(np.float32)-images[1];z=resid[material]
    noise=max(1.,float(np.median(np.abs(z-np.median(z)))*1.4826)) if z.size else 1.;threshold=float(np.clip(config['noise_multiple']*noise,config['weak_min'],config['weak_max']))
    d,records,status=reference_evidence(R,C,P_ref,P_cur,g,raw,config);d['valid_material_mask']=material
    return dict(gray=images,valley=[v[0] for v in vals],background=vals[0][1],material=material,roi=g,noise=noise,threshold=threshold,diff=d,reference_windows=records,reference_status=status,notch=notch_hypothesis(raw,g,config))

def peak_nodes(E,eligible,raw,V,bg,noise,c):
    peaks=eligible&(E>=np.roll(E,1,0))&(E>np.roll(E,-1,0));columns=[];total=0;dropped=0;features=[]
    for x in range(E.shape[1]):
        ys=np.flatnonzero(peaks[:,x]);total+=len(ys);chosen=[]
        for y in sorted(ys.tolist(),key=lambda y:(-float(E[y,x]),y)):
            if any(abs(y-t)<c['peak_separation'] for t in chosen):continue
            if len(chosen)<c['column_cap']:chosen.append(y)
            else:dropped+=1
        chosen.sort();columns.append(chosen)
        for y in chosen:
            depth=float(V[y,x]);half=float(raw[y,x])+depth*.5;a=y;b=y
            while a>0 and y-a<16 and raw[a-1,x]<half:a-=1
            while b+1<raw.shape[0] and b-y<16 and raw[b+1,x]<half:b+=1
            features.append([x,y,float(raw[y,x]),float(bg[y,x]),depth,b-a+1,noise,float(E[y,x]),1])
    return columns,np.asarray(features,np.float32).reshape(-1,9),dict(raw_peak_count=total,retained_count=len(features),capacity_dropped=dropped)

def fragments(columns,E,c):
    out=[];previous={}
    for x,ys in enumerate(columns):
        matches=[]
        for y in ys:
            for py,idx in previous.items():
                if abs(y-py)<=c['adjacent_dy']:matches.append((abs(y-py),-float(E[y,x]),y,py,idx))
        usedy=set();usedprev=set();now={}
        for _,__,y,py,idx in sorted(matches):
            if y in usedy or idx in usedprev:continue
            out[idx].append([x,y]);now[y]=idx;usedy.add(y);usedprev.add(idx)
        for y in ys:
            if y not in now:now[y]=len(out);out.append([[x,y]])
        previous=now
    return out

def slope(seg,end=True):
    a=seg[-6:] if end else seg[:6]
    return max(-.45,min(.45,(a[-1][1]-a[0][1])/max(1,a[-1][0]-a[0][0])))

def graph_paths(segs,E,g,notch,c):
    gap=int(np.clip(round(c['gap_fraction']*(g['xr']-g['xleft'])),c['gap_min'],c['gap_max']))
    order=sorted(range(len(segs)),key=lambda k:(segs[k][-1][0],segs[k][-1][1],k));ends={};dp={};edges=[];truncated=0
    for k in order:
        s=segs[k];x,y=s[0];options=[]
        if len(s)>=2:
            for xx in range(max(0,x-gap-1),x):
                for j in ends.get(xx,[]):
                    t=segs[j];dx=x-t[-1][0];dy=y-t[-1][1];a=slope(t);b=slope(s,False)
                    if len(t)<2 or abs(dy)>c['bridge_tolerance']+c['direction_limit']*dx or abs(dy-a*dx)>c['bridge_tolerance']+.2*dx or abs(a-b)>.6:continue
                    penalty=.12*(dx-1)+.25*abs(a-b);options.append((dp[j]['utility']-penalty,j,dx-1,penalty))
        options.sort(key=lambda a:(-a[0],a[1]));truncated+=max(0,len(options)-c['incoming_cap']);options=options[:c['incoming_cap']]
        for _,j,n,p in options:edges.append([j,k,n,p])
        utility=sum(min(2.,float(E[p[1],p[0]])) for p in s);best=options[0] if options and options[0][0]>0 else None
        dp[k]=dict(prev=best[1] if best else None,utility=utility+(best[0] if best else 0),count=len(s)+(dp[best[1]]['count'] if best else 0),gaps=best[2]+dp[best[1]]['gaps'] if best else 0)
        ends.setdefault(s[-1][0],[]).append(k)
    ranked=[]
    for k in order:
        state=dp[k]
        if state['count']<4:continue
        chain=[];j=k
        while j is not None:chain.append(j);j=dp[j]['prev']
        chain.reverse();first=segs[chain[0]][0];last=segs[k][-1];mean=state['utility']/state['count'];gapfrac=state['gaps']/max(1,last[0]-first[0]+1)
        origin=notch['point'];dist=math.hypot(first[0]+g['xa']-origin[0],first[1]+g['ya']-origin[1]) if origin else None
        prior=.35*math.exp(-dist/max(30,.25*(g['lower']-g['upper']))) if dist is not None else 0.
        score=mean+.3*(1-math.exp(-state['count']/40))-.6*gapfrac+prior
        ranked.append((score,k,chain,dict(mean_evidence=mean,observed=state['count'],gap_pixels=state['gaps'],origin_distance=dist,origin_bonus=prior,gap_fraction=gapfrac)))
    ranked.sort(key=lambda a:(-a[0],a[1]));selected=[]
    for item in ranked:
        chain=item[2]
        if any(set(chain).issubset(p[2]) or set(p[2]).issubset(chain) for p in selected):continue
        selected.append(item)
        if len(selected)>=c['paths_cap']:break
    paths=[]
    for score,k,chain,components in selected:
        trace=[];bridges=[]
        for j in chain:
            s=segs[j]
            if trace:
                px,py=trace[-1][:2];tx,ty=s[0];dx=tx-px
                if dx>1:
                    bridges.append(dict(start=[px+g['xa'],py+g['ya']],end=[tx+g['xa'],ty+g['ya']],missing=dx-1,status='INFERRED_GAP',physical_identity='NOT_EVALUABLE'))
                    trace.extend([[xx,py+(ty-py)*(xx-px)/dx,0] for xx in range(px+1,tx)])
            trace.extend([[p[0],p[1],1] for p in s])
        paths.append(dict(id=k,score=score,components=components,fragment_ids=chain,trace_local=trace,bridges=bridges))
    return paths,np.asarray(edges,np.float32).reshape(-1,4),dict(gap_bound=gap,incoming_truncated=truncated,fragments=len(segs),graph_edges=len(edges),eligible_routes=len(ranked))

def stops(path,a,c):
    t=path['trace_local'];obs=[i for i,p in enumerate(t) if p[2]];candidates=[];V=a['valley'][0];valid=a['material'];g=a['roi'];weak=a['threshold']
    if not obs:return [],None,'TIP_UNCERTAIN'
    indices=[i for i in obs if i==obs[-1] or (i+1<len(t) and not t[i+1][2])]
    for pos in range(12,len(obs)-12,4):
        before=np.mean([V[int(t[i][1]),int(t[i][0])] for i in obs[pos-12:pos]]);after=np.mean([V[int(t[i][1]),int(t[i][0])] for i in obs[pos:pos+12]])
        if before>2*weak and after<.5*before:indices.append(obs[pos-1])
    for i in sorted(set(indices)):
        x,y=map(int,t[i][:2]);recent=[t[j] for j in obs if max(0,i-12)<=j<=i]
        direction=slope(recent);neg=[];measurable=[];supports=[]
        for dx in range(1,c['stop_lookahead']+1):
            xx=x+dx;yy=round(y+direction*dx)
            if xx>=g['xr']-g['xa'] or yy<g['upper']-g['ya']+3 or yy>=g['lower']-g['ya']-3:break
            sl=np.s_[yy-2:yy+3,xx];ok=valid[sl];measurable.append(bool(ok.mean()>=.6));val=float(V[sl][ok].max()) if ok.any() else 0.;supports.append(val);neg.append(bool(ok.mean()>=.6 and val<weak))
        mat=sum(measurable)/c['stop_lookahead'];negative=sum(neg)/max(1,sum(measurable));pre=float(np.mean([V[int(p[1]),int(p[0])] for p in recent]));post=float(np.mean(supports)) if supports else pre
        decay=max(0.,min(1.,(pre-post)/max(pre,weak)));score=negative+decay+.2*min(len(recent)/12,1)
        eligible=mat>=c['stop_material'] and negative>=c['stop_negative'] and pre>=weak
        dr=a['diff']['signed_corrected'][y,x];q=a['diff']['ref_quality_map'][y,x]
        candidates.append(dict(trace_index=i,point=[x+g['xa'],y+g['ya']],score=score,eligible=eligible,after_material_fraction=mat,after_observable_negative_fraction=negative,before_current_valley=pre,after_current_valley=post,trusted_reference_support=float(q*max(0,dr)) if np.isfinite(dr) else None,reason='OBSERVABLE_SUPPORT_DECAY' if eligible else 'OCCLUSION_OR_SUPPORT_CONTINUATION_OR_ROI'))
    vs=sorted([s for s in candidates if s['eligible']],key=lambda s:(-s['score'],s['point'][0]))
    if not vs:return candidates,None,'ROI_LIMITED' if t[obs[-1]][0]>=g['xr']-g['xa']-2 else 'TIP_UNCERTAIN'
    best=vs[0]
    if any(abs(s['score']-best['score'])<=c['stop_ambiguity'] and np.linalg.norm(np.subtract(s['point'],best['point']))>10 for s in vs[1:]):return candidates,best,'TIP_UNCERTAIN'
    return candidates,best,'PROVISIONAL_TIP'

def run_mode(a,mode,c):
    fi=FILTERS.index(next(f for f in FILTERS if mode.endswith('_'+f)));V=a['valley'][0] if fi==0 else .5*a['valley'][0]+.5*a['valley'][fi]
    local=np.nan_to_num(a['diff']['aligned_local'],nan=0).astype(np.float32)
    if fi==1:local=cv2.medianBlur(local,3)
    if fi==2:local=cv2.GaussianBlur(local,(3,3),c['gaussian_sigma'])
    D=local-a['gray'][fi].astype(np.float32)-a['diff']['local_bias']
    if fi:D=.5*np.nan_to_num(a['diff']['signed_corrected'],nan=0)+.5*D
    q=a['diff']['ref_quality_map'].copy()
    if fi:q*=cv2.erode(a['diff']['local_warp_mask'].astype(np.uint8),np.ones((3,3),np.uint8))
    scale=3*a['noise']+c['valley_scale'];vn=np.clip(V/scale,0,4);dn=np.clip(np.maximum(D,0)/scale,0,4);kind=mode[0]
    E=vn if kind=='A' else q*dn if kind=='B' else vn+c['ref_bonus']*q*dn
    eligible=a['material']&((V>=a['threshold']) if kind!='B' else ((q>0)&(D>=a['threshold'])))
    columns,nodes,counts=peak_nodes(E,eligible,a['gray'][0],a['valley'][0],a['background'],a['noise'],c);segs=fragments(columns,E,c);paths,edges,gcounts=graph_paths(segs,E,a['roi'],a['notch'],c)
    for p in paths:
        candidates,best,status=stops(p,a,c);p['stop_candidates']=candidates;p['candidate_tip']=best['point'] if best else None;p['tip_status']=status
        p['last_observed_pixel']=[p['trace_local'][-1][0]+a['roi']['xa'],p['trace_local'][-1][1]+a['roi']['ya']]
        local_trace=p.pop('trace_local')
        p['observed_trace']=[[x+a['roi']['xa'],y+a['roi']['ya'],int(hit)] for x,y,hit in local_trace]
        p['pixel_states']=[['INFERRED_GAP'] if not hit else
            (['OBSERVED_CURRENT'] if V[int(y),int(x)]>=a['threshold'] else [])+
            (['OBSERVED_INCREMENT'] if kind!='A' and q[int(y),int(x)]>0 and D[int(y),int(x)]>=a['threshold'] else [])
            for x,y,hit in local_trace]
        p['gap_reasons']=[dict(x=x+a['roi']['xa'],y=y+a['roi']['ya'],reason='INVALID_MATERIAL' if not a['material'][int(round(y)),int(x)] else 'UNREGISTERED_REF' if kind=='B' and q[int(round(y)),int(x)]==0 else 'NO_SUPPORT') for x,y,hit in local_trace if not hit]
        p['selected_trace']=p['observed_trace'][:best['trace_index']+1] if best and status=='PROVISIONAL_TIP' else p['observed_trace']
    ambiguous=len(paths)>1 and paths[0]['score']-paths[1]['score']<=c['ambiguity'];p=paths[0] if paths else None
    state='REF_UNAVAILABLE' if kind=='B' and not q.any() else 'NO_EVIDENCE' if not p else 'PATH_AMBIGUOUS' if ambiguous else p['tip_status']
    flat=[[j,x+a['roi']['xa'],y+a['roi']['ya']] for j,s in enumerate(segs) for x,y in s]
    result=dict(mode=mode,output_state=state,path_status='AMBIGUOUS_PATHS' if ambiguous else 'PROVISIONAL_PATH' if p else 'NO_EVIDENCE',tip=p['candidate_tip'] if p and state=='PROVISIONAL_TIP' else None,candidate_tip=p['candidate_tip'] if p else None,last_observed_pixel=p['last_observed_pixel'] if p else None,tip_status=p['tip_status'] if p else state,tip_interval=[s['point'] for s in p['stop_candidates']] if p else [],chosen_path_id=p['id'] if p else None,paths=paths,counts={**counts,**gcounts},reference_use='DIFF_ONLY' if kind=='B' else 'OFF' if kind=='A' else 'FUSION' if q.any() else 'FALLBACK_TO_VALLEY',physical_main_crack_identity='UNVERIFIED',direction='+x ONLY',gt_accessed=False)
    return result,dict(nodes=nodes,segments=np.asarray(flat,np.float32).reshape(-1,3),edges=edges)

def detect(*,current_uint8,reference_uint8,P_ref,P_cur,config):
    a=evidence(current_uint8,reference_uint8,P_ref,P_cur,config);results=[];graphs={}
    for mode in MODES:
        if mode.startswith('C_FUSION') and not a['diff']['ref_quality_map'].any():
            source=mode.replace('C_FUSION','A_VALLEY_ONLY');r=copy.deepcopy(next(v for v in results if v['mode']==source));r['mode']=mode;r['reference_use']='FALLBACK_TO_VALLEY';graph=graphs[source]
        else:r,graph=run_mode(a,mode,config)
        results.append(r);graphs[mode]=graph
    return a,results,graphs
