from common_ap import *
from local_reference import *
cv2.setNumThreads(1)
guard();mm=rows(O/'00_protocol/inputs_manifest.csv');allrows=[];patches=[];geoms=[];photos=[];domains=[];costs=[];summary=[];alternatives=[];segments=[]
for group in dict.fromkeys(r['dataset_alias']for r in mm):
 rr=[r for r in mm if r['dataset_alias']==group];nr,nj,pp=native(O/f'07_performance/native/{group}_A')
 ref=read(rr[0]['input_image']);rp=json.loads(rr[0]['points']);cache=ReferenceCache(ref,rp)
 print('CACHE',group,len(cache.features),cache.roi,flush=True)
 fn=O/f'06_real_regression/{group}_predictions.jsonl';assert not fn.exists()
 with fn.open('w',encoding='utf8')as fo:
  for i,r in enumerate(rr):
   start=time.perf_counter();cur=ref if i==0 else read(r['input_image']);cp=json.loads(r['points']);co,u,d=anchors(cp);M=np.array(nj[i]['transform_reference_to_current'],float);pure=rigid(rp,cp)
   path=pp[i];target=path if len(path)else np.array([co]);reg=cache.match(cur,M,target);photo=cache.photo(cur,reg)
   width=nj[i].get('terminal_audit',{}).get('path_width_median_px',2)or 2
   ev,ems=path_evidence(ref,cur,path,reg,photo,width)
   valid=nr[i]['tip_valid']=='1';tip=[float(nr[i]['tip_x']),float(nr[i]['tip_y'])]if valid else None
   joint=reg['local_supported']and photo['state']=='PHOTO_SUPPORTED'
   record=dict(group=group,frame_id=i,filename=r['filename'],input_image=r['input_image'],input_sha256=r['input_sha256'],points=cp,A_tip_valid=valid,A_tip=tip,A_legacy_length_px=float(nr[i]['length_px'])if nr[i]['length_valid']=='1'else None,A_path=path,tip_valid=valid,tip=tip,tip_state='LEGACY_A_RESEARCH_FALLBACK'if valid else'UNKNOWN',tip_reason='NO_AUTOMATIC_REPLACEMENT_BEFORE_GATES',horizontal_length_px=float((np.array(tip)-co)@u)if tip else None,legacy_A_stop_reason=nj[i]['stop_reason'],path_role='A_AUXILIARY_PATH',path_valid=bool(len(path)),root_valid=nj[i]['root_confirmed'],root=None,reference_alignment_state=reg['state'],photometry_state=photo['state'],ownership_state='INSUFFICIENT_EVIDENCE',decision_action='KEEP_A_RESEARCH_FALLBACK',search_roi=cache.roi,audit_roi=bbox(target[-1:,:],16),candidate_count=int(valid),reg=reg,photo=photo,path_evidence=ev,native_core_ms=float(nr[i]['complete_core_ms']),phase='PHASE_UNKNOWN')
   fo.write(json.dumps(record,ensure_ascii=False,default=scalar,allow_nan=False)+'\n')
   base=dict(group=group,frame_id=i,input_sha256=r['input_sha256']);allrows.append(dict(**base,filename=r['filename'],A_tip_valid=valid,A_tip_x=tip[0]if tip else None,A_tip_y=tip[1]if tip else None,Aprime_tip_valid=valid,Aprime_tip_x=tip[0]if tip else None,Aprime_tip_y=tip[1]if tip else None,horizontal_length_px=record['horizontal_length_px'],A_legacy_arc_length_px=record['A_legacy_length_px'],decision_action=record['decision_action'],tip_reason=record['tip_reason'],reference_alignment_state=reg['state'],photometry_state=photo['state'],ownership_state=record['ownership_state'],native_A_core_ms=record['native_core_ms'],Aprime_native_ms='NOT_TESTED',true_tip_error_px='N/A'))
   for p in reg['patches']:patches.append(dict(**base,**p))
   delta=float(np.linalg.norm(apply(M,[np.array(rp).mean(0)])[0]-apply(pure,[np.array(rp).mean(0)])[0]));geoms.append(dict(**base,state=reg['state'],reason=reg['reason'],cached_features=len(cache.features),fit_n=reg['fit_n'],holdout_n=reg['holdout_n'],holdout_p90_px=reg['holdout_p90_px'],local_supported=reg['local_supported'],correction=reg['correction'],native_M=M,pure_anchor_M=pure,native_vs_pure_center_px=delta))
   photos.append(dict(**base,**photo));domains.append(dict(**base,polygon=reg['polygon'],audit_roi=record['audit_roi'],local_geometry=reg['local_supported'],local_joint=joint))
   costs.append(dict(**base,cache_cold_ms=cache.cache_ms if i==0 else 0.,reference_match_python_ms=reg['cost_ms'],photometry_python_ms=photo['cost_ms'],path_evidence_python_ms=ems,sidecar_python_ms=reg['cost_ms']+photo['cost_ms']+ems))
   for e in ev:segments.append(dict(**base,**e))
   if i in {0,1,len(rr)//2,len(rr)-1}:
    alt=cache.match(cur,M,target,alternative=True);alternatives.append(dict(**base,method='RAW_NCC',state=reg['state'],cost_ms=reg['cost_ms'],fit_n=reg['fit_n'],holdout_n=reg['holdout_n']));alternatives.append(dict(**base,method='HIGHPASS_NCC',state=alt['state'],cost_ms=alt['cost_ms'],fit_n=alt['fit_n'],holdout_n=alt['holdout_n']))
   if i%100==0:print('REFERENCE_AUDIT',group,i,reg['state'],photo['state'],flush=True)
 summary.append(dict(group=group,frames=len(rr),nonreference_frames=len(rr)-1,alignment_supported=sum(x['group']==group and x['frame_id']>0 and x['state']=='ALIGN_SUPPORTED'for x in geoms),joint_supported=sum(x['group']==group and x['frame_id']>0 and x['local_joint']for x in domains),A_confirmed=sum(x['group']==group and x['A_tip_valid']for x in allrows),changed_tips=0,role='RETIRED_EXPOSED_HISTORY'if group=='group_x'else'EXPOSED_DIAGNOSTIC',physical_MAE='N/A'))
 csvout(O/'03_reference_validity/patch_selection_per_frame.csv',patches);csvout(O/'03_reference_validity/geometric_fit_holdout.csv',geoms);csvout(O/'03_reference_validity/photometry_fit_holdout.csv',photos);csvout(O/'03_reference_validity/local_validity_domains.csv',domains);csvout(O/'03_reference_validity/cost_by_stage.csv',costs);csvout(O/'06_real_regression/six_groups_A_Aprime_per_frame.csv',allrows);csvout(O/'06_real_regression/unknown_and_alignment_coverage.csv',summary);csvout(O/'03_reference_validity/method_engineering_comparison.csv',alternatives)
 print('GROUP_DONE',summary[-1],flush=True)
from collections import Counter
csvout(O/'03_reference_validity/failure_reasons.csv',[dict(reason=k,n=v)for k,v in Counter(x['reason']for x in geoms).items()])
n=sum(x['nonreference_frames']for x in summary);supported=sum(x['joint_supported']for x in summary);zero=sum(x['group']!='group_x'and x['joint_supported']==0 for x in summary)
passed=supported/n>=.05 and zero<3
save(O/'03_reference_validity/gate1_decision.json',dict(pass_gate1=passed,joint_nonreference=supported,nonreference=n,rate=supported/n,active_zero_support_groups=zero,reason='LOCAL_REFERENCE_AVAILABILITY_PASSED'if passed else'NEAR_ALL_UNKNOWN_STOP_AUTOMATIC_TIP_REPLACEMENT',utc=utc()))
guard();print('GATE1',passed,supported,n,flush=True)
