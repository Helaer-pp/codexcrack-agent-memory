"""V3.6 anchored grayscale geometry with narrow signed-increment corroboration."""
import cv2
import numpy as np
from scipy.ndimage import median_filter
from research.notch_identity_v31.detector import px
from research.notch_identity_v31.terminal import trace_windowed
from research.notch_identity_v36 import terminal as baseline
from . import evidence,backbone
from research.notch_identity_v40.tracking import roots as ridge_roots

STAGES=('front','floor','v4_1')

def prepare(raw,hint,scale,stage='v4_1'):
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
    strength=ev['joint'] if stage!='front' else sig
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
    if not strong:return None,'NO_CONTINUOUS_NECK'
    obs=energy>=.85
    if stage!='front':
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
    if stage!='v4_1':
        from research.notch_identity_v40.tracking import admissible
        allowed,rejected=admissible([dict(root=list(seed),points=path,rank=1)],p)
        if not allowed:return None,next(iter(rejected),'RAW_GATE')
    else:
        # Only a closed incremental outline near the published branch can veto a strong neck.
        end=tuple(map(float,(path[-1,0],path[-1,1]-top)))
        def on_closed_ridge(h):
            bx,by,bw,bh=cv2.boundingRect(h)
            tail=path[(path[:,0]>=bx+bw-px(s,.025))&(path[:,0]<=bx+bw+px(s,.025))]
            return (end[0]<=bx+bw+px(s,.10) and len(tail) and
                    np.any((tail[:,1]-top>=by-px(s,.017))&(tail[:,1]-top<=by+bh+px(s,.017))))
        if any(on_closed_ridge(h) for h in holes):
            return None,'INCREMENT_CLOSED_RIM'
        if np.mean(ev['clear'][yy[indices],xx[indices]]<.25)>.85:return None,'FIXED_CONTOUR'
    return path,'CERTIFIED'

def fading_endpoint(path,p,ev):
    """Fit extinction to a coherent fading raw trunk and certify its end on measured pixels."""
    if len(path)<px(p[5],.20):return None
    s=p[5];front=p[6];gray=p[7];noise=p[8]
    x0,y0=path.T;w=px(s,.060);step=px(s,.012)
    x=np.arange(x0[0],min(gray.shape[1],x0[-1]+px(s,.075)+1))
    y=np.interp(x,x0,y0)
    slope=np.clip((y0[-1]-y0[max(0,len(y0)-w)])/max(1,x0[-1]-x0[max(0,len(y0)-w)]),-.55,.55)
    y[x>x0[-1]]=y0[-1]+slope*(x[x>x0[-1]]-x0[-1])
    offsets=np.arange(-px(s,.008),px(s,.008)+1)[:,None]
    yy=np.clip(np.rint(y).astype(int)+offsets,0,len(gray)-1)
    dep=p[4][yy,x]
    row=dep.argmax(axis=0);center=yy[row,np.arange(len(x))]
    depth=median_filter(dep.max(axis=0),size=max(3,2*px(s,.005)+1),mode='nearest')
    starts=np.arange(max(w,px(s,.09)),len(x)-w,step)
    for j in starts:
        segment=depth[j:j+w];t=np.arange(w);rate,intercept=np.polyfit(t,segment,1)
        if rate>=0 or intercept<max(6*noise,.045*p[-1]) or -rate*w<.42*intercept:continue
        resid=np.median(abs(segment-(intercept+rate*t)))
        if resid>max(1.4*noise,.12*intercept):continue
        zero=j+int(round(intercept/-rate))
        if not j+w-2<=zero<min(len(x),j+3*w):continue
        # Upstream and downstream windows must independently support a transition.
        hi=depth[max(0,j-w):j];lo=depth[zero:min(len(x),zero+w)]
        if len(lo)<step or np.median(hi)<.8*intercept or np.median(lo)>.40*np.median(hi):continue
        slope_y=(y[j+w-1]-y[j])/max(1,w-1)
        pred=y[j]+slope_y*(x-x[j])
        ok=(abs(center-pred)<=max(1.5,.007*s))&(dep.max(0)>=ev['raw_floor'])
        rows=np.clip(center-ev['top'],0,len(ev['signal'])-1)
        ok&=ev['signal'][rows,x]>=.50
        keep=np.flatnonzero(ok&(np.arange(len(x))<=zero)&(np.arange(len(x))>=zero-step*2))
        if not len(keep):continue
        k=keep[-1]
        prefix=path[path[:,0]<x[j]]
        ids=np.flatnonzero(ok&(np.arange(len(x))>=j)&(np.arange(len(x))<=k))
        return np.vstack((prefix,np.c_[x[ids],center[ids]]))
    return None

