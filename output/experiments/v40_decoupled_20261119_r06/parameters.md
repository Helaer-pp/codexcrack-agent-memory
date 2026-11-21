# V4.0 参数索引

以下按实现函数列出实参、窗宽、能量阈值、像素下限和归一化常数。继承项中也包括底层数值保护。

## research\notch_identity_v40\terminal.py

prepare

```python
   9 def prepare(raw,hint,scale,stage='v4_0'):
  12 return (*p[:-3],stage,*p[-2:]) if p is not None else None
```

refine

```python
  15 pts=np.asarray(path,dtype=np.float32);s=p[5];raw=p[4]
  16 tangent=np.gradient(pts,axis=0)
  17 normal=np.column_stack((-tangent[:,1],tangent[:,0]))
  18 normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-5)
  19 radius=min(2.,max(.75,.007*s))
  20 t=np.linspace(-radius,radius,9,dtype=np.float32)
  22 values=cv2.remap(raw,xy[:,:,0],xy[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
  23 j=values.argmax(axis=1);i=np.arange(len(j))
  24 peaks=(values[:,1:-1]>values[:,:-2])&(values[:,1:-1]>=values[:,2:])
  25 good=(j>0)&(j<8)&(peaks.sum(axis=1)==1)&(values[i,j]-np.maximum(values[:,0],values[:,-1])>p[8])
  26 x,y=pts.astype(int).T;good&=ev['clear'][y-ev['top'],x]>.75
  27 j=np.clip(j,1,7)
  28 a,b,c=values[i,j-1],values[i,j],values[i,j+1]
  29 fraction=np.clip(.5*(a-c)/np.minimum(a-2*b+c,-1e-6),-.5,.5)
  30 offset=np.where(good,t[j]+fraction*(t[1]-t[0]),0)
```

predict

```python
  34 base=(*p[:-3],'v3_4',*p[-2:]) if p is not None else None
  37 stage=p[-3] if p is not None else 'track_a'
  42 b=None;count=0;rejected={};candidates=[]
  50 origin=np.asarray(p[1]) if p is not None else np.zeros(2)
  53 noise_floor=ev['floor'] if ev is not None else None,refined=0,events=[])
  56 diag.update(track_b_tip=(path[-1]+origin).tolist(),track_b_root=root,
  57 events=[[int(col+origin[0]) for col in event] for event in b['events']])
  58 if stage=='v4_0':path,diag['refined']=refine(path,p,ev)
  59 path=(np.array(path)+origin).tolist();tip=path[-1]
  61 result=dict(status='VALID',root=root,points=path,tip=tip,diagnostics=dict(candidates=[dict(start=root,tip=tip,status='VALID',trace=trace)],pairs=[],selected=0))
```

## research\notch_identity_v40\evidence.py

offset_image

```python
  10 pad=cv2.copyMakeBorder(im,max(-dy,0),max(dy,0),max(-dx,0),max(dx,0),cv2.BORDER_REPLICATE)
  11 x=max(dx,0);y=max(dy,0)
```

registered

```python
  16 center=np.median(starts,axis=0)
  24 local=reg.local(min(gray.shape[1]-1,front+px(s,.24)),round(center[1]))
  27 f=cv2.warpAffine(fixed[sl],np.float32([[1,0,shift[0]],[0,1,shift[1]]]),(gray.shape[1],gray.shape[0]),
  28 flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
```

make

```python
  35 mid=int(np.median(np.array(starts)[:,1]));pad=px(s,.28)
  36 top=max(0,mid-pad);bottom=min(len(gray),mid+pad+1)
  37 cur=gray[top:bottom].astype(np.float32);f=aligned[top:bottom]
  42 high=diff-cv2.medianBlur(diff,3)
  43 flank=high[::max(1,px(s,.015)),::max(1,px(s,.015))]
  44 floor=max(.012*span,2.8*float(np.median(np.abs(flank-np.median(flank)))),1.5*noise)
  45 radii=sorted({px(s,fraction) for fraction in (.007,.014,.024)})
  46 reach=px(s,.025);kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*reach+1,2*reach+1))
  47 gx=cv2.Sobel(diff,cv2.CV_32F,1,0)
  48 gy=cv2.Sobel(diff,cv2.CV_32F,0,1)
  49 side=2*px(s,.009)+1
  50 norm=cv2.blur(gx*gx+gy*gy,(side,side))
  51 orientation=cv2.blur(gy*gy-gx*gx,(side,side))/np.maximum(norm,floor*floor)
  53 for angle in (-.52,0.,.52):
  55 k=px(s,.009)
  58 return .25*(offset_image(im,dx,dy)+2*im+offset_image(im,-dx,-dy))
  65 a,b=sides(sd,r);valleys.append(np.maximum(sd-np.maximum(a,b),0))
  66 a,b=sides(sf,r);fixed_valleys.append(np.maximum(np.minimum(a,b)-sf,0))
  67 a,b=sides(sc,r);current_valleys.append(np.maximum(np.minimum(a,b)-sc,0))
  70 r=px(s,.014);a,b=sides(sd,r);base=.5*(a+b)
  72 for j in range(-r,r+1):
  74 positive+=np.maximum(d-noise*.5,0)
  75 negative+=np.maximum(-d-noise*.5,0)
  76 energies.append(strength*np.clip(1-negative/np.maximum(positive,floor),0,1))
  82 ref=np.where((template>=.90*fixed_max)&(template>max(3*noise,.028*span)),template,0)
  83 near=cv2.dilate(ref,kernel)
  84 risk=np.clip((near/np.maximum(depth,floor)-.45)/.30,0,1)
  85 weighted=e*(1-.96*risk)
  87 clear[win]=1-risk[win];energy=np.maximum(energy,weighted)
  89 margin=radii[-1]+px(s,.01)
  90 valid=cv2.erode(valid.astype('uint8'),np.ones((2*margin+1,2*margin+1),np.uint8)).astype(bool)
  91 energy[~valid]=0;energy[:margin]=0;energy[-margin:]=0
```

smooth

```python
  58 return .25*(offset_image(im,dx,dy)+2*im+offset_image(im,-dx,-dy))
```

## research\notch_identity_v40\tracking.py

roots

