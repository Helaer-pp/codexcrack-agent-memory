"""Offline labels only, after complete frozen inference and native parity lock."""
from common import *
import argparse,zipfile,collections
import numpy as np
from scipy.spatial import cKDTree
SENTINELS=[('ct2',395),('group_h',78),('group_a',504),('ct3',65)]
CATEGORIES=['INPUT_OR_COORDINATE_ERROR','P1P2_TRACK_FAILURE','ROI_GEOMETRY_EXCLUSION','ORIGIN_WRONG_LOCK','REFERENCE_COMPENSATION_UNTRUSTWORTHY','MATERIAL_GRAY_VETO','CURRENT_VALLEY_MISSING','REFERENCE_DELTA_MISSING','PATH_JUMP_OR_OVEREXTEND','PREMATURE_GAP_STOP','NOT_OBSERVABLE','UNKNOWN','WITHIN_10']
def dense(points):
 p=np.asarray(points,float).reshape(-1,2);out=[]
 for a,b in zip(p[:-1],p[1:]):
  n=max(1,int(np.ceil(np.linalg.norm(b-a))));out.extend(a+(b-a)*np.arange(n)[:,None]/n)
 if len(p):out.append(p[-1])
 return np.asarray(out,float).reshape(-1,2)
def observed(trace):
 return np.asarray([[float(r['x']),float(r['selected_y'])] for r in trace if r['is_observed']=='True'],float).reshape(-1,2)
def visible_dense(trace):
 chunks=[];part=[]
 for r in trace:
  if r['is_observed']=='True':part.append([float(r['x']),float(r['selected_y'])])
  elif part:chunks.extend(dense(part));part=[]
 if part:chunks.extend(dense(part))
 return np.asarray(chunks,float).reshape(-1,2)
def load_labels(groups):
 assert read(OUT/'parity_gate.json')['passed'];labels={};access=[];flat=[]
 with zipfile.ZipFile(LABELS) as z:
  for row in rows(F/'selected_frames.csv'):
   g=row['dataset_id']
   if g not in groups:continue
   require(g,'comparison',uses_annotations=True)
   if g in VAL:assert (OUT/f'validation_complete_{g}.json').exists()
   raw=z.read(row['selected_json']);label=json.loads(raw);key=g,int(row['frame_id']);labels[key]=label;tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];flat.append(dict(group=g,frame_id=key[1],visibility='VISIBLE' if tips else 'UNCERTAIN',tip_x=tips[0][0] if tips else None,tip_y=tips[0][1] if tips else None));access.append(dict(group=g,frame_id=key[1],member=row['selected_json'],sha256=hashlib.sha256(raw).hexdigest(),use='comparison_only_after_inference'))
 save(OUT/'inputs'/('labels_offline_dev.csv' if groups==DEV else 'labels_offline_validation.csv'),flat);save(OUT/('annotation_access_dev.csv' if groups==DEV else 'annotation_access_validation.csv'),access);return labels
