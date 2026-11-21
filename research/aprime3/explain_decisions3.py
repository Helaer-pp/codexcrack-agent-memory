"""GT-nearest candidate analysis belongs exclusively to the offline evaluator."""
from common3 import *
fail={(r['case_id'],int(r['frame_id'])):r for r in rows(RUN/'01_diagnosis/failure_stage_audit.csv') if r['old_stage'] in ['CANDIDATE_EXISTS_STOP_CONTINUE_NOT_SEPARATED','STABILITY_OR_MORPHOLOGY_REJECTED']}
# Accept actual stage naming from the sealed records without a silent empty audit.
if len(fail)!=14:
 fail={(r['case_id'],int(r['frame_id'])):r for r in rows(RUN/'01_diagnosis/failure_stage_audit.csv') if r['old_stage']!='CANDIDATE_OMISSION_ON_REACHABLE_PATH' and r['A_stop']!='no_seed'}
assert len(fail)==14
rr=[]
for z in jl(OLD/'05_DEV/full_v3/decision_predictions.jsonl'):
 key=z['case_id'],z['frame_id']
 if key not in fail:continue
 gt=np.asarray(z['GT']['tip']);pool=z['pool'];c=min(pool,key=lambda c:np.linalg.norm(np.asarray(c['xy'])-gt));comp=next((a for a in z['final_comparison'] if a['candidate_id']==c['candidate_id']),{})
 reasons=[]
 if comp.get('pre_observed',0)<3:reasons.append('PRE_OBSERVED_LT3')
 if comp.get('disputed_coverage',0)<.9:reasons.append('DISPUTED_COVERAGE_LT090')
 if comp.get('static_fraction',0)<.85:reasons.append('STATIC_FRACTION_LT085')
 if comp.get('new_before',0)<.8:reasons.append('NEW_PREFIX_LT080')
 if comp.get('new_reappears'):reasons.append('CONTINUE_NEW_REAPPEARS')
 if c['origin']!='SUSTAINED_SUPPORT_CHANGE':reasons.append('MORPH_ORIGIN_NOT_SUPPORT_CHANGE')
 if c.get('pre_support',0)-c.get('post_support',0)<=2.5:reasons.append('MORPH_DROP_NOT_GT2_5')
 ss=z.get('stability',[]);bad=[k for k,s in enumerate(ss) if c['candidate_id'] not in s['stable_candidates']]
 if bad:reasons.append('GEOMETRY_PHOTO_PERTURBATION_CHANGED_PATTERN')
 rr.append(dict(case_id=key[0],frame_id=key[1],stage=fail[key]['old_stage'],GT_nearest_candidate_EVAL_ONLY=c['candidate_id'],GT_distance_EVAL_ONLY=float(np.linalg.norm(np.asarray(c['xy'])-gt)),origin=c['origin'],
    disputed_coverage=comp.get('disputed_coverage'),pre_observed=comp.get('pre_observed'),static_fraction=comp.get('static_fraction'),new_before=comp.get('new_before'),new_reappears=comp.get('new_reappears'),
    pre_support=c.get('pre_support'),post_support=c.get('post_support'),reasons=reasons,perturbations=len(ss),failed_perturbations=bad,original_final_reason=z['Aprime2']['reason']))
csvout(RUN/'01_diagnosis/stop_continue_14_exact_reasons.csv',rr)
print('DECISION14',collections.Counter(q for r in rr for q in r['reasons']),flush=True)