```python
  10 pad=px(s,.16);length=px(s,.026)
  11 lo=max(0,front-px(s,.14));hi=min(sig.shape[1]-length-1,front+px(s,.10))
  12 a=max(0,mid-pad);b=min(len(sig),mid+pad+1)
  14 patch=sig[a:b,lo:hi+length+1]
  16 score=np.zeros((len(patch),hi-lo+1),np.float32)
  17 for slope in (-.45,0,.45):
  20 yy=np.clip(np.arange(len(patch))+round(slope*j),0,len(patch)-1)
  21 mass+=np.log1p(patch[yy,j:j+score.shape[1]])
  23 score*=patch[:,:score.shape[1]]>=1.0
  24 score/=1+np.maximum(np.arange(lo,hi+1)-front,0)/max(1,.10*s)
  26 for _ in range(10):
  28 if score[y,x]<.75:break
  30 dx,dy=px(s,.035),px(s,.014)
  31 score[max(0,y-dy):y+dy+1,max(0,x-dx):x+dx+1]=0
```

trace

```python
  36 s=p[5];front=p[6];top=e['top'];mid=int(np.median(np.array(p[2])[:,1]))-top
  39 track,_,_,_=trace_windowed(sig,zero,x,y,px(s,.065),px(s,.055),px(s,.016),
  40 px(s,.016),px(s,.34),px(s,.05),px(s,.040),.78)
  41 if len(track)<px(s,.026):continue
  43 xx,yy=arr[:,:2].astype(int).T;val=arr[:,2]
  45 weak=val<.78;segments=np.flatnonzero(np.diff(np.r_[False,weak,False])).reshape(-1,2)
  48 if b-a<px(s,.014) or b>=len(val):continue
  49 w=px(s,.025);prev=max(0,a-w)
  50 slope=(yy[a-1]-yy[prev])/max(1,a-1-prev) if a else 0
  51 residual=abs(yy[b]-(yy[max(0,a-1)]+slope*(b-a+1)))
  52 ahead=min(len(yy)-1,b+w)
  53 exit_slope=(yy[ahead]-yy[b])/max(1,ahead-b)
  54 orientation=e['orientation'][yy[b:ahead+1],xx[b:ahead+1]]
  56 if np.median(orientation)<.15 or np.mean(val[b:ahead+1]>=1.15)<.5:
  58 if residual>max(1,.006*s) or abs(slope-exit_slope)>.36:
  61 if b-a>=px(s,.025) and np.max(np.abs(yy[b:ahead+1]-(yy[a-1]+slope*(np.arange(b,ahead+1)-a+1))))>max(1,.006*s):
  63 events.append([int(xx[a]),int(xx[b]),int(xx[min(len(xx)-1,b+w-1)])])
  67 offsets=np.arange(px(s,.035),px(s,.10)+1,2)
  68 side=sig[np.clip(yy[:,None]+np.r_[-offsets,offsets],0,len(sig)-1),xx[:,None]]
  69 background=max(1.15,float(np.percentile(side,97)))
  70 w=px(s,.033)
  71 strength=np.convolve(val,np.ones(w)/w,'valid') if len(val)>=w else np.empty(0)
  73 supported=np.flatnonzero((np.asarray(dense)>=.66)&(strength>=1.20*background))
  75 end=int(supported[-1]+w//2+1)
  79 block=px(s,.065)
  81 if end>2*block:
  83 above=np.convolve((orientation[:end]>.72).astype(int),np.ones(block,int),'valid')
  84 below=np.cumsum((orientation[:end]<.28)[::-1],dtype=int)[::-1]
  86 eligible=js[(above[js-block]>=block//2)&(below[js]>=np.floor(.8*(end-js-1))+1)]
  88 if (np.median(orientation[j-block:j])>.72 and
  89 np.quantile(orientation[j:end],.80)<.28 and
  90 np.median(val[j:end])<.4*np.median(val[j-block:j])):
  91 end=j+1;break
  93 ids=np.flatnonzero(val>=.85)
  95 w=px(s,.022)
  96 last=next((int(j) for j in ids[::-1] if j>=w and (val[j-w+1:j+1]>=.8).mean()>=.60),None)
  97 if last is None or xx[last]<front+px(s,.027) or xx[last]-x<px(s,.026):continue
  99 if len(obs)/(last+1)<.58:continue
 103 for col in range(x-1,max(front-1,x-px(s,.035)-1),-1):
 104 window=np.arange(max(0,row-1),min(len(sig),row+2))
 108 if prefix:path=np.vstack((prefix[::-1],path))
 110 if path[-1,0]+w>=sig.shape[1]:continue
 111 near=val[:min(last+1,px(s,.18))]
 112 rank=float(np.mean(np.log1p(near))*min(1.,len(obs)/max(1,.12*s))/(1+max(0,x-front)/max(1,.12*s)))
 113 candidates.append(dict(root=path[0].tolist(),points=path,rank=rank,events=[ev for ev in events if ev[2]<=xx[last]]))
```

admissible

```python
 118 gray=p[7];scale=p[5];front=p[6];mid=float(np.median(np.array(p[2])[:,1]))
 121 area=gray[:,:min(gray.shape[1],front+px(scale,.12)+1)]
 122 material=float(np.percentile(area,85))
 123 _,cc=cv2.connectedComponents((area<material-max(3.5*p[8],.07*p[-1])).astype('uint8'),connectivity=8)
 124 l=max(1,min(x for x,y in p[2])+1)
 125 core=area[:,:l]<material-.45*p[-1]
 126 counts=np.bincount(cc[:,:l][core],minlength=2);counts[0]=0
 130 mask=(gray<material-max(4*p[8],.12*p[-1])).astype('uint8')
 131 rad=px(scale,.005)
 132 mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*rad+1,2*rad+1)))
 133 contours,tree=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
 134 holes=[h for h,t in zip(contours,tree[0] if tree is not None else []) if t[3]>=0 and cv2.contourArea(h)>.00045*scale**2]
 139 elif any(abs(cv2.pointPolygonTest(h,tuple(map(float,path[-1])),True))<max(2,.018*scale) for h in holes):why='CLOSED_RIM'
 145 rejected[why]=rejected.get(why,0)+1
```

## research\notch_identity_v33\reference.py

align