def main(groups):
 for g in groups:assert (OUT/(f'python_complete_{g}.json' if g in DEV else f'validation_complete_{g}.json')).exists()
 labels=load_labels(groups);results=[];frames=[];failures=[];baseline=[];old={}
 for path in [D/'dev_frames.jsonl'] if groups==DEV else [D/'val_frames.jsonl']:
  for line in path.open(encoding='utf8'):
   r=json.loads(line);old[r['dataset_id'],r['frame_id']]=r
 for g in groups:
  manifest=rows(OUT/'inputs'/('manifest.csv' if g in DEV else 'validation_manifest.csv'));sequence=[r for r in manifest if r['group']==g]
  for row in sequence:
   f=int(row['frame_id']);folder=OUT/'py_runs'/g/str(f);metric=read(folder/'adapter_metrics.json');ok=metric['status']=='OK';metadata=read(folder/'metadata.json') if ok else {};frames.append(dict(group=g,frame_id=f,**metric));summary=rows(folder/'summary_results.csv') if ok else [dict(mode=m,threshold=t,tip_x='',tip_y='',stop_reason=metric['error']) for m in ['joint','current'] for t in [8,10,12]];label=labels.get((g,f));tips=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'] if label else [];parts=[dense(s['points']) for s in label['shapes'] if s['label']=='crack_path'] if label else [];gt=np.concatenate(parts) if parts else np.empty((0,2));tip=np.array(tips[0]) if tips else None;visibility='VISIBLE' if tips else 'UNCERTAIN' if label else 'UNLABELED';roi=metadata.get('ROI');arrays=None
   if label and (folder/'evidence_arrays.npz').exists():
    with np.load(folder/'evidence_arrays.npz') as archive:arrays={key:archive[key] for key in archive.files}
   if tip is not None:
    a=old.get((g,f),{});at=a.get('tip') if a.get('observed') else None;baseline.append(dict(group=g,frame_id=f,visibility=visibility,mode='A55a0',threshold='',provisional=False,coverage=at is not None,tip=at,error=float(np.linalg.norm(np.array(at)-tip)) if at is not None else None))
   for item in summary:
    mode=item['mode'];threshold=int(float(item['threshold']));pt=[float(item['tip_x']),float(item['tip_y'])] if item.get('tip_x','')!='' else None;r=dict(group=g,frame_id=f,split=role(g),mode=mode,threshold=threshold,status=metric['status'],visibility=visibility,provisional=True,formal_observed=False,coverage=pt is not None,tip=pt,error=float(np.linalg.norm(np.array(pt)-tip)) if pt is not None and tip is not None else None,stop_reason=item.get('stop_reason'),observed_points=item.get('observed_points'),visited_columns=item.get('visited_columns'),roi=roi,roi_contains_gt=None,sampling_roi_contains_gt=None,path_recall5=None,path_recall10=None,path_precision5=None,path_precision10=None,stage=None,reason=None)
    if tip is not None:
     if roi:r['roi_contains_gt']=bool(roi['x_left']<=tip[0]<roi['x_right'] and roi['y_top']<=tip[1]<=roi['y_bottom']);r['sampling_roi_contains_gt']=bool(roi['x_left']<=tip[0]<roi['x_right'] and roi['y_top']+2<=tip[1]<roi['y_bottom']-1)
     trace=rows(folder/f'trace_{mode}_T{threshold}p0.csv') if ok else [];path=visible_dense(trace);obs=observed(trace);tree=cKDTree(gt) if len(gt) else None
     if len(gt):
      d=cKDTree(path).query(gt)[0] if len(path) else np.full(len(gt),np.inf);back=tree.query(path)[0] if len(path) else []
      for tol in [5,10]:r[f'path_recall{tol}']=float(np.mean(d<=tol));r[f'path_precision{tol}']=float(np.mean(np.array(back)<=tol)) if len(back) else 0.
      r['gt_path_inside_roi_fraction']=float(np.mean((gt[:,0]>=roi['x_left'])&(gt[:,0]<roi['x_right'])&(gt[:,1]>=roi['y_top'])&(gt[:,1]<=roi['y_bottom']))) if roi else 0
     if trace:
      seed=[float(trace[0]['x']),float(trace[0]['predicted_y'])];r['first_predicted_point']=seed;r['initial_distance_gt_path']=float(tree.query(seed)[0]) if tree else None;r['last_visited_x']=float(trace[-1]['x']);r['last_missing_run']=int(trace[-1]['missing_run']);r['initial_gt_x_in_range']=bool(len(gt) and gt[:,0].min()-3<=seed[0]<=gt[:,0].max()+3)
     if pt is not None:r['signed_x_error']=pt[0]-tip[0]
     if arrays is not None:
      xa,ya,xb,yb=arrays['crop_xyxy'];x=int(round(tip[0]-xa));y=int(round(tip[1]-ya));inside=0<=x<xb-xa and 0<=y<yb-ya
      if inside:
       for k in ['csm','reference_aligned','valley','newdark','flank_low','valid_material','score']:r['gt_pixel_'+k]=float(arrays[k][y,x])
       ys=slice(max(0,y-3),min(arrays['valley'].shape[0],y+4));xs=slice(max(0,x-3),min(arrays['valley'].shape[1],x+4));v=arrays['valley'][ys,xs];d=arrays['newdark'][ys,xs];mask=arrays['valid_material'][ys,xs];r['gt_neighborhood_max_valley']=float(v.max());r['gt_neighborhood_max_delta']=float(d.max());r['gt_neighborhood_material_pixels']=int(mask.sum());r['gt_neighborhood_current_accepted']=int(np.sum(mask&(v>=threshold)));r['gt_neighborhood_joint_accepted']=int(np.sum(mask&(v>=threshold)&(d>=threshold)))
     if not ok:stage='P1P2_TRACK_FAILURE' if metric['status']=='POINT_INVALID' else 'INPUT_OR_COORDINATE_ERROR';reason=metric['error']
     elif not r['sampling_roi_contains_gt']:stage='ROI_GEOMETRY_EXCLUSION';reason='GT_OUTSIDE_P1P2_ROI or frozen sampling inset/right boundary; no ROI adjustment'
     elif r['error'] is not None and r['error']<=10:stage='WITHIN_10';reason='Provisional endpoint within10px; not independent confirmation'
     elif r.get('initial_gt_x_in_range') and (r.get('initial_distance_gt_path') or 0)>10:stage='ORIGIN_WRONG_LOCK';reason='First predicted center at xleft+6 lies >10px from labeled path; recorded before any accepted observation'
     elif r.get('gt_neighborhood_material_pixels')==0:stage='MATERIAL_GRAY_VETO';reason='No accepted material-mask pixel within3px of offline GT; inspect flank_low and ROI'
     elif r.get('gt_neighborhood_current_accepted')==0:stage='CURRENT_VALLEY_MISSING';reason='No material-valid current valley reaches frozen threshold within3px of GT'
     elif mode=='joint' and r.get('gt_neighborhood_joint_accepted')==0:stage='REFERENCE_DELTA_MISSING';reason='Current valley exists but no joint threshold support near GT; motion cause not independently established'
     elif pt is not None and pt[0]>tip[0]+10:stage='PATH_JUMP_OR_OVEREXTEND';reason='Final selected pixel extends >10px beyond labeled tip x'
     elif r.get('last_missing_run',0)>20 and r.get('last_visited_x',1e9)<tip[0]:stage='PREMATURE_GAP_STOP';reason='Observed trace ends after21 misses before GT x, despite near-GT evidence or unavailable diagnosis'
     else:stage='UNKNOWN';reason='Insufficient evidence for a unique causal attribution; retain arrays and complete column trace'
     r['stage']=stage;r['reason']=reason;failures.append(r.copy())
    results.append(r)
 summary=[]
 for group in groups+['DEVELOPMENT' if groups==DEV else 'VALIDATION_ONLY']:
  part=[r for r in results if r['group']==group or group not in groups]
  for mode in ['joint','current']:
   for threshold in [8,10,12]:
    rr=[r for r in part if r['mode']==mode and r['threshold']==threshold];v=[r for r in rr if r['visibility']=='VISIBLE'];errors=[r['error'] for r in v if r['error'] is not None];s=dict(group=group,mode=mode,threshold=threshold,frames=len(rr),successful_frames=sum(r['status']=='OK' for r in rr),visible=len(v),uncertain=sum(r['visibility']=='UNCERTAIN' for r in rr),provisional_coverage=sum(r['coverage'] for r in v),formal_observed=0,error_n=len(errors),roi_gt_outside=sum(r['roi_contains_gt'] is False for r in v),sampling_roi_gt_outside=sum(r['sampling_roi_contains_gt'] is False for r in v),error_p50=float(np.percentile(errors,50)) if errors else None,error_p95=float(np.percentile(errors,95)) if errors else None,error_max=max(errors) if errors else None)
    for tol in [3,5,10]:s[f'hit{tol}']=sum(e<=tol for e in errors);s[f'hit{tol}_fraction_all_visible']=s[f'hit{tol}']/len(v) if v else None
    for tol in [100,500]:s[f'over{tol}']=sum(e>tol for e in errors)
    for key in ['path_recall5','path_recall10','path_precision5','path_precision10']:s[key]=float(np.mean([r[key] or 0 for r in v])) if v else None
    summary.append(s)
 suffix='dev' if groups==DEV else 'validation';save(OUT/'tables'/f'all_frames_{suffix}.csv',frames);save(OUT/'tables'/f'all_results_{suffix}.csv',results);save(OUT/'tables'/f'group_summary_{suffix}.csv',summary);save(OUT/'tables'/f'failure_stages_{suffix}.csv',failures);save(OUT/'tables'/f'A55_comparison_rows_{suffix}.csv',baseline)
 counts=[]
 for category in CATEGORIES:
  rr=[r for r in failures if r['mode']=='joint' and r['threshold']==10 and r['stage']==category];counts.append(dict(stage=category,count=len(rr),representative=f"{rr[0]['group']}/{rr[0]['frame_id']}" if rr else None,evidence=rr[0]['reason'] if rr else 'No classified cases; not evidence that this failure mechanism is impossible'))
 save(OUT/'tables'/f'failure_counts_{suffix}.csv',counts);write(OUT/f'evaluation_{suffix}_complete.json',dict(frames=len(frames),result_rows=len(results),annotated=len(labels),visible=len(baseline),source_unchanged=sha(FROZEN)==EXPECTED_SHA));print([r for r in summary if r['group'] not in groups],flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--validation',action='store_true');a=p.parse_args();main(VAL if a.validation else DEV)
