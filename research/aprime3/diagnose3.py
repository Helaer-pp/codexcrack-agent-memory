from common3 import *
from candidate3 import legacy_trace,propose

fail={(r['case_id'],int(r['frame_id'])):r for r in rows(OLD/'05_DEV/full_v3/failure_stages.csv')}
labels={(z['case_id'],z['frame_id']):z for z in jl(RUN/'03_exposed_regression/evaluator_GT.jsonl')}
rawall=[];filters=[];result=[];newtrace=[]
for z in jl(RUN/'03_exposed_regression/inference_inputs.jsonl'):
    key=z['case_id'],z['frame_id']
    if key not in fail:continue
    r=fail[key];a=z['A']['formal'];cur=read(z['input_image']);gt=np.asarray(labels[key]['GT']['tip'])
    old,raw,filtered=legacy_trace(cur,a['raw_path'],a['tip'],a['confirmed_tip'],a['width_px'],z['tiles'])
    new,_,trace,cost=propose(cur,a['raw_path'],a['tip'],a['confirmed_tip'],a['width_px'],z['tiles'])
    for q in raw:rawall.append(dict(case_id=key[0],frame_id=key[1],**q,GT_distance_EVAL_ONLY=float(np.linalg.norm(np.asarray(q['raw_xy'])-gt))))
    for q in filtered:filters.append(dict(case_id=key[0],frame_id=key[1],**q))
    for q in trace:newtrace.append(dict(case_id=key[0],frame_id=key[1],**q))
    near=[q for q in raw if np.linalg.norm(np.asarray(q['raw_xy'])-gt)<=8]
    eligible={q['event_id'] for q in near if q['eligible']};fnear=[q for q in filtered if q['event_id'] in eligible]
    if not a['raw_path']:cause='NO_SEED_UNRESOLVED'
    elif not a['confirmed_tip'] and np.linalg.norm(np.asarray(a['raw_path'][-1])-gt)<=8:cause='VALID_ONLY_ENDPOINT_AND_END_WINDOW_EXCLUSION'
    elif eligible and any(q['reason']=='MERGED' for q in fnear):cause='EVENT_MERGED_WITH_STRONGER_DISTANT_CANDIDATE'
    elif eligible and any(q['reason']=='K_LIMIT' for q in fnear):cause='K_LIMIT'
    elif not eligible and near:cause='NO_THRESHOLD_QUALIFIED_EVENT_NEAR_GT'
    else:cause='DECISION_OR_REFINEMENT_REQUIRES_SEPARATE_AUDIT'
    err=min([float(np.linalg.norm(np.asarray(c['xy'])-gt)) for c in new],default=None)
    result.append(dict(case_id=key[0],frame_id=key[1],old_stage=r['stage'],family=r['family'],A_stop=r['A_stop'],
        cause=cause,old_candidate_n=len(old),new_candidate_n=len(new),old_oracle=float(r['oracle_error']) if r['oracle_error'] else None,new_oracle=err,
        new_candidate_correct=err is not None and err<=8,ms=cost['ms']))
csvout(RUN/'01_diagnosis/candidate_trace_raw.csv',rawall);csvout(RUN/'01_diagnosis/candidate_filter_audit.csv',filters)
csvout(RUN/'01_diagnosis/new_candidate_events.csv',newtrace);csvout(RUN/'01_diagnosis/failure_stage_audit.csv',result)
print(collections.Counter(r['cause'] for r in result if r['old_stage']=='CANDIDATE_OMISSION_ON_REACHABLE_PATH'),flush=True)
