"""Frozen V5.10 intensity field with an explicit reference-registration adapter."""
from dataclasses import replace
import cv2
import numpy as np
from research.notch_identity_v53.terminal import px,band_width
from research.notch_identity_v51.terminal import bilateral
from .registration import registered
from time import perf_counter
def buffered_bilateral(im,scale):
    radii=sorted({px(scale,r) for r in (.007,.014,.024)})
    pad=radii[-1]
    h=len(im)
    extended=cv2.copyMakeBorder(im,pad,pad,0,0,cv2.BORDER_REPLICATE)
    result=np.zeros_like(im)
    scratch=np.empty_like(im)
    for radius in radii:
        np.maximum(extended[pad-radius:pad-radius+h],extended[pad+radius:pad+radius+h],out=scratch)
        np.subtract(im,scratch,out=scratch)
        np.maximum(result,scratch,out=result)
    return result

def active_rows(p):
    center=int(np.median(np.asarray(p.starts)[:,1]))
    margin=px(p.scale,.23)
    return max(0,center-margin), min(len(p.local),center+margin+1)

def base_field(p,fixed,stage):
    tick0=perf_counter()
    timings={}
    def mark(key):
        nonlocal tick0
        now=perf_counter()
        timings[key]=(now-tick0)*1000
        tick0=now
    thin=buffered_bilateral
    s=p.scale;g=p.local.astype(np.float32);sig=max(.45,.003*s)
    # Straight line openings attenuate isolated spots while preserving a sloping valley.
    reach=px(s,.011)
    kernels=[]
    for slope in (-.55,0.,.55):
        rise=round(slope*reach)
        k=np.zeros((2*abs(rise)+1,2*reach+1),np.uint8)
        cv2.line(k,(0,abs(rise)-rise),(2*reach,abs(rise)+rise),1)
        kernels.append(k)
    texture=np.abs(g-cv2.GaussianBlur(g,(0,0),sigmaX=max(.5,.017*s)))
    sample=texture[::px(s,.012),p.front+px(s,.035)::px(s,.012)]
    # Strong background texture makes short oblique ridges discontinuous in a line opening.
    uniform=np.clip((3.2*p.noise-np.quantile(sample,.925))/(1.1*p.noise),0,1) if sample.size else 0.
    uniform=float(uniform)
    def ridge(im,depth=None,opened=None):
        a=thin(im,s) if depth is None else depth
        sustained=opened if opened is not None else np.maximum.reduce([cv2.morphologyEx(a,cv2.MORPH_OPEN,k) for k in kernels])
        clean=np.clip((.026*p.span-p.noise)/(.020*p.span),0,1)
        weak=np.clip((.19*p.span-a)/(.10*p.span),0,1)
        mix=.03+.87*uniform*clean*weak
        a=(1-mix)*a+mix*sustained
        return .60*a+.40*cv2.GaussianBlur(a,(0,0),sigmaX=sig,sigmaY=max(.35,sig*.52))
    depth=ridge(-g)
    size=2*px(s,.036)+1
    broad=cv2.blur(depth,(size,size))
    tau=np.maximum(2.25*p.noise+.007*p.span,1.9*broad)
    raw_score=2.1*np.tanh(depth/(2*tau))-.97
    original_raw=raw_score
    if p.stage=='v5_1':
        # Clip the background floor, raise the zero crossing and retain dynamic range for deep lines.
        base=np.maximum(tau, np.maximum(.033*p.span,3.8*p.noise))
        raw_score=np.maximum(-.56,2.45*np.tanh(depth/(2*base))-1.46)
    lateral=abs(np.arange(len(g))-int(np.median(np.array(p.starts)[:,1])))>.12*s
    sample=raw_score[lateral,p.front+px(s,.04)::4]
    stats={'background_raw':float(sample.mean()) if sample.size else None}
    mark('gray_ridge')
    stats['substeps_ms']=timings
    score=raw_score.copy();coarse=reg=None;source='RAW_ONLY'
    if fixed is not None:
        args=(p.sl,p.origin,p.starts,None,None,s,p.front,p.local,p.noise,None,p.raw,p.span)
        tick=perf_counter()
        coarse,reg,aligned=registered(args,fixed,stage)
        stats["registration_ms"]=(perf_counter()-tick)*1000
        mark('registration')
        if aligned is not None:
            valid=np.isfinite(aligned);f=np.where(valid,aligned,g);d=f-g
            adequate=valid.mean()>.65 and (reg.get('status')=='OK' or (coarse or {}).get('status')=='OK')
            if np.any(valid) and np.quantile(np.abs(d[::4,::4]),.995)>.01*p.span:
                ink=thin(d,s) 
                opened=np.maximum.reduce([cv2.morphologyEx(ink,cv2.MORPH_OPEN,k) for k in kernels]) if ink is not None else None
                inc=ridge(d,ink,opened);fd=thin(-f,s);r=px(s,.014)
                smooth=cv2.GaussianBlur(d,(0,0),sigmaX=sig,sigmaY=max(.35,.5*sig))
                plus=np.maximum(smooth,0);minus=np.maximum(-smooth,0)
                if stage=='S4':
                    channels=cv2.blur(cv2.merge((plus,minus)),(1,2*r+1))
                    pos,neg=channels[:,:,0],channels[:,:,1]
                else:pos=cv2.blur(plus,(1,2*r+1));neg=cv2.blur(minus,(1,2*r+1))
                inc*=np.clip(1-neg/np.maximum(pos,p.noise),0,1)
                reach=px(s,.025)
                # Require a sustained reference valley at a common local displacement.
                coherent=cv2.blur(fd,(2*px(s,.012)+1,1))
                prior=cv2.dilate(coherent,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*reach+1,2*reach+1)))
                risk=np.clip((prior/np.maximum(depth,tau)-.40)/.45,0,1)*np.clip((prior-2*p.noise)/tau,0,1)
                # A neighbouring static valley may start several columns beyond the active crack.
                # Retain displacement tolerance but require column overlap for a full static penalty.
                column_prior=cv2.dilate(coherent,np.ones((2*reach+1,3),np.uint8))
                overlap=np.clip(column_prior/np.maximum(prior,p.noise),0,1)
                risk*=.30+.70*overlap
                diff_tau=np.maximum(2.45*p.noise+.007*p.span,2*cv2.blur(inc,(size,size)))
                delta_score=2.1*np.tanh(inc/(2*diff_tau))-.97
                mark('diff_ridge_prior')
                distance=np.maximum(0,np.arange(g.shape[1],dtype=np.float32)-p.front)
                # Reference valleys overlap the open notch at the birth; ramp to full strength in material.
                prior_weight=np.clip((distance-.04*s)/(.14*s),0.,1.)
                background=delta_score[lateral,p.front+px(s,.04)::4]
                stats['background_diff']=float(background.mean()) if background.size else None
                active=slice(*active_rows(p)) if stage=='S4' else slice(None)
                # Later seed/audit calculations still need the full normalized arrays.
                strong=np.clip((delta_score-.32)/.42,0,1)*(1-risk*prior_weight)
                visible=depth>=np.maximum(1.35*p.noise,.007*p.span)
                def neck_value(raw,ds,rs,orig):
                    neck=1-prior_weight
                    v=(.90-.47*prior_weight)*raw+(.10+.47*prior_weight)*ds-1.38*rs*prior_weight
                    v+=.43*prior_weight*np.maximum(0,orig-raw)*np.clip((ds+.2)/.65,0,1)
                    return np.maximum(v,neck*np.maximum(raw,.93*ds)-.16-1.38*rs*prior_weight-(1-neck)*2.5)
                centre=neck_value(raw_score[active],delta_score[active],risk[active],original_raw[active])
                if stage=='S4':
                    fused=np.full(raw_score.shape,-2.5,dtype=centre.dtype)
                    fused[active]=centre
                else:fused=centre
                # Disconnected point texture in the far field has a strong instantaneous peak but little longitudinal support.
                line=cv2.morphologyEx(inc,cv2.MORPH_OPEN,np.ones((1,2*px(s,.011)+1),np.uint8))
                corr=np.clip(line/np.maximum(inc,p.noise),0,1)
                far=np.clip((distance-.25*s)/(.12*s),0,1)
                fused=np.maximum(fused,np.where(strong>.55,.90*delta_score-1.2*risk,-2.5))
                middle=cv2.blur(g,(2*px(s,.026)+1,2*px(s,.026)+1))
                broad_gray=cv2.blur(g,(2*px(s,.085)+1,2*px(s,.085)+1))
                flank=np.abs(middle[lateral,p.front+px(s,.06)::5]-broad_gray[lateral,p.front+px(s,.06)::5])
                rough=float(np.quantile(flank,.90))/p.span if flank.size else 1.
                smooth_material=float(np.clip((.0080-rough)/.0025,0,1))
                clean=float(np.clip((.028*p.span-p.noise)/(.015*p.span),0,1))
                # Measure relative valley depth before the lip responses saturate in tanh.
                birth=np.clip(1-distance/(.24*s),0,1)
                prominence=np.clip((depth/np.maximum(.16*p.span,6*p.noise)-.85),-.50,1.6)
                fused+=1.15*birth*prominence
                near_raw=raw_score-(2.2+1.2*risk)*np.clip((distance-.15*s)/(.12*s),0,1)
                fused=np.maximum(fused,near_raw)
                mark('fusion_background')
                reach=px(s,.032)
                # Join strong observations on both sides of a short gap along the same local tangent.
                neck_end=min(g.shape[1],p.front+px(s,.26))
                stem=np.minimum(depth[:,:neck_end],inc[:,:neck_end])*(1-risk[:,:neck_end]*prior_weight[:neck_end])
                stem=cv2.dilate(stem,np.ones((2*px(s,.003)+1,1),np.uint8))
                bridged=np.zeros_like(stem)
                for slope in (-.16,0.,.16):
                    dy=round(reach*slope);k=np.zeros((2*abs(dy)+1,2*reach+1),np.uint8)
                    cv2.line(k,(0,abs(dy)-dy),(2*reach,abs(dy)+dy),1)
                    bridged=np.maximum(bridged,cv2.morphologyEx(stem,cv2.MORPH_CLOSE,k))
                bridge=np.zeros_like(depth,dtype=bool)
                bridge[:,:neck_end]=(bridged>max(.17*p.span,7*p.noise))&(stem<.6*bridged)
                fused=np.maximum(fused,np.where(bridge,.66,-2.5))
                # On smooth material, disconnected spots can mimic a weak fade after the true tip.
                if ink is None:ink=thin(d,s)
                continuous=opened if opened is not None else np.maximum.reduce([cv2.morphologyEx(ink,cv2.MORPH_OPEN,k) for k in kernels])
                strength=np.clip((.21*p.span-inc)/(.10*p.span),0,1)
                width=2*px(s,.013)+1
                averaged=cv2.blur(d,(width,1))
                slow=bilateral(averaged,s)*np.clip(1-neg/np.maximum(pos,p.noise),0,1)
                slow_base=max(2.4*p.noise/np.sqrt(width),.025*p.span)
                sustained=(slow>slow_base)&(averaged>slow_base)&(risk<.35)&(depth>.55*p.noise)
                lift=np.clip(slow/slow_base-1,0,.75)*(1-clean)
                fused=np.maximum(fused,np.where(sustained & (far>.5),lift-.14,-2.5))
                penalty=1.65*far*clean*smooth_material*strength*np.clip(1-continuous/np.maximum(inc,p.noise),0,1)
                fused-=penalty+.40*far*clean*smooth_material*strength*(1-corr)
                mark('bridge_texture')
                if smooth_material>.05:
                    # A taper keeps a transverse gradient; repeated dots also vary along the axis.
                    sm=cv2.GaussianBlur(d,(0,0),sigmaX=max(.65,.0045*s))
                    gx=cv2.Sobel(sm,-1,1,0);gy=cv2.Sobel(sm,-1,0,1)
                    box=(2*px(s,.020)+1,2*px(s,.009)+1)
                    ratio=cv2.blur(gx*gx,box)/np.maximum(cv2.blur(gy*gy,box),.01*p.noise**2)
                    dot=np.clip((ratio-.20)/.40,0,1)
                    faded=np.clip(1-ratio/.60,0,1)*np.clip(slow/(.60*slow_base),0,1)
                    supported=(averaged>p.noise)&(depth>.4*p.noise)&(risk<.40)&(far>.5)
                    fused=np.maximum(fused,np.where(supported,.9*faded-.34,-2.5))
                    fused-=1.55*smooth_material*far*strength*dot
                    # A displaced scratch can remain unipolar locally, even in smooth material.
                    fused-=.45*smooth_material*far*risk*overlap
                    # An existing displaced line redistributes darkness across the normal;
                    # a superposed new crack adds integrated darkness even beside that line.
                    radius=px(s,.045);box_mass=(2*px(s,.012)+1,2*radius+1)
                    residual=d-cv2.blur(d,(2*px(s,.08)+1,2*px(s,.08)+1))
                    mass=cv2.blur(residual,box_mass)
                    strength_sum=cv2.blur(np.abs(residual),box_mass)
                    imbalance=np.clip(mass/np.maximum(strength_sum,.50*p.noise),0,1)
                    added=np.clip((imbalance-.07)/.26,0,1)
                    joined=np.minimum(raw_score,delta_score)+.26*added-.62*(1-added)
                    recover=(risk>.20)&(far>.5)&(added>.30)&(slow>.7*slow_base)&(ratio<.55)
                    fused=np.maximum(fused,np.where(recover,joined,-2.5))
                fused=np.where(visible|(strong>.55)|bridge|(sustained & (far>.5)),fused,np.minimum(fused,-.8))
                # Contiguous new dark ridges are needed when the registered views differ only by sensor noise.
                mark('tail_filters')
                if adequate and np.quantile(np.abs(d[valid][::8]),.95)<max(4*p.noise,.025*p.span):
                    width=max(1,px(s,.035))
                    near=strong[:,p.front:p.front+px(s,.30)]
                    if near.size and cv2.blur(near,(width,1)).max()<.40:
                        source='NO_INCREMENT'
                if source!='NO_INCREMENT':score=np.where(valid,fused,raw_score);source='JOINT'
            else:source='NO_INCREMENT' if adequate else 'UNREGISTERED_RAW'
        else:source='UNREGISTERED_RAW'
    # No legal seed behind the mouth or on a detached dark stroke.
    f=p.front;end=min(g.shape[1],f+px(s,.020)+1)
    seeds=np.zeros((len(g),end-f),np.uint8)
    mid=int(np.median(np.array(p.starts)[:,1]));pad=px(s,.16)
    patch=g[:,max(0,f-px(s,.055)):end]
    material=float(np.percentile(patch,70))
    _,cc=cv2.connectedComponents((patch<material-max(4*p.noise,.10*p.span)).astype('uint8'))
    left=f-max(0,f-px(s,.055));core=patch[:,:max(1,left-px(s,.025))]<p.black+.26*p.span
    counts=np.bincount(cc[:,:core.shape[1]][core],minlength=2);counts[0]=0
    if counts.max():
        connected=cc[:,left:]==counts.argmax()
        seeds[:]=connected&(depth[:,f:end]>tau[:,f:end])
        seeds[:max(0,mid-pad)]=0;seeds[mid+pad+1:]=0
        # A mouth-edge pixel with blank material immediately to its right is not a ridge birth.
        audit=cv2.dilate(depth,np.ones((2*px(s,.004)+1,1),np.uint8))
        for j in range(seeds.shape[1]):
            block=audit[:,f+j+1:min(g.shape[1],f+j+1+px(s,.010))]
            if block.shape[1]:seeds[:,j]&=(block>max(2*p.noise,.018*p.span)).mean(1)>=.65
    if source=='NO_INCREMENT' and p.stage!='neck_fusion':
        strong_depth=np.maximum(5.5*p.noise,.105*p.span)
        score=np.where(depth>=strong_depth,raw_score,np.minimum(raw_score,-.55))
        stats['strong_floor']=float(strong_depth)
        source='PREEXISTING_CHECK'
    mark('seeds_and_gate')
    return np.ascontiguousarray(score[:,f:].T,dtype=np.float32),np.ascontiguousarray(seeds.T),coarse,reg,source,stats

