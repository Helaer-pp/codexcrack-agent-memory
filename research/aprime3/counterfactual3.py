"""Runtime counterfactuals on fixed A paths. No physical labels are loaded."""
from common3 import *
from reference3 import Cache,evidence
from decision3 import decide
def execute():
 folder=RUN/'04_NEW_DEV';rr=[];items=[z for z in jl(folder/'predictions.jsonl') if z['frame_id']==2]
 for i,z in enumerate(items):
  ref=read(z['reference_image']);cur=read(z['input_image']);rp=np.asarray(z['reference_points']);a=z['A']['formal'];p=a['raw_path'];pool=z['pool'];M=np.asarray(z['A']['native']['transform_reference_to_current'])
  for mode in ['NORMAL','CANDIDATE_REVERSED','SWAPPED_REFERENCE','MASKED_REFERENCE','BLOCK_REMOVAL','GEOMETRY_PLUS_0_5','PHOTOMETRY_PLUS_2PCT','FIXED_PATH_REFERENCE_ROI_SHIFT']:
   r=ref;c=cur;pp=rp.copy();mat=M.copy();pool2=pool
   if mode=='SWAPPED_REFERENCE':
    other=read(items[(i+3)%len(items)]['reference_image']);r=cv2.resize(other,(ref.shape[1],ref.shape[0]))
   if mode=='MASKED_REFERENCE':r=np.full_like(ref,207)
   if mode=='PHOTOMETRY_PLUS_2PCT':c=np.clip(cur.astype(float)*1.02,0,255).astype(np.uint8)
   if mode=='GEOMETRY_PLUS_0_5':mat[:,2]+=[.5,0]
   if mode=='FIXED_PATH_REFERENCE_ROI_SHIFT':pp+=np.array([4.,0.])
   if mode=='CANDIDATE_REVERSED':pool2=list(reversed(pool))
   cache=Cache(r,pp)
   if mode=='BLOCK_REMOVAL':cache.features=[f for f in cache.features if int(f['q'][0]//(6*cache.h))%2==0]
   q,ev,st=evidence(cache,c,mat,p,pool2,a['width_px']);d,comp,perturb,_=decide(r,c,p,pool2,q,ev,a['tip'],a['confirmed_tip'],a['width_px'])
   row=dict(case_id=z['case_id'],frame_id=z['frame_id'],mode=mode,tip=d['tip'],valid=d['valid'],decision=d['decision'],coverage=st['coverage'],
       joint_queries=sum(x['reg']['local_supported'] and x['photo']['state']=='PHOTO_SUPPORTED' for x in q),changed_vs_normal=d['tip']!=z['modes']['FULL']['tip'],path_rerun=False)
   if mode in ['NORMAL','CANDIDATE_REVERSED']:assert row['tip']==z['modes']['FULL']['tip']
   rr.append(row)
  if i%30==0:print('COUNTERFACTUAL',i,flush=True)
 csvout(folder/'counterfactuals.csv',rr)
 write(folder/'roi_search_NOT_TESTED.md','实际重跑搜索 ROI：NOT_TESTED。冻结 A 公开 ABI 不提供 ROI 参数；本轮没有通过修改冻结搜索器来模拟。FIXED_PATH_REFERENCE_ROI_SHIFT 仅移动参考选块 ROI，保持 A 路径不变，不能作为搜索 ROI 鲁棒性证据。\n')
 print('COUNTERFACTUAL DONE',len(rr),flush=True)
if __name__=='__main__':execute()
