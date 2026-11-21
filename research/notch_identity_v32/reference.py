"""Suspicious tail only: independent local translation on off-path material."""
import cv2
import numpy as np
from research.notch_identity_v31.detector import px

def review(gray,fixed,points,scale,noise,contrast):
    pts=np.asarray(points,int);x,y=pts.T
    result=dict(status='SHORT_CONTEXT',ncc=None,shift=None,cut=None)
    look=px(scale,.15);search=px(scale,.025);pad=px(scale,.05)
    pts=pts[x>=x[-1]-look];x,y=pts.T
    if len(pts)<px(scale,.045):return result
    l,r=x[0]-pad,x[-1]+pad+1;t,b=y.min()-pad,y.max()+pad+1
    if min(l,t)<search or r+search>gray.shape[1] or b+search>gray.shape[0]:return result
    template=gray[t:b,l:r].astype(np.float32)
    search_img=fixed[t-search:b+search,l-search:r+search].astype(np.float32)
    if not np.isfinite(search_img).all():
        result['status']='REFERENCE_NOT_FINITE';return result
    mask=np.ones_like(template)
    # Exclude the line itself from translation estimation.
    cy=np.interp(np.arange(l,r),x,y).round().astype(int)-t
    mask[np.abs(np.arange(len(template))[:,None]-cy)<=px(scale,.016)]=0.
    n=mask.sum()
    a=(template-(template*mask).sum()/n)*mask
    energy=float((a*a).sum())
    if energy/n<max(2*noise,.025*contrast)**2:
        result['status']='LOW_ANCHOR_TEXTURE';return result
    def corr(image,k):return cv2.matchTemplate(image,k,cv2.TM_CCORR)
    var=np.maximum(1e-6,corr(search_img**2,mask)-corr(search_img,mask)**2/n)
    scores=corr(search_img,a)/np.sqrt(energy*var)
    by,bx=np.unravel_index(scores.argmax(),scores.shape)
    best=float(scores[by,bx]);other=scores.copy()
    radius=px(scale,.007)
    other[max(0,by-radius):by+radius+1,max(0,bx-radius):bx+radius+1]=-1.
    result.update(ncc=best,shift=[int(bx-search),int(by-search)])
    if best<.79 or best-float(other.max())<.025:
        result['status']='AMBIGUOUS_ALIGNMENT';return result
    dx,dy=result['shift']; rad=px(scale,.014)
    def valley(im,xx,yy):
        return np.minimum(im[yy-rad,xx].astype(float),im[yy+rad,xx].astype(float))-im[yy,xx]
    dc=valley(gray,x,y);df=valley(fixed,x+dx,y+dy)
    # Search backwards for a static, positively observed suffix. A separately
    # changed trunk must precede it; a persistent crack throughout is ambiguous.
    span=px(scale,.024)
    static=(dc>1.5*noise)&(df>1.5*noise)&(abs(dc-df)<=np.maximum(2*noise,.22*abs(dc)))
    cut=None
    for i in range(len(x)-span,-1,-1):
        if static[i:i+span].mean()<.72:break
        cut=i
    result['status']='NO_STATIC_SUFFIX'
    if cut is None:return result
    if cut<span or np.mean((dc[:cut]-df[:cut])>np.maximum(2*noise,.25*dc[:cut]))<.40:
        result['status']='STATIC_WITHOUT_CHANGE_BOUNDARY';return result
    result.update(status='TRIM_STATIC_SUFFIX',cut=int(x[cut]))
    return result

