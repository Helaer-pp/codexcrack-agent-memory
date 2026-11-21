"""Stateless image evidence. No paths, group names, frame identifiers or annotation input."""
import math
import cv2
import numpy as np
from skimage.morphology import skeletonize
from numba import njit
from .config import CONFIG,validate

NORMALS=[(0,1),(1,0),(1,1),(1,-1)]
DIRECTIONS=[(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]
FEATURE_NAMES=['pixels','span','median_valley','support_fraction','median_gray','median_scale','coherence',
               'fixed_fraction','fixed_delta','prev_fraction','prev_delta','start_x','start_y','end_x','end_y']

def ordered_points(p,shape):
    try:q=np.asarray(p,dtype=float)
    except (ValueError,TypeError):return None
    if q.shape!=(2,2) or not np.isfinite(q).all():return None
    h,w=shape
    if (q[:,0]<0).any() or (q[:,0]>=w).any() or (q[:,1]<0).any() or (q[:,1]>=h).any() or np.linalg.norm(q[1]-q[0])<20:return None
    return q[np.argsort(q[:,1],kind='stable')]

def scene_geometry(image,points,fixed,fixed_points,fallback,c):
    p=ordered_points(points,image.shape);observed=p is not None
    if p is None:p=ordered_points(fallback,image.shape)
    if p is None:p=ordered_points(fixed_points,image.shape)
    if p is None:raise ValueError('GEOMETRY: no usable current or historical P geometry')
    h,w=image.shape;scale=float(np.linalg.norm(p[1]-p[0]));mid=p.mean(0)
    xa=max(0,int(math.floor(min(p[:,0])-c['safe_left_margin']*scale)))
    ya=max(0,int(math.floor(min(p[:,1])-c['safe_y_margin']*scale)))
    xb=w;yb=min(h,int(math.ceil(max(p[:,1])+c['safe_y_margin']*scale))+1)
    if xb-xa<20 or yb-ya<20:raise ValueError('GEOMETRY: empty safe search area')
    rp=ordered_points(fixed_points,fixed.shape) if fixed is not None else None
    root=None;root_region=None;root_options=[]
    if rp is not None:
        d=float(np.linalg.norm(rp[1]-rp[0]));rm=rp.mean(0)
        x0=max(0,int(min(rp[:,0])-.8*d));x1=min(fixed.shape[1],int(max(rp[:,0])+1.2*d))
        y0=max(0,int(min(rp[:,1])+2));y1=min(fixed.shape[0],int(max(rp[:,1])-1))
        slab=(fixed[y0:y1,x0:x1]<c['notch_black']).astype(np.uint8)
        n,cc,stats,centers=cv2.connectedComponentsWithStats(slab,8)
        for k in range(1,n):
            xx,yy,ww,hh,area=map(int,stats[k]);cy=centers[k,1]+y0
            if xx>2 or ww<c['notch_min_width'] or abs(cy-rm[1])>.35*d:continue
            counts=(cc==k).sum(0);thick=np.flatnonzero(counts>=max(5,int(.025*d)))
            if not len(thick):continue
            end=int(thick[-1]);ys=np.flatnonzero(cc[:,end]==k)
            if not len(ys):continue
            pt=np.array([x0+end,y0+float(np.median(ys))]);delta=p.mean(0)-rp.mean(0);cur=pt+delta
            root_options.append(dict(point=cur.tolist(),reference_point=pt.tolist(),area=area,vertical_distance=abs(cy-rm[1]),bounds=[x0+xx,y0+yy,x0+xx+ww,y0+yy+hh]))
        if root_options:
            best=sorted(root_options,key=lambda z:(z['vertical_distance'],-z['area'],z['point'][0]))[0]
            root=best['point'];root_region=best['bounds']
    anchor=np.array(root if root is not None else mid,dtype=float)
    extent=max(24.,c['origin_extent']*scale)
    origin=[max(xa,anchor[0]-extent),max(ya,anchor[1]-.45*scale),min(xb-1,anchor[0]+extent),min(yb-1,anchor[1]+.45*scale)]
    return dict(bounds=[xa,ya,xb,yb],points_geometry=p.tolist(),points_observed=observed,scale=scale,center=mid.tolist(),
                root=root,root_region_reference=root_region,root_options=root_options,root_confidence='IMAGE_HYPOTHESIS' if root else 'UNVERIFIED_GEOMETRIC_ZONE',
                origin_zone=origin,direction=[1.,0.],physical_notch_certified=False)

def shifted(a,dx,dy):
    b=np.roll(a,(dy,dx),(0,1))
    if dy>0:b[:dy]=0
    elif dy<0:b[dy:]=0
    if dx>0:b[:,:dx]=0
    elif dx<0:b[:,dx:]=0
    return b

def raw_valleys(raw,c):
    image=raw.astype(np.float32);response=np.zeros_like(image);scale=np.zeros(raw.shape,np.uint8);normal=np.zeros(raw.shape,np.uint8);flank=np.zeros_like(image)
    # Smoothed derivatives estimate orientation only; all depths and pixels below remain RAW.
    smooth=cv2.GaussianBlur(image,(0,0),c['orientation_sigma'])
    xx=cv2.Sobel(smooth,cv2.CV_32F,2,0,ksize=3);yy=cv2.Sobel(smooth,cv2.CV_32F,0,2,ksize=3);xy=cv2.Sobel(smooth,cv2.CV_32F,1,1,ksize=3)
    disc=np.sqrt((xx-yy)**2+4*xy**2);major=(xx+yy+disc)*.5;minor=(xx+yy-disc)*.5
    angle=.5*np.arctan2(2*xy,xx-yy)
    affinity=np.stack([np.abs(np.cos(angle)*nx+np.sin(angle)*ny)/math.hypot(nx,ny) for nx,ny in NORMALS])
    chosen=np.argmax(affinity,axis=0);linear=(major>0)&(major>=c['linearity_min']*np.abs(minor))
    for k in c['normal_offsets']:
        for j,(nx,ny) in enumerate(NORMALS):
            side=np.minimum(shifted(image,k*nx,k*ny),shifted(image,-k*nx,-k*ny))
            depth=np.maximum(side-image,0)
            local=(depth>=shifted(depth,nx,ny))&(depth>=shifted(depth,-nx,-ny))
            better=(depth>response)&local&(side>=c['material_min'])&(chosen==j)&linear
            response[better]=depth[better];scale[better]=k;normal[better]=j;flank[better]=side[better]
    residue=image-cv2.medianBlur(raw,3).astype(np.float32)
    material=image>=c['material_min'];sample=residue[material][::7]
    noise=max(.5,float(np.median(np.abs(sample-np.median(sample)))*1.4826)) if sample.size else 1.
    threshold=float(np.clip(c['noise_factor']*noise,c['weak_min'],c['weak_max']))
    ridge=response>=threshold
    border=max(c['normal_offsets'])+1;ridge[:border]=False;ridge[-border:]=False;ridge[:,:border]=False;ridge[:,-border:]=False
    return response,scale,normal,flank,noise,threshold,ridge

def correlation(a,b):
    x=a.astype(np.float64).ravel();y=b.astype(np.float64).ravel();x=x-x.mean();y=y-y.mean()
    den=np.linalg.norm(x)*np.linalg.norm(y);return float(x@y/den) if den>1e-7 else 0.

def register_reference(reference,current,reference_points,current_points,scene,c):
    xa,ya,xb,yb=scene['bounds'];raw=current[ya:yb,xa:xb].astype(np.float32);shape=raw.shape
    missing=dict(aligned=np.full(shape,np.nan,np.float32),signed=np.full(shape,np.nan,np.float32),confidence=np.zeros(shape,np.float32),valid=np.zeros(shape,bool))
    if reference is None:return missing,dict(status='UNAVAILABLE',reason='NO_ACTUAL_PREVIOUS_FRAME',windows=[],valid_fraction=0.,budget_exhausted=False)
    rp=ordered_points(reference_points,reference.shape);cp=ordered_points(current_points,current.shape)
    if rp is None or cp is None:return missing,dict(status='UNAVAILABLE',reason='P_GEOMETRY_UNAVAILABLE',windows=[],valid_fraction=0.,budget_exhausted=False)
    Y,X=np.mgrid[ya:yb,xa:xb].astype(np.float32);den=max(1.,cp[1,1]-cp[0,1]);alpha=np.clip((Y-cp[0,1])/den,0,1);delta=cp-rp
    mx=X-((1-alpha)*delta[0,0]+alpha*delta[1,0]);my=Y-((1-alpha)*delta[0,1]+alpha*delta[1,1])
    coarse=cv2.remap(reference,mx.astype(np.float32),my.astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT).astype(np.float32)
    warp=(mx>=0)&(my>=0)&(mx<reference.shape[1]-1)&(my<reference.shape[0]-1)
    quality=np.zeros(shape,np.float32);correction_x=np.zeros(shape,np.float32);correction_y=np.zeros(shape,np.float32)
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
            legal=warp[y-radius:y+hh+radius,x-radius:x+width+radius].all()
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
            frac=np.clip((Y[:,x:x+width]-sides[0]['bounds'][1])/max(1,sides[1]['bounds'][1]-sides[0]['bounds'][1]),0,1)
            correction_x[:,x:x+width]=(1-frac)*sides[0]['shift'][0]+frac*sides[1]['shift'][0]
            correction_y[:,x:x+width]=(1-frac)*sides[0]['shift'][1]+frac*sides[1]['shift'][1]
            quality[:,x:x+width]=min(s['holdout_ncc'] for s in sides)
        windows.append(dict(x0=x+xa,x1=x+xa+width,sides=sides,trusted=valid))
    mx=(mx+correction_x).astype(np.float32);my=(my+correction_y).astype(np.float32)
    geometric=(mx>=0)&(my>=0)&(mx<reference.shape[1]-1)&(my<reference.shape[0]-1)
    aligned=cv2.remap(reference,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT).astype(np.float32);aligned[~geometric]=np.nan
    trusted=(quality>0)&geometric;quality[~trusted]=0;signed=aligned-raw
    # Signed diagnostic is retained even when not trusted. Unavailable inference values are NaN.
    return dict(aligned=aligned,signed=signed,confidence=quality,valid=trusted),dict(status='AVAILABLE' if trusted.any() else 'UNAVAILABLE',reason='LOCAL_TEXTURE_PROXY_NOT_PHYSICAL_CERTIFICATION' if trusted.any() else 'NO_TRUSTED_LOCAL_WINDOW',windows=windows,valid_fraction=float(trusted.mean()),budget_exhausted=exhausted)

def split_skeleton(skel,offset,c):
    ys,xs=np.nonzero(skel);n=len(xs)
    if n>c['max_skeleton_pixels']:return np.empty((0,2),np.int32),np.array([0],np.int32),[],dict(skeleton_pixels=n,budget_exhausted=True,reason='SKELETON_PIXEL_BUDGET')
    lookup=np.full((skel.shape[0]+2,skel.shape[1]+2),-1,np.int32);lookup[ys+1,xs+1]=np.arange(n,dtype=np.int32)
    adj=np.stack([lookup[ys+1+dy,xs+1+dx] for dx,dy in DIRECTIONS],axis=1) if n else np.empty((0,8),np.int32)
    degree=(adj>=0).sum(1);visited=np.zeros((n,8),bool);chains=[];cyclic=[];budget=False
    starts=list(np.flatnonzero(degree!=2))+list(np.flatnonzero(degree==2))
    for seed in starts:
        if degree[seed]==0:chains.append([int(seed)]);cyclic.append(False)
        for direction in range(8):
            if adj[seed,direction]<0 or visited[seed,direction]:continue
            chain=[int(seed)];at=int(seed);step=direction;closed=False
            while True:
                other=int(adj[at,step]);visited[at,step]=True;visited[other,7-step]=True;chain.append(other)
                if other==seed:closed=True;break
                if degree[other]!=2:break
                choices=np.flatnonzero((adj[other]>=0)&(adj[other]!=at))
                if not len(choices):break
                at=other;step=int(choices[0])
                if visited[at,step]:break
            chains.append(chain);cyclic.append(closed)
        if len(chains)>c['max_segments']:budget=True;break
    flat=[];ptr=[0]
    for chain in chains:
        flat.extend([[int(xs[i]+offset[0]),int(ys[i]+offset[1])] for i in chain]);ptr.append(len(flat))
    return np.asarray(flat,np.int32).reshape(-1,2),np.asarray(ptr,np.int32),cyclic,dict(skeleton_pixels=n,budget_exhausted=budget,reason='SEGMENT_BUDGET' if budget else None)

@njit(cache=True)
def _statistics(xy,ptr,raw,valley,scale,fvalid,fsigned,pvalid,psigned,xa,ya,threshold):
    features=np.empty((len(ptr)-1,15),np.float32)
    for k in range(len(ptr)-1):
        p=xy[ptr[k]:ptr[k+1]];x=p[:,0]-xa;y=p[:,1]-ya;n=len(p)
        displacement=math.hypot(float(p[-1,0]-p[0,0]),float(p[-1,1]-p[0,1]));arc=0.;supported=0
        depths=np.empty(n,np.float32);grays=np.empty(n,np.float32);scales=np.empty(n,np.float32)
        fv=np.empty(n,np.float32);pv=np.empty(n,np.float32);nf=0;npv=0
        for i in range(n):
            xx=int(x[i]);yy=int(y[i]);y0=max(0,yy-12);y1=min(raw.shape[0]-1,yy+12)
            depths[i]=valley[yy,xx];grays[i]=raw[yy,xx];scales[i]=scale[yy,xx];supported+=depths[i]>=threshold
            if i:arc+=math.hypot(float(p[i,0]-p[i-1,0]),float(p[i,1]-p[i-1,1]))
            if fvalid[yy,xx] and fvalid[y0,xx] and fvalid[y1,xx]:
                v=fsigned[yy,xx]-.5*(fsigned[y0,xx]+fsigned[y1,xx])
                if np.isfinite(v):fv[nf]=v;nf+=1
            if pvalid[yy,xx] and pvalid[y0,xx] and pvalid[y1,xx]:
                v=psigned[yy,xx]-.5*(psigned[y0,xx]+psigned[y1,xx])
                if np.isfinite(v):pv[npv]=v;npv+=1
        features[k,0]=n;features[k,1]=displacement;features[k,2]=np.median(depths);features[k,3]=supported/n
        features[k,4]=np.median(grays);features[k,5]=np.median(scales);features[k,6]=displacement/max(1.,arc)
        features[k,7]=nf/n;features[k,8]=np.median(fv[:nf]) if nf else np.nan
        features[k,9]=npv/n;features[k,10]=np.median(pv[:npv]) if npv else np.nan
        features[k,11]=p[0,0];features[k,12]=p[0,1];features[k,13]=p[-1,0];features[k,14]=p[-1,1]
    return features

def segment_statistics(xy,ptr,raw,valley,scale,fixed,prev,scene,threshold):
    return _statistics(xy,ptr,raw,valley,scale,fixed['valid'],fixed['signed'],prev['valid'],prev['signed'],scene['bounds'][0],scene['bounds'][1],threshold)

def prepare(current,points,fixed,fixed_points,previous=None,previous_points=None,fallback_points=None,config=None):
    c=CONFIG if config is None else config;validate(c)
    if not isinstance(current,np.ndarray) or current.dtype!=np.uint8 or current.ndim!=2:raise ValueError('INPUT: original uint8 grayscale required')
    if fixed is not None and (fixed.dtype!=np.uint8 or fixed.ndim!=2):raise ValueError('INPUT: invalid fixed reference')
    scene=scene_geometry(current,points,fixed,fixed_points,fallback_points,c);xa,ya,xb,yb=scene['bounds'];raw=current[ya:yb,xa:xb].copy()
    if raw.size>c['max_roi_pixels']:raise ValueError('BUDGET: SAFE_ROI_PIXEL_BUDGET')
    valley,scale,normal,background,noise,threshold,ridge=raw_valleys(raw,c)
    fixed_data,fixed_info=register_reference(fixed,current,fixed_points,points,scene,c)
    prev_data,prev_info=register_reference(previous,current,previous_points,points,scene,c)
    skel=skeletonize(ridge)
    count,components,stats,_=cv2.connectedComponentsWithStats(skel.astype(np.uint8),8)
    sy,sx=np.nonzero(skel);cid=components[sy,sx];tot=np.bincount(cid,minlength=count).astype(float)
    denom=np.maximum(tot,1);mx=np.bincount(cid,weights=sx,minlength=count)/denom;my=np.bincount(cid,weights=sy,minlength=count)/denom
    vx=np.bincount(cid,weights=sx.astype(float)**2,minlength=count)/denom-mx**2
    vy=np.bincount(cid,weights=sy.astype(float)**2,minlength=count)/denom-my**2
    cov=np.bincount(cid,weights=sx.astype(float)*sy,minlength=count)/denom-mx*my
    disc=np.sqrt(np.maximum(0,(vx-vy)**2+4*cov**2));linearity=(vx+vy+disc)/np.maximum(1.,vx+vy-disc)
    structure=(tot>=c['min_component_pixels'])&(np.maximum(stats[:,2],stats[:,3])>=8)&(linearity>=c['component_linearity']);structure[0]=False
    xy,ptr,cyclic,counts=split_skeleton(skel,[xa,ya],c)
    features=segment_statistics(xy,ptr,raw,valley,scale,fixed_data,prev_data,scene,threshold)
    component_ids=components[xy[ptr[:-1],1]-ya,xy[ptr[:-1],0]-xa] if len(ptr)>1 else np.array([],np.int32)
    return dict(scene=scene,raw=raw,valley=valley,scale=scale,normal=normal,background=background,threshold=threshold,noise=noise,
                xy=xy,ptr=ptr,cyclic=cyclic,features=features,component_ids=component_ids,component_structure=structure,component_stats=np.column_stack([tot,linearity,stats[:,2],stats[:,3]]),fixed=fixed_data,prev=prev_data,reference_info=dict(fixed=fixed_info,prev=prev_info),
                counts={**counts,'raw_ridge_pixels':int(ridge.sum()),'segments':len(ptr)-1,'safe_pixels':raw.size},
                opening_proxy=opening_projection(scene['points_geometry'],fixed_points,current.shape))


def opening_projection(points,fixed_points,shape):
    a=ordered_points(fixed_points,shape);b=ordered_points(points,shape)
    if a is None or b is None:return None
    axis=a[1]-a[0];axis=axis/np.linalg.norm(axis)
    return float(np.dot((b[1]-b[0])-(a[1]-a[0]),axis))
