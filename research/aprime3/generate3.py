"""NEW_DEV generation only. This process writes labels separately from inference."""
from common3 import *
FAMILIES=['STRONG_FALSE_TAIL','TRUE_LONG_MATCHED','STATIC_CROSS_THROUGH','WEAK_FADE','CURVE_55','CURVE_75','S_CURVE',
 'PREEXISTING_DARKENING','STATIC_DARKENING_NEGATIVE','STATIC_LINE_NEGATIVE','NO_CRACK','HOLE_MOTION','LOW_TEXTURE','SATURATED','LOCAL_AFFINE','PHOTOMETRIC_CHANGE','ROI_BOUNDARY']

def background(n,kind,rng):
 if kind==0:
    # Multiplicative bounded cascade, independent log-intensity across dyadic levels.
    a=np.ones((n,n),np.float32)
    for side in [4,8,16,32,64,128]:
        q=np.exp(rng.normal(0,.08,(side,side))).astype(np.float32)
        a*=cv2.resize(q,(n,n),interpolation=cv2.INTER_CUBIC)
    a=np.log(np.maximum(a,.01))
 elif kind==1:
    # Random-site Voronoi cell tessellation, not the old rectangular grain grid.
    mask=np.full((n,n),255,np.uint8);xy=rng.integers(0,n,(n*n//250,2));mask[xy[:,1],xy[:,0]]=0
    _,labels=cv2.distanceTransformWithLabels(mask,cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
    colors=rng.normal(0,1,int(labels.max())+1).astype(np.float32);a=cv2.GaussianBlur(colors[labels],(0,0),.9)
 else:
    # Finite random curved abrasion marks; sparse line impulses, not filtered white noise.
    a=np.zeros((n,n),np.float32)
    for _ in range(n*n//160):
        x,y=rng.uniform(0,n,2);ang=rng.uniform(0,2*np.pi);ll=rng.uniform(4,15)
        p=np.array([[x,y],[x+ll*np.cos(ang),y+ll*np.sin(ang)],[x+2*ll*np.cos(ang+.15),y+2*ll*np.sin(ang+.15)]])
        cv2.polylines(a,[np.rint(p).astype(np.int32)],False,float(rng.normal(0,2)),1,cv2.LINE_AA)
    a=cv2.GaussianBlur(a,(0,0),.8)
 a=(a-a.mean())*(3.2/max(1e-6,float(a.std())))
 return 207+a+rng.normal(0,.4,(n,n))

def valley(shape,p,sigma,contrast):
 m=np.full(shape,255,np.uint8);cv2.polylines(m,[np.rint(p*4).astype(np.int32)],False,0,1,cv2.LINE_8,shift=2)
 dist=cv2.distanceTransform(m,cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
 return contrast*np.exp(-.5*(dist/sigma)**2)

def generate():
 folder=RUN/'04_NEW_DEV';images=folder/'inputs';assert not images.exists(),'Use a new RunId; do not silently replace DEV'
 sources={str(p.relative_to(ROOT)):sha(p) for p in SOURCE.glob('*.py')}
 save(RUN/'00_protocol/pre_NEW_DEV_source_hashes.json',dict(utc=utc(),hashes=sources,role='DEV_PREREGISTRATION_NOT_TEST_FREEZE',seed_root=119051113,reps=6,backgrounds=3,families=FAMILIES))
 mi=[];gt=[]
 for bg in range(3):
  for rep in range(6):
   for family in FAMILIES:
    paired=family in FAMILIES[:2];identical=family in ['PREEXISTING_DARKENING','STATIC_DARKENING_NEGATIVE']
    family_seed=0 if paired else 7 if identical else FAMILIES.index(family)
    seed=119051113+bg*100000+rep*1000+family_seed;rng=np.random.default_rng(seed);n=[512,608][rep%2]
    base=background(n,bg,rng);o=np.array([.18*n,.46*n]);d=.34*n;rp=np.array([o+[0,-d/2],o+[0,d/2]]);rad=.043*n
    cv2.circle(base,tuple(o.astype(int)),round(rad),5,-1);root=o+[rad-1,0];t=np.linspace(0,1,600)
    theta=.025*np.sin(2*np.pi*t)
    if family in ['CURVE_55','CURVE_75']:theta=np.deg2rad(55 if family=='CURVE_55' else 75)*t
    if family=='S_CURVE':theta=.85*np.sin(2*np.pi*t)
    p=root+np.cumsum(np.column_stack([np.cos(theta),np.sin(theta)])*.27*n/len(t),axis=0)
    tail=p[-1]+np.column_stack([.23*n*t,.004*n*np.sin(np.pi*t)]);long=np.vstack([p,tail[1:]])
    w=[.85,1.1,1.4][rep%3];contrast=[38.,48.,62.][rep%3]
    ref=base.copy();cur=base.copy();positive=family not in ['STATIC_DARKENING_NEGATIVE','STATIC_LINE_NEGATIVE','NO_CRACK','HOLE_MOTION'];observable=positive and family!='SATURATED'
    if paired:
        cur=base-np.maximum(valley(base.shape,p,w,contrast),valley(base.shape,tail,w*1.4,.8*contrast))
        if family=='STRONG_FALSE_TAIL':ref-=valley(base.shape,tail,w*1.4,[8,12,18][rep%3])
        else:p=long
    elif identical:
        p=long;ref-=valley(base.shape,p,w,14.);cur-=valley(base.shape,p,w,48.)
    elif family=='STATIC_LINE_NEGATIVE':ref-=valley(base.shape,p,w,40);cur=ref.copy()
    elif family in ['NO_CRACK','HOLE_MOTION']:pass
    elif family=='SATURATED':ref[:]=255;cur[:]=255
    elif family=='LOW_TEXTURE':
        ref[:]=207;cv2.circle(ref,tuple(o.astype(int)),round(rad),5,-1);cur=ref-valley(base.shape,p,w,contrast)
    else:
        if family=='STATIC_CROSS_THROUGH':
            q=p[300];fiber=q+np.column_stack([.04*n*(t-.5),.25*n*(t-.5)]);ref-=valley(base.shape,fiber,1.,30);base=ref.copy()
        if family=='WEAK_FADE':
            line=valley(base.shape,p,w,14);xx=np.indices(base.shape)[1];line*=np.clip(1.-.55*(xx-root[0])/(.27*n),.45,1);cur=base-line
        else:cur=base-valley(base.shape,p,w,contrast)
    cid=f'NEWDEV_{bg}_{rep}_{family}';refpath=images/cid/'reference.png';ref8=np.clip(np.rint(ref),0,255).astype(np.uint8);refsha=put(refpath,ref8)
    for f in [1,2,3]:
        ang=.001*(f-2);R=np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]])
        M=np.column_stack([R,np.array([.45*f,-.3*f])]);a=cur.copy()
        if family=='LOCAL_AFFINE':M[:,:2]=np.array([[1.006,.004],[.003,.994]])@R
        if family=='PHOTOMETRIC_CHANGE':a=.9*a+17
        if family=='HOLE_MOTION':M[0,2]+=2
        if family=='ROI_BOUNDARY':M[0,2]+=.27*n
        im=cv2.warpAffine(a.astype(np.float32),M,(n,n),borderValue=207)
        im=np.clip(np.rint(im+rng.normal(0,.3,im.shape)),0,255).astype(np.uint8);cp=apply(M,rp);tp=apply(M,p)
        file=images/cid/f'{f:02d}.png';imsha=put(file,im)
        mi.append(dict(case_id=cid,frame_id=f,input_image=str(file),reference_image=str(refpath),points=cp.tolist(),reference_points=rp.tolist(),image_sha=imsha,reference_sha=refsha,mode='auto'))
        gt.append(dict(case_id=cid,frame_id=f,family=family,background=bg,seed=seed,pair_id=f'PAIR_{bg}_{rep}' if paired else None,
            identity_pair_id=f'IDENTITY_{bg}_{rep}' if identical else None,positive=positive,observable=observable,
            tip=tp[-1].tolist() if observable else None,path=tp.tolist() if observable else [],M_GT=M.tolist(),
            physical_growth_px=0 if family=='PREEXISTING_DARKENING' else None,definition='PROCEDURAL_VISIBLE_CENTERLINE_END_EVALUATOR_ONLY'))
 with (folder/'inference_manifest.jsonl').open('w',encoding='utf8') as f:
    for m in mi:dump_line(f,m)
 with (folder/'evaluator_GT.jsonl').open('w',encoding='utf8') as f:
    for z in gt:dump_line(f,z)
 csvout(folder/'generation_manifest.csv',mi);save(folder/'input_seal.json',dict(manifest_sha=sha(folder/'inference_manifest.jsonl'),GT_sha=sha(folder/'evaluator_GT.jsonl'),frames=len(mi),utc=utc(),role='NEW_DEV_NOT_TEST'))
 print('NEWDEV GENERATED',len(mi),len(set(m['case_id'] for m in mi)),flush=True)

if __name__=='__main__':generate()
