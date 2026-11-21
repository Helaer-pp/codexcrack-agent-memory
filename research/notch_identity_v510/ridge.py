"""Evidence on disjoint branches and a forward bridge ending at an observed downstream peak."""
import cv2
import numpy as np
from research.notch_identity_v54 import terminal as dp


def longest(mask):
    edges=np.flatnonzero(np.diff(np.r_[False,mask,False]))
    return int(max((b-a for a,b in zip(edges[::2],edges[1::2])),default=0))


def signed_difference(p,fixed,shift):
    dx,dy=shift
    gray=p.local[:,p.front:].astype(np.float32)
    matrix=np.float32([[1,0,dx+p.front],[0,1,dy]])
    mapped=cv2.warpAffine(fixed[p.sl],matrix,(gray.shape[1],len(gray)),
        flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
    return np.nan_to_num(mapped-gray,nan=0.).T


def prefer_active(candidates,red,delta,threshold):
    """Only evidence outside shared paths can change the published branch."""
    for path,item in candidates:
        x,y=path.T
        unique=np.ones(len(path),bool)
        for other,_ in candidates:
            if other is path:continue
            j=x-other[0,0]
            overlap=(j>=0)&(j<len(other))
            unique[overlap]&=np.abs(y[overlap]-other[j[overlap],1])>2
        values=delta[x,y]/threshold
        hit=unique & red[x,y] & (values>1)
        cols=int(hit.sum())
        gain=float(np.clip(values[hit]-1,0,3).sum())
        avg=float(values[unique].mean()) if unique.any() else 0.
        run=longest(hit)
        item['activity']=dict(columns=cols,run=run,gain=gain,mean=avg,
            active=cols>=4 and run>=3 and gain>=6 and avg>0,
            inactive=bool(unique.any() and (cols<=2 or avg<=0)))
    if not (any(b['activity']['active'] for _,b in candidates) and any(b['activity']['inactive'] for _,b in candidates)):
        return False
    for _,b in candidates:
        a=b['activity']
        b['merit']=float(b['merit']*(.35 if a['inactive'] else 1.)+(2*a['columns']+.65*a['gain'] if a['active'] else 0))
    return True


def middle_bridge(p,field,path,fine,core,strength,excluded,band):
    x,y=path.T
    witness=int((fine[x,y]&core[x,y]&(x<=x[0]+max(5,round(.1*p.scale)))).sum())
    info=dict(accepted=False,witness=witness,reason='NO_ATTACHED_SUPPORT')
    if witness<2:return path,info
    x0,y0=map(int,path[-1])
    n=min(len(field)-x0,max(24,round(.52*p.scale)))
    if n<=15:return path,dict(info,reason='SHORT_DOMAIN')
    radius=max(8,round(.13*p.scale))
    lo=max(0,y0-radius);hi=min(field.shape[1],y0+radius+1)
    sl=np.s_[x0:x0+n,lo:hi]
    f=field[sl];hit=fine[sl];v=strength[sl]
    row=np.arange(lo,hi)+p.origin[1];margin=max(3,round(.035*p.scale))
    safe=(row>=band[0]+margin)&(row<band[1]-margin)
    lifted=np.where(hit,np.maximum(f,np.minimum(1.3,.30+.35*v)),
        np.where(core[sl],np.clip(f,-.14,.12),np.minimum(f,-.38)))
    lifted=np.where(np.isfinite(f)&~excluded[sl]&safe[None,:],lifted,-np.inf).astype(np.float32)
    start=np.zeros((1,hi-lo),np.uint8);start[0,y0-lo]=1
    if not safe[y0-lo]:return path,dict(info,reason='EDGE_START')
    lifted[0,:]=0.
    tail,*_=dp.lattice(lifted,start,p.scale,False)
    if len(tail)<=15:return path,dict(info,reason='SHORT_RIDGE',proposed=len(tail)-1)
    tx,ty=tail.T
    raw=dp.increments(f,tail);raw[0]=0
    curve=np.cumsum(raw)
    ranked=[]
    for j in range(15,len(tail)):
        # Demand a separate rising segment in the original field and a local crest.
        if (j+1<len(tail) and curve[j+1]>curve[j]) or raw[j]<=0:continue
        bottom=int(np.argmin(curve[:j+1]))
        if bottom<2 or j-bottom<4 or curve[j]-curve[bottom]<2.0:continue
        if raw[j-2:j+1].mean()<=.08:continue
        mask=hit[tx[1:j+1],ty[1:j+1]]
        if mask.mean()<.30 or longest(mask)<6:continue
        # A maximum at the search boundary is censored; require a fall ahead in the raw field.
        col=int(tx[j]);yy=int(ty[j]);after=f[col+1:col+4,max(0,yy-1):yy+2]
        if len(after)<3 or np.max(after,axis=1).mean()>=np.mean(f[tx[j-2:j+1],ty[j-2:j+1]]):continue
        net=float(dp.increments(lifted,tail[:j+1])[1:].mean())
        if net>0:ranked.append((curve[j]-curve[bottom],j,net,float(mask.mean()),longest(mask)))
    if not ranked:return path,dict(info,reason='NO_INDEPENDENT_RISE',proposed=len(tail)-1)
    gain,j,net,fraction,run=max(ranked)
    return np.vstack((path,tail[1:j+1]+[x0,lo])),dict(info,accepted=True,reason='DOWNSTREAM_RISE',
        columns=j,gain=float(gain),mean_net=net,fine_fraction=fraction,continuous=run)