```python
  11 x0,y0,x1,y1=box
  12 x0=max(x0,0,search-dx); y0=max(y0,0,search-dy)
  13 x1=min(x1,w,w-search-dx); y1=min(y1,h,h-search-dy)
  15 if x1-x0<2*search+1 or y1-y0<2*search+1:return result
  16 block=fixed[y0+dy-search:y1+dy+search,x0+dx-search:x1+dx+search].astype(np.float32)
  17 mask=mask_fn(np.arange(x0,x1)[None,:],np.arange(y0,y1)[:,None]).astype(np.float32)
  19 invalid=cv2.dilate((~np.isfinite(block)).astype('uint8'),np.ones((2*search+1,2*search+1),np.uint8))
  20 mask*=1-invalid[search:-search,search:-search]
  23 if n<.35*mask.size:return result
  24 patch=current[y0:y1,x0:x1].astype(np.float32)
  26 energy=np.sum(tpl**2)
  27 if energy/n<max(1.8*noise,.02*contrast)**2:
  29 def corr(a,b):return cv2.matchTemplate(a,b,cv2.TM_CCORR)
  30 var=np.maximum(1e-5,corr(block**2,mask)-corr(block,mask)**2/n)
  33 best=float(np.clip(scores[by,bx],-1,1));others=scores.copy()
  34 rad=max(1,round(.32*search))
  35 others[max(0,by-rad):by+rad+1,max(0,bx-rad):bx+rad+1]=-1
  38 status='OK' if best>=.75 and gap>=.012 else 'AMBIGUOUS')
```

corr

```python
  29 def corr(a,b):return cv2.matchTemplate(a,b,cv2.TM_CCORR)
```

__init__

```python
  49 box=(x-px(scale,.40),y-px(scale,.23),x+px(scale,.52),y+px(scale,.23))
  51 return im-cv2.GaussianBlur(im,(0,0),max(.5,.018*scale))
  52 a=raw.astype(np.float32)
  53 b=np.where(np.isfinite(fixed),fixed,a).astype(np.float32)
  56 self.coarse=align(ta,tb,box,px(scale,.04),(0,0),noise,contrast,
  57 lambda xx,yy:(xx<x-px(scale,.05))|(abs(yy-y)>px(scale,.04)))
  62 for sign in (-1,1):
  63 center_y=y+sign*px(scale,.22)
  64 area=(x-px(scale,.22),center_y-px(scale,.12),x+px(scale,.50),center_y+px(scale,.12))
  65 anchors.append(align(ta,tb,area,px(scale,.04),(0,0),noise,contrast,
  67 if all(r['status']=='OK' for r in anchors) and np.linalg.norm(np.subtract(anchors[0]['shift'],anchors[1]['shift']))<=px(scale,.01):
```

local

```python
  77 box=(x-p(.21),y-p(.12),x+p(.11),y+p(.12))
  78 status=align(self.local_current,self.local_fixed,box,p(.015),self.coarse['shift'],self.noise,self.contrast,
  79 lambda xx,yy:np.broadcast_to(abs(yy-y)>p(.027),(yy.size,xx.size)))
  81 area=(x-p(.32),y-p(.24),x+p(.15),y+p(.24))
  82 wide=align(self.local_current,self.local_fixed,area,p(.015),self.coarse['shift'],self.noise,self.contrast,
  83 lambda xx,yy:np.broadcast_to(abs(yy-y)>p(.05),(yy.size,xx.size)))
```

measure

```python
  90 reg=self.local(x[-1],y[-1])
  92 dx,dy=reg['shift'];r=px(self.s,.014);h,w=self.gray.shape
  93 if (x+dx).min()<0 or (x+dx).max()>=w or min(y.min(),(y+dy).min())<r or max(y.max(),(y+dy).max())+r>=h:
```

protect

```python
 103 span=px(self.s,.022)
 105 pts=np.column_stack((x[i-span:i+span+1],y[i-span:i+span+1]))
 109 changed=(net>max(2*self.noise,.022*self.contrast))&(a>self.noise)
 110 return bool(changed[:span].mean()>=.65 and changed[span:].mean()>=.65)
```

review

```python
 113 pts=np.asarray(points); x=pts[:,0];s=self.s
 114 pts=pts[x>=x[-1]-px(s,.15)]
 119 changed=(net>max(2*self.noise,.025*self.contrast))&(a>self.noise)
 120 window=px(s,.022)
 122 static=(b>2*self.noise)&(abs(net)<=np.maximum(2*self.noise,.25*np.maximum(a,b)))
 123 weak=(a<max(2.5*self.noise,.035*self.contrast))&(~changed)
 126 k=int(last[-1])+1
 127 if len(pts)-k>=window and (static|weak)[k:].mean()>=.75 and changed[max(0,k-2*window):k].mean()>=.45:
 128 audit.update(decision='TRIM_STATIC' if static[k:].mean()>=.5 else 'TRIM_WEAK',cut=int(pts[k,0]))
 129 elif static.mean()>=.75:audit['decision']='PERSISTENT_NO_BOUNDARY'
```

rank

```python
 134 pts=pts[pts[:,0]<=pts[0,0]+px(self.s,.25)]
 136 if data is None:return dict(weight=0.,fraction=None,mean=None,status=reg['status'])
 138 val=np.clip(net/self.contrast,0,.5)
 139 fraction=float((net>max(2*self.noise,.025*self.contrast)).mean())
 141 return dict(weight=.65*fraction*np.sqrt(mean),fraction=fraction,mean=mean,status='OK')
```

texture

```python
  51 return im-cv2.GaussianBlur(im,(0,0),max(.5,.018*scale))
```

## research\notch_identity_v35\reference.py

contour

```python
   9 r=px(s,.24);bound=px(s,.025)
  10 xs=np.arange(x-px(s,.30),x+1)
  11 if xs[0]<bound or xs[-1]+bound>=raw.shape[1] or y-r<0 or y+r>=raw.shape[0]:return None
  13 a=im[y-r:y+r+1,cols]
  15 lo,hi=np.percentile(a,[12,85])
  16 if hi-lo<max(8*noise,.28*contrast):return None
  17 dark=a<lo+.40*(hi-lo)
  18 first=dark.argmax(0);last=2*r-dark[::-1].argmax(0)
  19 usable=(last-first>px(s,.035))&(first>0)&(last<2*r)&dark[r]
  24 for dx in range(-bound,bound+1):
  27 valid=cur[2]&fixed_edges[2]
  28 if valid.mean()<.75:continue
  29 a,b=cur[0][valid],cur[1][valid]
  30 if np.ptp(b-a)<px(s,.04):continue
  31 top=fixed_edges[0][valid]-a;bot=fixed_edges[1][valid]-b
  32 dy=int(round(np.median((top+bot)*.5)))
  33 loss=np.median(abs((top+bot)*.5-dy))+.3*np.mean(abs(np.r_[top-dy,bot-dy]))+.08*(abs(dx)+abs(dy))
  34 if abs(dy)<=bound and np.quantile(abs(np.r_[top-dy,bot-dy]),.85)<=px(s,.022):
```

