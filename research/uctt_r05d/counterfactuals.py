"""Post-hoc comparison of generic, isolated counterfactual branches."""
import zipfile,collections
import numpy as np
from common import *
from analyze import classify,original
def main():
 assert read(OUT/'cf_complete.json')['equivalence']=='PASS'
 selected=[r for r in rows(OUT/'selected_frames.csv') if role(r['dataset_id'])=='DEVELOPMENT'];result=[]
 with zipfile.ZipFile(R05/'human_annotations_six_groups_snapshot.zip') as z:
  for r in selected:
   g=r['dataset_id'];f=int(r['frame_id']);name=f'{g}__{f:06d}';base=read(OUT/'traces'/f'{name}.json');label=json.loads(z.read(r['selected_json']));tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];visible=len(tips)==1
   for variant in [1,2,3]:
    p=OUT/'traces'/f'{name}__CF{variant}.json'
    if not p.exists():continue
    t=read(p);output=t['selected_original'][-1] if t['selected_original'] else None;err=float(np.linalg.norm(np.array(output)-tips[0])) if visible and output else None
    with np.load(OUT/'maps'/f'{name}__CF{variant}.npz') as archive:m={k:archive[k] for k in archive.files}
    status,_=classify(t,m,label,err)
    actual=base['formal']['tip'];base_error=float(np.linalg.norm(np.array(actual)-tips[0])) if visible and actual else None
    # Distant candidate counts are not labelled false positives.
    pp=original([p['xy'] for p in t['peaks']],t);off=int(np.sum(np.linalg.norm(pp-tips[0],axis=1)>10)) if visible else None
    result.append(dict(dataset_id=g,frame_id=f,variant=f'CF{variant}',unique_changed_variable={1:'generic ROI extent x2; reference transform fixed',2:'local-reference drift from main transform; actual ROI/direction fixed',3:'disjoint-path ambiguity return bypassed; all other gates unchanged'}[variant],offline_only=True,deployable=False,source_sha256=r['source_sha256'],trace_sha256=sha(p),baseline_roi=base['roi'],counterfactual_roi=t['roi'],new_area_pixels=t['roi'][2]*t['roi'][3]-base['roi'][2]*base['roi'][3],baseline_tip_in_roi=(base['roi'][0]<=tips[0][0]<base['roi'][0]+base['roi'][2] and base['roi'][1]<=tips[0][1]<base['roi'][1]+base['roi'][3]) if visible else None,counterfactual_tip_in_roi=status['oracle_tip_in_roi'],baseline_observed=bool(actual),counterfactual_nonempty_path=bool(output),baseline_error_px=base_error,counterfactual_error_px=err,output_original=output,near_actual_peaks=status.get('actual_peak_count_within10'),distant_peaks_not_true_false_positives=off,candidate_count=len(t['peaks']),baseline_candidate_count=len(base['peaks']),first_failure_stage=status['first_failure_stage'],terminal=t['terminal_cause'],source=f'traces/{p.name}',annotation_state=status['annotation_state'],interpretation='OFFLINE_CAUSAL_PROBE_NOT_ACCURACY_GAIN'))
   probe=OUT/'traces'/f'{name}__CF4.json'
   if probe.exists():
    t=read(probe);path=original(t['selected_local'],base);output=path[-1].tolist() if len(path) else None;peaks=original([p['xy'] for p in t['peaks']],base);distance=np.linalg.norm(peaks-tips[0],axis=1) if visible else np.array([]);actual=base['formal']['tip']
    result.append(dict(dataset_id=g,frame_id=f,variant='CF4',unique_changed_variable=t['unique_variable'],offline_only=True,deployable=False,source_sha256=r['source_sha256'],trace_sha256=sha(probe),baseline_roi=base['roi'],counterfactual_roi=base['roi'],new_area_pixels=0,baseline_tip_in_roi=(base['roi'][0]<=tips[0][0]<base['roi'][0]+base['roi'][2] and base['roi'][1]<=tips[0][1]<base['roi'][1]+base['roi'][3]) if visible else None,counterfactual_tip_in_roi=(base['roi'][0]<=tips[0][0]<base['roi'][0]+base['roi'][2] and base['roi'][1]<=tips[0][1]<base['roi'][1]+base['roi'][3]) if visible else None,baseline_observed=bool(actual),counterfactual_nonempty_path=bool(output),baseline_error_px=float(np.linalg.norm(np.array(actual)-tips[0])) if visible and actual else None,counterfactual_error_px=float(np.linalg.norm(np.array(output)-tips[0])) if visible and output else None,output_original=output,near_actual_peaks=int(np.sum(distance<=10)) if visible else None,distant_peaks_not_true_false_positives=int(np.sum(distance>10)) if visible else None,candidate_count=len(t['peaks']),baseline_candidate_count=len(base['peaks']),first_failure_stage='INDETERMINATE',terminal='endpoint_only_probe',source=f'traces/{probe.name}',annotation_state='VISIBLE' if visible else 'UNCERTAIN',interpretation='EXACT_CONTROL_DP; reference-unavailable score bypass is OFFLINE ONLY; no full-stage replay',changed_score_pixels=t['changed_pixels'],input_map_sha256=t['input_map_sha256']))
 save(OUT/'counterfactual_results.csv',result)
 # Freeze everything that can affect classification before any new VAL replay.
 frozen={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'research/uctt_r05d').glob('*') if p.is_file() and p.suffix in ['.py','.hpp','.inc','.txt']}
 write(OUT/'diagnosis_frozen_before_validation.json',dict(source_hashes=frozen,tolerances=[3,5,10],evidence_neighborhood_px=10,annotation_training=False,validation_feedback=False,cf_results_sha256=sha(OUT/'counterfactual_results.csv'),note='Operational stage queries are frozen; no validation-driven selection. Generic ROI expansion avoids GT coordinates entering any native input. CF2 coarse main transform is not a proven independent ground-truth transform.'))
 print('COUNTERFACTUALS',len(result),'CLASSIFIER FROZEN',flush=True)
if __name__=='__main__':main()
