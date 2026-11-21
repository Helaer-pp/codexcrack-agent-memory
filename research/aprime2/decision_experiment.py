from common import *
from decision import validated_decision,select

def run_dev():
    folder=RUN/('05_DEV/full_v3' if '--prefilter' in sys.argv else '05_DEV/full_v2');allrows=[];counter=[];failures=[]
    last=None
    with (folder/'decision_predictions.jsonl').open('w',encoding='utf8') as out:
        for z in jl(folder/'evidence_predictions.jsonl'):
            a=z['A']['formal'];gt=z['GT'];cur=read(z['input_image'])
            if last!=z['case_id']:ref=read(z['reference_image']);last=z['case_id']
            dec,comp,perturb=validated_decision(ref,cur,a['raw_path'],z['pool'],z['queries'],z['path_evidence'],a['tip'],a['confirmed_tip'],a['width_px'])
            err=float(np.linalg.norm(np.array(dec['tip'])-gt['tip'])) if dec['valid'] and gt['observable'] else None
            correct=err is not None and err<=8
            row={k:z[k] for k in ['case_id','pair_id','frame_id','family','background','A_valid','A_error','A_correct','oracle_error','oracle_correct','failure_class','positive','observable']}
            row.update(Aprime2_valid=dec['valid'],Aprime2_error=err,Aprime2_correct=correct,decision=dec['decision'],reason=dec['reason'],
                changed=dec['tip']!=a['tip'],A_correct_changed_wrong=bool(z['A_correct'] and not correct),
                catastrophic=bool(z['A_correct'] and err is not None and err>160),corrected=bool(not z['A_correct'] and correct),
                loss=min(err,64) if err is not None else 32 if gt['observable'] else None,
                A_loss=min(z['A_error'],64) if z['A_error'] is not None else 32 if gt['observable'] else None,
                disputed_coverage=z['states']['coverage'])
            allrows.append(row)
            if gt['observable'] and not correct:failures.append(row)
            # Full runtime counterfactual order invariance, no GT used.
            perm,_,_=validated_decision(ref,cur,a['raw_path'],list(reversed(z['pool'])),z['queries'],z['path_evidence'],a['tip'],a['confirmed_tip'],a['width_px'])
            assert dec==perm
            counter.append(dict(case_id=z['case_id'],frame_id=z['frame_id'],candidate_permutation=True,
                reference_off_tip=a['tip'],reference_on_tip=dec['tip'],perturbations=len(perturb),decision=dec['decision']))
            dump_line(out,dict(**z,Aprime2=dec,final_comparison=comp,stability=perturb,metrics=row))
    csvout(folder/'final_per_frame.csv',allrows);csvout(folder/'final_failures.csv',failures);csvout(folder/'final_counterfactuals.csv',counter)
    counts=dict(frames=len(allrows),A_correct=sum(x['A_correct'] for x in allrows),Aprime2_correct=sum(x['Aprime2_correct'] for x in allrows),
        corrected=sum(x['corrected'] for x in allrows),A_correct_changed_wrong=sum(x['A_correct_changed_wrong'] for x in allrows),
        catastrophic=sum(x['catastrophic'] for x in allrows),changed=sum(x['changed'] for x in allrows))
    save(folder/'decision_summary.json',counts);print('DEV DECISION',counts,flush=True)

if __name__=='__main__':run_dev()
