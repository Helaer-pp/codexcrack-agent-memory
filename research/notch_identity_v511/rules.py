"""Coincident differential ridge and raw valley gates."""
import cv2
import numpy as np
from research.notch_identity_v54 import terminal as base
from research.notch_identity_v53.terminal import band_width,px
from research.notch_identity_v40.evidence import offset_image
from research.notch_identity_v510.ridge import longest
from numba import njit
def normal(p, fixed, shift, stage):
    # The sampling domain starts at the front. Replicated borders cannot read a left-side marker.
    gray = p.local[:, p.front:].astype(np.float32)
    dx, dy = shift
    reference = cv2.warpAffine(fixed[p.sl], np.float32([[1, 0, dx+p.front], [0, 1, dy]]),
        (gray.shape[1], len(gray)), flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_CONSTANT, borderValue=float('nan'))
    delta = np.where(np.isfinite(reference), reference-gray, 0.)
    threshold = max(1., 2.7*p.noise, .030*p.span)
    ridge = np.zeros_like(gray)
    dark = np.zeros_like(gray)
    dipole = np.zeros(gray.shape, bool)
    for slope in (-.70, -.34, 0., .34, .70):
        step = px(p.scale, .009)
        rise = round(step*slope)
        sm = .25*(2*delta + offset_image(delta, step, rise) + offset_image(delta, -step, -rise))
        for radius in sorted({px(p.scale, .008), px(p.scale, .016)}):
            x = round(-radius*slope/np.hypot(1,slope))
            y = max(1, round(radius/np.hypot(1,slope)))
            if stage=='S4':
                accumulate(gray,sm,ridge,dark,dipole,x,y,threshold)
                continue
            prominence = sm-np.maximum(offset_image(sm,x,y), offset_image(sm,-x,-y))
            eligible = (sm>1.25*threshold) & (prominence>.28*sm)
            ridge = np.maximum(ridge, np.where(eligible, prominence/threshold, 0.))
            dark = np.maximum(dark, np.minimum(offset_image(gray,x,y),offset_image(gray,-x,-y))-gray)
            blue = np.minimum(offset_image(sm,2*x,2*y), offset_image(sm,-2*x,-2*y))
            dipole |= (sm>threshold) & (blue < -threshold) & (-blue>.48*sm)
    def persistent(mask, n):
        spread = cv2.dilate(mask.astype('float32'), np.ones((3,1),np.uint8))
        return cv2.blur(spread,(n,1))>=.65
    core = dark > max(3*p.noise,.035*p.span)
    original_dip = dipole & ~(core & persistent(core,7))
    wide = (band_width(delta>threshold)>max(3,.035*p.scale)) & (ridge<1.6)
    morph = (ridge>1.) & persistent(ridge>1.,5) & ~wide
    dual = morph & core & (delta>threshold)
    dipole = original_dip & ~dual
    fine = morph & ~dipole
    ref_depth = base.baseline.bilateral(-np.where(np.isfinite(reference),reference,gray),p.scale)
    prior = cv2.dilate(ref_depth,np.ones((2*px(p.scale,.035)+1,3),np.uint8))
    bridge_fine = fine & (prior < np.maximum(4*p.noise,.52*np.maximum(delta,threshold)))
    return fine.T,core.T,dipole.T,ridge.T,(bridge_fine|dual).T,delta.T,dual.T,original_dip.T,morph.T



def rescue(field,entry,dual,scale,band,offset):
    limit=min(len(field),round(.55*scale))
    m=dual[:limit].copy()
    margin=max(3,round(.035*scale))
    y=np.arange(field.shape[1])+offset
    m&=(y>=band[0]+margin)&(y<band[1]-margin)
    if not (m.any(axis=1).sum()>=8):return None
    boosted=np.where(m,np.maximum(field[:limit],1.4),np.minimum(field[:limit],-.35))
    boosted[~np.isfinite(field[:limit])]=-np.inf
    z=base.lattice(boosted.astype('float32'),entry,scale,True)
    path=z[0]
    if len(path)<8:return None
    x,y=path.T;support=m[x,y]
    if longest(support)<8 or support.mean()<.55 or not support[-1]:return None
    return z


def signed_rank(candidates,dual,delta,threshold):
    if not any(longest(dual[tuple(path.T)])>=8 for path,_ in candidates):return
    for path,item in candidates:
        x,y=path.T
        unique=np.ones(len(x),bool)
        for other,_ in candidates:
            if other is path:continue
            pos=x-other[0,0];ok=(pos>=0)&(pos<len(other))
            unique[ok]&=abs(y[ok]-other[pos[ok],1])>2
        plus=int((unique & dual[x,y]).sum())
        blue=int((unique & (delta[x,y]<-threshold)).sum())
        item.update(dual_columns=plus,blue_columns=blue)
    if any(b['dual_columns']>=8 for _,b in candidates) and any(b['blue_columns']>=3 and b['blue_columns']>b['dual_columns'] for _,b in candidates):
        for _,b in candidates:b['merit']+=1.5*b['dual_columns']-2.0*b['blue_columns']


