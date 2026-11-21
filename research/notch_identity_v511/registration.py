"""Keep texture windows local to the notch and use continuous row-wise displacement."""
import cv2
import numpy as np
from research.notch_identity_v40.evidence import registered as legacy
from research.notch_identity_v31.detector import px


def material_reference(fixed, pair, refpair, notch_y, scale):
    # Anchor displacements are measured. Locate the interpolation interval on the
    # specimen so moving the two measurement windows does not move tile edges.
    h,w=fixed.shape
    half=max(10.,.50*scale)
    fraction=np.clip((np.arange(h)-notch_y+half)/(2*half),0,1)[:,None]
    displacements=pair-refpair
    spacing=abs(pair[1,1]-pair[0,1])
    gradient=(displacements[1]-displacements[0])/max(spacing,1.)
    offsets=displacements.mean(0)+np.array([-half,half])[:,None]*gradient
    move=(1-fraction)*offsets[0]+fraction*offsets[1]
    mx=(np.arange(w)[None,:]-move[:,0,None]).astype('float32')
    my=np.broadcast_to((np.arange(h)-move[:,1])[:,None],(h,w)).astype('float32')
    out=cv2.remap(fixed,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE).astype('float32')
    out[(mx<0)|(mx>w-1)|(my<0)|(my>h-1)]=np.nan
    return out,dict(center_y=float(notch_y),half=half,offsets=offsets.tolist())


def registered(args,fixed,stage):
    sl,origin,starts,_,_,s,front,gray,noise,_,raw,span=args
    f=fixed
    # Preserve the footprint of all NCC windows and Gaussian filter support.
    # The returned shift is applied to the full original ROI below.
    if stage=='S4':
        x,y=np.rint(np.median(starts,axis=0)+origin).astype(int)
        ys,xs=sl
        left=max(0,min(xs.start,x-px(s,.65)-40))//2*2
        top=max(0,min(ys.start,y-px(s,.50)-40))//2*2
        right=min(raw.shape[1],x+px(s,1.1)+40)
        bottom=min(len(raw),max(ys.stop,y+px(s,.50)+40))
        source=raw[top:bottom,left:right]
        cropped=(slice(ys.start-top,ys.stop-top),slice(xs.start-left,min(right,xs.stop or right)-left))
        offset=np.asarray(origin)-[left,top]
        fast=(cropped,offset,starts,None,None,s,front,source[cropped],noise,None,source,span)
        coarse,reg,_=legacy(fast,f[top:bottom,left:right])
    else:
        coarse,reg,aligned=legacy(args,f)
        if aligned is not None or stage in ('S1','S2'):return coarse,reg,aligned
    if not reg.get('shift'):
        # Retry only on material around the snapped notch. An exterior moving
        # shadow can dominate the larger two-flank correlation window.
        x,y=np.rint(np.median(starts,axis=0)+origin).astype(int)
        r=px(s,.065);l=max(0,x-2*r);t=max(0,y-r);right=min(raw.shape[1],x+r+1);b=min(len(raw),y+r+1)
        templ=raw[t:b,l:right].astype('float32');radius=px(s,.023)
        x0=max(0,l-radius);y0=max(0,t-radius)
        search=f[y0:min(len(f),b+radius),x0:min(f.shape[1],right+radius)].astype(np.float32,copy=False)
        if not templ.size or templ.std()<max(4*noise,.12*span) or not np.isfinite(search).all():return coarse,{},None
        corr=cv2.matchTemplate(search,templ,cv2.TM_CCOEFF_NORMED)
        _,peak,_,pos=cv2.minMaxLoc(corr)
        if peak<.90:return coarse,{},None
        shift=[int(x0+pos[0]-l),int(y0+pos[1]-t)]
        coarse=dict(status='OK',anchor='MATERIAL_NOTCH',shift=shift,ncc=peak)
        reg=dict(coarse,source='MATERIAL_NOTCH')
    dx,dy=reg['shift']
    mapped=cv2.warpAffine(f[sl],np.float32([[1,0,dx],[0,1,dy]]),(gray.shape[1],len(gray)),
                          flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
    return coarse,reg,mapped