## research\notch_identity_v34\terminal.py

prepare

```python
  14 def prepare(raw,hint,scale,stage='v3_4'):
  16 prep=base.prepare(raw,hint,scale,'v3_2')
  17 return (*prep[:-2],stage,raw,prep[-1]) if prep is not None else None
```

follow

```python
  20 x,y=start;r=px(scale,.014)
  21 seed=max(range(max(0,y-r),min(len(gray),y+r+1)),key=lambda j:min(4.,sig[j,x])-.35*abs(j-y)*288/scale)
  22 track,loss,reconnections,stop=trace_windowed(sig,bonus,x,seed,px(scale,.07),px(scale,.076),px(scale,.017),px(scale,.014),
  23 px(scale,.35),px(scale,.045),px(scale,.05),.80)
  24 audit=dict(first_loss=int(loss) if loss>=0 else None,reconnections=int(reconnections),
  29 arr=np.array(track);xx,yy=arr[:,:2].astype(int).T;score=arr[:,2];depth=resp[yy,xx]
  33 if stop==1 and support is not None and stage!='unlock' and support.coarse['status']=='OK':
  34 last_x,last_y=xx[-1],yy[-1]
  35 end=min(sig.shape[1],last_x+px(scale,.060)+1)
  36 if last_x+1<end:
  37 extra,_,_,_=trace_windowed(sig[:,:end],bonus[:,:end],last_x,last_y,px(scale,.07),px(scale,.076),
  38 px(scale,.017),end+1,end+1,end+1,px(scale,.05),.80)
  41 tx,ty=trial[:,:2].astype(int).T
  42 first=int(np.searchsorted(tx,xx[-1]-px(scale,.014)+1))
  44 arr=trial;xx,yy=tx,ty;score=arr[:,2];depth=resp[yy,xx];audit['lookahead']=len(extra)
  45 skip=0;waived=[];allowed=np.empty(0,np.int64)
  48 if why==3 and support is not None and support.accept_lip(xx,yy,events[-1]):
  50 if why not in (1,2) or support is None or not support.protect(xx,yy,limit):break
  52 skip=max(skip+1,limit+px(scale,.025))
  58 if limit==0:return reject('GEOMETRY_CUT_AT_ROOT')
  60 floor=.016*contrast
  61 strong=(score>=1)&(depth>=floor)
  62 obs= (score>=.55)&(depth>=floor)
  64 if not len(strong_ids) or strong_ids[0]>px(scale,.007):return reject('NO_ROOT_ATTACHMENT')
  65 be=max(1,round(.6*(strong_ids[-1]+1)));body_depth=depth[:be][strong[:be]]
  66 body=float(np.median(body_depth)) if len(body_depth) else float(depth[strong_ids[0]])
  67 win=px(scale,.021);ahead=px(scale,.035)
  68 ceiling=len(xx)-1
  72 sm=median_filter(depth,size=max(3,2*px(scale,.006)+1),mode='nearest')
  73 separation=px(scale,.04)
  74 j=np.arange(max(2*separation,px(scale,.15)),len(sm)-separation)
  76 low=depth[j]<np.maximum(2*noise,.14*body)
  77 decline=(sm[j-2*separation]>np.maximum(2.5*depth[j],.35*body)) & (sm[j-separation]>1.3*depth[j])
  82 tail=depth[cut+1:]
  83 if len(tail)<px(scale,.12):continue
  84 before=sm[cut-2*separation]
  85 if np.percentile(tail,85)>.80*before:continue
  86 samples=tail[:px(scale,.22)].astype(float)
  87 samples-=median_filter(samples,size=2*px(scale,.018)+1,mode="nearest")
  88 corr=0.
  89 for lag in range(px(scale,.009),px(scale,.035)+1):
  92 if den and len(samples)>3*lag:
  93 a2=samples[:-2*lag];b2=samples[2*lag:]
  94 d2=np.linalg.norm(a2)*np.linalg.norm(b2)
  95 if d2:
  96 corr=max(corr,min(float(a@b/den),float(a2@b2/d2)))
  97 if corr>.60:
 104 ceiling=min(ceiling,trough-1)
 107 if end+1<px(scale,.031):break
 108 sl=slice(max(0,end-win+1),end+1)
 109 if obs[sl].sum()<np.ceil(2*win/3):continue
 111 if ex+ahead>=gray.shape[1]:return reject('ROI_BOUNDARY')
 112 slope=(ey-yy[max(0,end-win+1)])/max(1,min(end,win-1))
 113 fx=np.arange(ex+1,ex+ahead+1)
 114 fy=np.clip(np.rint(ey+slope*(fx-ex)).astype(int),0,len(gray)-1)
 115 n=min(ahead,len(xx)-end-1);fy[:n]=yy[end+1:end+1+n]
 118 strong_gate=(strong[end] and strong[sl].sum()>=np.ceil(2*win/3)
 119 and local>=max(.18*body,2*noise,front+.35*min(mad,3*noise)) and local>front)
 120 smooth=float(np.mean(np.abs(np.diff(yy[sl])-slope))) if end>0 and len(yy[sl])>1 else 0.
 121 prior=depth[max(0,end-px(scale,.09)):max(1,end-win+1)]
 123 taper=(local>max(1.6*front,2.5*max(noise,mad),.25*nearby_body)
 124 and smooth<.85 and float(score[sl].mean())>=.80)
 128 if not allowed:audit['taper_rejections']=audit.get('taper_rejections',0)+1
 130 if (not strong_gate and not taper and support is not None and waived and ex>waived[0]
 131 and why in (1,2) and limit<len(arr) and end>=limit-px(scale,.014)
 132 and strong[end] and strong[sl].mean()>=.65):
 135 left_pts=arr[max(0,end-win+1):end+1,:2].astype(int)
 136 right_pts=arr[limit:limit+ahead,:2].astype(int)
 137 if len(right_pts)>=px(scale,.014):
 139 confirmed=(lt is not None and rt is not None and lt['good'].mean()>=.75 and
 140 rt['good'].mean()<=.25 and rt['dc'].mean()<.5*lt['dc'].mean())
 143 use=np.union1d(strong_ids[strong_ids<=end],idx[(idx<=end)&(idx>end-win)]) if taper else strong_ids[strong_ids<=end]
 145 dist=np.linalg.norm(np.diff(np.vstack(([x,seed],pts)),axis=0),axis=1).sum()
 146 if strong[:px(scale,.028)].mean()<.65 or np.linalg.norm(pts[-1]-[x,seed])/max(1.,dist)<.65:
 148 bridge=gray[min(seed,y):max(seed,y)+1,x]
 149 if len(bridge)>px(scale,.007) and bridge.max()>np.median(gray[:,x]):return reject('BRIGHT_ROOT_GAP')
 153 return dict(status='VALID',points=points,tip=points[-1],audit=audit)
```

