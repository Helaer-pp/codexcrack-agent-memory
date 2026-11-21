from common import *
from candidates import propose
from reference import MaterialCache,ReferenceCache,query_intervals,path_evidence
from decision import select

def execute():
    gate=json.loads((RUN/'03_A_candidate_audit/Gate0.json').read_text());assert gate['pass_gate0']
    mm=rows(ROOT/'data/inputs/six_groups_manifest.csv');lookup={(m['dataset_alias'],int(m['frame_id'])):m for m in mm}
    records=[];candidates=[];last=None;group_stats=[];patchfile=RUN/'04_reference_validity/real_patches.jsonl'
    with (RUN/'04_reference_validity/real_predictions.jsonl').open('w',encoding='utf8') as out,patchfile.open('w',encoding='utf8') as patches:
        for z in jl(RUN/'03_A_candidate_audit/native_tile_observer.jsonl'):
            g,i=z['group'],z['frame_id'];m=lookup[g,i]
            if g!=last:
                ref=read(lookup[g,0]['input_image']);rp=json.loads(lookup[g,0]['points'])
                old=ReferenceCache(ref,rp);frac=MaterialCache(ref,rp,False);bal=MaterialCache(ref,rp,True);last=g
                print('REAL CACHE',g,len(old.features),len(frac.features),len(bal.features),flush=True)
                save(RUN/f'04_reference_validity/cache_{g}.json',dict(old=len(old.features),fraction=len(frac.features),balanced=len(bal.features),
                    rejections=bal.rejections,features=[dict(x=f['q'][0],y=f['q'][1],role=f['role'],std=f['std']) for f in bal.features]))
            cur=ref if i==0 else read(m['input_image']);cp=json.loads(m['points']);a=z['A'];f=a['formal'];p=np.asarray(f['raw_path'],float).reshape(-1,2)
            M=np.array(a['native']['transform_reference_to_current']);target=p if len(p) else np.array([np.mean(cp,axis=0)])
            start=time.perf_counter();pool,prof,cost=propose(cur,p,f['tip'],f['confirmed_tip'],f['width_px'],z['tiles'])
            endpoint=[]
            for label,cache in [('legacy',old),('fraction_only',frac),('balanced_endpoint',bal)]:
                reg=cache.match(cur,M,target);photo=cache.photo(cur,reg)
                endpoint.append(dict(method=label,geometry=reg['local_supported'],joint=reg['local_supported'] and photo['state']=='PHOTO_SUPPORTED',reason=reg['reason'],photo_reason=photo['reason'],fit_n=reg['fit_n'],holdout_n=reg['holdout_n'],holdout_p90=reg['holdout_p90_px'],ms=reg['cost_ms']+photo['cost_ms']))
                dump_line(patches,dict(group=g,frame_id=i,method=label,reg=reg,photo=photo))
            queries,ev,states=query_intervals(bal,cur,M,p,pool,f['width_px'])
            dec,comp=select(pool,ev,f['tip'],f['confirmed_tip'])
            row=dict(group=g,frame_id=i,filename=m['filename'],A_valid=f['confirmed_tip'],A_tip=f['tip'],A_old_arc=f['length_px'],A_stop=a['native']['stop_reason'],
                Aprime2_valid=dec['valid'],Aprime2_tip=dec['tip'],decision=dec['decision'],reason=dec['reason'],candidate_count=len(pool),
                old_joint=endpoint[0]['joint'],fraction_joint=endpoint[1]['joint'],balanced_joint=endpoint[2]['joint'],
                interval_joint=any(q['reg']['local_supported'] and q['photo']['state']=='PHOTO_SUPPORTED' for q in queries),interval_coverage=states['coverage'],
                old_reason=endpoint[0]['reason'],fraction_reason=endpoint[1]['reason'],balanced_reason=endpoint[2]['reason'],
                python_sidecar_ms=(time.perf_counter()-start)*1000,full_native_ms='NOT_TESTED',physical_error='N/A',phase='PHASE_UNKNOWN',
                horizontal_length_px=float((np.asarray(f['tip'])-anchors(cp)[0])@anchors(cp)[1]) if f['confirmed_tip'] else None)
            records.append(row)
            for c in pool:candidates.append(dict(group=g,frame_id=i,**c))
            dump_line(out,dict(**row,input_image=m['input_image'],points=cp,reference_image=lookup[g,0]['input_image'],
                 A=a,pool=pool,profile=prof,queries=queries,path_evidence=ev,states=states,comparison=comp,endpoint_ablation=endpoint))
            if i%100==0:print('REAL AUDIT',g,i,'joint',row['old_joint'],row['fraction_joint'],row['balanced_joint'],row['interval_coverage'],flush=True)
    csvout(RUN/'04_reference_validity/real_per_frame.csv',records);csvout(RUN/'03_A_candidate_audit/real_all_candidates.csv',candidates)
    for g in dict.fromkeys(r['group'] for r in records):
        rr=[r for r in records if r['group']==g and r['frame_id']>0]
        group_stats.append(dict(group=g,current_frames=len(rr),**{k:sum(r[k] for r in rr) for k in ['old_joint','fraction_joint','balanced_joint','interval_joint']},
            mean_path_coverage=float(np.mean([r['interval_coverage'] for r in rr])),physical_MAE='N/A'))
    csvout(RUN/'04_reference_validity/real_coverage_by_group.csv',group_stats)
    save(RUN/'04_reference_validity/legacy_same_task_check.json',dict(nonreference=len(records)-6,legacy_joint=sum(r['old_joint'] for r in records if r['frame_id']>0),expected=337,
        exact_count=sum(r['old_joint'] for r in records if r['frame_id']>0)==337,new_task_coverage_not_equivalent=True))
    guard()

if __name__=='__main__':execute()
