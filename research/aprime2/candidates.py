"""Current-image / native-path proposals only. No group, GT or reference inputs."""
from common import *
from local_reference import mad
PARAM=dict(K=12,max_samples=4096,normal_offsets=5,min_window_px=8,max_window_px=24,
           change_snr=2.5,min_pre_snr=3.,geometry_angle_rad=.35,merge_width_factor=3.)

def profile(cur, path, width):
    p=np.asarray(path,float).reshape(-1,2)
    if len(p)<2:return None
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    step=max(1.,arc[-1]/(PARAM['max_samples']-1))
    s=np.unique(np.r_[np.arange(0,arc[-1],step),arc[-1]])
    xy=np.column_stack([np.interp(s,arc,p[:,k]) for k in (0,1)])
    t=np.gradient(xy,axis=0);t/=np.maximum(1e-9,np.linalg.norm(t,axis=1))[:,None]
    n=np.column_stack([-t[:,1],t[:,0]]);w=float(np.clip(width or 2.,1.,8.))
    offsets=np.linspace(-max(1.,w/2),max(1.,w/2),5)
    centers=xy[:,None]+n[:,None]*offsets[None,:,None]
    # Separate remaps keep each under OpenCV's short-coordinate dimension limit.
    a=sample(cur,centers);lo=sample(cur,centers-3*w*n[:,None]);hi=sample(cur,centers+3*w*n[:,None])
    valley=(lo+hi)/2-a;peak=valley.max(1);best=valley.argmax(1)
    noise=max(1.,mad(np.diff((lo+hi).mean(1)/2))/2**.5)
    valid=(centers[...,0].min(1)>=3*w+1)&(centers[...,0].max(1)<cur.shape[1]-3*w-1)&(centers[...,1].min(1)>=3*w+1)&(centers[...,1].max(1)<cur.shape[0]-3*w-1)
    return dict(xy=xy,s=s,t=t,n=n,width=w,offsets=offsets,peak=peak,center=valley[:,2],
                best=best,noise=noise,valid=valid,step=step)

def propose(cur,path,tip,valid,width=2.,tiles=None):
    start=time.perf_counter();pr=profile(cur,path,width);pool=[]
    if valid:
        assert tip is not None
        pool.append(dict(origin='A_ORIGINAL',xy=list(map(float,tip)),raw_xy=list(map(float,tip)),
                         A_original_bitwise=True,s=None,normal_offset=0.,reason='UNPRUNABLE_A',strength=None))
    if pr is None:return pool,[],dict(ms=(time.perf_counter()-start)*1000,A_state='A_VALID' if valid else 'A_NO_TIP')
    p,s,w=pr['xy'],pr['s'],pr['width'];sig=pr['peak']/pr['noise'];N=len(s)
    win=max(3,int(np.clip(4*w,PARAM['min_window_px'],PARAM['max_window_px'])/pr['step']))
    proposals=[];pre=np.zeros(N);post=np.zeros(N);turn=np.zeros(N)
    for j in range(win,N-win):
        pre[j]=np.median(sig[j-win:j]);post[j]=np.median(sig[j+1:j+win+1])
        turn[j]=np.arccos(np.clip(pr['t'][j-win]@pr['t'][j+win],-1,1))
        if pr['valid'][j-win:j+win+1].mean()<.9:continue
        if pre[j]>PARAM['min_pre_snr'] and pre[j]-post[j]>PARAM['change_snr']:
            proposals.append((pre[j]-post[j],j,'SUSTAINED_SUPPORT_CHANGE'))
        if turn[j]>PARAM['geometry_angle_rad'] and pre[j]>3:
            proposals.append((turn[j]*5,j,'BRANCH_OR_GEOMETRY_CHANGE'))
    if tiles is not None and len(tiles)>1:
        z=np.asarray(tiles)
        for a,b in zip(z[:-1],z[1:]):
            # Native support/gain change is only a proposal, never confirmation.
            if a[5]-b[5]>.25 or (a[4]>20 and b[4]<.4*a[4]):
                j=int(np.argmin(np.linalg.norm(p-b[:2],axis=1)))
                if win<=j<N-win:proposals.append((3+max(0.,a[5]-b[5])*5,j,'NATIVE_TILE_SUPPORT_CHANGE'))
    merge=max(4.,PARAM['merge_width_factor']*w)
    if pool:pool[0]['s']=float(s[np.argmin(np.linalg.norm(p-np.array(tip),axis=1))])
    # Round-robin types prevents texture changes from consuming every slot.
    groups={k:sorted([q for q in proposals if q[2]==k],reverse=True) for k in
            ['SUSTAINED_SUPPORT_CHANGE','BRANCH_OR_GEOMETRY_CHANGE','NATIVE_TILE_SUPPORT_CHANGE']}
    while len(pool)<PARAM['K'] and any(groups.values()):
        for origin,q in groups.items():
            if not q or len(pool)>=PARAM['K']:continue
            strength,j,_=q.pop(0);raw=p[j];offset=float(pr['offsets'][pr['best'][j]])
            xy=raw+offset*pr['n'][j]
            if any(np.linalg.norm(xy-c['xy'])<merge for c in pool):continue
            pool.append(dict(origin=origin,xy=xy.tolist(),raw_xy=raw.tolist(),A_original_bitwise=False,
                s=float(s[j]),normal_offset=offset,reason='WINDOW_PROPOSAL_NOT_PHYSICAL_TIP',
                strength=float(strength),pre_support=float(pre[j]),post_support=float(post[j]),
                local_R=float(sig[j]),local_G=float(turn[j]),local_W=w,local_U=None,
                branch_competition=None,history=None,competing_hypothesis='H_CONTINUE_TO_A_PATH_END'))
    for k,c in enumerate(pool):c['candidate_id']=k
    seq=[dict(s=float(s[i]),x=float(p[i,0]),y=float(p[i,1]),R_center=float(pr['center'][i]),
              R_normal_peak=float(pr['peak'][i]),noise=pr['noise'],Q=bool(pr['valid'][i]),
              G=float(turn[i]),pre=float(pre[i]),post=float(post[i])) for i in range(N)]
    return pool,seq,dict(ms=(time.perf_counter()-start)*1000,A_state='A_VALID' if valid else 'A_NO_TIP',
                         K=len(pool),sample_count=N,sampling_step=pr['step'])
