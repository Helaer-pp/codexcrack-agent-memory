"""Independent notch-lip lattices with image-scale normal evidence and optional dipole rejection."""
import cv2
import numpy as np
from research.notch_identity_v53.terminal import band_width
from research.notch_identity_v54 import terminal as clean
from research.notch_identity_v51 import terminal as base
from research.notch_identity_v40.evidence import offset_image
from . import native

STAGES=('branches','normal_bridge','v5_6')
global_free_end_dp=clean.global_free_end_dp

def prepare(raw,hint,scale,stage='v5_6'):
    # Historical paired-probe adapter. Only the constructed corridor sees these coordinates.
    pts=np.asarray(hint)+np.array([[0,-scale/2],[0,scale/2]])
    return native.prepare(raw,pts,stage)

def profiles(p,d,gray):
    threshold=max(2.7*p.noise,.030*p.span,1.)
    shape=d.shape
    fine=np.zeros(shape,bool);dip=np.zeros(shape,bool)
    raw_best=np.zeros(shape,np.float32);width=np.zeros(shape,np.float32)
    strength=np.zeros(shape,np.float32)
    radii=sorted(set(max(1,round(r*p.mouth_thickness)) for r in (.10,.20,.32)))
    for slope in (-.7,-.34,0.,.34,.7):
        den=np.hypot(1,slope)
        step=max(1,radii[0]);rise=round(step*slope)
        sm=(2*d+offset_image(d,step,rise)+offset_image(d,-step,-rise))*.25
        for rad in radii:
            nx,ny=round(-slope*rad/den),max(1,round(rad/den))
            a=offset_image(sm,nx,ny);b=offset_image(sm,-nx,-ny)
            ca=offset_image(gray,nx,ny);cb=offset_image(gray,-nx,-ny)
            core=np.maximum(0,np.minimum(ca,cb)-gray);raw_best=np.maximum(raw_best,core)
            prominence=sm-np.maximum(a,b)
            conf=(sm>1.25*threshold)&(prominence>threshold)&(prominence>.28*sm)
            update=conf & ((width==0)|(rad<width))
            width[update]=rad
            fine|=conf
            strength=np.maximum(strength,np.where(conf,prominence/threshold,0))
            blue=np.minimum(offset_image(sm,2*nx,2*ny),offset_image(sm,-2*nx,-2*ny))
            dip|=(sm>threshold)&(blue<-threshold)&(-blue>.48*sm)
    genuine=raw_best>max(3*p.noise,.035*p.span)
    stable=cv2.blur(cv2.dilate(genuine.astype('float32'),np.ones((3,1),np.uint8)),(7,1))>=.72
    dip&=~(genuine&stable)
    sustained=cv2.blur(cv2.dilate(fine.astype('float32'),np.ones((3,1),np.uint8)),(5,1))>=.62
    return (fine&sustained).T,dip.T,genuine.T,width.T,strength.T

def split_seeds(seeds):
    rows=np.flatnonzero(seeds.any(axis=0))
    if not len(rows):return []
    groups=list(np.split(rows,np.flatnonzero(np.diff(rows)>2)+1))
    while len(groups)>3:
        j=int(np.argmin([b[0]-a[-1] for a,b in zip(groups,groups[1:])]))
        groups[j:j+2]=[np.r_[groups[j],groups[j+1]]]
    if len(groups)==1 and len(rows)>=8:
        groups=list(np.array_split(rows,3 if len(rows)>=15 else 2))
    return groups

