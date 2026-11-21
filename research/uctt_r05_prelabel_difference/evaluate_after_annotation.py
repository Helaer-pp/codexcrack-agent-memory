"""Import actual human labels. Empty/uncertain samples are never negatives.

No tip is inferred from differences. Optional externally declared predictions are
evaluated separately; the default has no point predictions and reports N/A.
"""
import argparse,collections
from scipy.ndimage import distance_transform_edt
from common import *
from annotation_qc import validate

def region(shapes,label,shape,roi,scale,tolerance=5):
 mask=np.zeros(shape,np.uint8);sx,sy=scale;x0,y0,_,_=roi
 for s in shapes:
  if s['label']!=label:continue
  points=np.array([[(x-x0)*sx,(y-y0)*sy] for x,y in s['points']],np.int32)
  if s['shape_type']=='polygon':cv2.fillPoly(mask,[points],1)
  elif len(points)>1:cv2.polylines(mask,[points],False,1,1)
 if not mask.any():return mask.astype(bool)
 return distance_transform_edt(1-mask,sampling=(1/sy,1/sx))<=tolerance

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--package',type=Path,default=PACKAGE);ap.add_argument('--include-holdout',action='store_true');ap.add_argument('--locked-rules-sha');ap.add_argument('--predictions',type=Path);args=ap.parse_args()
 progress=validate(args.package);counts=collections.Counter(r['annotation_status'] for r in progress)
 if counts['UNANNOTATED']==len(progress):
  write(OUT/'annotation_evaluation.json',dict(status='AWAITING_MANUAL_ANNOTATION',status_counts=dict(counts),real_tip_accuracy=None,denominator=0,production_algorithm_updated=False));print('AWAITING_MANUAL_ANNOTATION');return
 if args.include_holdout:assert args.locked_rules_sha==sha(OUT/'global_rules.json'),'Holdout requires exact frozen global-rules SHA'
 predictions={}
 if args.predictions:
  for r in rows(args.predictions):
   assert r['output_type'] in ['observed','predicted','fallback'];predictions[r['dataset_id'],r['frame_id']]=r
 manifest=rows(args.package/'selection_manifest.csv');output=[];errors=[]
 for r,p in zip(manifest,progress):
  assert (r['dataset_id'],r['frame_id'])==(p['dataset_id'],p['frame_id'])
  if r['split']=='holdout' and not args.include_holdout:continue
  status=p['annotation_status'];g=r['dataset_id'];frame=r['frame_id'];labels=json.loads((args.package/r['selected_json']).read_text(encoding='utf8'));key=(g,frame)
  if status not in ['ANNOTATED_VISIBLE','NO_VISIBLE_CRACK']:
   output.append(dict(dataset_id=g,frame_id=frame,split=r['split'],status=status,exclusion_reason='incomplete_or_uncertain_not_negative'));continue
  pred=predictions.get(key);tips=[s['points'][0] for s in labels['shapes'] if s['label']=='crack_tip'];error=None
  if tips and pred and pred['valid'].lower()=='true' and pred['output_type']=='observed':
   error=float(np.linalg.norm(np.array(tips[0])-np.array([float(pred['x']),float(pred['y'])])));errors.append(dict(dataset_id=g,split=r['split'],error_px=error))
  f=OUT/'diagnostics'/f'{g}__frame_{int(frame):06d}.npz'
  if not f.exists():output.append(dict(dataset_id=g,frame_id=frame,status=status,exclusion_reason='difference_artifact_unavailable'));continue
  with np.load(f) as data:
   common=data['common_mask'];shape=common.shape;roi=data['roi'];scale=data['scale'];interference=region(labels['shapes'],'interference',shape,roi,scale)
   for arm in ['E1_FIXED_REF','E2_MATCHED_HISTORY']:
    field=arm+'_signed_difference'
    for tol in [3,5,10]:
     path=region(labels['shapes'],'crack_path',shape,roi,scale,tol);target=common&path;intr=common&interference;activation=abs(data[field])>25 if field in data else np.zeros(shape,bool)
     output.append(dict(dataset_id=g,frame_id=frame,split=r['split'],status=status,arm=arm,tolerance_original_px=tol,common_pixel_count=int(common.sum()),path_common_pixels=int(target.sum()),path_in_roi_pixels=int(path.sum()),path_common_coverage=float(target.sum()/path.sum()) if path.any() else None,path_difference_support=float(activation[target].mean()) if target.any() and field in data else None,interference_activation=float(activation[intr].mean()) if intr.any() and field in data else None,off_path_activation=float(activation[common&~path].mean()) if (common&~path).any() and field in data else None,tip_error_original_px=error,tip_prediction_status='OBSERVED_EVALUATED' if error is not None else 'N/A_NO_OBSERVED_TIP',exclusion_reason='' if common.any() and field in data else 'no_valid_paired_difference'))
 save(OUT/'annotation_evaluation_frames.csv',output)
 summaries=[]
 for g,split in sorted({(e['dataset_id'],e['split']) for e in errors}):
  ee=np.array([e['error_px'] for e in errors if e['dataset_id']==g and e['split']==split]);summaries.append(dict(dataset_id=g,split=split,denominator=len(ee),p50_px=float(np.median(ee)),p95_px=float(np.percentile(ee,95)),max_px=float(ee.max()),within3=float(np.mean(ee<=3)),within5=float(np.mean(ee<=5)),within10=float(np.mean(ee<=10))))
 write(OUT/'annotation_evaluation.json',dict(status='HUMAN_LABELS_IMPORTED',status_counts=dict(counts),tip_metrics=summaries,tip_metrics_status='EVALUATED' if errors else 'N/A_NO_OBSERVED_PREDICTIONS',holdout_evaluated=args.include_holdout,physical_stage='human metadata only; never inferred from frame order',caution='difference support does not require coverage of an unchanged historical crack; annotation tolerance is not exact GT precision'))

if __name__=='__main__':main()
