from common import *
import gzip,numpy as np,collections

def main():
 metrics=rows(OUT/'experiments/B0_frame_metrics.csv');gt={(r['dataset_id'],r['frame_id']):r for r in rows(OUT/'experiments/B0_candidate_reachability.csv')}
 full=[]
 for m in metrics:
  x=dict(m);g=gt.get((m['dataset_id'],m['frame_id']))
  x.update(has_offline_annotation=bool(g),gt_visibility=g['visibility'] if g else 'NOT_ANNOTATED',A0_error_px=g['A0_error_px'] if g else None,new_gt_error_px=None,new_error_status='NO_OBSERVED_OUTPUT',evaluation_role='DEVELOPMENT')
  full.append(x)
 save(OUT/'experiments/frame_metrics.csv',full)
 save(OUT/'experiments/candidate_reachability.csv',list(gt.values()))
 save(OUT/'experiments/comparison_by_group.csv',rows(OUT/'experiments/B0_comparison_by_group.csv'))
 # Detailed rows for every selected frame; complete all-frame native details
 # remain in the streaming compressed archive, avoiding multi-GB CSV expansion.
 ww=[];ss=[];rr=[];tt=[]
 for key,g in gt.items():
  dataset,f=key;t=read(OUT/'traces'/f'B0_{dataset}_{f}.json');prefix=dict(dataset_id=dataset,frame_id=f,variant='B0',scope='all80 selected; all1565 full traces in B0_frames.jsonl.gz')
  for w in t['windows']:ww.append(dict(prefix,**w,frontier_kind='untrusted_static_control',gap_reason='not_stepwise',search_incomplete=t['search_incomplete']))
  for seg in t['segments']:ss.append(dict(prefix,**{k:v for k,v in seg.items() if k!='points'},actual_point_count=len(seg['points']),gap_link='NONE',trusted_history_written=False))
  rr.append(dict(prefix,status='NOT_VERIFIED',calls=0,left_quality='NOT_IMPLEMENTED',right_quality='NOT_IMPLEMENTED',new_old_state='UNKNOWN',reason='S1 current-only; S3 not enabled'))
  for c in t['candidates']:tt.append(dict(prefix,candidate_id=c['id'],canonical_id=c['canonical_id'],xy=c['xy'],candidate_exists=True,path_supported='CURRENT_LOCAL_SEGMENT_ONLY',attribution_state='UNKNOWN',terminal_supported=False,tip_observed=False,window_cut=c['window_cut'],reason='SHADOW_ONLY_NOT_A_TERMINAL_DECISION',search_incomplete=t['search_incomplete']))
 save(OUT/'experiments/window_trace.csv',ww);save(OUT/'experiments/segment_trace.csv',ss);save(OUT/'experiments/reference_trace.csv',rr);save(OUT/'experiments/terminal_audit.csv',tt)
 safety=rows(OUT/'tests/r03_original.csv')
 save(OUT/'experiments/first_lock_safety.csv',[dict(x,implementation='R03_ORIGINAL_UNMODIFIED',interpretation='original legacy fault fixture; not a R05F first-lock acceptance') for x in safety]+[dict(implementation='R05F_B0',test='trusted_history',status='NOT_VERIFIED',interpretation='S1 writes no history and confirms no tips; this cannot establish nontrivial first-lock safety')])
 perf=[]
 clean=rows(OUT/'experiments/clean_performance_frames.csv') if (OUT/'experiments/clean_performance_frames.csv').exists() else []
 base=rows(OUT/'baseline_timings.csv')
 def stats(g,variant,scope,values):
  v=np.array(values,float)
  return dict(dataset_id=g,variant=variant,scope=scope,n=len(v),p50_ms=float(np.median(v)),p95_ms=float(np.percentile(v,95)),p99_ms=float(np.percentile(v,99)),max_ms=float(v.max()),over50=int(np.sum(v>50)),cpu='Ryzen9 7950X',target_i7='NOT_VERIFIED',threads=4)
 for group in DEV+['ALL']:
  for name,key,source in [('B0','dll_process_wall_ms',clean),('A_RELEASE','A_release_call_ms',clean)]:
   vals=[float(r[key]) for r in source if (group=='ALL' or r['dataset_id']==group) and (name!='A_RELEASE' or r['reference_frame']!='True')]
   if vals:perf.append(stats(group,name,'clean serialized native process; I/O/debug excluded; A excludes cached references',vals))
  for name in ['A_FROZEN','A0_CLONE']:
   for key in ['native_api_ms','local_reference_ms','match_template_ms','legacy_score_ms','legacy_dp_ms','legacy_terminal_ms']:
    vals=[float(r[key]) for r in base if r['mode']==name and r['reference_query']!='True' and r.get(key) and (group=='ALL' or r['dataset_id']==group)]
    if vals:perf.append(stats(group,name,key,vals))
 save(OUT/'experiments/performance.csv',perf)
 write(OUT/'tables_complete.json',dict(full_frames=len(full),selected_frames=len(gt),windows=len(ww),segments=len(ss),candidates=len(tt),all_frame_detail_archive='traces/B0_frames.jsonl.gz',csv_trace_scope='all selected80 frames; full1565 source archive kept'))
 print('TABLES COMPLETE',len(full),len(ww),len(ss),len(tt),flush=True)
if __name__=='__main__':main()
