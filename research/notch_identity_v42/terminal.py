"""V3.6 anchored grayscale geometry with narrow signed-increment corroboration."""
import cv2
import numpy as np
from scipy.ndimage import median_filter
from research.notch_identity_v31.detector import px
from research.notch_identity_v31.terminal import trace_windowed
from research.notch_identity_v36 import terminal as baseline
from research.notch_identity_v41 import evidence
from research.notch_identity_v41.terminal import fading_endpoint,resolved_trunk,resolved_end,weak_extension,static_suffix
from . import backbone
from research.notch_identity_v40.tracking import roots as ridge_roots

STAGES=('no_break','v4_2')

def prepare(raw,hint,scale,stage='v4_2'):
    if stage not in STAGES:raise ValueError(stage)
    p=baseline.prepare(raw,hint,scale)
    return (*p[:-3],stage,*p[-2:]) if p is not None else None

def anchored(p):
    front=p[6];s=p[5]
    seeds=list(dict.fromkeys((max(x,front),y) for x,y in p[2] if x<=front+px(s,.10)))
    return (*p[:2],seeds,*p[3:-3],'v3_6',*p[-2:])

def incremental_seeds(ev,p):
    # Physically crop the array passed to the seed search; no candidate sees the rear wall.
    front=p[6];mid=int(np.median(np.array(p[2])[:,1]))-ev['top']
    local=ridge_roots(ev['signal'][:,front:],0,mid,p[5])
    return [(front+x,y+ev['top']) for x,y in local]