predict

```python
 163 support=Support(raw,fixed,sl,(left,top),np.median(starts,axis=0),scale,noise,contrast)
 167 bonus=np.where((sig>=.55)&(sig<1.),np.clip(bonus,0,.08),0).astype(np.float32)
 168 bonus[:,:front+px(scale,.2)+1]=0
 169 ref_time=[];audits=[];cache={};mid=float(np.median([p[1] for p in starts]))
 179 ref['before_tip']=[oldtip[0]+left,oldtip[1]+top]
 184 rec['rank_bonus']=rank['weight'];rec['tier']=rank.get('tier',0)
 193 for j in range(3):event[j]+=left
 197 result=competition.predict((sl,(left,top),starts,sig,np.clip(resp/contrast,0,1)*255,scale,front),bonus,candidate)
```

candidate

```python
 179 ref['before_tip']=[oldtip[0]+left,oldtip[1]+top]
 184 rec['rank_bonus']=rank['weight'];rec['tier']=rank.get('tier',0)
 193 for j in range(3):event[j]+=left
```

## research\notch_identity_v32\terminal.py

prepare

```python
  14 def prepare(raw,hint,scale,stage='v3_2'):
  16 if stage in (*previous.STAGES,'s3t'):return previous.prepare(raw,hint,scale,stage)
  22 top=max(0,front[1]-px(scale,.55));left=max(0,min(x for x,y in starts)-px(scale,.035))
  23 sl=np.s_[top:front[1]+px(scale,.55)+1,left:]
  25 gray=raw_band.astype(np.float32);resp=np.zeros_like(gray)
  26 material=black+.17*contrast
  27 for frac in (.007,.014,.024):
  29 if 2*r<len(gray):
  30 side=np.minimum(gray[:-2*r],gray[2*r:])
  31 resp[r:-r]=np.maximum(resp[r:-r],np.where(side>material,side-gray[r:-r],0))
  32 smooth=cv2.GaussianBlur(resp,(0,0),max(.01,scale/288),max(.01,.65*scale/288))
  33 evidence=.55*resp+.45*smooth
  34 stride=px(scale,.014)
  35 residual=(gray-cv2.medianBlur(raw_band,3))[::stride,::stride]
  36 noise=max(contrast*.006,float(1.4826*np.median(abs(residual-np.median(residual)))),1e-6)
  37 col=np.percentile(evidence[::px(scale,.01)],85,axis=0).astype(np.float32)
  38 local=median_filter(col,size=2*px(scale,.05)+1,mode='nearest')
  41 window=2*px(scale,.05)+1
  42 mean=cv2.blur(col.reshape(1,-1),(window,1)).ravel()
  44 floor=contrast*.023
  45 signal=np.ascontiguousarray(evidence/np.maximum(floor,envelope+1.8*noise))
  46 return (sl,(left,top),[(x-left,y-top) for x,y in starts],signal,resp,scale,front[0]-left,raw_band,noise,stage,contrast)
```

follow

```python
  50 x,y=start;r=px(scale,.014)
  51 seed=max(range(max(0,y-r),min(len(gray),y+r+1)),key=lambda j:min(4.,sig[j,x])-.35*abs(j-y)*288/scale)
  52 track,loss,reconnections,stop=trace_windowed(sig,bonus,x,seed,px(scale,.07),px(scale,.076),px(scale,.017),px(scale,.014),
  53 px(scale,.35),px(scale,.045),px(scale,.05),.80)
  54 audit=dict(first_loss=int(loss) if loss>=0 else None,reconnections=int(reconnections),
  59 arr=np.array(track);xx,yy=arr[:,:2].astype(int).T;score=arr[:,2];depth=resp[yy,xx]
  60 distal=stage in ('distal','reference','v3_2');same=stage=='v3_2'
  65 if limit==0:return reject('GEOMETRY_CUT_AT_ROOT')
  67 floor=.016*contrast
  68 strong=(score>=1)&(depth>=floor)
  69 obs= (score>=.55)&(depth>=floor)
  71 if not len(strong_ids) or strong_ids[0]>px(scale,.007):return reject('NO_ROOT_ATTACHMENT')
  72 be=max(1,round(.6*(strong_ids[-1]+1)));body_depth=depth[:be][strong[:be]]
  73 body=float(np.median(body_depth)) if len(body_depth) else float(depth[strong_ids[0]])
  74 win=px(scale,.021);ahead=px(scale,.035)
  75 ceiling=len(xx)-1
  79 sm=median_filter(depth,size=max(3,2*px(scale,.006)+1),mode='nearest')
  80 separation=px(scale,.04)
  81 j=np.arange(max(2*separation,px(scale,.15)),len(sm)-separation)
  83 low=depth[j]<np.maximum(2*noise,.14*body)
  84 decline=(sm[j-2*separation]>np.maximum(2.5*depth[j],.35*body)) & (sm[j-separation]>1.3*depth[j])
  89 tail=depth[cut+1:]
  90 if len(tail)<px(scale,.12):continue
  91 before=sm[cut-2*separation]
  92 if np.percentile(tail,85)>.80*before:continue
  93 samples=tail[:px(scale,.22)].astype(float)
  94 samples-=median_filter(samples,size=2*px(scale,.018)+1,mode="nearest")
  95 corr=0.
  96 for lag in range(px(scale,.009),px(scale,.035)+1):
  99 if den and len(samples)>3*lag:
 100 a2=samples[:-2*lag];b2=samples[2*lag:]
 101 d2=np.linalg.norm(a2)*np.linalg.norm(b2)
 102 if d2:
 103 corr=max(corr,min(float(a@b/den),float(a2@b2/d2)))
 104 if corr>.60:
 109 ceiling=min(ceiling,trough-1)
 112 if end+1<px(scale,.031):break
 113 sl=slice(max(0,end-win+1),end+1)
 114 if obs[sl].sum()<np.ceil(2*win/3):continue
 116 if ex+ahead>=gray.shape[1]:return reject('ROI_BOUNDARY')
 117 slope=(ey-yy[max(0,end-win+1)])/max(1,min(end,win-1))
 118 fx=np.arange(ex+1,ex+ahead+1)
 119 fy=np.clip(np.rint(ey+slope*(fx-ex)).astype(int),0,len(gray)-1)
 120 n=min(ahead,len(xx)-end-1);fy[:n]=yy[end+1:end+1+n]
 123 strong_gate=(strong[end] and strong[sl].sum()>=np.ceil(2*win/3)
 124 and local>=max(.18*body,2*noise,front+.35*min(mad,3*noise)) and local>front)
 125 smooth=float(np.mean(np.abs(np.diff(yy[sl])-slope))) if end>0 and len(yy[sl])>1 else 0.
 126 prior=depth[max(0,end-px(scale,.09)):max(1,end-win+1)]
 128 taper=(local>max(1.6*front,2.5*max(noise,mad),.25*nearby_body)
 129 and smooth<.85 and float(score[sl].mean())>=.80)
 133 if not allowed:audit['taper_rejections']=audit.get('taper_rejections',0)+1
 136 use=np.union1d(strong_ids[strong_ids<=end],idx[(idx<=end)&(idx>end-win)]) if taper else strong_ids[strong_ids<=end]
 138 dist=np.linalg.norm(np.diff(np.vstack(([x,seed],pts)),axis=0),axis=1).sum()
 139 if strong[:px(scale,.028)].mean()<.65 or np.linalg.norm(pts[-1]-[x,seed])/max(1.,dist)<.65:
 141 bridge=gray[min(seed,y):max(seed,y)+1,x]
 142 if len(bridge)>px(scale,.007) and bridge.max()>np.median(gray[:,x]):return reject('BRIGHT_ROOT_GAP')
 146 return dict(status='VALID',points=points,tip=points[-1],audit=audit)
```

