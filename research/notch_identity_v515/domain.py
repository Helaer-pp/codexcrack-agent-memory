"""Build the upstream reference map only after locating the physical notch."""
import cv2
import numpy as np
from research.unified_crack_tip_60q.features import correlation, CONFIG


def mapped_reference(reference,current,rp,cp,scene,c):
    xa,ya,xb,yb=scene['bounds']
    raw=current[ya:yb,xa:xb].astype(np.float32)
    shape=raw.shape
    Y=np.arange(ya,yb,dtype=np.float32)[:,None]
    X=np.arange(xa,xb,dtype=np.float32)[None,:]
    alpha=np.clip((Y-cp[0,1])/max(1.,cp[1,1]-cp[0,1]),0,1)
    delta=cp-rp
    mx=(X-((1-alpha)*delta[0,0]+alpha*delta[1,0])).astype(np.float32)
    my=(Y-((1-alpha)*delta[0,1]+alpha*delta[1,1])).astype(np.float32)
    my=np.broadcast_to(my,shape).copy()
    coarse=cv2.remap(reference,mx,my,cv2.INTER_LINEAR).astype(np.float32)
    warp=(mx>=0)&(my>=0)&(mx<reference.shape[1]-1)&(my<reference.shape[0]-1)
    correction_x=np.zeros(shape,np.float32);correction_y=np.zeros(shape,np.float32)
    windows=[];radius=c['ref_search'];hh=2*c['ref_halfheight'];exhausted=False
    for x in range(radius,shape[1]-radius,c['ref_tile']):
        width=min(c['ref_tile'],shape[1]-radius-x)
        if width<12:continue
        sides=[]
        for py in cp[:,1]:
            # Material context beyond the P point interval, outside the central opening.
            center=py+(-.18 if py==cp[0,1] else .18)*scene['scale']-ya
            y=int(np.clip(round(center)-hh//2,radius,shape[0]-hh-radius))
            if shape[0]<hh+2*radius:continue
            cur=raw[y:y+hh,x:x+width];base=coarse[y:y+hh,x:x+width]
            std0=float(cur.std());std1=float(base.std());material=float(np.mean((cur>=c['material_min'])&(base>=c['material_min'])))
            legal=(warp[y-radius:y+hh+radius,x-radius:x+width+radius].all() and
                   cur.min()>5 and coarse[y-radius:y+hh+radius,x-radius:x+width+radius].min()>5)
            reason='LOW_TEXTURE_OR_MATERIAL';shift=[0,0];score=correlation(base,cur);bias=float(np.median(base-cur));hold=score
            available=bool(legal and std0>=c['ref_std'] and std1>=c['ref_std'] and material>=c['ref_material_fraction'])
            if len(windows)*2+len(sides)>=c['ref_max_windows']:available=False;exhausted=True;reason='REGISTRATION_BUDGET'
            if available:
                search=coarse[y-radius:y+hh+radius,x-radius:x+width+radius]
                match=cv2.matchTemplate(search,cur,cv2.TM_CCOEFF_NORMED);_,score,_,loc=cv2.minMaxLoc(match)
                sx,sy=loc[0]-radius,loc[1]-radius;shift=[sx,sy]
                corrected=coarse[y+sy:y+sy+hh,x+sx:x+sx+width];bias=float(np.median(corrected-cur))
                hold=min(correlation(corrected[::2,::2],cur[::2,::2]),correlation(corrected[1::2,1::2],cur[1::2,1::2]))
                available=bool(score>=c['ref_ncc'] and hold>=c['ref_ncc']-.05 and abs(bias)<=c['ref_bias_max'])
                reason='TRUSTED_LOCAL_TEXTURE' if available else 'CORRELATION_OR_PHOTOMETRIC_MISMATCH'
            elif not legal:reason='WARP_OUTSIDE_REFERENCE'
            sides.append(dict(bounds=[xa+x,ya+y,xa+x+width,ya+y+hh],std_current=std0,std_reference=std1,material=material,ncc=float(score),holdout_ncc=hold,bias=bias,shift=shift,trusted=available,reason=reason))
        valid=len(sides)==2 and all(s['trusted'] for s in sides)
        if valid:
            frac=np.clip((Y-sides[0]['bounds'][1])/max(1,sides[1]['bounds'][1]-sides[0]['bounds'][1]),0,1)
            correction_x[:,x:x+width]=(1-frac)*sides[0]['shift'][0]+frac*sides[1]['shift'][0]
            correction_y[:,x:x+width]=(1-frac)*sides[0]['shift'][1]+frac*sides[1]['shift'][1]

        windows.append(dict(x0=x+xa,x1=x+xa+width,sides=sides,trusted=valid))
    mx+=correction_x;my+=correction_y
    good=(mx>=0)&(my>=0)&(mx<reference.shape[1]-1)&(my<reference.shape[0]-1)
    aligned=cv2.remap(reference,mx,my,cv2.INTER_LINEAR).astype(np.float32)
    aligned[~good]=np.nan
    return aligned,dict(windows=windows,status='MAPPED')


def align_frame(current,fixed,cp,rp,box,prep,stage='S1'):
    l,t,r,b=box
    empty=dict(windows=[],status='NO_NOTCH')
    if prep is None:return np.empty((0,0),np.float32),[],empty
    p,band,_=prep
    x=max(l,l+p.origin[0]+p.front-round(.08*p.scale))
    center=t+p.origin[1]+int(np.median(np.asarray(p.starts)[:,1]))
    top=max(t+band[0],center-round(.51*p.scale))
    bottom=min(t+band[1],center+round(.51*p.scale)+1)
    if stage!='S1' and p.local.size>250000:
        # Include a registration halo around the native-resolution search strip.
        top=max(top,center-round(.23*p.scale))
        bottom=min(bottom,center+round(.23*p.scale)+1)
    bounds=[int(x),int(top),int(r),int(bottom)]
    scene=dict(bounds=bounds,scale=float(np.linalg.norm(cp[1]-cp[0])))
    aligned,info=mapped_reference(fixed,current,rp,cp,scene,CONFIG)
    return aligned,bounds,info


def embed(aligned,bounds,box):
    l,t,r,b=box
    result=np.full((b-t,r-l),np.nan,np.float32)
    if bounds:
        x,y,right,bottom=bounds
        result[y-t:bottom-t,x-l:right-l]=aligned
    return result


def replay(fixed,cp,rp,bounds,info):
    """Reproduce the two OpenCV resampling operations from saved registration windows."""
    x,y,r,b=bounds
    Y,X=np.mgrid[y:b,x:r].astype(np.float32)
    fraction=np.clip((Y-cp[0,1])/max(1.,cp[1,1]-cp[0,1]),0,1)
    delta=cp-rp
    mx=X-((1-fraction)*delta[0,0]+fraction*delta[1,0])
    my=Y-((1-fraction)*delta[0,1]+fraction*delta[1,1])
    mx=mx.astype(np.float32);my=my.astype(np.float32)
    for window in info['windows']:
        if not window['trusted']:continue
        a,z=window['sides']
        sl=np.s_[:,window['x0']-x:window['x1']-x]
        frac=np.clip((Y[sl]-a['bounds'][1])/max(1,z['bounds'][1]-a['bounds'][1]),0,1)
        mx[sl]+=(1-frac)*a['shift'][0]+frac*z['shift'][0]
        my[sl]+=(1-frac)*a['shift'][1]+frac*z['shift'][1]
    mx=mx.astype(np.float32);my=my.astype(np.float32)
    good=(mx>=0)&(my>=0)&(mx<fixed.shape[1]-1)&(my<fixed.shape[0]-1)
    aligned=cv2.remap(fixed,mx,my,cv2.INTER_LINEAR).astype(np.float32)
    aligned[~good]=np.nan
    return aligned
