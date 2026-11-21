"""Offline evidence tables; does not feed labels back to inference."""
from common3 import *
def execute():
 for kind,rel in [('exposed','03_exposed_regression'),('new','04_NEW_DEV'),('real','03_exposed_regression')]:
  folder=RUN/rel;fn='real_predictions.jsonl' if kind=='real' else 'predictions.jsonl';cc=[];ff=[];iv=[];pp=[]
  for z in jl(folder/fn):
   identity=dict(case_id=z.get('case_id',z.get('group')),frame_id=z['frame_id']);comp={c['candidate_id']:c for c in z['comparison']};hist={h['candidate_id']:h for h in z['history']}
   for c in z['pool']:
    ca=comp.get(c['candidate_id'],{});hh=hist.get(c['candidate_id'],{});cc.append({**identity,**c,**ca,**{k:v for k,v in hh.items() if k!='candidate_id'}})
   for j,q in enumerate(z['queries']):
    reg=q['reg'];ph=q['photo'];rejections=collections.Counter(p['reason'] for p in reg['patches'])
    ff.append({**identity,**reg.get('funnel',{}),**dict(query=j,fit=reg['fit_n'],holdout=reg['holdout_n'],geometry=reg['state'],geometry_reason=reg['reason'],
       photo_state=ph['state'],photo_reason=ph['reason'],match_rejection_counts=dict(rejections),coverage=z['states']['coverage'])})
    for p in reg['patches']:pp.append(dict(**identity,query=j,**p))
   for e in z['path_evidence']:iv.append(dict(**identity,**e))
  csvout(folder/('real_per_candidate_evidence.csv' if kind=='real' else 'per_candidate_evidence.csv'),cc)
  csvout(folder/('real_reference_reject_funnel.csv' if kind=='real' else 'reference_reject_funnel_detailed.csv'),ff)
  csvout(folder/('real_interval_evidence.csv' if kind=='real' else 'interval_evidence.csv'),iv)
  csvout(folder/('real_patch_evidence.csv' if kind=='real' else 'patch_evidence.csv'),pp)
  if kind=='real':csvout(RUN/'01_diagnosis/reference_reject_funnel.csv',ff)
  print('DETAIL TABLES',kind,len(cc),len(ff),flush=True)
 fail=rows(RUN/'01_diagnosis/failure_stage_audit.csv');seed={(r['case_id'],r['frame_id']):r for r in rows(RUN/'01_diagnosis/native_seed_gates.csv')}
 ev={(r['case_id'],r['frame_id']):r for r in rows(RUN/'03_exposed_regression/evaluated_per_frame_all_modes.csv') if r['mode']=='FULL'}
 old={(z['case_id'],str(z['frame_id'])):z for z in jl(OLD/'05_DEV/full_v3/decision_predictions.jsonl')}
 current={(z['case_id'],str(z['frame_id'])):z for z in jl(RUN/'03_exposed_regression/predictions.jsonl')};rr=[]
 for f in fail:
  key=f['case_id'],f['frame_id'];prev=old[key];now=current[key];m=ev[key];sd=seed[key];comps=prev.get('final_comparison',[])
  counts=collections.Counter()
  for c in comps:
   if c.get('disputed_coverage',0)<.9:counts['INSUFFICIENT_DISPUTED_COVERAGE']+=1
   if c.get('static_fraction',0)<.85:counts['STATIC_FRACTION_BELOW_085']+=1
   if c.get('new_before',0)<.8:counts['NEW_PREFIX_BELOW_080']+=1
   if c.get('new_reappears'):counts['NEW_REAPPEARS_CONTINUE']+=1
  row=dict(**f,seed_stage=sd['seed_gate'],startup_peak=sd['startup_peak'],startup_fraction=sd['startup_fraction'],seed_support=sd['support_count'],seed_gain=sd['gain'],
     old_final_reason=prev['Aprime2']['reason'],old_failed_constraints=dict(counts),old_pattern_candidates=sum(c.get('H_STOP_pattern',False) for c in comps),
     new_final_reason=now['modes']['FULL'].get('reason'),new_final_error=m['error'],new_final_correct=m['correct'],new_guarded_status=now['modes']['FULL']['decision'],
     new_legacy_pattern_status=now['modes']['LEGACY_PATTERN_WITH_NEW_EVIDENCE']['decision'],new_coverage=m['new_coverage'])
  rr.append(row)
 csvout(RUN/'03_exposed_regression/A_prime2_failure_recheck.csv',rr)
 keyframes=[]
 for z in jl(RUN/'03_exposed_regression/real_predictions.jsonl'):
  if (z['group']=='group_x' and z['frame_id'] in [51,473]) or (z['group']=='ct2' and z['frame_id'] in [6,18,84]):
   keyframes.append(dict(group=z['group'],frame_id=z['frame_id'],A_stop=z['A_stop'],A_tip=z['A_tip'],A_old_arc_px=z['A_old_arc_px'],K=z['K'],coverage=z['coverage'],decision=z['decision'],reason=z['reason'],
      FIT=[q['reg']['fit_n'] for q in z['queries']],HOLDOUT=[q['reg']['holdout_n'] for q in z['queries']],geometry_reasons=[q['reg']['reason'] for q in z['queries']],cache=[q['reg']['funnel'].get('cached') for q in z['queries']]))
 csvout(RUN/'03_exposed_regression/group_x_51_473_and_CT2_cases.csv',keyframes)
 # Identical image evidence / different physical stories is an explicit impossibility witness.
 labs={(z['case_id'],z['frame_id']):z for z in jl(RUN/'04_NEW_DEV/evaluator_GT.jsonl')};inputs={(z['case_id'],z['frame_id']):z for z in jl(RUN/'04_NEW_DEV/inference_manifest.jsonl')};ident=collections.defaultdict(list)
 for k,g in labs.items():
  if g.get('identity_pair_id'):ident[g['identity_pair_id'],g['frame_id']].append((g,inputs[k]))
 witness=[]
 for (pid,f),pair in ident.items():
  (a,ia),(b,ib)=pair;same=ia['image_sha']==ib['image_sha'] and ia['reference_sha']==ib['reference_sha'] and ia['points']==ib['points'];assert same
  witness.append(dict(pair_id=pid,frame_id=f,same_reference_current_anchors=same,positive_a=a['positive'],positive_b=b['positive'],interpretation='OPTICALLY_IDENTICAL_PHYSICAL_STORIES_NOT_IDENTIFIABLE'))
 csvout(RUN/'04_NEW_DEV/identity_counterexample_audit.csv',witness)
 print('POSTPROCESS DONE',len(rr),len(witness),flush=True)
if __name__=='__main__':execute()
