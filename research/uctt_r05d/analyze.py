"""Offline oracle queries. No detector imports, calls, training or fitting."""
import argparse,zipfile,collections,math
import numpy as np,cv2
from common import *
TOLERANCES=[3,5,10]
def original(points,t):
 p=np.array(points,float).reshape(-1,2).copy();x,y,w,h=t['roi'];u,v=p[:,0].copy(),p[:,1].copy()
 if t['turn']==1:p[:,0]=w-1-v;p[:,1]=u
 elif t['turn']==2:p[:,0]=w-1-u;p[:,1]=h-1-v
 elif t['turn']==3:p[:,0]=v;p[:,1]=h-1-u
 return p+[x,y]
def local(points,t):
 x,y,w,h=t['roi'];p=np.array(points,float).reshape(-1,2)-[x,y];u,v=p[:,0].copy(),p[:,1].copy()
 if t['turn']==1:p[:,0]=v;p[:,1]=w-1-u
 elif t['turn']==2:p[:,0]=w-1-u;p[:,1]=h-1-v
 elif t['turn']==3:p[:,0]=h-1-v;p[:,1]=u
 return p
def inside(point,roi):
 x,y,w,h=roi;return x<=point[0]<x+w and y<=point[1]<y+h
def samples(label):
 pp=[];weights=[]
 for s in label['shapes']:
  if s['label']!='crack_path':continue
  for a,b in zip(s['points'][:-1],s['points'][1:]):
   a,b=np.array(a),np.array(b);length=np.linalg.norm(b-a);n=max(1,int(np.ceil(length/.5)))
   pp.extend(a+(np.arange(n)[:,None]+.5)/n*(b-a));weights.extend([length/n]*n)
 return np.array(pp).reshape(-1,2),np.array(weights)
def sample_map(points,t,m):
 p=np.rint(local(points,t)).astype(int);ok=(p[:,0]>=0)&(p[:,1]>=0)&(p[:,0]<m.shape[1])&(p[:,1]<m.shape[0]);v=np.full(len(p),np.nan);v[ok]=m[p[ok,1],p[ok,0]];return v
def roundtrip(t):
 p=np.array([[t['roi'][0],t['roi'][1]],t['center'],*t['selected_original']],float)
 err=float(np.max(np.abs(original(local(p,t),t)-p))) if len(p) else 0
 affine=np.array(t['tip_transform']).reshape(2,3);rot=affine[:,:2];shift=affine[:,2];mapped=p@rot.T+shift;back=(mapped-shift)@np.linalg.inv(rot).T
 return max(err,float(np.max(np.abs(back-p))))
