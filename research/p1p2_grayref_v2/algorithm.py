"""Image-only deterministic V2. No paths, names, frame indices, labels or history."""
import math,time
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter,gaussian_filter1d
MODES=['V2_NUMERIC_CONTROL','V2_ORIGIN_ONLY','V2_REF_ONLY','V2_COMBINED','V2_TERMINAL']
FIELDS=['reference_aligned','csm','rsm','valley','newdark','flank_low','valid_material','score']
STATUS=['REFERENCE_UNAVAILABLE','REFERENCE_UNRELIABLE','EXISTING_DARK_OR_NO_INCREMENT','NEW_DARK_SUPPORTED']
PARAMS=dict(threshold=10,material=135,halfwidth=7,gap_max=20,origin_fraction=.35,origin_min=24,origin_max=96,origin_step=4,nms_x=8,nms_y=6,seed_budget=24,path_budget=3,short_columns=32,min_observations=8,min_run=4,connection_min=.5,ambiguity_margin=3,quality_tile=64,quality_std=2,quality_ncc=.75,positive_bonus=.25,prediction_units=1024,score_units=1000000,terminal_window=8)
def quant(v):return math.floor(v*1000000+.5) if v>=0 else -math.floor(-v*1000000+.5)
def divround(n,d):return (2*n+d)//(2*d) if n>=0 else -((2*(-n)+d)//(2*d))
def predict(obs,x,seed_y):
 if not obs:return seed_y*1024
 hist=obs[-12:];n=len(hist);last=hist[-1]
 if n<5:return last[1]*1024
 sx=sum(p[0] for p in hist);sy=sum(p[1] for p in hist);num=n*sum(p[0]*p[1] for p in hist)-sx*sy;den=n*sum(p[0]*p[0] for p in hist)-sx*sx
 if not den:return last[1]*1024
 if 5*abs(num)>den:num=1 if num>0 else -1;den=5
 return last[1]*1024+divround(num*(x-last[0])*1024,den)
def evidence(R,C,rp,cp):
 if R.shape!=C.shape or R.ndim!=2 or C.dtype!=np.uint8 or R.dtype!=np.uint8:raise ValueError('Image shape/type invalid')
 pts=np.asarray([rp,cp],float)
 if pts.shape!=(2,2,2) or not np.all(np.isfinite(pts)):raise ValueError('Invalid P coordinates')
 h,w=C.shape
 if np.any(pts[:,:,0]<0) or np.any(pts[:,:,0]>=w) or np.any(pts[:,:,1]<0) or np.any(pts[:,:,1]>=h) or rp[0][1]>=rp[1][1] or cp[0][1]>=cp[1][1]:raise ValueError('Expected valid upper/lower P coordinates')
 p1,p2=cp;upper=math.ceil(p1[1]);lower=math.floor(p2[1]);xl=math.ceil(max(p1[0],p2[0]))
 if lower-upper<25 or not (0<=xl+50<w and 15<=upper<lower<h-15):raise ValueError('P geometry outside V1 ROI contract')
 mid=round((p1[1]+p2[1])/2);line=gaussian_filter1d(np.mean(C[mid-8:mid+9,:].astype(np.float32),axis=0),25);xr=w-25
 for x in range(xl+300,w-120):
  if line[x]<95 and float(np.mean(line[x:x+95]))<95:xr=x;break
 xa=max(0,xl-30);xb=min(w,xr+24);ya=max(0,upper-24);yb=min(h,lower+24);ca=C[ya:yb,xa:xb].astype(np.float32);Y,X=np.mgrid[ya:yb,xa:xb].astype(np.float32)
 alpha=np.clip((Y-p1[1])/(p2[1]-p1[1]),0,1);dx=(1-alpha)*(cp[0][0]-rp[0][0])+alpha*(cp[1][0]-rp[1][0]);dy=(1-alpha)*(cp[0][1]-rp[0][1])+alpha*(cp[1][1]-rp[1][1]);mx=X-dx;my=Y-dy
 ar=cv2.remap(R,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101).astype(np.float32);csm=gaussian_filter(ca,.7);rsm=gaussian_filter(ar,.7);valley=np.zeros_like(csm)
 for side in [6,9,12]:valley=np.maximum(valley,(np.roll(csm,-side,axis=0)+np.roll(csm,side,axis=0))*.5-csm)
 delta=rsm-csm;flank=np.minimum(np.roll(csm,10,axis=0),np.roll(csm,-10,axis=0));mask=np.zeros_like(csm,dtype=bool);mask[upper-ya+2:lower-ya-1,xl-xa:xr-xa]=True;valid=(flank>135)&mask;score=np.sqrt(np.maximum(valley,0)*np.maximum(delta,0));score[~valid]=0
 a=dict(zip(FIELDS,[ar,csm,rsm,valley,delta,flank,valid,score]));g=dict(xleft=xl,xr=xr,upper=upper,lower=lower,xa=xa,ya=ya,xb=xb,yb=yb)
 q=quality(ca,ar,g,(mx>=0)&(mx<w-1)&(my>=0)&(my<h-1),bool(np.array_equal(R,C)))
 return a,g,q
