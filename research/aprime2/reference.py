"""Uniform patch eligibility; unchanged independent local validation thresholds."""
from common import *
from local_reference import ReferenceCache, P, bbox, highpass, inside, path_evidence, mad
PARAM=dict(cache_limit=480,max_queries=3,max_patches_per_query=48,bad_fraction=.03,
           min_std=1.5,low=45,high=252,spatial_block_patch_halves=6)

class MaterialCache(ReferenceCache):
    def __init__(self,ref,rp,balanced=True,prefilter=False):
        start=time.perf_counter();self.ref=ref;self.rp=np.asarray(rp,float)
        o,u,d=anchors(rp);self.d=d;self.h=int(np.clip(round(.025*d),6,16));self.radius=int(np.clip(round(.025*d),5,12))
        v=np.array([-u[1],u[0]]);corners=np.array([o+a*u+b*v for a in [-.35*d,3.2*d] for b in [-1.25*d,1.25*d]])
        b=bbox(corners);H,W=ref.shape;x0,y0=max(0,int(b[0])),max(0,int(b[1]));x1,y1=min(W,int(b[2])+1),min(H,int(b[3])+1)
        self.roi=[x0,y0,x1,y1];crop=ref[y0:y1,x0:x1];scale=min(1.,900/max(crop.shape))
        small=cv2.resize(crop,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
        mask=((small>45)&(small<252)).astype(np.uint8)*255
        if prefilter:
            # Keep invalid sharp edges from consuming the GFTT candidate budget.
            # This is the same <=3% patch contract, applied BEFORE corner ranking.
            er=max(3,2*int((self.h+2)*scale)+1)
            bad=((small<=45)|(small>=252)).astype(np.float32)
            fraction=cv2.boxFilter(bad,-1,(er,er),normalize=True,borderType=cv2.BORDER_CONSTANT)
            mask=(fraction<=PARAM['bad_fraction']).astype(np.uint8)*255
        limit=PARAM['cache_limit'] if balanced else P['max_features']
        self.features=[];self.rejections=collections.Counter();h=self.h
        pts=cv2.goodFeaturesToTrack(small,maxCorners=limit*3,qualityLevel=.01,minDistance=max(3,3*h*scale),mask=mask,blockSize=3)
        choices=[]
        for q in [] if pts is None else pts[:,0,:]/scale+[x0,y0]:
            x,y=np.rint(q).astype(int)
            if x-h<0 or y-h<0 or x+h>=W or y+h>=H:self.rejections['MASK_BORDER']+=1;continue
            t=ref[y-h:y+h+1,x-h:x+h+1].astype(np.float32)
            sat=float(np.mean(t>=252));dark=float(np.mean(t<=45))
            if sat+dark>.03:self.rejections['SATURATED' if sat>=dark else 'DARK_CLIPPED']+=1;continue
            if t.std()<1.5:self.rejections['LOW_TEXTURE']+=1;continue
            cell=6*h;role='FIT' if (x//cell+y//cell)%2==0 else 'HOLDOUT'
            choices.append(dict(q=np.array([x,y],float),template=t,hp=highpass(t),role=role,std=float(t.std()),
                                bucket=(int((x-x0)//(12*h)),int((y-y0)//(12*h)))))
        if balanced:
            buckets=collections.defaultdict(list)
            for f in choices:buckets[f['bucket']].append(f)
            choices=[]
            while any(buckets.values()):
                for k in sorted(buckets):
                    if buckets[k]:choices.append(buckets[k].pop(0))
        for f in choices:
            if any(np.linalg.norm(f['q']-g['q'])<3*h for g in self.features):continue
            self.features.append(f)
            if len(self.features)>=limit:break
        self.cache_ms=(time.perf_counter()-start)*1000

def query_intervals(cache,cur,M,path,pool,width):
    p=np.asarray(path,float).reshape(-1,2)
    if len(p)<2:return [],[],dict(coverage=0.,reason='NO_A_PATH',geometry='UNKNOWN',photometry='UNKNOWN',increment='UNKNOWN',ownership='UNKNOWN')
    s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    early=sorted([c for c in pool if not c['A_original_bitwise']],key=lambda c:(-c['strength'],c['s']))
    targets=[p[-1]]
    if early:
        c=early[0];targets+=[np.asarray(c['raw_xy']),p[np.argmin(abs(s-(c['s']+s[-1])/2))]]
    else:targets+=[p[len(p)//3],p[2*len(p)//3]]
    queries=[];all_ev=[]
    for q in targets[:PARAM['max_queries']]:
        # Appending an existing path point only changes the query center, not its exclusion band.
        reg=cache.match(cur,M,np.vstack([p,q]));photo=cache.photo(cur,reg)
        ev,_=path_evidence(cache.ref,cur,p,reg,photo,width)
        queries.append(dict(target=q,reg=reg,photo=photo));all_ev.append(ev)
    merged=[]
    for i in range(len(all_ev[0])):
        choices=[e[i] for e in all_ev if e[i]['O']]
        e=(choices[0] if choices else all_ev[0][i]).copy()
        # Conflicting independently supported domains are UNKNOWN.
        if choices and max(x['DeltaV'] for x in choices)-min(x['DeltaV'] for x in choices)>max(3.,3*(queries[0]['photo'].get('noise') or 1.)):
            e.update(O=False,ownership_state='EVIDENCE_UNSTABLE')
        merged.append(e)
    ds=np.diff([e['arc_s'] for e in merged]);valid=np.array([e['O'] for e in merged])
    coverage=float(np.sum(ds*(valid[:-1]&valid[1:]))/max(1.,s[-1])) if len(ds) else 0.
    return queries,merged,dict(coverage=coverage,geometry='SUPPORTED' if any(q['reg']['local_supported'] for q in queries) else 'UNKNOWN',
        photometry='SUPPORTED' if any(q['photo']['state']=='PHOTO_SUPPORTED' for q in queries) else 'UNKNOWN',
        increment='SUPPORTED' if coverage>=.9 else 'UNKNOWN',ownership='UNKNOWN',
        reason='DOMAIN_COVERAGE_MEASURED_NOT_OWNERSHIP_PROOF',query_count=len(queries),max_patch_budget=144)
