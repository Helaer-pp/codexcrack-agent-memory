"""Inference process: no generator, evaluator, physical label or family is read here."""
from common3 import *
from native_bridge import engine,stops
from candidate3 import propose,old_propose
from reference import MaterialCache,query_intervals
from reference3 import Cache,evidence
from decision3 import decide,EndpointHistory
from decision import validated_decision

def execute(kind):
 folder=RUN/('03_exposed_regression' if kind=='exposed' else '04_NEW_DEV')
 manifest=folder/('inference_inputs.jsonl' if kind=='exposed' else 'inference_manifest.jsonl')
 last=None;eng=None;records=[];crows=[];funnels=[]
 with (folder/'predictions.jsonl').open('w',encoding='utf8') as out:
  for ii,z in enumerate(jl(manifest)):
   if last!=z['case_id']:
    if eng:eng.close()
    ref=read(z['reference_image']);rp=z['reference_points'];oldcache=MaterialCache(ref,rp,True,True);cache=Cache(ref,rp);hist=EndpointHistory();last=z['case_id']
    if 'A' not in z:eng=engine(ref,rp,'auto',True);eng.run(ref,rp,True)
   cur=read(z['input_image']);started=time.perf_counter()
   if 'A' in z:a=z['A'];tiles=z['tiles']
   else:a=eng.run(cur,z['points']);tiles,_=stops(eng)
   f=a['formal'];p=f['raw_path'];tip=f['tip'];valid=f['confirmed_tip'];w=f['width_px'];M=np.asarray(a['native']['transform_reference_to_current'],float)
   old,_,_=old_propose(cur,p,tip,valid,w,tiles);pool,profile,events,cost=propose(cur,p,tip,valid,w,tiles)
   end,_,_,_=propose(cur,p,tip,valid,w,tiles,'ENDPOINT_ONLY');multi,_,_,_=propose(cur,p,tip,valid,w,tiles,'MULTISCALE_ONLY')
   qo,eo,so=evidence(oldcache,cur,M,p,old,w)
   qno,eno,sno=evidence(oldcache,cur,M,p,pool,w)
   qon,eon,son=evidence(cache,cur,M,p,old,w)
   qn,en,sn=evidence(cache,cur,M,p,pool,w)
   base=dict(valid=bool(valid),tip=tip if valid else None,decision='A_FALLBACK_NOT_VERIFIED')
   do,co,po,lo=decide(ref,cur,p,old,qo,eo,tip,valid,w)
   dno,cno,pno,lno=decide(ref,cur,p,pool,qno,eno,tip,valid,w)
   don,con,pon,lon=decide(ref,cur,p,old,qon,eon,tip,valid,w)
   final,comp,perturb,legacy=decide(ref,cur,p,pool,qn,en,tip,valid,w)
   perm,*_=decide(ref,cur,p,list(reversed(pool)),qn,en,tip,valid,w);assert final==perm
   history=hist.update(M,pool,qn,tip,valid)
   modes={'A_ONLY':base,'CANDIDATE_AUDIT':base,'REFERENCE_AUDIT':base,'OLD_CANDIDATE_OLD_REFERENCE':do,
       'NEW_CANDIDATE_OLD_REFERENCE':dno,'OLD_CANDIDATE_NEW_REFERENCE':don,'COMBINED_NO_SELECT':base,'FULL':final,'AP2_LEGACY_RULE':lo,'LEGACY_PATTERN_WITH_NEW_EVIDENCE':legacy,'NO_REFERENCE':base}
   projected=float((np.asarray(final['tip'])-anchors(z['points'])[0])@anchors(z['points'])[1]) if final['valid'] else None
   row=dict(case_id=last,frame_id=z['frame_id'],A_valid=valid,A_tip=tip,A_stop=a['native']['stop_reason'],
       research_valid=final['decision']=='RESEARCH_RELOCATED',research_tip=final['tip'] if final['decision']=='RESEARCH_RELOCATED' else None,
       selected_output_valid=final['valid'],selected_output_tip=final['tip'],decision=final['decision'],reason=final.get('reason'),
       old_K=len(old),K=len(pool),old_coverage=so['coverage'],new_coverage=sn['coverage'],candidate_order_invariant=True,
       projected_length_px=projected,A_old_arc_px=f['length_px'],sidecar_including_native_ms=(time.perf_counter()-started)*1000,
       physical_accuracy='N/A',phase='PHASE_UNKNOWN')
   records.append(row)
   for c in pool:crows.append(dict(case_id=last,frame_id=z['frame_id'],**c))
   for label,qq in [('OLD_REF_OLD_POOL',qo),('NEW_REF_NEW_POOL',qn)]:
    for j,q in enumerate(qq):
     r=q['reg'];funnels.append(dict(case_id=last,frame_id=z['frame_id'],variant=label,query=j,**r.get('funnel',{}),
         fit_n=r['fit_n'],holdout_n=r['holdout_n'],supported=r['local_supported'],reason=r['reason'],photo=q['photo']['state'],coverage=sn['coverage'] if label.startswith('NEW') else so['coverage']))
   dump_line(out,dict(**row,input_image=z['input_image'],reference_image=z['reference_image'],points=z['points'],reference_points=rp,
       A=a,tiles=tiles,pool=pool,old_pool=old,endpoint_only_pool=end,multiscale_only_pool=multi,events=events,profile=profile,
       modes=modes,queries=qn,path_evidence=en,states=sn,old_states=so,comparison=comp,stability=perturb,history=history))
   if ii%30==0:print('INFER',kind,ii,last,row['decision'],flush=True)
 if eng:eng.close()
 csvout(folder/'per_frame_predictions.csv',records);csvout(folder/'per_candidate_evidence.csv',crows);csvout(folder/'reference_reject_funnel.csv',funnels)
 print('INFERENCE DONE',kind,len(records),flush=True)

if __name__=='__main__':execute(sys.argv[1] if len(sys.argv)>1 else 'new')
