"""DEV ablation of selector ordering, then exposed four-group diagnostic only.
Not an endpoint-decision revision, not a new TEST.
"""
from common import *
from reference import MaterialCache,query_intervals

def execute():
    results=[]
    # Predeclared exposed DEV paired/weak/crossing/negative families, all 540 frames.
    last=None
    for z in jl(RUN/'05_DEV/full_v2/decision_predictions.jsonl'):
        if z['case_id']!=last:
            ref=read(z['reference_image']);cache=MaterialCache(ref,z['reference_points'],prefilter=True);last=z['case_id']
        a=z['A']['formal'];cur=read(z['input_image']);M=np.array(z['A']['native']['transform_reference_to_current'])
        q,ev,st=query_intervals(cache,cur,M,a['raw_path'],z['pool'],a['width_px'])
        local_errors=[]
        for x in q:
            if x['reg']['local_supported']:
                p=np.asarray(x['target']);inv=cv2.invertAffineTransform(np.asarray(z['M_GT']))
                pref=apply(inv,[p])[0];local_errors.append(float(np.linalg.norm(apply(x['reg']['M'],[pref])[0]-p)))
        results.append(dict(case_id=z['case_id'],frame_id=z['frame_id'],family=z['family'],old_features=len(z['queries'][0]['reg']['patches']) if z['queries'] else 0,
            cached_features=len(cache.features),old_path_coverage=z['states']['coverage'],prefilter_coverage=st['coverage'],
            known_rigid_GT=z['family']!='LOCAL_MISREGISTRATION',max_local_GT_error=max(local_errors) if local_errors else None,
            false_accept=bool(z['family']!='LOCAL_MISREGISTRATION' and local_errors and max(local_errors)>1.)))
    csvout(RUN/'04_reference_validity/prefilter_DEV_diagnostic.csv',results)
    save(RUN/'04_reference_validity/prefilter_DEV_summary.json',dict(frames=len(results),old_mean_coverage=float(np.mean([x['old_path_coverage'] for x in results])),
        new_mean_coverage=float(np.mean([x['prefilter_coverage'] for x in results])),known_rigid_false_accept=sum(x['false_accept'] for x in results)))
    # Only four original development groups: retired/validation groups do not tune this change.
    last=None;rr=[];mm=rows(ROOT/'data/inputs/six_groups_manifest.csv');first={m['dataset_alias']:m for m in mm if m['frame_id']=='0'}
    for z in jl(RUN/'04_reference_validity/real_predictions.jsonl'):
        g=z['group']
        if g not in ['group_a','group_c','ct2','group_h']:continue
        if g!=last:
            ref=read(first[g]['input_image']);cache=MaterialCache(ref,json.loads(first[g]['points']),prefilter=True);last=g
        cur=read(z['input_image']);a=z['A']['formal'];p=a['raw_path'] or [np.mean(z['points'],axis=0).tolist()];M=np.asarray(z['A']['native']['transform_reference_to_current'])
        reg=cache.match(cur,M,p);photo=cache.photo(cur,reg)
        rr.append(dict(group=g,frame_id=z['frame_id'],cache_features=len(cache.features),old_joint=z['old_joint'],v2_joint=z['balanced_joint'],
            prefilter_joint=reg['local_supported'] and photo['state']=='PHOTO_SUPPORTED',reason=reg['reason'],holdout_p90=reg['holdout_p90_px']))
        if z['frame_id']%150==0:print('PREFILTER DIAG',g,z['frame_id'],len(cache.features),flush=True)
    csvout(RUN/'04_reference_validity/prefilter_four_groups_diagnostic.csv',rr)
    print('PREFILTER DONE',flush=True)

if __name__=='__main__':execute()