def classify(t,m,label,error):
 tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];state='VISIBLE' if len(tips)==1 else 'UNCERTAIN'
 out=dict(annotation_state=state,first_failure_stage='INDETERMINATE',failure_subtype='UNCERTAIN_LABEL',evidence_level='INSUFFICIENT_DATA',oracle_tip_in_roi=None,oracle_tip_evidence_available=None,oracle_near_candidate=None,nearest_candidate_distance=None,selected_candidate_distance=error,coordinate_roundtrip_px=roundtrip(t),diagnostic_tolerance_px=10,missing_internal_state=None)
 if state!='VISIBLE':return out,[]
 tip=np.array(tips[0]);inroi=inside(tip,t['roi']);out['oracle_tip_in_roi']=inroi
 x,y,w,h=t['roi'];out['distance_to_nearest_roi_boundary']=float(min(tip[0]-x,x+w-1-tip[0],tip[1]-y,y+h-1-tip[1]))
 out['oracle_tip_in_main_roi']=any(cv2.pointPolygonTest(np.array(p,np.float32),tuple(map(float,tip)),False)>=0 for p in t['main_rois'])
 out['roi_exclusion_direction']='ahead' if tip[0]>=x+w else 'behind' if tip[0]<x else 'vertical' if not inroi else 'inside'
 peaks=t['peaks'];coords=original([p['xy'] for p in peaks],t);dist=np.linalg.norm(coords-tip,axis=1);near=np.where(dist<=10)[0]
 for tol in TOLERANCES:out[f'actual_peak_count_within{tol}']=int(np.sum(dist<=tol))
 out['nearest_candidate_distance']=float(dist.min()) if len(dist) else None;out['oracle_near_candidate']=bool(len(near))
 score=m.get('score');score_available=False;strong=None
 if score is not None:
  q=local([tip],t)[0];yy,xx=np.indices(score.shape);area=(xx-q[0])**2+(yy-q[1])**2<=25
  values=score[area];larger=(xx-q[0])**2+(yy-q[1])**2<=100;values10=score[larger];strong=bool(np.any(values10>=3)) if len(values10) else None;score_available=bool(len(values10))
  out['tip5px_score_max']=float(values.max()) if len(values) else None
  out['tip10px_score_max']=float(values10.max()) if len(values10) else None
 out['oracle_tip_evidence_available']=strong
 local_trace=OUT/'traces'/f"{t['dataset_id']}__{int(t['frame_id']):06d}__local.json"
 if local_trace.exists() and not t.get('variant'):
  local_data=read(local_trace);tile=next((v for v in local_data['tiles'] if inside(tip,v['tile'])),None)
  if tile:out['local_reference_at_tip']=tile;out['local_reference_recompute_bitwise_equal']=local_data['registered_bitwise_hash_matches_D0']
 if not t['registration_valid']:stage,sub,level='G0','TIP_REGISTRATION_UNAVAILABLE','DIRECT_TRACE'
 elif not inroi:stage,sub,level='G0','TIP_OUTSIDE_ACTUAL_ENDPOINT_ROI','DIRECT_TRACE'
 elif out['coordinate_roundtrip_px']>1e-7:stage,sub,level='G5','COORDINATE_ROUNDTRIP_ERROR','DIRECT_TRACE'
 elif error is not None and error<=10:stage,sub,level='NONE','OUTPUT_WITHIN_10PX_COMPARISON_TOLERANCE','DIRECT_TRACE'
 elif not score_available:stage,sub,level='INDETERMINATE','EVIDENCE_MAP_NOT_EXPOSED','INSUFFICIENT_DATA'
 elif not strong:stage,sub,level='G1','NO_SCORE_GE3_WITHIN_10PX_OF_LABEL','DIRECT_TRACE'
 elif not len(near):stage,sub,level='G2','NO_GENERATED_LOCAL_MAXIMUM_WITHIN10PX','DIRECT_TRACE'
 else:
  stages={peaks[i]['stage'] for i in near}
  if 'not_visited_after_rank_stop' in stages and any(p['stage']=='competing_disjoint_paths' for p in peaks):stage,sub,level='INDETERMINATE','NEAR_PEAK_UNVISITED_AFTER_GLOBAL_AMBIGUITY_RETURN','INSUFFICIENT_DATA';out['missing_internal_state']='near peak tail/material audit never executed after global ambiguity return'
  elif stages&{'rank_gain_stop','not_visited_after_rank_stop','same_path_earlier','interior_shoulder','duplicate_endpoint'}:stage,sub,level='G3','NEAR_PEAK_NOT_SELECTED_RANK_OR_PATH_COMPETITION','DIRECT_TRACE'
  elif stages&{'path_too_short','path_hits_below_72pct','tail_hits_below_65pct','ahead_outside','ahead_dark_below55','ahead_continues_4','competing_disjoint_paths','nonforward_tail'}:stage,sub,level='G4','NEAR_PEAK_REJECTED_'+','.join(sorted(stages)),'DIRECT_TRACE'
  else:stage,sub,level='INDETERMINATE','NEAR_PEAK_WITH_UNRESOLVED_SELECTION_ORDER','INSUFFICIENT_DATA'
 out.update(first_failure_stage=stage,failure_subtype=sub,evidence_level=level)
 if stage=='G1' and out.get('local_reference_at_tip',{}).get('stage') not in [None,'accepted']:
  out['failure_subtype']='LOCAL_REFERENCE_'+out['local_reference_at_tip']['stage']
 # Stage labels describe trace reachability, not physically proven root causes.
 out['root_cause_proven_by_intervention']=False
 pp,weights=samples(label);length=float(weights.sum());out['human_path_length_px']=length
 pathinside=np.array([inside(p,t['roi']) for p in pp]);out['path_inside_roi_fraction']=float(np.dot(weights,pathinside)/length) if length else None
 if score is not None and length:
  scores=sample_map(pp,t,score);out['full_path_score_ge3_fraction']=float(np.dot(weights,np.nan_to_num(scores,nan=-99)>=3)/length)
  reasons=sample_map(pp,t,m['reason']);out['full_path_computed_fraction']=float(np.dot(weights,np.isin(reasons,[5,6]))/length)
  for window in [10,25,50]:
   # Euclidean neighborhood is explicitly named; not silently called arc length.
   tail=np.linalg.norm(pp-tip,axis=1)<=window
   out[f'tip_neighborhood_{window}px_path_score_ge3_fraction']=float(np.dot(weights[tail],np.nan_to_num(scores[tail],nan=-99)>=3)/weights[tail].sum()) if np.any(tail) else None
   arc_to_tip=np.cumsum(weights)-weights/2 if np.linalg.norm(pp[0]-tip)<np.linalg.norm(pp[-1]-tip) else length-np.cumsum(weights)+weights/2
   back=arc_to_tip<=window;out[f'path_arc_last_{window}px_score_ge3_fraction']=float(np.dot(weights[back],np.nan_to_num(scores[back],nan=-99)>=3)/weights[back].sum()) if np.any(back) else None
  out['tip5px_reason_counts']={str(int(k)):int(v) for k,v in zip(*np.unique(m['reason'][area],return_counts=True))}
  out['tip10px_reason_counts']={str(int(k)):int(v) for k,v in zip(*np.unique(m['reason'][larger],return_counts=True))}
  shapes=[s for s in label['shapes'] if s['label']=='crack_path']
  path=np.array(shapes[0]['points'],float)
  if np.linalg.norm(path[0]-tip)<np.linalg.norm(path[-1]-tip):path=path[::-1]
  direction=path[-1]-path[-2];direction/=max(np.linalg.norm(direction),1e-12)
  ahead=sample_map(tip+np.arange(1,26)[:,None]*direction,t,score);out['ahead25px_score_ge3_fraction']=float(np.mean(np.nan_to_num(ahead,nan=-99)>=3));out['ahead25px_computed_fraction']=float(np.mean(np.isfinite(ahead)))
 if t['selected_original']:
  end=np.array(t['selected_original'][-1]);out['internal_tip_to_returned_px']=float(np.linalg.norm(end-np.array(t['formal']['tip']))) if t.get('formal',{}).get('tip') is not None else None
 return out,[dict(candidate_id=i,source='ACTUAL_PRODUCTION_PEAK_BEFORE_RANK_FILTER',endpoint_original=coords[i].tolist(),distance_to_human_tip_px=float(dist[i]),gain=p['gain'],stage=p['stage'],path_local_reverse=p['line_local_reverse'],hits=p['hits'],tail_hits=p['tail_hits'],shared=p['shared'],slope=p['slope']) for i,p in enumerate(peaks)]
