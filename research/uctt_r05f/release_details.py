"""Investigate independently observed packaged/build baseline hash mismatch."""
from baseline import *

def diff(a,b,p=''):
 if isinstance(a,dict) and isinstance(b,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:out.append(dict(field=p+'/'+k,release=a.get(k,'<MISSING>'),build=b.get(k,'<MISSING>')))
   else:out+=diff(a[k],b[k],p+'/'+k)
  return out
 if a==b:return []
 return [dict(field=p,release=a if not isinstance(a,list) else f'list length {len(a)}',build=b if not isinstance(b,list) else f'list length {len(b)}')]

def main():
 cv2.setNumThreads(1);release=load(ROOT/'output/releases/A_Win64_OpenCV440/bin/CrackV4.dll');build=load(ROOT/'output/build/src/cpp/a/Release/CrackV4.dll')
 old={(r['dataset_id'],r['frame_id']):r for r in map(json.loads,(OUT/'A0_frames.jsonl').read_text().splitlines())}
 modes={r['id']:r['mode'] for r in read(ROOT/'config/datasets.json')['groups']};modes['ct3']='auto';groups=collections.defaultdict(list)
 for r in filter_rows(rows(OUT/'input_inventory_allowed.csv'),'development'):groups[r['dataset_id']].append(r)
 metrics=[];samples=[]
 for g,seq in groups.items():
  a=b=None
  try:
   for i,r in enumerate(seq):
    require(g,'development');assert int(r['frame_order'])==i;raw=Path(r['source_image']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];im=cv2.imdecode(np.frombuffer(raw,np.uint8),0);pp=json.loads(r['points']);f=int(r['frame_id'])
    if a is None:a=make(release,im,pp,modes[g]);b=make(build,im,pp,modes[g])
    ra=clean(a.run(im,pp,is_reference=i==0));ref=old[g,f];fd=diff(ra['formal'],ref['formal']);gd=diff(ra['geometry'],ref['geometry'])
    metrics.append(dict(dataset_id=g,frame_id=f,formal_exact=not fd,geometry_exact=not gd,formal_differences=fd,geometry_differences=gd))
    if i<3:
     rb=clean(b.run(im,pp,is_reference=i==0));samples.append(dict(dataset_id=g,frame_id=f,release=ra,build=rb,differences=diff(ra,rb)))
    if (i+1)%100==0:print('release detail',g,f,'formal',not fd,'geometry',not gd,flush=True)
  finally:
   if a:a.close()
   if b:b.close()
 save(OUT/'release_field_equivalence.csv',metrics);write(OUT/'release_sample_differences.json',samples)
 result=dict(frames=len(metrics),formal_exact=sum(r['formal_exact'] for r in metrics),geometry_exact=sum(r['geometry_exact'] for r in metrics),full_digest_equivalence=read(OUT/'release_equivalence.json'),formal_difference_fields=dict(collections.Counter(d['field'] for r in metrics for d in r['formal_differences'])),geometry_difference_fields=dict(collections.Counter(d['field'] for r in metrics for d in r['geometry_differences'])),sample_difference_fields=dict(collections.Counter(d['field'] for r in samples for d in r['differences'])),scope='all1565 formal+geometry comparison; native JSON compared for first3 frames pergroup only; no binary equivalence claim')
 write(OUT/'release_field_summary.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