def extend(p,field,path,fine,core,strength,excluded,band,dual,valley):
    x0,y0=path[-1];n=min(len(field)-x0,max(24,round(.52*p.scale)))
    info=dict(accepted=False,reason='SHORT_OR_UNATTACHED')
    if n<=8:return path,info
    radius=max(8,round(.13*p.scale))
    lo=max(0,y0-radius);hi=min(field.shape[1],y0+radius+1)
    sl=np.s_[x0:x0+n,lo:hi];f=field[sl];hit=fine[sl];both=dual[sl]
    margin=max(3,round(.035*p.scale))
    rows=np.arange(lo,hi)+p.origin[1]
    safe=(rows>=band[0]+margin)&(rows<band[1]-margin)
    if not safe[y0-lo]:return path,dict(info,reason='EDGE_START')
    lifted=np.where(hit,np.maximum(f,np.minimum(1.4,.32+.38*strength[sl])),
                    np.where(core[sl],np.clip(f,-.14,.12),np.minimum(f,-.38)))
    lifted=np.where(np.isfinite(f)&~excluded[sl]&safe,lifted,-np.inf).astype('float32')
    # A short fork can reattach within four rows. Preserve every original
    # coordinate and require dual support immediately after the lateral step.
    start=np.zeros((1,hi-lo),np.uint8);start[0,y0-lo]=1
    offset=max(1,min(4,round(.012*p.scale)))
    for row in range(max(0,y0-lo-offset),min(hi-lo,y0-lo+offset+1)):
        if safe[row] and both[1:4,max(0,row-1):row+2].any(1).all():start[0,row]=1
    lifted[0]=0
    tail,*_=base.lattice(lifted,start,p.scale,False)
    if len(tail)<=8:return path,dict(info,proposed=max(0,len(tail)-1))
    tx,ty=tail.T;measured=both[tx,ty];raw=base.increments(f,tail);raw[0]=0
    curve=np.cumsum(raw);bottom=np.minimum.accumulate(curve)
    gain=np.cumsum(base.increments(lifted,tail))
    witness=bool((fine[tuple(path.T)]&core[tuple(path.T)])[:max(6,round(.10*p.scale))].sum()>=2)
    for j in range(len(tail)-1,7,-1):
        mask=measured[1:j+1];short=longest(mask)>=8 and mask.mean()>=.70 and mask[:4].any()
        rising=valley and witness and j>=15 and longest(hit[tx[1:j+1],ty[1:j+1]])>=6 and curve[j]-bottom[j]>=1.0 and raw[j-2:j+1].mean()>.05
        if not(short or rising) or gain[j]/j<=.12 or not measured[j-1:j+1].all():continue
        return np.vstack((path,tail[1:j+1]+[x0,lo])),dict(accepted=True,reason='DUAL_RUN' if short else 'VALLEY_RISE',columns=j,
                 fine_fraction=float(hit[tx[1:j+1],ty[1:j+1]].mean()),dual_fraction=float(mask.mean()),lateral_step=int(ty[0]+lo-y0))
    return path,dict(info,reason='NO_SUPPORTED_TERMINUS',proposed=len(tail)-1)

def reachable_width(field,seeds,scale):
    bound=0.
    for x,m in enumerate(field.max(axis=1)):
        bound+=float(m)
        if x<len(seeds):bound=max(bound,0.,float(m))
        if x>=len(seeds) and bound<-.105*scale:
            return min(len(field),max(x,round(.55*scale))+round(.52*scale)+max(48,round(.13*scale)))
    return len(field)

@njit
def accumulate(gray,sm,ridge,dark,dip,x,y,threshold):
    # Exact replicated-border neighbourhoods, without materializing six shifted images.
    h,w=sm.shape
    for i in range(h):
        up=min(h-1,max(0,i-y));down=min(h-1,max(0,i+y))
        far_up=min(h-1,max(0,i-2*y));far_down=min(h-1,max(0,i+2*y))
        for j in range(w):
            left=min(w-1,max(0,j-x));right=min(w-1,max(0,j+x))
            val=sm[i,j]
            prom=val-max(sm[down,right],sm[up,left])
            if val>np.float32(1.25*threshold) and prom>np.float32(.28)*val:
                ridge[i,j]=max(ridge[i,j],prom/np.float32(threshold))
            dark[i,j]=max(dark[i,j],min(gray[down,right],gray[up,left])-gray[i,j])
            blue=min(sm[far_down,min(w-1,max(0,j+2*x))],sm[far_up,min(w-1,max(0,j-2*x))])
            if val>np.float32(threshold) and blue < -np.float32(threshold) and -blue>np.float32(.48)*val:dip[i,j]=True
