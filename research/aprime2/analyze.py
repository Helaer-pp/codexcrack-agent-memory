from common import *

def analyze():
    folder=RUN/('05_DEV/full_v3' if '--prefilter' in sys.argv else '05_DEV/full_v2');r=list(jl(folder/'decision_predictions.jsonl'));fail=[];family=[];pairs=collections.defaultdict(list)
    for z in r:
        m=z['metrics'];gt=z['GT'];a=z['A']['formal']
        if z['pair_id']:pairs[z['pair_id']].append(z)
        if not gt['observable'] or m['Aprime2_correct']:continue
        if not a['raw_path']:stage='SEARCH_NO_PATH'
        elif (z['path_distance'] or 0)>8:stage='PATH_DIVERGENCE'
        elif not z['oracle_correct']:stage='CANDIDATE_OMISSION_ON_REACHABLE_PATH'
        else:
            best=min(z['pool'],key=lambda c:np.linalg.norm(np.asarray(c['xy'])-gt['tip']))
            comparison=next((x for x in z['final_comparison'] if x['candidate_id']==best['candidate_id']),{})
            if comparison.get('disputed_coverage',0)<.9:stage='CANDIDATE_EXISTS_REFERENCE_INTERVAL_UNKNOWN'
            elif not comparison.get('H_STOP_pattern'):stage='CANDIDATE_EXISTS_STOP_CONTINUE_NOT_SEPARATED'
            else:stage='STABILITY_OR_MORPHOLOGY_REJECTED'
        fail.append(dict(case_id=z['case_id'],frame_id=z['frame_id'],family=z['family'],stage=stage,A_stop=z['A']['native']['stop_reason'],
            path_distance=z['path_distance'],oracle_error=z['oracle_error'],A_error=z['A_error'],Aprime2_error=m['Aprime2_error'],
            A_tip=a['tip'],GT_EVAL_ONLY=gt['tip'],candidate_count=len(z['pool']),coverage=z['states']['coverage']))
    for fam in dict.fromkeys(z['family'] for z in r):
        q=[z for z in r if z['family']==fam];obs=[z for z in q if z['GT']['observable']]
        family.append(dict(family=fam,frames=len(q),observable=len(obs),A_correct=sum(z['A_correct'] for z in q),
            oracle_correct=sum(z['oracle_correct'] for z in q),selected_correct=sum(z['metrics']['Aprime2_correct'] for z in q),
            A_valid=sum(z['A_valid'] for z in q),negative_FP=sum(not z['GT']['positive'] and z['A_valid'] for z in q),
            changed=sum(z['metrics']['changed'] for z in q),A_correct_changed_wrong=sum(z['metrics']['A_correct_changed_wrong'] for z in q)))
    csvout(folder/'failure_stages.csv',fail);csvout(folder/'by_family.csv',family)
    pairrows=[]
    for pid,zz in pairs.items():
        cases={z['case_id'] for z in zz};frameids={z['frame_id'] for z in zz};both=0;oldboth=0
        for i in frameids:
            q=[z for z in zz if z['frame_id']==i];assert len(q)==2 and q[0]['image_sha']==q[1]['image_sha']
            both+=all(z['metrics']['Aprime2_correct'] for z in q);oldboth+=all(z['A_correct'] for z in q)
        pairrows.append(dict(pair_id=pid,frames=len(frameids),both_correct_frames=both,A_both_correct_frames=oldboth,
            all_frames_both_correct=both==len(frameids),any_frame_both_correct=both>0))
    csvout(folder/'matched_pair_final.csv',pairrows)
    clusters=collections.defaultdict(list)
    for z in r:
        if z['GT']['observable']:clusters[z['pair_id'] or z['case_id']].append(z['metrics']['A_loss']-z['metrics']['loss'])
    vv=list(clusters.values());rng=np.random.default_rng(551105);boots=[]
    for _ in range(3000):
        ix=rng.integers(0,len(vv),len(vv));boots.append(np.mean([x for i in ix for x in vv[i]]))
    save(folder/'DEV_statistics.json',dict(label='EXPOSED_DEV_DESCRIPTIVE_NOT_CONFIRMATORY',clusters=len(vv),
        observable_frames=sum(z['GT']['observable'] for z in r),mean_loss_reduction=float(np.mean([x for a in vv for x in a])),
        cluster_bootstrap_95=list(map(float,np.percentile(boots,[2.5,97.5]))),both_correct_independent_pairs=sum(x['all_frames_both_correct'] for x in pairrows),
        both_correct_pair_frames=sum(x['both_correct_frames'] for x in pairrows),failure_stages=dict(collections.Counter(x['stage'] for x in fail))))
    key={'group_x':{51,473},'ct2':{6,18,84},'three_point_bend':{100,300,519}}
    historical=[];reasons=collections.Counter()
    for z in jl(RUN/'04_reference_validity/real_predictions.jsonl'):
        for ab in z['endpoint_ablation']:
            if z['frame_id']>0:reasons[z['group'],ab['method'],ab['reason'],ab['photo_reason']]+=1
        if z['frame_id'] not in key.get(z['group'],set()):continue
        f=z['A']['formal'];native=z['A']['native'];t=native['terminal_audit']
        historical.append(dict(group=z['group'],frame_id=z['frame_id'],A_tip=f['tip'],A_valid=f['confirmed_tip'],
            A_arc=f['length_px'],stop=native['stop_reason'],history_prefix_hits=native.get('temporal_hits'),endpoint_hits=t.get('endpoint_hits'),
            candidates=len(z['pool']),candidate_positions=[c['xy'] for c in z['pool']],coverage=z['states']['coverage'],
            query_reasons=[q['reg']['reason'] for q in z['queries']],fit_counts=[q['reg']['fit_n'] for q in z['queries']],
            holdout_counts=[q['reg']['holdout_n'] for q in z['queries']],physical_GT='N/A',
            inference='A can continue on dark texture; unsupported reference intervals cannot validate an earlier physical endpoint.'))
    csvout(RUN/'09_reports/historical_failure_frames.csv',historical)
    csvout(RUN/'04_reference_validity/failure_reasons_by_group.csv',[dict(group=g,method=m,geometry_reason=a,photo_reason=b,frames=n) for (g,m,a,b),n in reasons.items()])
    print('ANALYZED',len(fail),'DEV failures',len(historical),'historical key frames',flush=True)

if __name__=='__main__':analyze()
