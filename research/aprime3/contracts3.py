from common3 import *
import ast
def execute():
 guard();checks=[]
 for rel in ['03_exposed_regression/inference_inputs.jsonl','04_NEW_DEV/inference_manifest.jsonl']:
  for z in jl(RUN/rel):assert not {'GT','M_GT','family','observable','tip_true'}&set(z)
  checks.append(dict(check='NO_LABELS_IN_INPUT_'+rel,passed=True))
 for name in ['infer3.py','real3.py','candidate3.py','reference3.py','decision3.py']:
  src=(SOURCE/name).read_text(encoding='utf8');tree=ast.parse(src)
  mods=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]+[a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
  assert not any(m.startswith(('generate','evaluate','postprocess')) for m in mods)
 checks.append(dict(check='NO_GENERATOR_OR_EVALUATOR_IMPORT_IN_RUNTIME',passed=True))
 for rel in ['03_exposed_regression/predictions.jsonl','04_NEW_DEV/predictions.jsonl','03_exposed_regression/real_predictions.jsonl']:
  count=0;last=None
  for z in jl(RUN/rel):
   a=z['A']['formal'];assert len(z['pool'])<=12
   if a['confirmed_tip']:assert sum(c['A_original_bitwise'] and np.array_equal(c['xy'],a['tip']) for c in z['pool'])==1
   key=z.get('case_id',z.get('group'))
   if key!=last:assert not any(h['status']=='SUPPORTED_LOCAL_PROXIMITY_ONLY' for h in z['history']);last=key
   dec=z.get('decision_result',z.get('modes',{}).get('FULL'))
   if not dec['valid']:assert dec['tip'] is None
   for q in z['queries']:
    f=q['reg']['funnel'];assert f['scanned']<=192 and f['selected_for_matching']<=48 and f['NCC_attempted']<=f['selected_for_matching']
    if q['reg']['local_supported']:assert q['reg']['fit_n']>=6 and q['reg']['holdout_n']>=4 and q['reg']['holdout_p90_px']<=1.
   count+=1
  checks.append(dict(check='CANDIDATE_BUDGET_BITWISE_A_VALIDITY_HISTORY_PATCHES_'+rel,passed=True,frames=count))
 cf=rows(RUN/'04_NEW_DEV/counterfactuals.csv');assert len(cf)==306*8
 assert all(r['joint_queries']=='0' for r in cf if r['mode']=='MASKED_REFERENCE')
 assert all(r['changed_vs_normal']=='False' for r in cf if r['mode']=='CANDIDATE_REVERSED')
 checks.append(dict(check='MASKED_REFERENCE_UNKNOWN_AND_ORDER_INVARIANT',passed=True,frames=len(cf)))
 eq=rows(RUN/'03_exposed_regression/AP3_seed_observer_3035_equalities.csv');assert len(eq)==3035 and all(r['AP3_observer_equal']=='True' for r in eq)
 checks.append(dict(check='SEED_OBSERVER_3035_STATE_TIP_ARC_FLOAT64_EXACT',passed=True))
 assert not (RUN/'05_NEW_TEST/inputs').exists();checks.append(dict(check='NO_TEST_EXECUTED_WITH_FAILED_PRECONDITIONS',passed=True))
 csvout(RUN/'00_audit/contract_tests.csv',checks);save(RUN/'00_audit/contract_summary.json',dict(passed=True,checks=len(checks),utc=utc()))
 print('CONTRACTS PASSED',len(checks),flush=True)
if __name__=='__main__':execute()
