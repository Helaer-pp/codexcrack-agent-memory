from common import *
from reference import MaterialCache,ReferenceCache,query_intervals,path_evidence
from decision import select
from candidates import propose

def evaluate_dev():
    v3='--prefilter' in sys.argv
    folder=RUN/('05_DEV/full_v3' if v3 else '05_DEV/full_v2');folder.mkdir(parents=True,exist_ok=True)
    summary=[];candidate_rows=[];counter=[];last=None;cache=None
    with (folder/'evidence_predictions.jsonl').open('w',encoding='utf8') as out:
        for z in jl(RUN/'05_DEV/full_v2/predictions.jsonl'):
            if z['case_id']!=last:
                ref=read(z['reference_image']);cache=MaterialCache(ref,z['reference_points'],prefilter=v3);last=z['case_id']
            cur=read(z['input_image']);a=z['A'];p=a['formal']['raw_path'];M=np.array(a['native']['transform_reference_to_current'])
            queries,ev,states=query_intervals(cache,cur,M,p,z['pool'],a['formal']['width_px'])
            dec,comp=select(z['pool'],ev,a['formal']['tip'],a['formal']['confirmed_tip'])
            # Candidate permutation and evidence removal are executable counterfactuals.
            perm,pa=select(list(reversed(z['pool'])),ev,a['formal']['tip'],a['formal']['confirmed_tip'])
            assert dec==perm
            off,_=select(z['pool'],[],a['formal']['tip'],a['formal']['confirmed_tip'])
            row={k:z[k] for k in ['case_id','pair_id','family','background','frame_id','A_valid','A_error','A_correct','oracle_error','oracle_correct','failure_class','positive','observable']}
            row.update(states)
            row.update(Aprime2_valid=dec['valid'],Aprime2_error=z['A_error'],Aprime2_correct=z['A_correct'],
                       decision=dec['decision'],reason=dec['reason'],
                       stop_patterns=sum(c['H_STOP_pattern'] for c in comp),reference_features=len(cache.features),
                       full_native_ms='NOT_TESTED',GT_scope='PROCEDURAL_ENDPOINT_EVAL_ONLY')
            summary.append(row);counter.append(dict(case_id=z['case_id'],frame_id=z['frame_id'],candidate_order_invariant=True,
                        reference_off_decision=off['decision'],reference_on_decision=dec['decision'],changed_physical_prediction=False))
            for c in z['pool']:
                cc=next((r for r in comp if r['candidate_id']==c['candidate_id']),{})
                candidate_rows.append(dict(case_id=z['case_id'],frame_id=z['frame_id'],**(c|cc)))
            dump_line(out,dict(**z,queries=queries,path_evidence=ev,states=states,decision_result=dec,comparison=comp))
        csvout(folder/'evaluated_per_frame.csv',summary);csvout(folder/'all_candidates.csv',candidate_rows);csvout(folder/'counterfactuals.csv',counter)
    save(folder/'summary.json',dict(frames=len(summary),A_correct=sum(x['A_correct'] for x in summary),
        oracle_correct=sum(x['oracle_correct'] for x in summary),Aprime2_correct=sum(x['Aprime2_correct'] for x in summary),
        stop_pattern_frames=sum(x['stop_patterns']>0 for x in summary),automatic_relocation=False,
        conclusion='PATTERN_IS_NOT_SUFFICIENT_PHYSICAL_OWNERSHIP_EVIDENCE'))

if __name__=='__main__':evaluate_dev()