def resolved_trunk(path,p):
    """A multi-pixel opening does not follow the contrast law of an unresolved line."""
    if len(path)<6:return False
    x,y=path[len(path)//4:3*len(path)//4].T
    rad=px(p[5],.03);g=p[7].astype(np.float32,copy=False)
    if np.min(y)<rad or np.max(y)+rad>=len(g):return False
    base=np.minimum(g[y-rad,x],g[y+rad,x])
    threshold=(g[y,x]+base)*.5
    widths=(g[y+np.arange(-rad,rad+1)[:,None],x]<threshold).sum(axis=0)
    return np.median(widths)>=max(1.5,.0046*p[5])

def resolved_end(path,p,ev):
    # Retain the geometric end of a resolved opening unless its distal increment
    # is lost against lateral material noise. Restrict the correction to one local window.
    x,y=path.T;s=p[5];yy=y-ev['top'];w=px(s,.018)
    if len(x)<3*w or yy.min()<0 or yy.max()>=len(ev['signal']):return path
    signal=ev['signal'][yy,x];dep=p[4][y,x]
    if np.median(signal[-3*w:-w])<1.5:return path
    flank=px(s,.04);offsets=np.r_[-flank:-flank//2,flank//2:flank+1]
    bg=ev['signal'][np.clip(yy[-3*w:,None]+offsets,0,len(ev['signal'])-1),x[-3*w:,None]]
    cutoff=max(1.2,float(np.percentile(bg,96)))
    supported=(signal>=cutoff)&(dep>=ev['raw_floor'])
    trailing=np.flatnonzero(supported[-2*w:])
    if len(trailing) and trailing[-1]<2*w-1:
        j=len(path)-2*w+trailing[-1]
        # Return the center of the final contiguous measurement footprint.
        # A lone threshold crossing has no resolved spatial extent.
        footprint=max(1,px(s,.009))
        a=max(0,j-footprint+1)
        confident=np.flatnonzero(supported[a:j+1])
        center=a+int(np.median(confident))
        return path[:center+1]
    return path

def same_lip_prefix(path,p):
    if len(path)<2:return path
    s=p[5];x,y=path.T
    for j in np.flatnonzero((np.diff(x)>=px(s,.012))&(x[:-1]<=p[6]+px(s,.32))):
        first=max(0,np.searchsorted(x,x[j]-px(s,.035)))
        slope=(y[j]-y[first])/max(1,x[j]-x[first])
        predicted=y[j]+np.clip(slope,-.65,.65)*(x[j+1]-x[j])
        if abs(y[j+1]-predicted)>max(2,.016*s):return path[:j+1]
    return path

def weak_extension(path,p,ev):
    """Recover a few directly observed terminal columns after a fading shoulder."""
    x,y=path.T;s=p[5];depth=p[4][y,x];w=px(s,.03)
    if len(x)<4*w or np.median(depth[-w:])>.65*np.median(depth[-4*w:-2*w]):return path
    slope=np.clip((y[-1]-y[-w])/max(1,x[-1]-x[-w]),-.6,.6)
    extra=[];top=ev['top'];gap=0
    for col in range(x[-1]+1,min(p[7].shape[1],x[-1]+px(s,.036)+1)):
        cy=round(y[-1]+slope*(col-x[-1]));rad=px(s,.004)
        ys=np.arange(max(top,cy-rad),min(top+len(ev['signal']),cy+rad+1))
        if not len(ys):break
        k=ys[np.argmax(p[4][ys,col])]
        if (p[4][k,col]<max(ev['raw_floor'],1.65*p[8]) or ev['signal'][k-top,col]<.65 or
            ev['delta'][k-top,col]<max(1.5*p[8],.01*p[-1])):
            gap+=1
            if gap>=max(1,px(s,.006)):break
            continue
        gap=0;extra.append((col,k))
    return np.vstack((path,extra)) if extra else path

def static_suffix(path,p,ev):
    """Require a common deformation offset across a run of the reference ridge."""
    s=p[5];x,y=path.T;yy=y-ev['top'];f=ev['fixed'];rad=px(s,.014)
    if min(yy)<rad or max(yy)>=len(f)-rad:return None
    w=px(s,.055)
    if len(path)<2*w:return None
    cur=p[4][y,x]; off=np.arange(-px(s,.025)-1,px(s,.025)+2)[:,None]
    rows=np.clip(yy+off,rad,len(f)-rad-1)
    depth=np.minimum(f[rows-rad,x],f[rows+rad,x])-f[rows,x]
    compatible=depth>=np.maximum.reduce([np.full_like(cur,3*p[8]),np.full_like(cur,.045*p[-1]),.55*cur])
    # A matching run must persist to the terminal neighborhood. Its displacement
    # may be either sign, but remains the same across a local tangent window.
    # Allow one sampled row of subpixel rounding around a common deformation.
    compatible=cv2.dilate(compatible.astype('uint8'),np.ones((3,1),np.uint8)).astype(bool)
    density=cv2.blur(compatible.astype('float32'),(w,1),anchor=(0,0),borderType=cv2.BORDER_REPLICATE).max(0)
    match=density>=.72
    if not match[-w:].any():return None
    breaks=np.flatnonzero((~match)&(np.arange(len(match))<len(match)-w))
    j=int(breaks[-1]+1) if len(breaks) else 0
    if j<px(s,.045):return None
    tail_slope=(y[-1]-y[j])/max(1,x[-1]-x[j])
    head=max(0,j-w)
    head_slope=(y[j]-y[head])/max(1,x[j]-x[head])
    required=.045 if abs(tail_slope-head_slope)>.14 else .085
    if len(path)-j<px(s,required):return None
    # The window is forward-looking; find the first measured compatible pixel.
    j+=int(np.argmax(compatible[:,j:j+w].any(axis=0)))
    return path[:max(1,j)]

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
        holes=difference_holes(ev,p) if stage=='v4_1' else []
        for seed in incremental_seeds(ev,p):
            alt,why=certified_path(p,ev,seed,stage,holes)
            audit['trials'].append(dict(seed=(np.asarray(seed)+org).tolist(),status=why,tip=(alt[-1]+org).tolist() if alt is not None else None))
            if alt is None:
                audit['rejections'][why]=audit['rejections'].get(why,0)+1
                continue
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
    if len(chosen) and stage!='front':
        kept=same_lip_prefix(chosen,p)
        if kept is not chosen:
            chosen=kept;audit['stop']='CROSS_LIP_BREAK'
        broad=resolved_trunk(chosen,p)
        fade=None if broad else fading_endpoint(chosen,p,ev)
        if fade is not None and audit['stop']!='CROSS_LIP_BREAK':
            chosen=fade;audit['stop']='MEASURED_FADE'
        elif broad:
            end=resolved_end(chosen,p,ev)
            if end is not chosen:chosen=end;audit['stop']='RESOLVED_INCREMENT_END'
        elif len(chosen)>1 and audit['stop']!='CROSS_LIP_BREAK':
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