def quality(ca,ar,g,inbounds,same):
 records=[]
 for x in range(g['xleft'],g['xr'],64):
  sides=[];end=min(x+64,g['xr'])
  for top in [True,False]:
   y0=g['upper']+14 if top else g['lower']-30;y1=y0+16;sl=np.s_[y0-g['ya']:y1-g['ya'],x-g['xa']:end-g['xa']];c=ca[sl].astype(np.int64).ravel();r=ar[sl].astype(np.int64).ravel();n=len(c)
   sc=int(c.sum());sr=int(r.sum());cc=n*int((c*c).sum())-sc*sc;rr=n*int((r*r).sum())-sr*sr;cr=n*int((c*r).sum())-sc*sr;stdc=math.sqrt(max(0,cc))/max(1,n);stdr=math.sqrt(max(0,rr))/max(1,n);ncc=cr/math.sqrt(cc*rr) if cc>0 and rr>0 else 0.;bright=float(np.mean((c>135)&(r>135))) if n else 0
   available=n>=64 and stdc>=2 and stdr>=2 and bright>=.5 and bool(np.all(inbounds[sl])) and not same
   sides.append(dict(side='upper' if top else 'lower',bounds=[x,y0,end,y1],n=n,ncc=quant(ncc)/1e6,std_current=quant(stdc)/1e6,std_reference=quant(stdr)/1e6,bright_fraction=quant(bright)/1e6,available=available))
  code=0 if not all(s['available'] for s in sides) else 2 if min(s['ncc'] for s in sides)>=.75 else 1
  records.append(dict(x0=x,x1=end,code=code,quality=min(s['ncc'] for s in sides),reason='SAME_IMAGE_NO_INCREMENT' if same else 'QUALITY_CHECK',sides=sides))
 return records