def make(p,fixed,stage):
    score,seeds,coarse,reg,source,stats=base_field(replace(p,stage='v5_1'),fixed,stage)
    if source!='JOINT':return score,seeds,coarse,reg,source,stats
    s=p.scale;front=p.front;n=min(len(score),px(s,.25)+1)
    g=p.local[:,front:front+n].astype(np.float32)
    dx,dy=reg['shift']
    # Inverse map into the same geometrically aligned reference used by V5.1.
    warped=cv2.warpAffine(fixed[p.sl],np.float32([[1,0,dx+front],[0,1,dy]]),(n,len(g)),
        flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
    d=np.where(np.isfinite(warped),warped-g,0.)
    d=cv2.GaussianBlur(d,(0,0),max(.40,.0025*s))
    floor=max(3*p.noise,.038*p.span)
    width=band_width(d>floor)
    radius=px(s,.012)
    def prominence(im):
        pad=cv2.copyMakeBorder(im,radius,radius,0,0,cv2.BORDER_REPLICATE)
        return np.maximum(0,im-np.maximum(pad[:-2*radius],pad[2*radius:]))
    crest=np.maximum(prominence(d),prominence(-g))/np.maximum(d,floor)
    wide=np.clip((width-.024*s)/(.015*s),0,1)
    flat=np.clip((.56-crest)/.36,0,1)
    taper=np.clip((.25-np.arange(n)/s)/.05,0,1)
    weight=wide*flat*taper
    if p.stage=='v5_3':
        near_radius=px(s,.0065)
        def close_contrast(im):
            pad=cv2.copyMakeBorder(im,near_radius,near_radius,0,0,cv2.BORDER_REPLICATE)
            return np.maximum(0,im-np.maximum(pad[:-2*near_radius],pad[2*near_radius:]))
        dark=close_contrast(-g)
        thin=close_contrast(d)
        denom=np.maximum(d,floor)
        narrow_valley=np.clip((dark/denom-.11)/.27,0,1)
        medium=np.clip((width/s-.014)/.013,0,1)
        flank=cv2.dilate(g,np.ones((2*px(s,.025)+1,1),np.uint8))-g
        glare=np.clip((flank-.10*p.span)/(.15*p.span),0,1)
        diffuse=np.clip((.60-thin/denom)/.44,0,1)
        arc=medium*(1-narrow_valley)*np.maximum(diffuse,glare)
        weight=np.maximum(weight,arc*taper)
    original=score[:n].T
    reduction=weight*np.maximum(0,original-.015)
    original-=reduction
    if p.stage=='v5_3':original-=.42*arc*taper*(d>floor)
    stats.update(blob_pixels=int((weight>.5).sum()),max_blob_reduction=float(reduction.max()))
    return score,seeds,coarse,reg,source,stats