def main():
 arg=argparse.ArgumentParser();arg.add_argument('phase',choices=['dev','val']);phase=arg.parse_args().phase
 assert read(OUT/f'{phase}_complete.json')['equivalence']=='PASS'
 groups=['group_a','ct2','group_h','ct3'] if phase=='dev' else ['group_c','three_point_bend']
 selected=[r for r in rows(OUT/'selected_frames.csv') if r['dataset_id'] in groups]
 old={(r['dataset_id'],r['frame_id']):r for r in rows(R05/'production_tip_comparison.csv')}
 coverage={(r['dataset_id'],r['frame_id']):r for r in rows(R05/'path_coverage.csv')}
 records=[];candidates=[];audits=[];reg=[];evidence=[]
 with zipfile.ZipFile(R05/'human_annotations_six_groups_snapshot.zip') as z:
  for r in selected:
   require(r['dataset_id'],'comparison',uses_annotations=True);g=r['dataset_id'];f=int(r['frame_id']);name=f'{g}__{f:06d}';t=read(OUT/'traces'/f'{name}.json');label=json.loads(z.read(r['selected_json']));p=old[g,str(f)];error=float(p['error_original_px']) if p['error_original_px'] else None
   with np.load(OUT/'maps'/f'{name}.npz') as archive:m={k:archive[k] for k in archive.files}
   result,peaks=classify(t,m,label,error);state=result['annotation_state']
   stratum='uncertain' if state=='UNCERTAIN' else 'no_observation' if p['observed']!='True' else 'relatively_correct' if error<=10 else 'early_stop' if float(p['predicted_x'])<float(p['human_tip_x']) and abs(float(p['predicted_y'])-float(p['human_tip_y']))<150 else 'far_off_path'
   base=dict(dataset_id=g,frame_id=f,group_role=role(g),variant='D0_TRACE_ONLY',image_size=t['image_size'],roi=t['roi'],main_rois=t['main_rois'],observed=p['observed']=='True',error_original_px=error,stratum=stratum,source_sha256=r['source_sha256'],evidence=f'traces/{name}.json',map=f'maps/{name}.npz',source_location='src/cpp/a/roi_tip.inc:146 measureTip; :68 distalLine; CrackV4.cpp:748 estimateTipMotion')
   records.append(dict(**base,**result));candidates.extend(dict(dataset_id=g,frame_id=f,**c) for c in peaks)
   audits.append(dict(dataset_id=g,frame_id=f,path_exists=bool(t['selected_original']),path_valid=p['observed']=='True',terminal_supported=p['observed']=='True',terminal_cause=t['terminal_cause'],reason=p['terminal_reason'],actual_peak_count=len(peaks),peak_rejection_counts=dict(collections.Counter(c['stage'] for c in peaks)),path_exists_equals_terminal=True,independent_root_identity_test=False,actual_condition_source='roi_tip.inc:95-140 and :224',trace=f'traces/{name}.json'))
   reg.append(dict(dataset_id=g,frame_id=f,tip_transform=t['tip_transform'],main_transform=t['main_transform'],branch=t['motion_branch'],valid=t['registration_valid'],inliers=t['solve_inliers'],angle=t['solve_angle'],residual=t['solve_residual'],matches=t['matches'],roundtrip_px=result['coordinate_roundtrip_px'],coordinate_direction='reference_original_to_current_original',template_quality_not_physical_truth=True))
   evidence.append(dict(dataset_id=g,frame_id=f,endpoint_evidence='actual_local_dark_valley_plus_registered_reference_NOT_FRANGI',evidence_status=result['failure_subtype'],**{k:v for k,v in result.items() if 'path_' in k or 'score' in k or 'reason_counts' in k or 'neighborhood' in k},E1_E2_separate_common_path_fraction=coverage[g,str(f)]['path_common_fraction'],E1_E2_not_production_input=True))
 save(OUT/f'reachability_{phase}.csv',records);save(OUT/f'candidate_{phase}.csv',candidates);save(OUT/f'terminal_{phase}.csv',audits);save(OUT/f'registration_{phase}.csv',reg);save(OUT/f'evidence_{phase}.csv',evidence)
 print(phase,len(records),dict(collections.Counter(r['first_failure_stage'] for r in records)),flush=True)
if __name__=='__main__':main()
