"""Two Euclidean image fits with withheld geometric strips for validation.

Regions are geometric *proxies*, not guaranteed crack-free without human labels.
P1/P2 only initialize each side independently. The central transition is invalid.
"""
import time
import cv2,numpy as np
from select_causal_history import RULES,state

def context(image,row):
 st=state(row)
 if st is None:return None
 H,W=image.shape;mx,my=st['M'];x0=max(0,int(mx-.035*W));x1=min(W,x0+RULES['roi_max_width']);half=max(96,min(.15*H,.8*st['D']))
 y0=max(0,int(my-half));y1=min(H,int(my+half));scale=min(1,RULES['roi_output_max_width']/(x1-x0));w=int(round((x1-x0)*scale));h=int(round((y1-y0)*scale))
 if w<64 or h<64:return None
 current=cv2.resize(image[y0:y1,x0:x1],(w,h),interpolation=cv2.INTER_AREA);sx=w/(x1-x0);sy=h/(y1-y0);mid=int(round((my-y0)*sy));band=max(3,int(h*RULES['transition_half_fraction']))
 yy,xx=np.indices((h,w));inner=(xx>=int(.06*w))&(xx<int(.94*w));top=yy<mid-band;bottom=yy>mid+band
 topfit=inner&(yy<int(.65*max(1,mid-band)));botfit=inner&(yy>int(mid+band+.35*(h-mid-band)))
 hold=(inner&top&~topfit)|(inner&bottom&~botfit);candidate=inner&(abs(yy-mid)<int(.24*h))&(top|bottom)
 return dict(current=current,roi=[x0,y0,x1,y1],scale=[sx,sy],sides=[top,bottom],fits=[topfit,botfit],holdout=hold,candidate=candidate,transition=~(top|bottom),state=st)

def register(ref,past,ctx):
 start=time.perf_counter();a=ctx['current'];h,w=a.shape;st=state(past);blank=np.zeros_like(a,dtype=bool);warp=np.zeros_like(a);valid=blank.copy();logs=[]
 if st is None:return dict(warp=warp,mask=valid,valid=False,sides=[],reason='no_valid_p1p2',ms=(time.perf_counter()-start)*1000)
 x0,y0,_,_=ctx['roi'];sx,sy=ctx['scale'];full=np.ones(ref.shape,np.uint8)*255
 for side in range(2):
  region=ctx['sides'][side];fit=ctx['fits'][side];validation=region&ctx['holdout'];delta=np.array(ctx['state']['points'][side])-np.array(st['points'][side]);seed=np.array([[sx,0,sx*(delta[0]-x0)],[0,sy,sy*(delta[1]-y0)]],np.float32)
  initial=cv2.warpAffine(ref,seed,(w,h),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
  ys,xs=np.where(fit);record=dict(side='top' if side==0 else 'bottom',valid=False,reason='',seed=seed.tolist(),warp=None,ncc=None,p95=None,coverage=0.,normalization_offset=None)
  if len(xs)<256:record['reason']='insufficient_texture';logs.append(record);continue
  l,r=int(xs.min()),int(xs.max()+1);u,b=int(ys.min()),int(ys.max()+1);aa=a[u:b,l:r];bb=initial[u:b,l:r];texture=float(np.std(aa));record['texture_std']=texture
  if texture<RULES['minimum_texture_std']:record['reason']='insufficient_texture';logs.append(record);continue
  fitmask=((aa>5)&(aa<250)&(bb>5)&(bb<250)).astype(np.uint8)*255;ecc=np.eye(2,3,dtype=np.float32)
  try:
   cc,ecc=cv2.findTransformECC(aa.astype(np.float32)/255,bb.astype(np.float32)/255,ecc,cv2.MOTION_EUCLIDEAN,(cv2.TERM_CRITERIA_COUNT|cv2.TERM_CRITERIA_EPS,RULES['ecc_iterations'],1e-5),fitmask,5)
   adjust=np.eye(3);adjust[:2]=cv2.invertAffineTransform(ecc);off=np.eye(3);off[:2,2]=[l,u];s=np.eye(3);s[:2]=seed;matrix=(off@adjust@np.linalg.inv(off)@s)[:2].astype(np.float32)
   aligned=cv2.warpAffine(ref,matrix,(w,h),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
   covered=cv2.warpAffine(full,matrix,(w,h),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)==255
   covered&=(a>5)&(a<250)&(aligned>5)&(aligned<250);vv=validation&covered;coverage=float(np.sum(region&covered)/max(1,region.sum()))
   record.update(warp=matrix.tolist(),fit_ecc=float(cc),coverage=coverage)
   if vv.sum()<128:record['reason']='insufficient_valid_area'
   else:
    av=a[vv].astype(float);bv=aligned[vv].astype(float);ncc=float(np.corrcoef(av,bv)[0,1]) if min(av.std(),bv.std())>1 else 0.;p95=float(np.percentile(abs(av-bv),95));offset=float(np.clip(np.median(a[fit&covered].astype(float)-aligned[fit&covered]),-20,20)) if (fit&covered).any() else 0
    record.update(ncc=ncc,p95=p95,normalization_offset=offset)
    if coverage<RULES['minimum_side_coverage']:record['reason']='insufficient_valid_area'
    elif ncc<RULES['minimum_holdout_ncc'] or p95>RULES['maximum_holdout_p95']:record['reason']='poor_registration'
    else:record['valid']=True
   warp[region]=aligned[region]
   if record['valid']:valid|=region&covered
  except cv2.error:record['reason']='ecc_nonconvergence'
  logs.append(record)
 good=all(r['valid'] for r in logs) and len(logs)==2
 return dict(warp=warp,mask=valid,valid=good,sides=logs,reason='' if good else '|'.join(r['reason'] for r in logs if not r['valid']),ms=(time.perf_counter()-start)*1000)

def metrics(ctx,result,common):
 if result is None or not result['valid'] or not common.any():return dict(static_residual_median=None,static_residual_p95=None,activation_area_ratio=None,connected_component_count=None,candidate_region_signal=None,false_residual_proxy=None)
 diff=abs(ctx['current'].astype(np.float32)-result['warp'].astype(np.float32));static=common&ctx['holdout'];candidate=common&ctx['candidate'];act=(diff>RULES['activation_threshold'])&common
 n,labels,stats,_=cv2.connectedComponentsWithStats(act.astype(np.uint8),8)
 return dict(static_residual_median=float(np.median(diff[static])) if static.any() else None,static_residual_p95=float(np.percentile(diff[static],95)) if static.any() else None,activation_area_ratio=float(act[common].mean()),connected_component_count=int(np.sum(stats[1:,cv2.CC_STAT_AREA]>=RULES['component_min_pixels'])),candidate_region_signal=float(diff[candidate].mean()) if candidate.any() else None,false_residual_proxy=float(act[static].mean()) if static.any() else None)