predict

```python
 153 if len(prepared)<=9 or prepared[9] not in STAGES:return previous.predict(prepared,bonus)
 157 bonus=np.where((sig>=.55)&(sig<1.),np.clip(bonus,0,.08),0).astype(np.float32)
 158 bonus[:,:front+px(scale,.2)+1]=0
 159 ref_time=[];audits=[];cache={};mid=float(np.median([p[1] for p in starts]))
 163 if rec['tip'] and stage in ('reference','v3_2') and fixed is not None:
 164 pts=np.asarray(rec['points']);span=px(scale,.028)
 166 if len(pts)>2*span:
 167 dx,dy=np.diff(pts[[-2*span,-span,-1]],axis=0).T
 168 bend=abs(np.diff(np.arctan2(dy,dx))[0])>np.deg2rad(20)
 172 key=pts[pts[:,0]>=pts[-1,0]-px(scale,.15)].tobytes()
 174 t0=time.perf_counter()
 176 ref_time.append(time.perf_counter()-t0)
 181 a=rec['audit'];ref['before_tip']=[oldtip[0]+left,oldtip[1]+top]
 186 if not reason and stage=='v3_2' and guards.open_rim(rec['points'],front,mid,scale,gray):
 192 for j in range(3):event[j]+=left
 195 result=competition.predict((sl,(left,top),starts,sig,np.clip(resp/contrast,0,1)*255,scale,front),bonus,candidate)
```

candidate

```python
 163 if rec['tip'] and stage in ('reference','v3_2') and fixed is not None:
 164 pts=np.asarray(rec['points']);span=px(scale,.028)
 166 if len(pts)>2*span:
 167 dx,dy=np.diff(pts[[-2*span,-span,-1]],axis=0).T
 168 bend=abs(np.diff(np.arctan2(dy,dx))[0])>np.deg2rad(20)
 172 key=pts[pts[:,0]>=pts[-1,0]-px(scale,.15)].tobytes()
 174 t0=time.perf_counter()
 176 ref_time.append(time.perf_counter()-t0)
 181 a=rec['audit'];ref['before_tip']=[oldtip[0]+left,oldtip[1]+top]
 186 if not reason and stage=='v3_2' and guards.open_rim(rec['points'],front,mid,scale,gray):
 192 for j in range(3):event[j]+=left
```

## research\notch_identity_v32\guards.py

width

```python
   9 lo=max(0,y-r);hi=min(gray.shape[0]-1,y+r)
  11 half=(center+min(float(gray[lo,x]),float(gray[hi,x])))/2
  13 while a>lo and gray[a-1,x]<=half:a-=1
  14 while b<hi and gray[b+1,x]<=half:b+=1
  15 return b-a+1
```

inspect_track

```python
  19 """Replay V3.1 provisional events before any point is admitted to competition."""
  20 gap=max(1,round(.014*scale));recover=max(1,round(.05*scale))
  21 span=max(2,round(.027*scale));near=round(.35*scale)
  22 weak=0;pending=-1;dark_gap=0
  25 x=int(arr[i,0]);v=arr[i,2]
  27 dark_gap=dark_gap+1 if v<.85 else 0
  28 if dark_gap>=gap:return i-dark_gap+1,1,events
  30 if i>=3*span:
  32 if arr[k,2]<.85 and arr[k-1,2]<1. and arr[k-span,0]-start>near:
  33 m1=(arr[k-1,1]-arr[k-span,1])/max(1,span-1)
  34 m2=(arr[i,1]-arr[k+1,1])/max(1,span-1)
  35 if abs(math.atan(m2)-math.atan(m1))>math.radians(22):
  36 return k-1,2,events
  37 weak=0 if v>=.8 else weak+1
  38 if weak>=gap and pending<0:pending=i-weak+1
  39 if pending<0 or i-pending+1<gap+recover:continue
  40 left=i-recover+1
  41 if v<1 or np.minimum(4.,arr[left:i+1,2]).mean()<1.05 or (arr[left:i+1,2]>=1).mean()<.8:continue
  42 good=True;residual=-1.;ratio=-1.
  43 if pending>=span+1:
  45 after=arr[left:i+1]
  46 xm=pre[:,0].mean();ym=pre[:,1].mean()
  47 slope=np.sum((pre[:,0]-xm)*(pre[:,1]-ym))/max(1.,np.sum((pre[:,0]-xm)**2))
  48 residual=np.median(np.abs(after[:,1]-(ym+slope*(after[:,0]-xm))))
  49 rad=max(1,round(.023*scale))
  50 wa=np.median(np.array([width(gray,int(vv[0]),int(vv[1]),rad) for vv in pre]))
  51 wb=np.median(np.array([width(gray,int(vv[0]),int(vv[1]),rad) for vv in after]))
  52 ratio=max(wa,wb)/max(1.,min(wa,wb))
  53 good=residual<=max(1.,.012*scale) and ratio<=2.
  57 events.append((int(arr[pending,0]),int(arr[left,0]),x,residual,ratio,int(accepted)))
  58 if not accepted:return pending,3,events
  59 weak=0;pending=-1
  60 return len(arr),0,events
```

