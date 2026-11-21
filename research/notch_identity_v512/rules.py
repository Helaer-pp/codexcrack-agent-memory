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

def blank_crossing(initial, proposed, dual):
    """Test only the unobserved interval between the old tip and the proposed tip."""
    x,y=initial[-1]
    tail=proposed[proposed[:,0]>x]
    if not len(tail):return False
    dx,dy=tail[-1]-initial[-1]
    if dx<=25 and abs(dy)<=15:return False
    tx,ty=tail.T
    supported=dual[tx,ty]
    return longest(supported)<8 or longest(~supported)>max(8,round(.20*len(tail))) or longest(~supported)>16


def extension_lock(initial,proposed,dual,field,scale,stage):
    if blank_crossing(initial,proposed,dual):return 'BRIDGE_BLANK_SPAN'
    if stage=='S1':return None
    # Beyond a mature stem, a second dark line must pay its own extension cost.
    # Negative signed field over the extension indicates a displaced static trace.
    tail=proposed[len(initial):]
    if len(initial)>.18*scale and len(tail)>=8:
        increments=base.increments(field,proposed)[len(initial):]
        if increments.mean()<=0 and increments[-min(5,len(tail)):].mean()<=0:
            return 'STATIC_EXTENSION_COST'
    return None


def fork_from_entry(field,entry,dual,core,scale,band,offset):
    # Start at a measured mouth component. Permit a single small step to an
    # immediately supported fork. Restore a path beginning on the actual seed.
    span=min(len(field),round(.55*scale))
    if span<9 or not dual[:span].any():return None
    radius=min(4,max(1,round(.012*scale)))
    starts=np.zeros_like(entry)
    seeds=np.argwhere(entry)
    for x,y in seeds:
        if x+3>=span:continue
        for row in range(max(0,y-radius),min(field.shape[1],y+radius+1)):
            if dual[x+1:x+4,row].all() and core[x,min(y,row):max(y,row)+1].all():
                starts[x,row]=1
    if not starts.any():return None
    result=rescue(field,starts,dual,scale,band,offset)
    if result is None:return None
    path=result[0];x,y=path[0]
    roots=[int(ry) for rx,ry in seeds if rx==x and abs(ry-y)<=radius and core[x,min(ry,y):max(ry,y)+1].all()]
    if not roots:return None
    path[0,1]=min(roots,key=lambda row:abs(row-y))
    return result


def connected_competition(candidates,dual,delta,threshold,scale):
    ordinary=[c for c in candidates if not c[1]['promoted']]
    leader=max(ordinary,key=lambda c:c[1]['merit'])[0] if ordinary else None
    accepted=list(ordinary)
    for path,item in candidates:
        if not item['promoted']:continue
        x,y=path.T
        near=dual[x,y]
        # A promoted path must reach the first red run from its seed without
        # paying for a long, unsupported connection to a detached scratch.
        supported=longest(near)>=8 and near[:max(4,round(.025*scale))].any() and longest(~near)<=max(4,round(.025*scale))
        opposing=False
        if leader is not None:
            lx,ly=leader.T
            j=lx-x[0];inside=(j>=0)&(j<len(path))
            independent=np.ones(len(lx),bool)
            independent[inside]=abs(ly[inside]-y[j[inside]])>2
            blue=independent&(delta[lx,ly]<-threshold)
            opposing=longest(blue)>=3 and blue.sum()>np.sum(independent&dual[lx,ly])
        item['blue_competitor']=bool(opposing)
        if supported and (opposing or (leader is None and not item['fork_rescue'])):
            accepted.append((path,item))
        else:item['reason']='DETACHED_RESCUE' if not supported else 'NO_BLUE_COMPETITOR'
    return accepted

def local_recovery(path,values,back,direction,field,dual,core):
    """A nearby connected peak can survive a shallow one-column shift in the valley score."""
    x0,y0=path[-1]
    if len(path)<25:return path,None
    end=min(len(values)-1,x0+25)
    candidates=[]
    for x in range(x0+8,end):
        y=int(np.argmax(values[x]))
        value=values[x,y]
        if abs(y-y0)>15 or not np.isfinite(value) or value<max(values[x-1].max(),values[x+1].max()):continue
        alt=base.unwind(back,x,y,direction[x,y])
        if len(alt)<=len(path) or not np.array_equal(alt[:len(path)],path):continue
        tx,ty=alt[len(path):].T
        support=dual[tx,ty] | dual[tx,np.maximum(0,ty-1)] | dual[tx,np.minimum(dual.shape[1]-1,ty+1)]
        if support.sum()<6 or support.mean()<1/3 or longest(~support)>6 or core[tx,ty].mean()<.65:continue
        steps=base.increments(field,alt)[len(path):]
        rise=np.cumsum(steps);gain=float(rise[-1]-rise.min())
        if gain<1.5 or steps[-3:].min()<=0 or steps[-3:].mean()<.20:continue
        candidates.append((float(value),alt,dict(reason='SHORT_ATTACHED_PEAK',gain=gain,columns=len(tx))))
    if not candidates:return path,None
    _,best,details=candidates[-1]
    return best,details
