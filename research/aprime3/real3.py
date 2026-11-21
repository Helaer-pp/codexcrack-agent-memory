"""Locked rules applied to exposed real sequences. No physical GT is available."""
from common3 import *
from native3 import engine3,seed
from native_bridge import stops
from candidate3 import propose
from reference3 import Cache,evidence
from decision3 import decide,EndpointHistory
def execute():
 save(RUN/'00_protocol/pre_real_locked_sources.json',{str(p.relative_to(ROOT)):sha(p) for p in SOURCE.rglob('*') if p.is_file()})
 mm=rows(ROOT/'data/inputs/six_groups_manifest.csv');rr=[];equals=[];ff=[];cand=[]
 folder=RUN/'03_exposed_regression'
 with (folder/'real_predictions.jsonl').open('w',encoding='utf8') as out:
  for g in dict.fromkeys(m['dataset_alias'] for m in mm):
   seq=[m for m in mm if m['dataset_alias']==g];_,nj,paths=native(ROOT/f'data/frozen_a_replay/{g}_A')
   ref=read(seq[0]['input_image']);rp=json.loads(seq[0]['points']);cache=Cache(ref,rp);hist=EndpointHistory();e=engine3(ref,rp,seq[0]['mode'])
   save(folder/f'patch_cache_{g}.json',dict(funnel=cache.cache_funnel,patches=cache.patch_quality))
   for i,m in enumerate(seq):
    cur=ref if i==0 else read(m['input_image']);cp=json.loads(m['points']);a=e.run(cur,cp,i==0);f=a['formal'];p=f['raw_path'];M=np.asarray(a['native']['transform_reference_to_current']);zz,_=stops(e)
    equal=api.normalized(a['native'])==api.normalized(nj[i]) and np.asarray(p,dtype='<f8').tobytes()==paths[i].astype('<f8').tobytes();assert equal,(g,i)
    equals.append(dict(group=g,frame_id=i,AP3_observer_equal=equal))
    start=time.perf_counter();pool,prof,trace,cost=propose(cur,p,f['tip'],f['confirmed_tip'],f['width_px'],zz)
    q,ev,st=evidence(cache,cur,M,p,pool,f['width_px']);dec,comp,perturb,legacy=decide(ref,cur,p,pool,q,ev,f['tip'],f['confirmed_tip'],f['width_px'])
    history=hist.update(M,pool,q,f['tip'],f['confirmed_tip'])
    tip=dec['tip'];row=dict(group=g,frame_id=i,filename=m['filename'],A_valid=f['confirmed_tip'],A_tip=f['tip'],A_stop=a['native']['stop_reason'],
     research_valid=dec['decision']=='RESEARCH_RELOCATED',research_tip=tip if dec['decision']=='RESEARCH_RELOCATED' else None,
     selected_output_valid=dec['valid'],selected_output_tip=tip,decision=dec['decision'],reason=dec.get('reason'),changed=tip!=f['tip'],
     coverage=st['coverage'],any_query_joint=any(x['reg']['local_supported'] and x['photo']['state']=='PHOTO_SUPPORTED' for x in q),K=len(pool),
     projected_length_px=float((np.asarray(tip)-anchors(cp)[0])@anchors(cp)[1]) if dec['valid'] else None,
     A_old_arc_px=f['length_px'],sidecar_ms=(time.perf_counter()-start)*1000,physical_error='N/A',phase='PHASE_UNKNOWN')
    rr.append(row)
    for j,x in enumerate(q):ff.append(dict(group=g,frame_id=i,query=j,**x['reg'].get('funnel',{}),photo_state=x['photo']['state'],photo_reason=x['photo']['reason'],coverage=st['coverage']))
    for c in pool:cand.append(dict(group=g,frame_id=i,**c))
    dump_line(out,dict(**row,input_image=m['input_image'],reference_image=seq[0]['input_image'],points=cp,reference_points=rp,A=a,pool=pool,queries=q,path_evidence=ev,states=st,comparison=comp,decision_result=dec,legacy_pattern_result=legacy,history=history,seed=seed(e)))
    if i%100==0:print('REAL',g,i,'coverage',st['coverage'],'K',len(pool),flush=True)
   e.close();csvout(folder/'AP3_seed_observer_3035_equalities.csv',equals)
 csvout(folder/'real_per_frame.csv',rr);csvout(folder/'real_per_candidate.csv',cand);csvout(RUN/'01_diagnosis/reference_reject_funnel.csv',ff)
 outsummary=[]
 for g in dict.fromkeys(m['group'] for m in rr):
  q=[m for m in rr if m['group']==g and m['frame_id']>0];outsummary.append(dict(group=g,n=len(q),any_joint=sum(m['any_query_joint'] for m in q),mean_coverage=float(np.mean([m['coverage'] for m in q])),changed=sum(m['changed'] for m in q),physical_MAE='N/A'))
 csvout(folder/'real_summary.csv',outsummary);guard();print('REAL DONE',outsummary,flush=True)
if __name__=='__main__':execute()