taper_evidence

```python
  63 win=px(scale,.021)
  64 if i+1<3*win:return False,{}
  65 blocks=np.median(depth[i-3*win+1:i+1].reshape(3,win),axis=1)
  66 tail=blocks[-1]
  68 decay=blocks[0]>=tail and np.all(np.diff(blocks)<=max(noise,.10*blocks[0]))
  69 y=yy[i-3*win+1:i+1]
  70 angles=np.arctan((y[win-1::win]-y[::win])/max(1,win-1))
  71 turn=float(np.rad2deg(abs(angles[-1]-np.median(angles[:2]))))
  72 clear=front<=1.5*noise and tail>=3*max(front,noise) and mad<=2.5*noise
  73 return bool(clear and decay and turn<=18),dict(clear=bool(clear),decay=bool(decay),angle=turn)
```

rebound_cut

```python
  78 win=px(scale,.017)
  79 if len(depth)<5*win:return len(depth)
  80 lo=max(3*win,len(depth)-px(scale,.18))
  81 for k in range(lo,len(depth)-2*win):
  82 if depth[k]>2*noise:continue
  84 before=np.median(depth[k-2*win:k-win]);after=np.median(depth[k+win:k+2*win])
  87 earlier=np.median(depth[k-3*win:k-2*win])
  88 next_block=np.median(depth[k:k+2])
  89 later=np.median(depth[k+win//2+1:k+win+2])
  90 if (win<=2 and earlier>before>2.5*max(depth[k],noise) and next_block<=2.5*noise and
  91 later>max(3*noise,2*depth[k]) and after>max(3*noise,2*depth[k])):
  93 if valley<=2*noise and before>max(4*noise,2.5*valley) and after>max(4*noise,2.5*valley):
```

open_rim

```python
  99 if len(pts)<2:return False
 101 drift=y[-1]-y[0];offset=y[0]-mid_y
 102 return bool((x[-1]-front)/scale<.06 and abs(offset)>max(px(scale,.012),2*width(gray,x[0],y[0],px(scale,.02))) and
 103 drift*offset>0 and abs(drift)/max(1,x[-1]-x[0])>.45)
```

## research\notch_identity_v31\terminal.py

prepare

```python
  14 def prepare(raw,hint,scale,stage='v3_1'):
  16 return v3.prepare(raw,hint,scale,stage)
  17 level=STAGES.index(stage)+1
  18 found,black,contrast=locate_root(raw,hint,scale,level==4)
  22 top=max(0,front[1]-px(scale,.55));left=max(0,min(x for x,y in starts)-px(scale,.035))
  23 sl=np.s_[top:front[1]+px(scale,.55)+1,left:]
  25 if level==1:
  26 signal,resp,noise=v3.valley_image(raw_band,scale)
  28 gray=raw_band.astype(np.float32);resp=np.zeros_like(gray)
  29 material=black+.17*contrast if level==4 else 40
  30 for frac in (.007,.014,.024):
  32 if 2*r<len(gray):
  33 side=np.minimum(gray[:-2*r],gray[2*r:])
  34 resp[r:-r]=np.maximum(resp[r:-r],np.where(side>material,side-gray[r:-r],0))
  35 smooth=cv2.GaussianBlur(resp,(0,0),max(.01,scale/288),max(.01,.65*scale/288))
  36 evidence=.55*resp+.45*smooth
  37 stride=px(scale,.014)
  38 residual=(gray-cv2.medianBlur(raw_band,3))[::stride,::stride]
  39 noise=max(contrast*.006 if level==4 else 1.,float(1.4826*np.median(abs(residual-np.median(residual)))),1e-6)
  40 col=np.percentile(evidence[::px(scale,.01)],85,axis=0).astype(np.float32)
  41 local=median_filter(col,size=2*px(scale,.05)+1,mode='nearest')
  42 floor=contrast*.023 if level==4 else 4.
  43 signal=np.ascontiguousarray(evidence/np.maximum(floor,np.maximum(col,local)+1.8*noise))
  44 return (sl,(left,top),[(x-left,y-top) for x,y in starts],signal,resp,scale,front[0]-left,raw_band,noise,stage,contrast)
```

trace_windowed

```python
  52 slope=0.
  53 weak=0
  54 pending=-1
  55 first_loss=-1
  56 recovered=0
  57 stop=0
  58 while x+1<w:
  59 n=min(horizon,w-x-1); lo=max(0,y-band); hi=min(h,y+band+1); height=hi-lo
  60 prev=np.full(height,-1e10);prev[y-lo]=0.
  61 parents=np.zeros((n,height),np.int32)
  63 nxt=np.full(height,-1e10)
  65 best=-1e10
  66 for j in range(max(0,i-2),min(height,i+3)):
  68 score=prev[j]-.40*abs(dy)-.28*abs(dy-slope)
  71 v=sig[lo+i,x+t+1]
  72 drift=abs(lo+i-y-slope*(t+1))
  73 nxt[i]=best+min(v,4.)-1.1+bonus[lo+i,x+t+1]-.10*drift/max(1.,n*.3)
  75 idx=np.argmax(prev);line=np.empty(n,np.int32)
  76 for t in range(n-1,-1,-1):
  79 yy=line[t];x+=1;v=sig[yy,x]
  80 if v>=1.:
  81 slope=.75*slope+.25*(yy-y)
  84 weak=0 if v>=threshold else weak+1
  85 if weak>=gap and pending<0:
  87 if first_loss<0:first_loss=pts[pending][0]
  90 return pts if soft<1. else pts[:pending],first_loss,recovered,1
  91 if pending>=0:
  95 return pts[:pending],first_loss,recovered,2
  97 support=0.;count=0
  99 sv=pts[k][2];support+=min(4.,sv);count+=sv>=1.
 100 if support/recover>=1.05 and count>=.8*recover and v>=1.:
 101 pending=-1;recovered+=1;weak=0
 102 if pending>=0:
 103 return pts[:pending],first_loss,recovered,3
```

follow

