"""Keep texture windows local to the notch and use continuous row-wise displacement."""
import cv2
import numpy as np
from research.notch_identity_v40.evidence import registered as legacy
from research.notch_identity_v31.detector import px


def registered(args,fixed,stage):
    sl,origin,starts,_,_,s,front,gray,noise,_,raw,span=args
    f=fixed
    # Preserve the footprint of all NCC windows and Gaussian filter support.
    # The returned shift is applied to the full original ROI below.
    coarse,reg,aligned=legacy(args,f)
    if aligned is not None:return coarse,reg,aligned
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
