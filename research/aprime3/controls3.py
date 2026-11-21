"""Offline known-motion experiment: GT evaluates methods, never enters them."""
from common3 import *
from generate3 import background
from reference import MaterialCache
from reference3 import Cache
def execute():
 rr=[];details=[]
 for bg in range(3):
  for rep in range(4):
   rng=np.random.default_rng(711930001+100*bg+rep);n=512;base=np.clip(np.rint(background(n,bg,rng)),0,255).astype(np.uint8)
   rp=np.array([[95,150],[95,350]],float);path=np.column_stack([np.arange(130.,300.),np.full(170,250.)])
   for cond in ['shift_0.5','shift_1','shift_3','shift_5','photo','affine_unmodelled','repeated','occlusion','compression','saturated','existing_line']:
    ref=base.copy();M=np.array([[1.,0.,2.25],[0.,1.,-1.25]])
    if cond=='repeated':
     yy,xx=np.indices((n,n));ref=np.clip(200+12*np.sin(xx*2*np.pi/8)*np.cos(yy*2*np.pi/8),0,255).astype(np.uint8)
    if cond=='saturated':ref[:]=255
    if cond=='existing_line':cv2.line(ref,(130,250),(300,250),160,2)
    if cond=='affine_unmodelled':M=np.array([[1.015,.012,-1.],[.006,.985,1.]])
    cur=cv2.warpAffine(ref,M,(n,n),borderValue=207)
    if cond=='photo':cur=np.clip(.9*cur.astype(float)+17,0,255).astype(np.uint8)
    if cond=='occlusion':cur[220:285,260:330]=250
    if cond=='compression':cur=cv2.imdecode(cv2.imencode('.jpg',cur,[cv2.IMWRITE_JPEG_QUALITY,60])[1],0)
    # Input comes only from anchors; the exact affine map is not supplied to match.
    guess=rigid(rp,apply(M,rp));off=float(cond.split('_')[-1]) if cond.startswith('shift_') else 0.;guess[:,2]-=[off,0]
    cp=apply(M,path)
    for name,cache in [('OLD_V3',MaterialCache(ref,rp,True,True)),('AP3',Cache(ref,rp))]:
     reg=cache.match(cur,guess,cp);ph=cache.photo(cur,reg)
     q=path[-1]+np.array([[-16,-16],[-16,16],[16,-16],[16,16]])
     err=np.linalg.norm(apply(reg['M'],q)-apply(M,q),axis=1)
     r=dict(background=bg,rep=rep,condition=cond,method=name,geometry=reg['local_supported'],joint=reg['local_supported'] and ph['state']=='PHOTO_SUPPORTED',
         error_max=float(max(err)),false_accept=reg['local_supported'] and max(err)>1,fit=reg['fit_n'],holdout=reg['holdout_n'],reason=reg['reason'],photo_reason=ph['reason'])
     rr.append(r);details.append(dict(**r,reg=reg,photo=ph))
 csvout(RUN/'01_diagnosis/known_motion_controls.csv',rr)
 with (RUN/'01_diagnosis/known_motion_details.jsonl').open('w',encoding='utf8') as f:
  for z in details:dump_line(f,z)
 summary=[dict(method=name,n=len(q),geometry=sum(r['geometry'] for r in q),joint=sum(r['joint'] for r in q),false_accept=sum(r['false_accept'] for r in q),max_accepted_error=max([r['error_max'] for r in q if r['geometry']]+[0.])) for name in ['OLD_V3','AP3'] for q in [[r for r in rr if r['method']==name]]]
 save(RUN/'01_diagnosis/known_motion_summary.json',summary);print('CONTROLS',summary,flush=True)
if __name__=='__main__':execute()
