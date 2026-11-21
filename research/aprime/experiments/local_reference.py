"""Deterministic offline research sidecar. No endpoint decisions, no second search.
Only grayscale arrays, ordered anchors, A map and A path enter runtime methods.
"""
from common_ap import *
P=dict(max_features=160,max_live_patches=48,min_fit=6,min_holdout=4,ncc=.65,peak_margin=.015,holdout_p90_px=1.,max_translation_px=12.)

def highpass(x):
 x=x.astype(np.float32);return x-cv2.GaussianBlur(x,(0,0),1.2)
def mad(x):
 x=np.asarray(x,float);return float(1.4826*np.median(np.abs(x-np.median(x))))if x.size else 0.
def bbox(p,pad=0):
 p=np.asarray(p);return [float(p[:,0].min()-pad),float(p[:,1].min()-pad),float(p[:,0].max()+pad),float(p[:,1].max()+pad)]
def inside(hull,q):
 return bool(len(hull)>=3 and all(cv2.pointPolygonTest(np.asarray(hull,np.float32),tuple(map(float,p)),False)>=0 for p in np.asarray(q)))

class ReferenceCache:
 def __init__(self,ref,rp):
  start=time.perf_counter();self.ref=ref;self.rp=np.asarray(rp,float);o,u,d=anchors(rp);self.d=d
  self.h=int(np.clip(round(.025*d),6,16));self.radius=int(np.clip(round(.025*d),5,12))
  v=np.array([-u[1],u[0]]);corners=np.array([o+a*u+b*v for a in [-.35*d,3.2*d]for b in [-1.25*d,1.25*d]])
  b=bbox(corners);H,W=ref.shape;x0,y0=max(0,int(b[0])),max(0,int(b[1]));x1,y1=min(W,int(b[2])+1),min(H,int(b[3])+1)
  self.roi=[x0,y0,x1,y1];crop=ref[y0:y1,x0:x1];scale=min(1.,900/max(crop.shape))
  small=cv2.resize(crop,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
  mask=((small>45)&(small<252)).astype(np.uint8)*255
  er=max(3,2*int((self.h+2)*scale)+1);mask=cv2.erode(mask,np.ones((er,er),np.uint8))
  pts=cv2.goodFeaturesToTrack(small,maxCorners=P['max_features']*3,qualityLevel=.01,minDistance=max(3,3*self.h*scale),mask=mask,blockSize=3)
  self.features=[];self.rejections={};h=self.h
  for q in []if pts is None else pts[:,0,:]/scale+[x0,y0]:
   x,y=np.rint(q).astype(int)
   if x-h<0 or y-h<0 or x+h>=W or y+h>=H:continue
   t=ref[y-h:y+h+1,x-h:x+h+1].astype(np.float32)
   if float(np.std(t))<1.5 or float(np.mean((t<=45)|(t>=252)))>.03:continue
   # Spatial block assignment is fixed from reference pixels, not frame labels.
   cell=6*h; role='FIT'if (x//cell+y//cell)%2==0 else'HOLDOUT'
   if any(np.linalg.norm(np.array([x,y])-f['q'])<3*h for f in self.features):continue
   self.features.append(dict(q=np.array([x,y],float),template=t,hp=highpass(t),role=role,std=float(t.std())))
   if len(self.features)>=P['max_features']:break
  self.cache_ms=(time.perf_counter()-start)*1000
 def match(self,cur,M,path,alternative=False):
  start=time.perf_counter();H,W=cur.shape;h=self.h;r=self.radius
  target=np.asarray(path[-1]if len(path)else anchors(self.rp)[0],float)
  # Target is CURRENT coordinates; fallback caller supplies transformed anchor.
  inv=cv2.invertAffineTransform(np.asarray(M,float));tref=apply(inv,[target])[0]
  choices=sorted(self.features,key=lambda f:float(np.linalg.norm(f['q']-tref)))
  choices=[f for f in choices if np.linalg.norm(f['q']-tref)<=max(80,min(.85*self.d,430))][:P['max_live_patches']]
  path=np.asarray(path,float);records=[]
  g=np.arange(-h-r,h+r+1,dtype=float);xx,yy=np.meshgrid(g,g);grid=np.stack([xx,yy],-1)
  for k,f in enumerate(choices):
   q=f['q'];pred=apply(M,[q])[0];rec=dict(patch_id=k,reference_x=q[0],reference_y=q[1],role=f['role'],texture_std=f['std'],selected=False,reason='',ncc=None,margin=None,dx=None,dy=None)
   if len(path)and np.min(np.linalg.norm(path-pred,axis=1))<max(3*h,.06*self.d):rec['reason']='CRACK_BAND_EXCLUDED';records.append(rec);continue
   pp=apply(M,grid+q)
   if pp[...,0].min()<1 or pp[...,1].min()<1 or pp[...,0].max()>=W-1 or pp[...,1].max()>=H-1:rec['reason']='CURRENT_OUT_OF_VIEW';records.append(rec);continue
   warped=sample(cur,pp).astype(np.float32)
   a=highpass(warped)if alternative else warped;tpl=f['hp']if alternative else f['template']
   cc=cv2.matchTemplate(a,tpl,cv2.TM_CCOEFF_NORMED);_,peak,_,loc=cv2.minMaxLoc(cc);px,py=loc
   masked=cc.copy();masked[max(0,py-2):py+3,max(0,px-2):px+3]=-1
   margin=float(peak-masked.max());delta=np.array([px-r,py-r],float)
   for dim,idx,n in [(0,px,cc.shape[1]),(1,py,cc.shape[0])]:
    if 0<idx<n-1:
     vm=cc[py,px-1]if dim==0 else cc[py-1,px];vp=cc[py,px+1]if dim==0 else cc[py+1,px];den=vm-2*peak+vp
     if abs(den)>1e-8:delta[dim]+=float(np.clip(.5*(vm-vp)/den,-.5,.5))
   dc=M[:,:2]@delta;rec.update(ncc=float(peak),margin=margin,dx=float(dc[0]),dy=float(dc[1]))
   if peak<P['ncc']:rec['reason']='LOW_NCC'
   elif margin<P['peak_margin']:rec['reason']='REPEATED_OR_AMBIGUOUS_TEXTURE'
   elif px in(0,2*r)or py in(0,2*r):rec['reason']='SEARCH_BOUNDARY'
   else:rec.update(selected=True,reason='MATCH_ACCEPTED')
   records.append(rec)
  fit=[p for p in records if p['selected']and p['role']=='FIT'];hold=[p for p in records if p['selected']and p['role']=='HOLDOUT']
  out=dict(state='ALIGN_UNKNOWN',reason='INSUFFICIENT_SPATIAL_FIT_HOLDOUT',fit_n=len(fit),holdout_n=len(hold),holdout_p90_px=None,correction=[0.,0.],polygon=[],local_supported=False,patches=records)
  if len(fit)>=P['min_fit']and len(hold)>=P['min_holdout']:
   dd=np.array([[p['dx'],p['dy']]for p in fit]);center=np.median(dd,axis=0);res=np.linalg.norm(dd-center,axis=1);good=res<=1.25
   if good.sum()>=P['min_fit']:
    center=np.median(dd[good],axis=0);hr=np.linalg.norm(np.array([[p['dx'],p['dy']]for p in hold])-center,axis=1);q90=float(np.percentile(hr,90))
    hp=apply(M,[[p['reference_x'],p['reference_y']]for p in hold])+center
    hull=cv2.convexHull(hp.astype(np.float32)).reshape(-1,2);audit=target+np.array([[-16,-16],[16,-16],[16,16],[-16,16]])
    out.update(correction=center.tolist(),holdout_p90_px=q90,polygon=hull.tolist())
    if np.linalg.norm(center)>P['max_translation_px']:out.update(state='ALIGN_CONTRADICTED',reason='EXCESSIVE_RESIDUAL_TRANSLATION')
    elif q90>P['holdout_p90_px']:out.update(state='ALIGN_CONTRADICTED',reason='HOLDOUT_RESIDUAL_FAILED')
    elif not inside(hull,audit):out['reason']='CANDIDATE_AUDIT_NOT_COVERED_BY_HOLDOUT'
    else:out.update(state='ALIGN_SUPPORTED',reason='LOCAL_HOLDOUT_PASSED',local_supported=True)
   else:out['reason']='FIT_NOT_RIGID_WITHIN_ONE_PIXEL'
  out['M']=np.asarray(M,float).copy();out['M'][:,2]+=out['correction'];out['cost_ms']=(time.perf_counter()-start)*1000
  return out

 def photo(self,cur,reg):
  start=time.perf_counter();h=self.h;g=np.arange(-h,h+1,2);xx,yy=np.meshgrid(g,g);grid=np.stack([xx,yy],-1)
  fit=[];hold=[];noise=[]
  for p in reg['patches']:
   if not p['selected']:continue
   q=np.array([p['reference_x'],p['reference_y']]);a=sample(self.ref,grid+q);b=sample(cur,apply(reg['M'],grid+q))
   (fit if p['role']=='FIT'else hold).append((a.ravel(),b.ravel()))
   noise.append(max(.5,mad(a-cv2.GaussianBlur(a,(0,0),.8))))
  out=dict(state='PHOTO_UNKNOWN',reason='GEOMETRY_NOT_LOCALLY_SUPPORTED',a=1.,b=0.,noise=float(np.median(noise))if noise else None,holdout_residual_mad=None,holdout_bias=None,fit_samples=0,holdout_samples=0)
  if reg['local_supported']and fit and hold:
   x,y=np.concatenate([f[0]for f in fit]),np.concatenate([f[1]for f in fit]);xh,yh=np.concatenate([f[0]for f in hold]),np.concatenate([f[1]for f in hold])
   a=1.;b=float(np.median(y-x));model='OFFSET'
   if np.percentile(x,90)-np.percentile(x,10)>=12:
    X=np.column_stack([x,np.ones(len(x))]);w=np.ones(len(x))
    for _ in range(3):
     ab=np.linalg.lstsq(X*w[:,None],y*w,rcond=None)[0];e=y-X@ab;w=np.minimum(1.,max(1.,2.5*mad(e))/np.maximum(1e-6,np.abs(e)))
    a,b=map(float,ab);model='ROBUST_AFFINE'
   e=yh-a*xh-b;bias=float(np.median(e));n=out['noise'];er=mad(e)
   out.update(a=a,b=b,model=model,holdout_residual_mad=er,holdout_bias=bias,fit_samples=len(x),holdout_samples=len(xh))
   if not .5<=a<=2.:out['reason']='GAIN_NOT_IDENTIFIABLE_OR_EXCESSIVE'
   elif abs(bias)>max(3.,3*n)or er>max(4.,2.5*n):out.update(state='PHOTO_CONTRADICTED',reason='PHOTO_HOLDOUT_FAILED')
   else:out.update(state='PHOTO_SUPPORTED',reason='ROBUST_HOLDOUT_PASSED')
  out['cost_ms']=(time.perf_counter()-start)*1000;return out

def path_evidence(ref,cur,path,reg,photo,width=2.):
 start=time.perf_counter();p=np.asarray(path,float)
 if len(p)<2:return [],(time.perf_counter()-start)*1000
 ds=np.linalg.norm(np.diff(p,axis=0),axis=1);ss=np.r_[0,np.cumsum(ds)];idx=np.unique(np.r_[np.searchsorted(ss,np.arange(0,ss[-1],4)),len(p)-1]).astype(int);idx=idx[idx<len(p)]
 tang=np.gradient(p,axis=0);tang/=np.maximum(1e-9,np.linalg.norm(tang,axis=1))[:,None];n=np.column_stack([-tang[:,1],tang[:,0]])
 w=float(np.clip(width,1.,8.));p=p[idx];n=n[idx];q=np.stack([p,p-3*w*n,p+3*w*n],axis=1)
 c=sample(cur,q);ir=cv2.invertAffineTransform(reg['M']);r=photo['a']*sample(ref,apply(ir,q))+photo['b'];vc=c[:,1:].mean(1)-c[:,0];vr=r[:,1:].mean(1)-r[:,0];noise=photo['noise']or 1.
 rr=[]
 for k,i in enumerate(idx):
  observable=reg['local_supported']and photo['state']=='PHOTO_SUPPORTED'and inside(reg['polygon'],q[k])
  if not observable:state='INSUFFICIENT_EVIDENCE'
  elif vc[k]>3*noise and vc[k]-vr[k]>3*noise:state='NEW_CRACK_SUPPORTED'
  elif vc[k]>3*noise and vr[k]>3*noise:state='STATIC_OR_BRIDGE_RISK'
  else:state='INSUFFICIENT_EVIDENCE'
  rr.append(dict(path_index=int(i),arc_s=float(ss[i]),x=float(p[k,0]),y=float(p[k,1]),Vcur=float(vc[k]),Vref=float(vr[k]),DeltaV=float(vc[k]-vr[k]),D=float(r[k,0]-c[k,0]),Q=float(vc[k]/noise),G=float(np.dot(tang[i],tang[max(0,i-1)])),O=bool(observable),ownership_state=state))
 return rr,(time.perf_counter()-start)*1000
