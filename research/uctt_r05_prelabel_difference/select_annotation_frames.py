import collections,math
from common import *
KNOWN={'ct2':[(8,'R02/R03/R04 initial-ROI tip disagreement')],'group_h':[(5,'R04 early disconnected candidate'),(78,'R04 large paired candidate displacement')],'group_c':[(69,'R03 paired-tip displacement'),(38,'R03 full-length status disagreement')],'group_x':[(1,'R03/R04 exposed initial-tip disagreement')],'group_a':[(241,'R03/R04 rare confirmed candidate; NOT physical GT')],'ct3':[(20,'R04 D1/D2 confirmation rejection regression')],'three_point_bend':[(20,'R04 D2 confirmation rejection regression')]}
EXTRA={'ct2':[6,7,9],'group_h':[1,2,3,4,6,77,79],'group_c':[37,39,68,70],'group_x':[2]}
def select(rr):
 rr=[r for r in rr if r['decode_ok']=='True' and r['duplicate_exact']=='False'];n=len(rr);g=rr[0]['dataset_id'];picked={}
 def add(r,bucket,why,known=''):
  q=dict(r,quota_bucket=bucket,provisional_stage='TIME_QUARTILE_'+bucket[1]+'_PHYSICAL_STAGE_UNKNOWN' if bucket!='S4' else 'DIFFICULT_CANDIDATE_PHYSICAL_STATE_UNKNOWN',selection_reason=why,known_failure_case=known,annotation_status='UNANNOTATED',duplicate_cluster=g+'_order_'+r['frame_order']);picked[int(r['frame_id'])]=q
 for frame,why in KNOWN[g]:
  r=next(r for r in rr if int(r['frame_id'])==frame);add(r,'S4',why,'historical_case_index_verified_against_source_mapping')
 # Difficulty proxies do not assert crack visibility or physical loading state.
 distances=[float(r['opening_distance']) if r['opening_distance'] else float('nan') for r in rr]
 jumps={int(r['frame_id']):abs(distances[i]-distances[i-1]) if i else 0 for i,r in enumerate(rr)}
 rankers=[('large_opening_proxy_change',lambda r:-jumps[int(r['frame_id'])]),('low_whole_image_texture_proxy',lambda r:float(r['texture_proxy'])),('high_saturation_proxy',lambda r:-float(r['saturation_proxy'])),('opening_proxy_extreme',lambda r:-abs(float(r['opening_distance'])-float(np.nanmedian(distances))) if r['opening_distance'] else 0)]
 for label,key in rankers:
  if sum(r['quota_bucket']=='S4' for r in picked.values())>=4:break
  pool=[r for r in rr if int(r['frame_id']) not in picked and all(abs(int(r['frame_order'])-int(q['frame_order']))>=max(3,n//30) for q in picked.values())]
  if pool:add(min(pool,key=lambda r:(key(r),int(r['frame_order']))),'S4',label+'; proxy only, requires human verification')
 for stage in range(4):
  pool=[r for r in rr if min(3,int(int(r['frame_order'])*4/n))==stage and int(r['frame_id']) not in picked]
  values=[float(r['opening_distance']) for r in pool if r['opening_distance']];spread=max(1e-6,float(np.ptp(values))) if values else 1
  chosen=[]
  for j,quantile in enumerate([.1,.35,.65,.9]):
   usable=[r for r in pool if int(r['frame_id']) not in picked and all(abs(int(r['frame_order'])-int(q['frame_order']))>=max(2,n//60) for q in chosen)]
   if not usable:usable=[r for r in pool if int(r['frame_id']) not in picked]
   target=float(np.quantile(values,quantile)) if values else None
   if stage==0 and j==0:r=min(usable,key=lambda x:int(x['frame_order']))
   else:
    def score(r):
     d=abs(float(r['opening_distance'])-target)/spread if target is not None and r['opening_distance'] else 1
     position=(int(r['frame_order'])-stage*n/4)/(n/4)
     return d+.3*abs(position-quantile),int(r['frame_order'])
    r=min(usable,key=score)
   add(r,'S'+str(stage),f'time quartile {stage+1}; opening quantile target {quantile}; no detector length or visibility used');chosen.append(r)
 result=sorted(picked.values(),key=lambda r:int(r['frame_order']));assert len(result)==20
 # Exactly five contiguous selected cases, with the largest boundary separation.
 blocks=[]
 for start in range(16):
  block=result[start:start+5]
  if any(r['known_failure_case'] for r in block):continue
  left=int(block[0]['frame_order'])-int(result[start-1]['frame_order']) if start else n
  right=int(result[start+5]['frame_order'])-int(block[-1]['frame_order']) if start+5<20 else n
  blocks.append((min(left,right),start))
 _,start=max(blocks);hold={r['frame_id'] for r in result[start:start+5]}
 for r in result:
  r['split']='holdout' if r['frame_id'] in hold else 'development';r['holdout_status']='PROSPECTIVE_INTERNAL_SPLIT_OF_ALREADY_EXPOSED_SEQUENCE_NOT_INDEPENDENT'
  r['use_for_parameter_tuning']=g not in ['group_x','three_point_bend'] and r['split']=='development'
 return result
def main():
 inventory=rows(OUT/'input_inventory.csv');groups=collections.defaultdict(list)
 for r in inventory:groups[r['dataset_id']].append(r)
 selection=[];reserve=[];pairrows=[]
 for g,rr in groups.items():
  picked=select(rr);assert [r['sha256'] for r in picked]==[r['sha256'] for r in select(rr)]
  selection.extend(picked)
  for f in EXTRA.get(g,[]):
   if str(f) not in {r['frame_id'] for r in picked}:
    r=next(r for r in rr if int(r['frame_id'])==f);reserve.append(dict(dataset_id=g,frame_id=f,source_image=r['source_image'],sha256=r['sha256'],reason='adjacent known failure neighborhood; reserve to avoid spending S4 quota on near-duplicates'))
  candidates=[];n=len(rr)
  for i,r in enumerate(rr):
   if not r['opening_distance']:continue
   for h in range(i):
    if not rr[h]['opening_distance']:continue
    delta=abs(float(r['opening_distance'])-float(rr[h]['opening_distance']));age=i-h
    if age>=max(10,int(n*.25)):candidates.append((delta,age,h,i))
  used=[]
  for delta,age,h,i in sorted(candidates,key=lambda z:(z[0],-z[1],z[2])):
   if any(abs(i-q)<max(3,n//20) for q in used):continue
   pairrows.append(dict(dataset_id=g,pair_kind='similar_opening_distant_time',earlier_frame=rr[h]['frame_id'],later_frame=rr[i]['frame_id'],opening_delta=delta,age_frames=age,selection='offline analysis pair, not automatic online reference selection'));used.append(i)
   if len(used)==3:break
  near=[]
  for i in range(1,n):
   if rr[i]['opening_distance'] and rr[i-1]['opening_distance']:near.append((abs(float(rr[i]['opening_distance'])-float(rr[i-1]['opening_distance'])),i-1,i))
  used=[]
  for delta,h,i in sorted(near,reverse=True):
   if any(abs(i-q)<max(3,n//20) for q in used):continue
   pairrows.append(dict(dataset_id=g,pair_kind='near_time_large_opening_change',earlier_frame=rr[h]['frame_id'],later_frame=rr[i]['frame_id'],opening_delta=delta,age_frames=1,selection='top relative changes within this stream, not proof of large physical opening'));used.append(i)
   if len(used)==3:break
 save(OUT/'selection_internal.csv',selection);save(OUT/'reserve_frame_candidates.csv',reserve);save(OUT/'opening_analysis_pairs.csv',pairrows)
 write(OUT/'selection_rules.json',dict(seed=20261111,randomness_used=False,quota={'S0':4,'S1':4,'S2':4,'S3':4,'S4':4},known=KNOWN,selection_repeatability='PASS',splits='15 development + 5 contiguous selected holdout; maximize temporal boundary gaps; no independent holdout claim',physical_stages='UNKNOWN; time quartiles only',parameter_revisions_after_annotations=0))
 print([(g,[int(r['frame_id']) for r in selection if r['dataset_id']==g]) for g in groups])
if __name__=='__main__':main()