def predict(p,bonus=None,fixed=None,archive=None):
    d=dict(decision='NO_NOTCH',stop='NO_NOTCH',pick='NONE',branches=[],rejections={},events=[],trials=[])
    m=dict(status='no_tip',points=[],root=None,tip=None,diagnostics=dict(dual=d,candidates=[],selected=None,pairs=[]))
    if p is None:return m
    fixed_crop=None;shift=(0,0);quality=None
    if fixed is not None:fixed_crop,shift,quality=native.fixed_crop(p,fixed)
    from dataclasses import replace
    score,seeds,coarse,reg,source,_=base.fields(replace(p,stage='v5_1'),fixed_crop)
    org=p.native_origin+np.asarray(p.origin)+[p.front,0]
    if reg and reg.get('shift') is not None:
        dx,dy=reg['shift']
    else:dx=dy=0
    net_shift=[int(dx+shift[0]),int(dy+shift[1])]
    registration=dict(status='OK' if reg and reg.get('status')=='OK' else 'APPROXIMATE',shift=net_shift,ncc=(reg or {}).get('ncc',quality),source='NATIVE')
    d.update(decision=source,registration=registration,front=int(org[0]),optical_scale=p.scale,thickness=p.mouth_thickness,
             seed_band=seeds.shape[0],native_bounds=p.native_bounds,stop='NO_LEGAL_BRANCH')
    m['diagnostics']['coarse']=coarse
    gray=p.local[:,p.front:].astype(np.float32)
    diff=np.zeros_like(gray)
    if source=='JOINT':
        ref=cv2.warpAffine(fixed_crop[p.sl],np.float32([[1,0,dx+p.front],[0,1,dy]]),(gray.shape[1],len(gray)),
            flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
        diff=np.where(np.isfinite(ref),ref-gray,0.)
    fine,dip,core,width,strength=profiles(p,diff,gray)
    floor=max(3*p.noise,.032*p.span)
    wide=band_width(diff>floor).T>max(3.,.32*p.mouth_thickness)
    if source=='JOINT':
        # A broad opening with an actual sharp central valley remains admissible.
        near=max(1,round(.095*p.mouth_thickness))
        upper=offset_image(gray,0,near);lower=offset_image(gray,0,-near)
        sharp=(np.minimum(upper,lower)-gray).T>np.maximum(floor,.24*diff.T)
        wide&=~sharp
        fine&=~wide
        score[wide]=np.minimum(score[wide],.0)
        # A displaced pre-existing dark stroke is ineligible for a differential lift.
        refdepth=base.bilateral(-np.where(np.isfinite(ref),ref,gray),p.scale)
        old=cv2.dilate(cv2.blur(refdepth,(max(1,round(.3*p.mouth_thickness)),1)),
            np.ones((2*max(2,round(.48*p.mouth_thickness))+1,3),np.uint8))
        fine&=(old.T<np.maximum(4*p.noise,.43*np.maximum(diff.T,floor)))
    # Reject a forked hollow opening when its front consists of separated, thick dark walls.
    body_local=p.body_root-p.native_origin
    slit_votes=0
    for lag in (1,2,3,4):
        col=int(np.clip(body_local[0]-lag,0,p.raw.shape[1]-1))
        rr=int(max(28,4*p.mouth_thickness));cy=int(body_local[1])
        dark=p.raw[max(0,cy-rr):min(len(p.raw),cy+rr+1),col]<p.black+.28*p.span
        edge=np.flatnonzero(np.diff(np.r_[False,dark,False]))
        runs=[(a,b) for a,b in zip(edge[::2],edge[1::2]) if b-a>=max(2,.15*p.mouth_thickness)]
        if any(hi[0]-lo[1]>max(2,.35*p.mouth_thickness) for lo,hi in zip(runs,runs[1:])):slit_votes+=1
    if slit_votes>=2:
        d['stop']='OPEN_FORK';return m
    if source=='JOINT':
        # Snap incremental entry pixels to the observed body boundary before grouping roots.
        depth=max(3,round(.42*p.mouth_thickness))
        left=p.local[:,max(0,p.front-depth):p.front+1]
        adjacent=(left<p.black+.32*p.span).any(axis=1)
        adjacent=cv2.dilate(adjacent[:,None].astype('uint8'),np.ones((3,1),np.uint8)).ravel()>0
        near_rows=abs(np.arange(len(adjacent))-np.median(np.array(p.starts)[:,1]))<2.2*p.mouth_thickness
        for k in range(min(3,len(seeds))):
            born=(core[k]&fine[k]&adjacent&near_rows)&(diff[:,k]>floor)
            seeds[k,born]=1
    groups=split_seeds(seeds);centres=[np.median(q) for q in groups]
    common=score.copy()
    if p.stage=='v5_6' and source=='JOINT':
        common[dip]=np.minimum(common[dip],-.70)
    # Only the corridor uses anchor direction. All candidate distances and debts below use image morphology.
    mid=np.median(np.asarray(p.starts)[:,1])
    xx,yy=np.ogrid[:len(score),:score.shape[1]]
    axis=mid+xx*p.normal[1]/max(.10,p.normal[0])
    outside=abs(yy-axis)>(max(35,4*p.mouth_thickness)+.20*xx)
    common[outside]=-50.
    best=-np.inf;winner=None;candidates=[]
    for j,group in enumerate(groups):
        start=np.zeros_like(seeds);start[:,group]=seeds[:,group]
        field=common.copy()
        if len(groups)>1:
            # Other entrances cannot be used by this channel within the contact zone.
            boundary=min(len(field),max(4,round(p.mouth_thickness)))
            ownership=np.argmin(abs(np.arange(score.shape[1])[:,None]-centres),axis=1)
            field[:boundary,ownership!=j]=-50.
        birth=max(6,round(1.7*p.mouth_thickness))
        witness=np.any((core[:birth]&fine[:birth])[:,max(0,int(group.min())-2):int(group.max())+3])
        basepath,bv,V,B,D=clean.lattice(field,start,p.scale*3,False)
        bridge=False
        if source=='JOINT' and witness and p.stage!='branches' and len(basepath):
            eligible=fine & (~dip if p.stage=='v5_6' else True) & ~outside
            boosted=field.copy()
            mask=eligible & (field>-30)
            boosted[mask]=np.maximum(boosted[mask],np.minimum(.94,.15+.20*strength[mask]))
            path,value,V2,B2,D2=clean.lattice(boosted,start,p.scale*3,False)
            if len(path) and path[-1,0]>basepath[-1,0]:
                extra=path[:,0]>basepath[-1,0]
                ok=(eligible[path[extra,0],path[extra,1]].mean()>=.30 and clean.increments(boosted,path)[extra].mean()>0)
            else:ok=True
            if ok and len(path):
                field,basepath,bv,V,B,D=boosted,path,value,V2,B2,D2;bridge=True
        path=basepath;value=bv
        if len(path)<2:continue
        x,y=path.T
        # Consider downstream cumulative local maxima only inside this same branch's predecessor table.
        if source=='JOINT' and p.stage!='branches' and witness:
            lo=x[-1]+max(4,round(.4*p.mouth_thickness));hi=min(len(field),x[-1]+max(28,round(4*p.mouth_thickness)))
            if lo<hi:
                v=V[lo-1:min(len(V),hi+1)];region=V[lo:hi]
                xs,ys=np.where((region>=cv2.dilate(v,np.ones((3,3),np.uint8))[1:1+hi-lo])&(region>.64*bv)&(field[lo:hi]>.08))
                for h in np.lexsort((-region[xs,ys],-xs)):
                    ax=xs[h]+lo;ay=ys[h];alt=clean.unwind(B,ax,ay,D[ax,ay])
                    k=int(x[-1]-alt[0,0])
                    if k<0 or abs(alt[k,1]-y[-1])>max(2,.18*p.mouth_thickness):continue
                    ex=alt[k+1:];ef=fine[ex[:,0],ex[:,1]]
                    if p.stage=='v5_6':ef=ef&~dip[ex[:,0],ex[:,1]]
                    net=clean.increments(field,alt)[k+1:]
                    if ef.mean()<.30 or net.mean()<=0:continue
                    path=alt;x,y=path.T;value=float(V[ax,ay]);break
        good=(core[x,y] & (field[x,y]>.08) & ~wide[x,y])
        used=fine[x,y] & (~dip[x,y] if p.stage=='v5_6' else True)
        clear=used|good;paired=used&good
        rr=max(3,int(round(p.mouth_thickness*.32)))
        tail=float(np.mean(clear[-rr:]));joint=float(paired.mean())
        phys=float(.55*clear.sum()+.85*paired.sum()+tail*rr+.85*value)
        threshold=max(3.,p.scale*.040);reason='VALID'
        if value<=threshold or len(path)<max(4,round(.40*p.mouth_thickness)):reason='LOW_SUPPORT'
        elif clean.topology.check(p.local,path+[p.front,0],p.front,p.scale,True)=='CLOSED_RIM':reason='CLOSED_RIM'
        elif source=='PREEXISTING_CHECK':
            strong=(field[x,y]>.10)&(x>1)
            slices=np.flatnonzero(np.diff(np.r_[False,strong[:birth*2],False]))
            if max((b-a for a,b in zip(slices[::2],slices[1::2])),default=0)<max(4,round(.48*p.mouth_thickness)):reason='NO_CONFIRMED_PREEXISTING'
        elif source=='JOINT' and len(x)>=4 and np.any(
                (gray[y[:3],x[:3]]>p.black+.78*p.span)&(np.abs(diff[y[:3],x[:3]])<floor*.55)&~core[x[:3],y[:3]]) and not np.any(fine[x[:2],y[:2]]):
            reason='DETACHED_START'
        elif source=='JOINT' and (wide[x,y].mean()>.52 or (len(x)<1.0*p.mouth_thickness and np.mean(used[-rr:]&good[-rr:])<.5)):
            reason='BROAD_OR_SHORT_EDGE'
        elif source=='JOINT' and (clear.sum()<max(3,round(.5*p.mouth_thickness)) or (joint<.08 and tail<.5)):
            reason='DIFFUSE_OR_DETACHED'
        item=dict(id=j,seed_rows=[int(group.min()),int(group.max())],root=(path[0]+org).tolist(),tip=(path[-1]+org).tolist(),
                  value=float(value),merit=phys,net_length=int(clear.sum()),joint_fraction=joint,tail=tail,bridge=bridge,reason=reason)
        d['branches'].append(item)
        if archive is not None:candidates.append((j,V.max(axis=1)))
        if reason=='VALID' and phys>best:
            best=phys;winner=(path.copy(),item)
    if archive is not None:
        archive.update(origin=org,branch_ids=np.array([j for j,_ in candidates],int),curves=np.array([v for _,v in candidates],np.float32))
    if winner is None:return m
    path,item=winner;pts=(path+org).tolist()
    d.update(stop='ACCEPTED_PEAK',pick='BRANCH_'+str(item['id']),peak=pts[-1],score=item['value'])
    m.update(status='VALID',root=pts[0],tip=pts[-1],points=pts)
    m['diagnostics'].update(selected=0,candidates=[dict(start=pts[0],tip=pts[-1],trace=dict(gate=source,stop=d['stop'],reference=registration))])
    return m
