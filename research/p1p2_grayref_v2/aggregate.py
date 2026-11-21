from v2common import *
from algorithm import STATUS
import collections,numpy as np
def main():
 assert (OUT/'validation_evaluation_complete.json').exists();allrows=rows(OUT/'all_results_dev.csv')+rows(OUT/'all_results_validation.csv');assert len(allrows)==2647*6;save(OUT/'all_results.csv',allrows);save(OUT/'group_summary.csv',rows(OUT/'group_summary_dev.csv')+rows(OUT/'group_summary_validation.csv'));save(OUT/'first_divergence_vs_v1.csv',rows(OUT/'first_divergence_vs_v1_dev.csv')+rows(OUT/'first_divergence_vs_v1_validation.csv'))
 streams={};writers={}
 schemas=dict(init_candidates=['group','frame_id','mode','id','x','y','initial_score','valley','delta','reference_status','edge_risk','reason','rank','short_score','connection','short_observed','max_run'],path_hypotheses=['group','frame_id','mode','path_id','seed','short_score','chosen','observed','missing','last_visited_x','raw_tip','kind','terminal_index','terminal_score','compatible_recapture','reason'],reference_quality=['group','frame_id','kind','x0','x1','quality_code','quality','reason','upper','lower','audit','mode','status_counts'])
 for name,fields in schemas.items():
  streams[name]=(OUT/f'{name}.csv').open('w',encoding='utf-8-sig',newline='');writers[name]=csv.DictWriter(streams[name],fieldnames=fields,extrasaction='ignore');writers[name].writeheader()
 def emit(name,r):writers[name].writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
 layercounts=collections.Counter();failed=[];trace_diagnostics=[]
 for group in DEV+VAL:
  for fid in range(1,COUNTS[group]+1):
   d=unpack(OUT/'frames'/group/str(fid)/'result.json.gz');base=dict(group=group,frame_id=fid)
   for result in [d['baseline']]+d['results']:
    tr=result['trace'];obs=[t for t in tr if t[2]]
    trace_diagnostics.append(dict(**base,mode=result['mode'],recapture_count=sum(bool(t[2]) and not bool(tr[i-1][2]) for i,t in enumerate(tr) if i),visited_columns=len(tr),first_visited_x=tr[0][0] if tr else None,last_visited_x=tr[-1][0] if tr else None,observed_y_min=min(t[1] for t in obs) if obs else None,observed_y_max=max(t[1] for t in obs) if obs else None,stop_reason=result['stop_reason'],output_state=result['output_state'],note='Chosen path only; missed segments remain predictions, recapture alone does not certify physical identity'))
   for q in d['reference_quality']:emit('reference_quality',dict(**base,kind='V1_REMAP_TEXTURE_CHECK',x0=q['x0'],x1=q['x1'],quality_code=q['code'],quality=q['quality'],reason=q['reason'],upper=q['sides'][0],lower=q['sides'][1]))
   for q in d['independent_material_audit']:emit('reference_quality',dict(**base,kind='INDEPENDENT_NCC_NOT_APPLIED',audit=q))
   for r in d['results']:
    ident=dict(**base,mode=r['mode']);emit('reference_quality',dict(**ident,kind='SELECTED_TRACE_PIXEL_STATUS',status_counts=r['reference_status_counts']))
    for c in r['seeds']:emit('init_candidates',dict(**ident,**c));layercounts['seeds']+=1
    if not r['seeds']:emit('init_candidates',dict(**ident,reason='NO_CANDIDATES'))
    for p in r['paths']:
     obs=[x[:2] for x in p['trace'] if x[2]];emit('path_hypotheses',dict(**ident,path_id=p['id'],seed=p['seed'],short_score=p['short_score'],chosen=p['id']==r['chosen_path_id'],observed=len(obs),missing=len(p['trace'])-len(obs),last_visited_x=p['trace'][-1][0] if p['trace'] else None,raw_tip=obs[-1] if obs else None,kind='PATH'));layercounts['paths']+=1
    if not r['paths']:emit('path_hypotheses',dict(**ident,kind='NO_PATH',reason=r['stop_reason']))
    for s in r['terminal_candidates']:emit('path_hypotheses',dict(**ident,path_id=r['chosen_path_id'],raw_tip=[s['x'],s['y']],kind='STOP_CANDIDATE',terminal_index=s['index'],terminal_score=s['score'],compatible_recapture=s['compatible_recapture'],chosen=s['selected']));layercounts['stops']+=1
   for p in (OUT/'frames'/group/str(fid)/'v1').glob('summary_results.csv'):
    for r in rows(p):failed.append(dict(group=group,frame_id=fid,**r))
 for s in streams.values():s.close()
 save(OUT/'v1_six_mode_results.csv',failed);assert len(failed)==15882;save(OUT/'trace_diagnostics.csv',trace_diagnostics)
 perf=rows(OUT/'runtime_frames_dev.csv')+rows(OUT/'runtime_frames_validation.csv');native=rows(OUT/'native_runtime_frames.csv') if (OUT/'native_runtime_frames.csv').exists() else [];runtime=[]
 for group in DEV+VAL:
  rr=[r for r in perf if r['group']==group]
  for field in ['python_v2_ms','python_preprocess_ms','decode_hash_ms','v1_compute_export_ms']:
   v=[float(r[field]) for r in rr];runtime.append(dict(group=group,component=field,n=len(v),p50=float(np.percentile(v,50)),p95=float(np.percentile(v,95)),p99=float(np.percentile(v,99)),maximum=max(v),peak_worker_process_rss_bytes=max(int(r['process_peak_rss_bytes']) for r in rr),note='Python worker; V2 detector excludes decode/export/startup; RSS is entire process'))
  nn=[r for r in native if r['group']==group]
  if nn:
   for field in ['native_ms','api_wall_ms']:
    v=[float(r[field]) for r in nn];runtime.append(dict(group=group,component=field,n=len(v),p50=float(np.percentile(v,50)),p95=float(np.percentile(v,95)),p99=float(np.percentile(v,99)),maximum=max(v),peak_worker_process_rss_bytes=max(int(r['peak_rss']) for r in nn),note='Native detector or API incl JSON/copy; process RSS includes Python bridge, not isolated DLL allocation'))
 save(OUT/'runtime_performance.csv',runtime);write(OUT/'aggregate_complete.json',dict(utc=utc(),all_result_rows=len(allrows),v1_six_rows=len(failed),**layercounts));print('AGGREGATE COMPLETE',dict(layercounts),flush=True)
if __name__=='__main__':main()
