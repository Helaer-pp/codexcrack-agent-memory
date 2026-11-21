"""Reference registration and narrow, orientation-selective incremental evidence."""
import cv2
import numpy as np
from research.notch_identity_v31.detector import px
from research.notch_identity_v33.reference import Support as Registration
from research.notch_identity_v35.reference import contour

def offset_image(im,dx,dy):
    h,w=im.shape
    pad=cv2.copyMakeBorder(im,max(-dy,0),max(dy,0),max(-dx,0),max(dx,0),cv2.BORDER_REPLICATE)
    x=max(dx,0);y=max(dy,0)
    return pad[y:y+h,x:x+w]

def registered(p,fixed):
    sl,origin,starts,_,_,s,front,gray,noise,_,raw,span=p
    center=np.median(starts,axis=0)
    reg=Registration(raw,fixed,sl,origin,center,s,noise,span)
    if reg.coarse['status']!='OK':
        c=contour(raw,fixed,center+origin,s,noise,span)
        if c:reg.coarse=c
    if reg.coarse['status']!='OK':return reg.coarse,{},None
    # Use one off-crack flank measurement ahead of the mouth. Both stages map
    # from the current grid into the already geometrically remapped reference.
    local=reg.local(min(gray.shape[1]-1,front+px(s,.24)),round(center[1]))
    shift=local['shift'] if local['status']=='OK' else reg.coarse['shift']
    local=dict(local,shift=shift,source='FINE' if local['status']=='OK' else reg.coarse['anchor'])
    f=cv2.warpAffine(fixed[sl],np.float32([[1,0,shift[0]],[0,1,shift[1]]]),(gray.shape[1],gray.shape[0]),
        flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
    return reg.coarse,local,f

def make(p,fixed):
    _,_,starts,_,_,s,_,gray,noise,_,_,span=p
    coarse,reg,aligned=registered(p,fixed)
    if aligned is None:return None,coarse,reg
    mid=int(np.median(np.array(starts)[:,1]));pad=px(s,.28)
    top=max(0,mid-pad);bottom=min(len(gray),mid+pad+1)
    cur=gray[top:bottom].astype(np.float32);f=aligned[top:bottom]
    valid=np.isfinite(f)
    f=np.where(valid,f,cur)
    diff=f-cur
    # Local noise estimate from signed high-frequency residuals, sampled off-axis.
    high=diff-cv2.medianBlur(diff,3)
    flank=high[::max(1,px(s,.015)),::max(1,px(s,.015))]
    floor=max(.012*span,2.8*float(np.median(np.abs(flank-np.median(flank)))),1.5*noise)
    radii=sorted({px(s,fraction) for fraction in (.007,.014,.024)})
    reach=px(s,.025);kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*reach+1,2*reach+1))
    gx=cv2.Sobel(diff,cv2.CV_32F,1,0)
    gy=cv2.Sobel(diff,cv2.CV_32F,0,1)
    side=2*px(s,.009)+1
    norm=cv2.blur(gx*gx+gy*gy,(side,side))
    orientation=cv2.blur(gy*gy-gx*gx,(side,side))/np.maximum(norm,floor*floor)
    energies=[];depths=[];templates=[]
    for angle in (-.52,0.,.52):
        tx,ty=np.cos(angle),np.sin(angle)
        k=px(s,.009)
        def smooth(im):
            dx,dy=round(k*tx),round(k*ty)
            return .25*(offset_image(im,dx,dy)+2*im+offset_image(im,-dx,-dy))
        sd=smooth(diff);sf=smooth(f);sc=smooth(cur)
        def sides(im,r):
            dx,dy=round(-ty*r),round(tx*r)
            return offset_image(im,dx,dy),offset_image(im,-dx,-dy)
        valleys=[];fixed_valleys=[];current_valleys=[]
        for r in radii:
            a,b=sides(sd,r);valleys.append(np.maximum(sd-np.maximum(a,b),0))
            a,b=sides(sf,r);fixed_valleys.append(np.maximum(np.minimum(a,b)-sf,0))
            a,b=sides(sc,r);current_valleys.append(np.maximum(np.minimum(a,b)-sc,0))
        strength=np.maximum.reduce(valleys)
        # Signed normal energies relative to flanks remove broad illumination offsets.
        r=px(s,.014);a,b=sides(sd,r);base=.5*(a+b)
        positive=np.zeros_like(sd);negative=np.zeros_like(sd)
        for j in range(-r,r+1):
            d=offset_image(sd,round(-ty*j),round(tx*j))-base
            positive+=np.maximum(d-noise*.5,0)
            negative+=np.maximum(-d-noise*.5,0)
        energies.append(strength*np.clip(1-negative/np.maximum(positive,floor),0,1))
        depths.append(np.maximum.reduce(current_valleys));templates.append(np.maximum.reduce(fixed_valleys))
    fixed_max=np.maximum.reduce(templates)
    energy=np.zeros_like(cur);clear=np.ones_like(cur)
    for e,depth,template in zip(energies,depths,templates):
        # Compare tangent-coherent valley depths only for compatible orientations.
        ref=np.where((template>=.90*fixed_max)&(template>max(3*noise,.028*span)),template,0)
        near=cv2.dilate(ref,kernel)
        risk=np.clip((near/np.maximum(depth,floor)-.45)/.30,0,1)
        weighted=e*(1-.96*risk)
        win=weighted>energy
        clear[win]=1-risk[win];energy=np.maximum(energy,weighted)

    margin=radii[-1]+px(s,.01)
    valid=cv2.erode(valid.astype('uint8'),np.ones((2*margin+1,2*margin+1),np.uint8)).astype(bool)
    energy[~valid]=0;energy[:margin]=0;energy[-margin:]=0
    return dict(signal=energy/floor,orientation=orientation,clear=clear,top=top,floor=floor),coarse,reg