def difference_holes(ev,p):
    s=p[5];rad=px(s,.004)
    mask=(ev['signal']>=1.1).astype('uint8')
    kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*rad+1,2*rad+1))
    front=p[6];near=mask[:,front+1:front+px(s,.02)+1]
    lip=np.flatnonzero(near.any(axis=1))
    if len(lip):
        mask[lip.min():lip.max()+1,front:front+2]=1
    mask=cv2.dilate(mask,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*rad+1,2*rad+1)))
    contours,tree=cv2.findContours(cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    return [c for c,t in zip(contours,tree[0] if tree is not None else []) if t[3]>=0 and cv2.contourArea(c)>.00045*s*s]

def certified_path(p,ev,seed,stage,holes):
    s=p[5];front=p[6];top=ev['top'];x,y=seed
    sig=ev['signal'];ys=y-top
    # DP works on the joint ridge; the current-frame floor is checked again at publication.
    strength=ev['joint']
    track,_,_,_=trace_windowed(strength,ev['zero'],x,ys,px(s,.065),px(s,.05),px(s,.016),
                               px(s,.014),px(s,.32),px(s,.045),px(s,.045),.85)
    if len(track)<px(s,.04):return None,'SHORT_INCREMENT'
    arr=np.vstack(([x,ys,strength[ys,x]],track));xx,yy=arr[:,:2].astype(int).T
    energy=sig[yy,xx];raw=ev['depth'][yy,xx];orient=ev['orientation'][yy,xx]
    near=xx<=x+px(s,.045)
    strong=(energy[near]>=1.35).mean()>=.78 and np.median(orient[near])>.18
    # Trace back to the mouth in the permitted band: a detached line cannot claim a neck.
    if x>front+px(s,.007):
        w=px(s,.009);row=ys
        for col in range(x-1,front,-1):
            rows=np.arange(max(0,row-1),min(len(sig),row+2))
            row=int(rows[np.argmax(sig[rows,col])])
            if sig[row,col]<.85:
                if col>front+px(s,.006):strong=False
                break
    start=max(front+1,x-px(s,.10));row=ys;prefix=[]
    for col in range(x-1,start-1,-1):
        rows=np.arange(max(0,row-1),min(len(sig),row+2))
        row=int(rows[np.argmax(ev['depth'][rows,col])])
        if ev['delta'][row,col]<max(2.5*p[8],.016*p[-1]) or ev['depth'][row,col]<ev['raw_floor']:break
        prefix.append((col,row+top))
    if x>front+1 and (not prefix or prefix[-1][0]>front+1):strong=False
    rescued=False
    if not strong and stage=='v4_2':
        body=(xx>=x+px(s,.012))&(xx<=x+px(s,.14))
        if body.sum()>=px(s,.032):
            delta=ev['delta'][yy[body],xx[body]]
            rescued=(np.median(energy[body])>=1.5 and (delta>ev['raw_floor']).mean()>=.75
                     and np.mean(ev['clear'][yy[body],xx[body]]>.5)>=.7)
    if not strong and not rescued:return None,'NO_INCREMENT_SUPPORT'
    obs=energy>=.85
    if len(obs):
        obs&=raw>=ev['raw_floor']
        # First sustained disappearance ends a distal branch, even if speckles reappear.
        gap=px(s,.018)
        lack=np.convolve((~obs).astype(float),np.ones(gap),'valid')
        cuts=np.flatnonzero((lack>=gap-.01)&(xx[:len(lack)]>x+px(s,.08)))
        if len(cuts):obs[cuts[0]:]=False
    indices=np.flatnonzero(obs)
    if len(indices)<px(s,.04):return None,'NO_SUPPORTED_END'
    path=np.c_[xx[indices],yy[indices]+top]
    if prefix:path=np.vstack((prefix[::-1],path))
    end=tuple(map(float,(path[-1,0],path[-1,1]-top)))
    for h in holes:
        bx,by,bw,bh=cv2.boundingRect(h)
        tail=path[(path[:,0]>=bx+bw-px(s,.025))&(path[:,0]<=bx+bw+px(s,.025))]
        if end[0]<=bx+bw+px(s,.10) and len(tail) and np.any((tail[:,1]-top>=by-px(s,.017))&(tail[:,1]-top<=by+bh+px(s,.017))):
            return None,'INCREMENT_CLOSED_RIM'
    if np.mean(ev['clear'][yy[indices],xx[indices]]<.25)>.85:return None,'FIXED_CONTOUR'
    return path,'BODY_INCREMENT' if rescued else 'CERTIFIED'

def parallel_recovery(path,p,ev):
    """Replace a switched segment only when both lip ridges are independently observed."""
    if len(path)<4:return path
    x,y=path.T;s=p[5];rad=px(s,.005);signal=ev['signal'];top=ev['top']
    for j in np.flatnonzero((np.diff(x)>=px(s,.012))&(x[:-1]<p[6]+px(s,.30))):
        i=np.searchsorted(x,x[j]-px(s,.035))
        incoming=np.clip((y[j]-y[i])/max(1,x[j]-x[i]),-.5,.5)
        k=j+1;disp=y[k]-y[j]-incoming*(x[k]-x[j])
        if abs(disp)<max(3,.017*s):continue
        cols=np.arange(max(x[0],x[j]-px(s,.030)),x[j]+1)
        if len(cols)<px(s,.018):continue
        centers=np.interp(cols,x,y)
        def peak(rows,cols):
            yy=np.clip(np.rint(rows).astype(int)+np.arange(-rad,rad+1)[:,None],top,top+len(signal)-1)
            weight=ev['joint'][yy-top,cols]
            best=weight.argmax(axis=0)
            return yy[best,np.arange(len(cols))],weight[best,np.arange(len(cols))]
        _,first=peak(centers,cols);_,other=peak(centers+disp,cols)
        if np.mean((first>=1.35)&(other>=1.35))<.70:continue
        # After the interruption search only the continuation of the incoming tangent.
        ids=np.arange(k,len(x));xx=x[ids];cy=y[j]+incoming*(xx-x[j])
        close=np.flatnonzero((abs(y[ids]-cy)<=rad+1)&(xx>x[k]+px(s,.025)))
        if not len(close):continue
        end=ids[close[0]]
        if x[end]-x[j]>.22*s:continue
        cols=np.arange(x[j]+1,x[end])
        yy,good=peak(y[j]+incoming*(cols-x[j]),cols)
        if (good>=1.35).sum()<px(s,.018):continue
        valid=good>=1.1
        return np.vstack((path[:j+1],np.c_[cols[valid],yy[valid]],path[end:]))
    return path

def predict(p,bonus=None,fixed=None):
    if fixed is None:return baseline.predict(p,None)
    if p is None:
        result=baseline.predict(None,None)
        result['diagnostics']['dual']={'decision':'NO_NOTCH','events':[]}
        return result
    stage=p[-3];base=anchored(p);result=backbone.predict(base,bonus,fixed)
    ev,coarse,reg=evidence.make(p,fixed)
    org=np.asarray(p[1]);s=p[5]
    audit=dict(decision='ANCHORED_V36',registration=reg,events=[],front=int(p[6]+org[0]),base_tip=result['tip'],rejections={},trials=[],stop='BASE_TERMINAL')
    result['diagnostics']['dual']=audit
    if ev is None:
        if result['tip'] and result['tip'][0]-org[0]-p[6]<px(s,.048) and all(x!=p[6] for x,y in p[2]):
            audit.update(stop='UNCONFIRMED_PROJECTED_FRAGMENT')
            return dict(status='NO_ELIGIBLE_ROOT_TRACE',root=result['root'],tip=None,points=[],diagnostics=dict(dual=audit,candidates=[],pairs=[],coarse=coarse))
        return result
    band=p[4][ev['top']:ev['top']+len(ev['signal'])]
    # Low-amplitude threshold uses native gray levels and the local noise estimate.
    ev.update(depth=band,raw_floor=max(1.25*p[8],.007*p[-1]),zero=np.zeros_like(ev['signal']))
    ev['joint']=np.ascontiguousarray(ev['signal']*np.clip(band/ev['raw_floor'],0,1))
    path=np.asarray(result['points'],int).reshape(-1,2)-org
    chosen=path
    ref=result['diagnostics'];idx=ref.get('selected')
    tr=ref['candidates'][idx]['trace'] if idx is not None else {}
    check=tr.get('reference') or {}
    weak=not len(path) or check.get('decision') in ('NO_SUPPORTED_BOUNDARY','TRIM_MATCHED_SHAPE','STRIP_STATIC_BRANCH') or tr.get('geometry') in ('DISTAL_KINK','DISTAL_BRIGHT_GAP')
    if weak:
        holes=difference_holes(ev,p)
        for seed in incremental_seeds(ev,p):
            alt,why=certified_path(p,ev,seed,stage,holes)
            audit['trials'].append(dict(seed=(np.asarray(seed)+org).tolist(),status=why,tip=(alt[-1]+org).tolist() if alt is not None else None))
            if alt is None:
                audit['rejections'][why]=audit['rejections'].get(why,0)+1
                continue
            if why=='BODY_INCREMENT' and not len(path) and seed[0]>p[6]+px(s,.006):
                # Reject an isolated stroke only if the entire approach contains a white gap.
                a,b=seed;rr=px(s,.020);cols=slice(p[6]+1,a);region=band[max(0,b-ev['top']-rr):b-ev['top']+rr+1,cols]
                if region.size and (np.quantile(region,.92,axis=0)<max(3*p[8],.035*p[-1])).sum()>=px(s,.005):
                    audit['trials'][-1]['status']='DETACHED_IN_WHITE';continue
            if len(path) and alt[-1,0]<path[-1,0]-.12*s and check.get('decision')!='NO_SUPPORTED_BOUNDARY':continue
            if len(path):
                # Preserve the established raw geometry through a weak near-mouth band.
                # Use the incremental branch when the baselines disagree in the stem
                # or the raw output ends on reference-matched texture.
                length=min(path[-1,0],alt[-1,0],p[6]+px(s,.23))
                cols=np.arange(max(path[0,0],alt[0,0]),length+1)
                same=len(cols)>px(s,.035) and np.median(abs(np.interp(cols,*path.T)-np.interp(cols,*alt.T)))<px(s,.014)
                if same and check.get('decision') not in ('STRIP_STATIC_BRANCH','TRIM_MATCHED_SHAPE'):
                    break
            chosen=alt;audit.update(decision='FRONT_INCREMENT',stop='DUAL_SUPPORT_END');break
    if len(chosen):
        repaired=parallel_recovery(chosen,p,ev)
        if repaired is not chosen:
            chosen=repaired;audit['lip_identity']='OBSERVED_PARALLEL_RECOVERY'
        broad=resolved_trunk(chosen,p)
        fade=None if broad else fading_endpoint(chosen,p,ev)
        if fade is not None and fade[-1,0]>chosen[-1,0]+px(s,.030):
            # Disallow a long extrapolation across a sharp termination. A true
            # fading shoulder must already attenuate on the observed trunk.
            xx,yy=chosen.T;depth=p[4][yy,xx];w=px(s,.026)
            if len(xx)>=3*w and np.median(depth[-2*w:-w])>=.72*np.median(depth[-3*w:-2*w]):
                fade=None
        if fade is not None:
            chosen=fade;audit['stop']='MEASURED_FADE'
        elif broad:
            end=resolved_end(chosen,p,ev)
            if end is not chosen:chosen=end;audit['stop']='RESOLVED_INCREMENT_END'
        elif len(chosen)>1:
            extended=weak_extension(chosen,p,ev)
            if extended is not chosen:
                chosen=extended;audit['stop']='OBSERVED_WEAK_END'
        trimmed=static_suffix(chosen,p,ev)
        if trimmed is not None:chosen=trimmed;audit['stop']='MATCHED_REFERENCE_SUFFIX'
    if len(chosen) and (chosen is not path):
        pts=(chosen+org).tolist();tip=pts[-1];start=pts[0]
        trace=dict(first_loss=None,gate=audit['decision'],stop=audit['stop'],reference=reg)
        result=dict(status='VALID',root=start,points=pts,tip=tip,diagnostics=dict(dual=audit,selected=0,candidates=[dict(start=start,tip=tip,status='VALID',trace=trace)],pairs=[],coarse=coarse))
    return result