```python
 108 x,y=start;r=px(scale,.014)
 109 seed=max(range(max(0,y-r),min(len(gray),y+r+1)),key=lambda j:min(4.,sig[j,x])-.35*abs(j-y)*288/scale)
 110 track,loss,reconnections,stop=trace_windowed(sig,bonus,x,seed,px(scale,.07),px(scale,.076),px(scale,.017),px(scale,.014),
 111 px(scale,.35),px(scale,.045),px(scale,.05),.80 if level>=2 else 1.)
 112 audit=dict(first_loss=int(loss) if loss>=0 else None,reconnections=int(reconnections),
 117 arr=np.array(track);xx,yy=arr[:,:2].astype(int).T;score=arr[:,2];depth=resp[yy,xx]
 118 floor=.016*contrast if level==4 else 3.
 119 strong=(score>=1)&(depth>=floor)
 120 obs=strong if level==1 else (score>=.55)&(depth>=floor)
 122 if not len(strong_ids) or strong_ids[0]>px(scale,.007):return reject('NO_ROOT_ATTACHMENT')
 123 be=max(1,round(.6*(strong_ids[-1]+1)));body_depth=depth[:be][strong[:be]]
 124 body=float(np.median(body_depth)) if len(body_depth) else float(depth[strong_ids[0]])
 125 win=px(scale,.021);ahead=px(scale,.035)
 126 ceiling=len(xx)-1
 127 if level>=2:
 130 sm=median_filter(depth,size=max(3,2*px(scale,.006)+1),mode='nearest')
 131 separation=px(scale,.04)
 132 j=np.arange(max(2*separation,px(scale,.15)),len(sm)-separation)
 134 low=depth[j]<np.maximum(2*noise,.14*body)
 135 decline=(sm[j-2*separation]>np.maximum(2.5*depth[j],.35*body)) & (sm[j-separation]>1.3*depth[j])
 140 tail=depth[cut+1:]
 141 if len(tail)<px(scale,.12):continue
 142 before=sm[cut-2*separation]
 143 if np.percentile(tail,85)>.80*before:continue
 144 samples=tail[:px(scale,.22)].astype(float)
 145 samples-=median_filter(samples,size=2*px(scale,.018)+1,mode="nearest")
 146 corr=0.
 147 for lag in range(px(scale,.009),px(scale,.035)+1):
 150 if den and len(samples)>3*lag:
 151 a2=samples[:-2*lag];b2=samples[2*lag:]
 152 d2=np.linalg.norm(a2)*np.linalg.norm(b2)
 153 if d2:
 154 corr=max(corr,min(float(a@b/den),float(a2@b2/d2)))
 155 if corr>.60:
 158 if end+1<px(scale,.031):break
 159 sl=slice(max(0,end-win+1),end+1)
 160 if obs[sl].sum()<np.ceil(2*win/3):continue
 162 if ex+ahead>=gray.shape[1]:return reject('ROI_BOUNDARY')
 163 slope=(ey-yy[max(0,end-win+1)])/max(1,min(end,win-1))
 164 fx=np.arange(ex+1,ex+ahead+1)
 165 fy=np.clip(np.rint(ey+slope*(fx-ex)).astype(int),0,len(gray)-1)
 166 n=min(ahead,len(xx)-end-1);fy[:n]=yy[end+1:end+1+n]
 170 strong_gate=(strong[end] and strong[sl].sum()>=np.ceil(2*win/3)
 171 and local*(1+assist if level<3 else 1)>=max(.18*body,2*noise,front+.35*min(mad,3*noise)) and local>front)
 172 smooth=float(np.mean(np.abs(np.diff(yy[sl])-slope))) if end>0 and len(yy[sl])>1 else 0.
 173 prior=depth[max(0,end-px(scale,.09)):max(1,end-win+1)]
 175 taper=(level>=2 and local>max(1.6*front,2.5*max(noise,mad),.25*nearby_body)
 176 and smooth<.85 and float(score[sl].mean())>=.80)
 179 use=np.union1d(strong_ids[strong_ids<=end],idx[(idx<=end)&(idx>end-win)]) if taper else strong_ids[strong_ids<=end]
 181 dist=np.linalg.norm(np.diff(np.vstack(([x,seed],pts)),axis=0),axis=1).sum()
 182 if strong[:px(scale,.028)].mean()<.65 or np.linalg.norm(pts[-1]-[x,seed])/max(1.,dist)<.65:
 184 bridge=gray[min(seed,y):max(seed,y)+1,x]
 185 if len(bridge)>px(scale,.007) and bridge.max()>np.median(gray[:,x]):return reject('BRIGHT_ROOT_GAP')
 189 return dict(status='VALID',points=points,tip=points[-1],audit=audit)
```

predict

```python
 195 if len(prepared)==10:return v3.predict(prepared,bonus)
 197 level=STAGES.index(stage)+1
 199 if level<3:
 200 bonus=bonus*np.clip(sig-1.,0,1)
 202 bonus=np.where((sig>=.55)&(sig<1.),np.clip(bonus,0,.08),0).astype(np.float32)
 203 bonus[:,:front+px(scale,.2)+1]=0
 208 reason=topology.check(gray,rec['points'],front,scale,level==4)
 217 rank_resp=np.clip(resp/contrast,0,1)*255 if level==4 else resp
```

candidate

```python
 208 reason=topology.check(gray,rec['points'],front,scale,level==4)
```

## research\notch_identity_v31\topology.py

check

```python
  12 pad=px(scale,.1)
  13 left=max(0,x[0]-pad);top=max(0,y.min()-pad)
  14 patch=raw[top:y.max()+pad+1,left:x[-1]+pad+1]
  15 background=float(np.percentile(patch,75))
  17 mask=(patch<background-.30*(background-ink)).astype(np.uint8)
  19 r=px(scale,.004)
  20 kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
  21 mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel)
  22 contours,tree=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
  23 for c,h in zip(contours,tree[0] if tree is not None else []):
  24 if h[3]<0 or cv2.contourArea(c)/scale**2<.00045:
  26 bx,by,bw,bh=cv2.boundingRect(c)
  27 if bw/scale>.045 and bh/scale>.014 and abs(left+bx+bw-1-x[-1])<.033*scale and top+by-.025*scale<=y[-1]<=top+by+bh+.025*scale:
  29 dx=max(1,x[-1]-x[0])
  30 if (x[-1]-front)/scale<.06 and abs(y[-1]-y[0])/dx>.65:
  31 if np.mean(raw[y,x]<background-.65*(background-ink))>.8:
```