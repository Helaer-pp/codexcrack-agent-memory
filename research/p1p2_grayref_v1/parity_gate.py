from common import *
import numpy as np
def main():
 assert sha(FROZEN)==EXPECTED_SHA;dllsha=sha(BUILD/'Release/P1P2GrayRefV1.dll');allrows=[];summary=[];array_checks=[]
 for g in DEV:
  complete=read(OUT/f'cpp_complete_{g}.json');assert complete['dll_sha256']==dllsha
  rr=rows(OUT/'tables'/f'parity_{g}.csv');allrows.extend(rr);errors=[float(r['tip_distance']) for r in rr if r['tip_distance']!=''];summary.append(dict(group=g,frames=complete['frames'],cases=len(rr),status_equal=sum(r['status_equal']=='True' for r in rr),tip_exact=sum(r['tip_exact']=='True' for r in rr),trace_structure_equal=sum(r['trace_structure_equal']=='True' for r in rr),roi_equal=sum(r.get('roi_equal')=='True' for r in rr),points_equal=sum(r.get('points_equal')=='True' for r in rr),candidate_counts_equal=sum(r['candidate_counts_equal']=='True' for r in rr),endpoint_delta_p50=float(np.percentile(errors,50)) if errors else None,endpoint_delta_p95=float(np.percentile(errors,95)) if errors else None,endpoint_delta_max=max(errors) if errors else None,predicted_max_abs=max(float(r['predicted_max_abs'] or 0) for r in rr)))
 for r in rows(F/'selected_frames.csv'):
  g=r['dataset_id'];f=int(r['frame_id'])
  if g not in DEV:continue
  with np.load(OUT/'py_runs'/g/str(f)/'evidence_arrays.npz') as py,np.load(OUT/'cpp_runs'/g/str(f)/'evidence_arrays.npz') as cpp:
   for key in cpp.files:array_checks.append(dict(group=g,frame_id=f,field=key,shape_equal=py[key].shape==cpp[key].shape,max_abs=float(np.max(np.abs(py[key].astype(float)-cpp[key].astype(float)))),different_pixels=int(np.count_nonzero(py[key]!=cpp[key]))))
 save(OUT/'tables/py_cpp_parity.csv',allrows);save(OUT/'tables/parity_by_group.csv',summary);save(OUT/'tables/selected_array_parity.csv',array_checks)
 passed=all(r['tip_exact']=='True' and r['trace_structure_equal']=='True' and r['status_equal']=='True' and r.get('roi_equal')=='True' and r.get('points_equal')=='True' for r in allrows)
 passed=passed and read(OUT/'regression/regression_checks.json')['six_full_summary_rows_equal'] and all(r['passed']=='True' for r in rows(OUT/'tests/contract_matrix.csv'))
 files=list((ROOT/'research/p1p2_grayref_v1').glob('*.hpp'))+list((ROOT/'research/p1p2_grayref_v1').glob('*.cpp'))+[ROOT/'research/p1p2_grayref_v1/CMakeLists.txt',ROOT/'research/p1p2_grayref_v1/native.py',BUILD/'Release/P1P2GrayRefV1.dll',FROZEN]
 write(OUT/'parity_gate.json',dict(passed=passed,frames=1565,cases=len(allrows),summary=summary,array_exact_cases=sum(r['different_pixels']==0 for r in array_checks),array_cases=len(array_checks),max_array_difference=max(r['max_abs'] for r in array_checks),files={str(p.relative_to(ROOT)):sha(p) for p in files},rule='All1565x6 success/error, points, ROI, provisional endpoints, full per-column integer decisions identical; floating arrays separately measured; six golden rows and input-error contracts pass',annotations_read=0,validation_new_images_read=0))
 print('PARITY',passed,summary,flush=True);assert passed,'Do not enter validation before parity passes'
if __name__=='__main__':main()