class Tracker:
 def __init__(self,a,g,q,cp):self.a=a;self.g=g;self.q=q;self.cp=cp;self.center=(cp[0][1]+cp[1][1])/2;self.sigma=max(12,(g['lower']-g['upper'])*.23)
 def pixel(self,x,y,m2):
  i=y-self.g['ya'];j=x-self.g['xa'];v=float(self.a['valley'][i,j]);d=float(self.a['newdark'][i,j]);valid=bool(self.a['valid_material'][i,j]);qt=self.q[min(len(self.q)-1,max(0,(x-self.g['xleft'])//64))];status=3 if qt['code']==2 and d>=10 else qt['code']
  strength=v*(1+.25*min(max(d,0),40)/40*max(0,qt['quality'])) if m2 and status==3 else v if m2 else float(np.float32(math.sqrt(max(v,0)*max(d,0))))
  return v,d,valid,quant(strength),status,bool(valid and v>=10 and (m2 or d>=10))
 def seed_score(self,x,y,m2,current=False):
  v,d,ok,s,status,accept=self.pixel(x,y,m2);value=max(v,0) if current else s/1e6;return quant(value*math.exp(-.5*((y-self.center)/self.sigma)**2)) if ok else 0
 def initial(self,m2):
  g=self.g;x=g['xleft']+6;ys=range(g['upper']+7,g['lower']-7);y=max(ys,key=lambda y:self.seed_score(x,y,m2));return x,y,self.seed_score(x,y,m2)
 def walk(self,seed,m2,limit=None):
  x0,y0=seed;g=self.g;obs=[];trace=[];gap=0
  for x in range(x0,min(g['xr'],x0+limit) if limit else g['xr']):
   pred=predict(obs,x,y0);lo=max(g['upper']+3,(pred-7*1024)//1024);hi=min(g['lower']-3,-(-(pred+7*1024)//1024)+1);best=None;anybest=None
   for y in range(lo,hi):
    v,d,ok,strength,status,hit=self.pixel(x,y,m2);merit=strength-divround(550000*abs(y*1024-pred),1024);item=(merit,y,v,d,status,strength)
    if anybest is None or merit>anybest[0]:anybest=item
    if hit and (best is None or merit>best[0]):best=item
   hit=best is not None;b=best or anybest
   if b is None:break
   merit,y,v,d,status,strength=b
   if hit:obs.append([x,y]);gap=0
   else:gap+=1
   trace.append([x,y,hit,gap,pred,lo,hi,v,d,status,strength,merit])
   if gap>20:break
  return trace
 def connection(self,x,y):
  total=0;hits=0
  for xx in range(x-1,self.g['xleft']+5,-1):
   ys=range(max(self.g['upper']+3,y-3),min(self.g['lower']-3,y+4));yy=max(ys,key=lambda yy:quant(self.pixel(xx,yy,True)[0]) if self.pixel(xx,yy,True)[2] else -1);v,d,ok,*_=self.pixel(xx,yy,True);total+=1
   if ok and v>=10:y=yy;hits+=1
  return hits/total if total else 1.
 def seeds(self,m2):
  g=self.g;start=g['xleft']+6;width=min(96,max(24,math.floor(.35*(g['lower']-g['upper'])+.5)));points=set()
  for x in range(start,min(start+width+1,g['xr']),4):
   for y in range(g['upper']+7,g['lower']-7):
    v,d,ok,*_=self.pixel(x,y,True)
    if ok and v>=10 and v>=float(self.a['valley'][y-g['ya']-1,x-g['xa']]) and v>float(self.a['valley'][y-g['ya']+1,x-g['xa']]):points.add((x,y))
  for ref in [False,True]:
   x,y,s=self.initial(ref)
   if self.pixel(x,y,True)[5]:points.add((x,y))
  candidates=[]
  for idx,(x,y) in enumerate(sorted(points)):
   v,d,ok,_,status,_=self.pixel(x,y,m2);candidates.append(dict(id=idx,x=x,y=y,initial_score=self.seed_score(x,y,True,current=True),valley=v,delta=d,reference_status=status,edge_risk=float(self.a['csm'][y-g['ya'],x-g['xa']])<80,reason='BUDGET',rank=0,short_score=0,connection=0.,short_observed=0,max_run=0))
  kept=[]
  for c in sorted(candidates,key=lambda c:(-c['initial_score'],c['x'],c['y'])):
   if any(abs(c['x']-b['x'])<=8 and abs(c['y']-b['y'])<=6 for b in kept):c['reason']='NMS_DUPLICATE';continue
   if len(kept)>=24:continue
   kept.append(c);t=self.walk((c['x'],c['y']),m2,32);obs=[r for r in t if r[2]];run=0;longest=0
   for r in t:run=run+1 if r[2] else 0;longest=max(longest,run)
   connect=self.connection(c['x'],c['y']);density=len(obs)/max(1,len(t));strength=sum(min(r[7],30) for r in obs)/max(1,len(obs))/30;curve=sum(abs(obs[i][1]-2*obs[i-1][1]+obs[i-2][1]) for i in range(2,len(obs)))/max(1,len(obs)-2)
   c.update(short_score=quant(70*density+15*strength+15*connect-2*curve),connection=quant(connect)/1e6,short_observed=len(obs),max_run=longest,reason='SHORT_SUPPORTED' if len(obs)>=8 and longest>=4 and connect>=.5 else 'SHORT_OR_CONNECTION_UNSUPPORTED')
  ranked=sorted([c for c in kept if c['reason']=='SHORT_SUPPORTED'],key=lambda c:(-c['short_score'],c['x'],c['y']));chosen=[]
  for rank,c in enumerate(ranked,1):
   c['rank']=rank
   if any(abs(c['y']-b['y'])<=7 for b in chosen):c['reason']='SAME_ORIGIN_BAND';continue
   if len(chosen)<3:chosen.append(c);c['reason']='PATH_HYPOTHESIS'
   else:c['reason']='PATH_BUDGET'
  return candidates,chosen
def terminal_candidates(trace):
 obs=[i for i,r in enumerate(trace) if r[2]];out=[]
 for i in obs:
  if i!=obs[-1] and trace[i+1][2]:continue
  before=trace[max(0,i-7):i+1];after=trace[i+1:i+9];pre=sum(r[2] for r in before)/8;post=sum(r[2] for r in after)/8;pv=sum(max(0,r[7]) for r in before if r[2])/max(1,sum(r[2] for r in before));av=sum(max(0,r[7]) for r in after)/8;nextobs=next((r for r in after if r[2]),None);compatible=bool(post>=.75 and nextobs and abs(nextobs[1]*1024-nextobs[4])<=3*1024);score=quant(2*(1-post)+pre+max(0,(pv-av)/max(10,pv))-(2 if compatible else 0));out.append(dict(index=i,x=trace[i][0],y=trace[i][1],score=score,before_density=pre,after_density=post,compatible_recapture=compatible,selected=False))
 if out:best=max(out,key=lambda c:(c['score'],-c['x']));best['selected']=True
 return out
def run_mode(a,g,q,cp,mode):
 tick=time.perf_counter();tracker=Tracker(a,g,q,cp);m1=mode in ['V2_ORIGIN_ONLY','V2_COMBINED','V2_TERMINAL'];m2=mode in ['V2_REF_ONLY','V2_COMBINED','V2_TERMINAL'];seeds=[];paths=[];ambiguous=False
 if m1:
  seeds,chosen=tracker.seeds(m2)
  if len(chosen)>1:ambiguous=chosen[0]['short_score']-chosen[1]['short_score']<=3000000
 else:
  x,y,s=tracker.initial(m2);c=dict(id=0,x=x,y=y,initial_score=s,reason='SINGLE_COLUMN' if s>0 else 'ZERO_INIT_GUARD',rank=1,short_score=0);seeds=[c];chosen=[c] if s>0 else []
 for c in chosen:
  trace=tracker.walk((c['x'],c['y']),m2);paths.append(dict(id=c['id'],seed=[c['x'],c['y']],trace=trace,short_score=c['short_score']))
 trace=paths[0]['trace'] if paths else [];stops=terminal_candidates(trace) if mode=='V2_TERMINAL' else [];raw=[r[:2] for r in trace if r[2]];candidate_tip=raw[-1] if raw else None;stop='NO_SUPPORTED_ORIGIN' if not paths else 'GAP_LIMIT' if trace and trace[-1][3]>20 else 'RIGHT_BOUNDARY'
 if stops:
  selected=next(c for c in stops if c['selected']);trace=trace[:selected['index']+1];stop='COMPETING_STOP_EVIDENCE';raw=[r[:2] for r in trace if r[2]];candidate_tip=raw[-1] if raw else None
 state='NO_TIP' if not raw else 'UNCERTAIN' if len(raw)<8 or ambiguous else 'ROI_LIMITED' if candidate_tip[0]>=g['xr']-2 else 'PROVISIONAL_OBSERVED'
 if not raw and seeds and m1:state='UNCERTAIN'
 tip=candidate_tip if state=='PROVISIONAL_OBSERVED' else None
 return dict(mode=mode,output_state=state,tip=tip,candidate_tip=candidate_tip,roi=g,seed_candidates_count=len(seeds),seeds=seeds,paths=paths,chosen_seed=paths[0]['seed'] if paths else None,chosen_path_id=paths[0]['id'] if paths else None,trace=trace,terminal_candidates=stops,ambiguous=ambiguous,observed_path_count=len(raw),predicted_gap_count=sum(not r[2] for r in trace),last_visited_x=paths[0]['trace'][-1][0] if paths and paths[0]['trace'] else None,stop_reason=stop,reference_status_counts={STATUS[i]:sum(r[9]==i for r in trace) for i in range(4)},gt_accessed_at_inference=False,runtime_ms=(time.perf_counter()-tick)*1000)
def detect(R,C,rp,cp):
 tick=time.perf_counter()
 try:a,g,q=evidence(R,C,rp,cp)
 except (ValueError,IndexError,cv2.error) as e:return dict(status='INPUT_ERROR',error=str(e),results=[dict(mode=m,output_state='INPUT_ERROR',tip=None,trace=[],seeds=[],paths=[],error=str(e)) for m in MODES]),None
 preprocess=(time.perf_counter()-tick)*1000;results=[run_mode(a,g,q,cp,m) for m in MODES]
 return dict(status='OK',roi=g,reference_points=rp,current_points=cp,reference_quality=q,results=results,preprocess_ms=preprocess,runtime_ms=(time.perf_counter()-tick)*1000),a
