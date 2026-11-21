"""Same endpoint, same A mapping: isolate patch selection from query/candidate changes."""
from common3 import *
from reference import MaterialCache
from reference3 import Cache
last=None;rr=[]
for z in jl(RUN/'03_exposed_regression/real_predictions.jsonl'):
 g=z['group']
 if g!=last:
  ref=read(z['reference_image']);rp=z['reference_points'];old=MaterialCache(ref,rp,True,True);new=Cache(ref,rp);last=g
 if z['frame_id']==0:continue
 cur=read(z['input_image']);p=np.asarray(z['A']['formal']['raw_path']);M=np.asarray(z['A']['native']['transform_reference_to_current']);target=p if len(p) else np.array([np.mean(z['points'],axis=0)])
 for method,cache in [('OLD_V3_ENDPOINT',old),('AP3_ENDPOINT',new)]:
  reg=cache.match(cur,M,target);photo=cache.photo(cur,reg)
  rr.append(dict(group=g,frame_id=z['frame_id'],method=method,cached=len(cache.features),geometry=reg['local_supported'],joint=reg['local_supported'] and photo['state']=='PHOTO_SUPPORTED',
   FIT=reg['fit_n'],HOLDOUT=reg['holdout_n'],reason=reg['reason'],photo_reason=photo['reason'],patch_reasons=dict(collections.Counter(p['reason'] for p in reg['patches'])),funnel=reg.get('funnel')))
 if z['frame_id']%150==0:print('REFERENCE_ENDPOINT',g,z['frame_id'],flush=True)
csvout(RUN/'03_exposed_regression/same_endpoint_reference_compare.csv',rr)
summary=[]
for g in dict.fromkeys(r['group'] for r in rr):
 for method in ['OLD_V3_ENDPOINT','AP3_ENDPOINT']:
  q=[r for r in rr if r['group']==g and r['method']==method];reasons=collections.Counter(r['reason'] for r in q if not r['geometry']);patch=collections.Counter()
  for r in q:patch.update(r['patch_reasons'])
  summary.append(dict(group=g,method=method,n=len(q),cached=q[0]['cached'],geometry=sum(r['geometry'] for r in q),joint=sum(r['joint'] for r in q),reasons=dict(reasons),patch_reasons=dict(patch)))
save(RUN/'03_exposed_regression/same_endpoint_reference_summary.json',summary);print('REFERENCE COMPARE DONE',flush=True)
