"""Additional output consistency checks; no new input/parameter search."""
from analyze import *

def main():
 c={n:load_case(n) for n in ['A','B','C','D']+[f'CF_geometry_{g}_motion_{m}' for g in ['A','D'] for m in ['A','D']]}
 records=[]
 for name in c:
  case=c[name]
  for mode in ['joint','current']:
   candidates=[r for r in case['candidates'] if r['mode']==mode];selected={r['x']:r for r in candidates if r['selected']=='True'};t=trace(name,mode);ok=len(selected)==len(t) and all(selected[r['x']]['y']==r['selected_y'] and selected[r['x']]['is_observed']==r['is_observed'] and selected[r['x']]['missing_run']==r['missing_run'] for r in t);assert ok;records.append(dict(case=name,mode=mode,executed_columns=len(t),captured_selected_columns=len(selected),captured_candidates=len(candidates),matches_original_trace=ok))
 save(OUT/'column_observer_gate.csv',records);save(OUT/'first_30_columns.csv',[dict(case=name,mode=mode,**r) for name in 'ABCD' for mode in ['joint','current'] for r in trace(name,mode)[:30]])
 imagechecks=[]
 for name in 'ABCD':
  a=cv2.imread(str(OUT/'runs'/name/'result_overlay.png'));b=cv2.imread(str(OUT/'runs'/(name+'_plain')/'result_overlay.png'));equal=np.array_equal(a,b);assert equal;imagechecks.append(dict(case=name,decoded_overlay_pixels_equal=equal,array_sha256=array_sha(a)))
 save(OUT/'observer_overlay_gate.csv',imagechecks)
 fieldchecks=[]
 for motion,base in [('A',c['A']),('D',c['D'])]:
  for geom in ['A','D']:
   target=c[f'CF_geometry_{geom}_motion_{motion}'];box=intersection(base,target)
   for field in ['alpha','dx','dy','reference_aligned']:
    a=crop_global(base,field,box);b=crop_global(target,field,box);eq=np.array_equal(a,b);assert eq;fieldchecks.append(dict(motion=motion,geometry=geom,field=field,overlap_box=box,common_global_pixels_exact=eq,max_abs=float(np.max(np.abs(a-b)))))
 save(OUT/'counterfactual_motion_field_gate.csv',fieldchecks)
 common_checks=[]
 for name in 'BCD':
  a=c['A'];b=c[name];ga=a['observer']['geometry'];gb=b['observer']['geometry'];box=[max(ga['xleft'],gb['xleft']),max(ga['upper'],gb['upper'])+2,min(ga['xr'],gb['xr']),min(ga['lower'],gb['lower'])-1]
  for key in ['ca','csm','valley','flank_low','valid_material']:
   eq=np.array_equal(crop_global(a,key,box),crop_global(b,key,box));assert eq;common_checks.append(dict(comparison='A vs '+name,field=key,common_sampling_ROI=box,exact=eq))
 save(OUT/'current_evidence_common_ROI_gate.csv',common_checks)
 # Auxiliary existing native DLL comparison only; Python evidence remains authoritative.
 sys.path.insert(0,str(ROOT/'research/p1p2_grayref_v1'));import native
 config=read(OUT/'inputs.json');ref=cv2.imread(config['reference'],0);cur=cv2.imread(config['current'],0);native_rows=[]
 n=native.Native()
 for name in 'ABCD':
  case=c[name];h=n.create(ref,case['observer']['reference_points'])
  try:r=n.process(h,cur,case['observer']['current_points'])
  finally:n.close(h)
  write(OUT/'cpp_contrast'/f'{name}.json',r)
  for s in case['summary']:
   t=next(t for t in r['traces'] if t['mode']==s['mode'] and t['threshold']==float(s['threshold']));pt=tip(s);native_rows.append(dict(case=name,mode=s['mode'],threshold=s['threshold'],python_tip=pt,cpp_tip=t['tip'],tip_equal=pt==t['tip'],interpretation='Auxiliary comparison; not used to infer Python root cause'))
 save(OUT/'cpp_contrast.csv',native_rows)
 write(OUT/'controls_audit_complete.json',dict(observer_selected_columns_match=True,overlay_pixel_identity=True,pure_controls_13_arrays_each_exact=True,donor_motion_fields_common_global_pixels_exact=True,cpp_cases=4,frozen_sha_unchanged=sha(FROZEN)==SHA));print('CONTROLS AUDIT COMPLETE',flush=True)
if __name__=='__main__':main()
