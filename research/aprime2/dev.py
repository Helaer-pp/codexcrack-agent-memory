"""New material processes; procedural GT stays exclusively in offline evaluation."""
from common import *
from native_bridge import engine, stops
from candidates import propose

FAMILIES=['STRONG_FALSE_TAIL','TRUE_LONG_MATCHED','STATIC_CROSS_THROUGH','WEAK_FADE',
          'S_CURVE','CURVE_55','CURVE_75','STATIC_LINE_NEGATIVE','HOLE_MOTION',
          'LOW_TEXTURE','SATURATED','PHOTOMETRIC_CHANGE','ROI_BOUNDARY','LOCAL_MISREGISTRATION','PREEXISTING']
TEXTURE_VERSION=1 if '--v1' in sys.argv else 2

def material(n,kind,rng):
    if kind==0:
        # Compound Poisson shot field: independently placed small material grains.
        a=np.zeros((n,n),np.float32)
        for _ in range(n*n//90):
            x,y=rng.integers(0,n,2);cv2.circle(a,(int(x),int(y)),int(rng.integers(1,4)),float(rng.normal(0,5)),-1)
        a=cv2.GaussianBlur(a,(0,0),.7)
    elif kind==1:
        # Piecewise grain cells, independently coloured, smoothed grain boundaries.
        q=rng.normal(0,3,(n//9+1,n//9+1)).astype(np.float32)
        a=cv2.resize(q,(n,n),interpolation=cv2.INTER_NEAREST);a=cv2.GaussianBlur(a,(0,0),1.1)
    else:
        # Anisotropic abrasion field: finite-support moving-average noise.
        q=rng.normal(0,8,(n,n)).astype(np.float32)
        a=cv2.GaussianBlur(q,(7,3),1.8,.5)
    # DEV v2: sufficient material texture without changing validation thresholds.
    if TEXTURE_VERSION==2:a=(a-a.mean())*(3.2/max(float(a.std()),1e-6))
    return 205+a+rng.normal(0,.45,(n,n))

def valley(shape,p,sigma,contrast):
    mask=np.full(shape,255,np.uint8)
    cv2.polylines(mask,[np.rint(p*4).astype(np.int32)],False,0,1,cv2.LINE_8,shift=2)
    distance=cv2.distanceTransform(mask,cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    return contrast*np.exp(-.5*(distance/sigma)**2)

def case_images(kind,rep,family):
    shared='PAIR' if family in FAMILIES[:2] else family
    seed=611050700+kind*10000+rep*100+(['PAIR']+FAMILIES[2:]).index(shared)
    rng=np.random.default_rng(seed);n=[512,640][rep%2];base=material(n,kind,rng)
    o=np.array([.18*n,.47*n]);d=.34*n;rp=np.array([o+[0,-d/2],o+[0,d/2]])
    radius=.043*n;cv2.circle(base,tuple(o.astype(int)),round(radius),5,-1)
    t=np.linspace(0,1,650);p=o+[radius-1,0]+np.column_stack([.27*n*t,.003*n*np.sin(np.pi*t)])
    w=[.8,1.1,1.45][rep%3];contrast=[38,48,62][rep%3]
    if family in ['CURVE_55','CURVE_75','S_CURVE']:
        theta=(np.deg2rad(55 if family=='CURVE_55' else 75)*t) if family!='S_CURVE' else .8*np.sin(2*np.pi*t)
        p=o+[radius-1,0]+np.cumsum(np.column_stack([np.cos(theta),np.sin(theta)])*.30*n/len(t),axis=0)
    tail=p[-1]+np.column_stack([.23*n*t,.006*n*np.sin(np.pi*t)])
    full=np.vstack([p,tail[1:]])
    ref=base.copy();cur=base.copy();positive=family not in ['STATIC_LINE_NEGATIVE','HOLE_MOTION'];observable=positive and family!='SATURATED'
    if shared=='PAIR':
        # Identical current pixels. Reference carries a faint preexisting surface line.
        # Current tail contrast change is deliberately a plausible specular/photometric confound.
        short=valley(base.shape,p,w,contrast);long=valley(base.shape,tail,w*1.4,contrast*.80)
        cur=base-np.maximum(short,long)
        if family=='STRONG_FALSE_TAIL':ref=base-valley(base.shape,tail,w*1.4,[8,12,18][rep%3])
        else:p=full
    elif family=='STATIC_LINE_NEGATIVE':ref=base-valley(base.shape,p,w,contrast);cur=ref.copy()
    elif family=='HOLE_MOTION':cur=base.copy()
    elif family=='LOW_TEXTURE':
        ref=np.full_like(base,205);cv2.circle(ref,tuple(o.astype(int)),round(radius),5,-1);cur=ref-valley(base.shape,p,w,contrast)
    elif family=='SATURATED':
        ref=np.clip(base+70,0,255);cur=ref.copy()
    else:
        if family=='STATIC_CROSS_THROUGH':
            q=p[int(.48*len(p))];fiber=q+np.column_stack([.02*n*(t-.5),.25*n*(t-.5)])
            ref-=valley(base.shape,fiber,1.,32);base=ref.copy()
        if family=='PREEXISTING':ref-=valley(base.shape,p[:300],w,28)
        cur=base-valley(base.shape,p,w,10 if family=='WEAK_FADE' else contrast)
    ref=np.clip(np.rint(ref),0,255).astype(np.uint8);frames=[];gt=[]
    for f in (1,2,3):
        M=np.array([[1.,0.,.35*f],[0.,1.,-.25*f]])
        image=cur.copy();tp=p.copy()
        if family=='PHOTOMETRIC_CHANGE':image=.92*image+14
        if family=='LOCAL_MISREGISTRATION':
            yy,xx=np.mgrid[:n,:n];dx=2.5*np.sin(yy*8/n)
            image=cv2.remap(image.astype(np.float32),(xx+dx).astype(np.float32),yy.astype(np.float32),cv2.INTER_LINEAR)
            tp[:,0]-=2.5*np.sin(tp[:,1]*8/n)
        if family=='ROI_BOUNDARY':M[0,2]+=.38*n
        if family=='HOLE_MOTION':M[0,2]+=2
        im=cv2.warpAffine(image.astype(np.float32),M,(n,n),borderValue=205)
        im=np.clip(np.rint(im+rng.normal(0,.3,im.shape)),0,255).astype(np.uint8)
        points=apply(M,rp);tip=apply(M,tp)[-1] if observable else None
        if tip is not None and (tip[0]>=n-2 or tip[1]>=n-2):observable=False;tip=None
        frames.append((im,points,M));gt.append(dict(positive=positive,observable=observable,tip=tip,path=apply(M,tp) if observable else []))
    return ref,rp,frames,gt,seed

def run_dev(probe=False):
    guard();allrows=[];pairs=collections.defaultdict(dict);manifest=[]
    families=FAMILIES[:2] if probe else FAMILIES
    folder=RUN/('05_DEV/'+('probe' if probe else 'full')+('_v2' if TEXTURE_VERSION==2 else ''))
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/'predictions.jsonl').open('w',encoding='utf8') as out:
        for kind in range(3):
            for rep in range(6 if probe else 4):
                for family in families:
                    cid=f'DEV_{kind}_{rep}_{family}';ref,rp,frames,gts,seed=case_images(kind,rep,family)
                    fn=folder/'inputs'/cid/'reference.png';rsha=put(fn,ref)
                    e=engine(ref,rp,'auto',True);e.run(ref,rp,True)
                    for i,((im,points,M),gt) in enumerate(zip(frames,gts),1):
                        path=folder/'inputs'/cid/f'{i:02d}.png';ish=put(path,im)
                        a=e.run(im,points);z,over=stops(e);f=a['formal']
                        pool,seq,cost=propose(im,f['raw_path'],f['tip'],f['confirmed_tip'],f['width_px'],z)
                        err=float(np.linalg.norm(np.array(f['tip'])-gt['tip'])) if gt['observable'] and f['confirmed_tip'] else None
                        oracle=min([float(np.linalg.norm(np.array(c['xy'])-gt['tip'])) for c in pool],default=None) if gt['observable'] else None
                        patherr=min(np.linalg.norm(np.asarray(f['raw_path'])-gt['tip'],axis=1),default=1e6) if gt['observable'] and len(f['raw_path']) else None
                        row=dict(case_id=cid,pair_id=f'DEV_PAIR_{kind}_{rep}' if family in FAMILIES[:2] else None,
                            family=family,background=kind,frame_id=i,A_valid=f['confirmed_tip'],A_error=err,A_correct=err is not None and err<=8,
                            oracle_error=oracle,oracle_correct=oracle is not None and oracle<=8,candidate_count=len(pool),path_distance=patherr,
                            failure_class='PATH_DIVERGENCE' if patherr is not None and patherr>8 else 'CANDIDATE_OMISSION' if gt['observable'] and (oracle is None or oracle>8) else 'CANDIDATE_AVAILABLE' if gt['observable'] else 'NEGATIVE_OR_UNOBSERVABLE',
                            positive=gt['positive'],observable=gt['observable'],reference_image=str(fn),input_image=str(path),image_sha=ish,reference_sha=rsha,seed=seed)
                        allrows.append(row);dump_line(out,dict(**row,points=points,reference_points=rp,M_GT=M,GT=gt,A=a,tiles=z,pool=pool,profile=seq,candidate_cost=cost))
                        manifest.append(dict(case_id=cid,frame_id=i,input_image=str(path),input_sha256=ish,reference_sha256=rsha,points=points,reference_points=rp))
                        if row['pair_id']:pairs[row['pair_id'],i][family]=row
                    e.close()
                    print('DEV',cid,[(r['A_error'],r['oracle_error']) for r in allrows[-3:]],flush=True)
    paired=[]
    for (pid,i),q in pairs.items():
        a,b=q['STRONG_FALSE_TAIL'],q['TRUE_LONG_MATCHED'];assert a['image_sha']==b['image_sha'] and a['reference_sha']!=b['reference_sha']
        paired.append(dict(pair_id=pid,frame_id=i,same_current=True,different_reference=True,
            activated=bool(a['A_error'] is not None and a['A_error']>32 and b['A_correct']),
            A_false_error=a['A_error'],A_long_correct=b['A_correct'],short_oracle=a['oracle_correct'],long_oracle=b['oracle_correct']))
    activated={p['pair_id'] for p in paired if p['activated']}
    summary=dict(cases=len(set(x['case_id'] for x in allrows)),frames=len(allrows),activated_pairs=len(activated),
        activated_pair_frames=sum(x['activated'] for x in paired),backgrounds=len({x.split('_')[2] for x in activated}),
        pass_activation=len(activated)>=12 and len({x.split('_')[2] for x in activated})>=3,
        A_correct=sum(x['A_correct'] for x in allrows),oracle_correct=sum(x['oracle_correct'] for x in allrows))
    csvout(folder/'per_frame.csv',allrows);csvout(folder/'pairs.csv',paired);csvout(folder/'input_manifest.csv',manifest)
    save(folder/'activation.json',summary);print('ACTIVATION',summary,flush=True)

if __name__=='__main__':run_dev('--probe' in sys.argv)
