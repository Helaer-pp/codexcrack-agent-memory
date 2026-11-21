"""Patch quality precedes match budget. Holdout thresholds remain frozen."""
from common3 import *
from local_reference import ReferenceCache,highpass,bbox,inside,path_evidence
from reference import query_intervals
PARAM=dict(cache_limit=480,corner_limit=1440,scan_limit=192,match_limit=48,query_limit=3,
    bad_fraction=.03,min_std=1.5,low=45,high=252)

class Cache(ReferenceCache):
 def __init__(self,ref,rp):
    start=time.perf_counter();self.ref=ref;self.rp=np.asarray(rp,float);o,u,d=anchors(rp);self.d=d
    self.h=int(np.clip(round(.025*d),6,16));self.radius=int(np.clip(round(.025*d),5,12));h=self.h
    v=np.array([-u[1],u[0]]);b=bbox(np.array([o+a*u+b*v for a in [-.35*d,3.2*d] for b in [-1.25*d,1.25*d]]))
    H,W=ref.shape;x0,y0=max(0,int(b[0])),max(0,int(b[1]));x1,y1=min(W,int(b[2])+1),min(H,int(b[3])+1)
    self.roi=[x0,y0,x1,y1];crop=ref[y0:y1,x0:x1];scale=min(1.,900/max(crop.shape));small=cv2.resize(crop,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
    er=max(3,2*int((h+2)*scale)+1);bad=((small<=45)|(small>=252)).astype(np.float32)
    fraction=cv2.boxFilter(bad,-1,(er,er),normalize=True,borderType=cv2.BORDER_CONSTANT)
    # Pixel fraction plus cheap patch texture variance, before GFTT takes its budget.
    f=small.astype(np.float32);mean=cv2.boxFilter(f,-1,(er,er));var=np.maximum(0,cv2.boxFilter(f*f,-1,(er,er))-mean*mean)
    mask=((fraction<=.03)&(var>=1.5**2)).astype(np.uint8)*255
    pts=cv2.goodFeaturesToTrack(small,maxCorners=1440,qualityLevel=.01,minDistance=max(3,3*h*scale),mask=mask,blockSize=3)
    pts=[] if pts is None else pts[:,0,:]/scale+[x0,y0];choices=[];self.patch_quality=[];self.rejections=collections.Counter()
    for q in pts:
        x,y=np.rint(q).astype(int);reason='PASS'
        if x-h<0 or y-h<0 or x+h>=W or y+h>=H:reason='MASK_BORDER';t=None
        else:
            t=ref[y-h:y+h+1,x-h:x+h+1].astype(np.float32);sat=float(np.mean(t>=252));dark=float(np.mean(t<=45))
            if sat+dark>.03:reason='SATURATED' if sat>=dark else 'DARK_CLIPPED'
            elif t.std()<1.5:reason='LOW_TEXTURE'
        self.patch_quality.append(dict(x=int(x),y=int(y),reason=reason,std=float(t.std()) if t is not None else None))
        if reason!='PASS':self.rejections[reason]+=1;continue
        cell=6*h;choices.append(dict(q=np.array([x,y],float),template=t,hp=highpass(t),role='FIT' if (x//cell+y//cell)%2==0 else 'HOLDOUT',std=float(t.std()),bucket=(int((x-x0)//(12*h)),int((y-y0)//(12*h)))))
    buckets=collections.defaultdict(list)
    for f in choices:buckets[f['bucket']].append(f)
    ordered=[]
    while any(buckets.values()):
        for k in sorted(buckets):
            if buckets[k]:ordered.append(buckets[k].pop(0))
    self.features=[];merged=0
    for f in ordered:
        if any(np.linalg.norm(f['q']-g['q'])<3*h for g in self.features):merged+=1;continue
        if len(self.features)<480:self.features.append(f)
    self.cache_funnel=dict(coarse_pixels=int(small.size),patch_quality_mask_pixels=int(np.count_nonzero(mask)),gftt_candidates=len(pts),patch_quality_pass=len(choices),spatial_merged=merged,cached=len(self.features),rejections=dict(self.rejections))
    self.cache_ms=(time.perf_counter()-start)*1000;self.last_funnel={}
 def match(self,cur,M,path,alternative=False):
    started=time.perf_counter();p=np.asarray(path,float);target=p[-1];inv=cv2.invertAffineTransform(np.asarray(M,float));qref=apply(inv,[target])[0]
    radius=max(80,min(.85*self.d,430));choices=sorted([f for f in self.features if np.linalg.norm(f['q']-qref)<=radius],key=lambda f:np.linalg.norm(f['q']-qref))
    available=[];reject=collections.Counter();scanned=0;h=self.h;r=self.radius;H,W=cur.shape
    for f in choices[:192]:
        scanned+=1;pred=apply(M,[f['q']])[0]
        if np.min(np.linalg.norm(p-pred,axis=1))<max(3*h,.06*self.d):reject['PATH_BAND_BEFORE_BUDGET']+=1;continue
        margin=(h+r)*1.5
        if not (margin<=pred[0]<W-margin and margin<=pred[1]<H-margin):reject['CURRENT_BORDER_BEFORE_BUDGET']+=1;continue
        x,y=np.rint(pred).astype(int);patch=cur[y-h:y+h+1,x-h:x+h+1]
        if np.mean((patch<=45)|(patch>=252))>.03:reject['CURRENT_CLIPPED_BEFORE_BUDGET']+=1;continue
        if patch.std()<1.5:reject['CURRENT_LOW_TEXTURE_BEFORE_BUDGET']+=1;continue
        available.append(f)
    # Fill the match quota only with eligible positions, preserving distance ordering.
    selected=available[:48];original=self.features
    try:
        self.features=selected;reg=super().match(cur,M,path,alternative)
    finally:self.features=original
    self.last_funnel=dict(cached=len(original),within_query_radius=len(choices),scanned=scanned,prebudget_eligible=len(available),selected_for_matching=len(selected),
        scan_budget_exhausted=len(choices)>192,rejections=dict(reject),NCC_attempted=sum(p.get('ncc') is not None for p in reg['patches']),NCC_accepted=sum(p['selected'] for p in reg['patches']),
        FIT=reg['fit_n'],HOLDOUT=reg['holdout_n'],geometry=reg['state'],geometry_reason=reg['reason'],cost_ms=(time.perf_counter()-started)*1000)
    reg['funnel']=self.last_funnel;return reg

def evidence(cache,cur,M,path,pool,width):
    q,ev,st=query_intervals(cache,cur,M,path,pool,width)
    intervals=[]
    for e in ev:
        noise=max(1.,abs(e['Vcur']/e['Q'])) if abs(e['Q'])>1e-9 else 1.
        if not e['O']:state='UNKNOWN'
        elif e['Vcur']>3*noise and e['Vref']<3*noise and e['DeltaV']>3*noise:state='SUPPORTED_NEW'
        elif e['Vref']>6*noise and abs(e['DeltaV'])<=3*noise:state='SUPPORTED_STATIC'
        elif e['Vref']>3*noise and e['DeltaV']>3*noise:state='UNKNOWN_REFERENCE_DARKENING'
        else:state='UNKNOWN'
        e['interval_state']=state
        if intervals and intervals[-1]['state']==state:intervals[-1]['end_s']=e['arc_s']
        else:intervals.append(dict(start_s=e['arc_s'],end_s=e['arc_s'],state=state))
    st['continuous_intervals']=intervals
    st['frame_any_patch_valid']=any(x['reg']['local_supported'] for x in q)
    st['max_unknown_run_px']=max([i['end_s']-i['start_s'] for i in intervals if i['state'].startswith('UNKNOWN')]+[0.])
    return q,ev,st
