"""Frozen-output comparison against human labels; never runs training or a detector.

Human points are consumed only after predictions/warps/masks and thresholds are
locked. Entire labelled path length is retained in coverage denominators.
"""
from pathlib import Path
import sys,json,csv,hashlib,zipfile,collections,math,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/python'))
from crackv4.dataset_policy import role,require,filter_rows,POLICY_PATH,policy
BASE=ROOT/'output/runs/uctt_r05_prelabel_difference_20261111_r01'
PACKAGE=BASE/'R05_LabelMe_Annotation_Package'
OUT=ROOT/'output/runs/r05_annotation_validation_20261111_r01'
ARMS=['E1_FIXED_REF','E2_MATCHED_HISTORY','C0_NEAREST_PAST','C1_OPENING_ONLY']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def rows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def save(p,rr):
 if not rr:return
 with Path(p).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rr for k in r)));w.writeheader()
  for r in rr:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()})
def active_rows(rr):return filter_rows(rr,'comparison',uses_annotations=True)
def classify(d):
 c=collections.Counter(s['label'] for s in d['shapes'])
 if d['flags'].get('no_visible_crack',False):return 'NO_VISIBLE_CRACK'
 if c['uncertain_region'] and not c['crack_tip']:return 'UNCERTAIN'
 if c['crack_tip']==1 and c['crack_path']:return 'VISIBLE'
 return 'INCOMPLETE_OR_AMBIGUOUS'
def validate_label(d,r,p):
 allowed={'crack_path':{'linestrip'},'crack_tip':{'point'},'uncertain_region':{'polygon'},'branch_path':{'linestrip'},'interference':{'linestrip','polygon'}}
 w,h=int(r['image_width']),int(r['image_height']);assert (d['imageWidth'],d['imageHeight'])==(w,h)
 assert ((p/r['selected_json']).parent/d['imagePath']).resolve()==(p/r['selected_image']).resolve()
 for s in d['shapes']:
  typ=s['shape_type'];assert typ in allowed[s['label']];assert len(s['points'])>={'point':1,'linestrip':2,'polygon':3}[typ]
  if typ=='point':assert len(s['points'])==1
  assert all(len(pt)==2 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in pt) and 0<=pt[0]<w and 0<=pt[1]<h for pt in s['points'])
 assert isinstance(d['flags'].get('no_visible_crack',False),bool)
 if d['flags'].get('no_visible_crack',False):assert not any(s['label'] in ['crack_path','crack_tip','branch_path'] for s in d['shapes'])

def sample_paths(shapes,step=.5):
 points=[];weights=[]
 for s in shapes:
  if s['label']!='crack_path':continue
  for a,b in zip(s['points'][:-1],s['points'][1:]):
   a,b=np.array(a,float),np.array(b,float);length=float(np.linalg.norm(b-a))
   if length<=1e-12:continue
   n=max(1,int(math.ceil(length/step)));points.extend(a+(np.arange(n)[:,None]+.5)/n*(b-a));weights.extend([length/n]*n)
 return np.array(points).reshape(-1,2),np.array(weights)

def sample_mask(points,mask,roi,scale):
 if not len(points):return np.array([],bool)
 x=np.floor((points[:,0]-roi[0]+.5)*scale[0]).astype(int);y=np.floor((points[:,1]-roi[1]+.5)*scale[1]).astype(int)
 inside=(x>=0)&(x<mask.shape[1])&(y>=0)&(y<mask.shape[0]);valid=np.zeros(len(x),bool);valid[inside]=mask[y[inside],x[inside]]
 return valid

def tube_distance(shapes,shape,roi,scale,maximum=10):
 yy,xx=np.indices(shape);xx=roi[0]+(xx+.5)/scale[0]-.5;yy=roi[1]+(yy+.5)/scale[1]-.5;distance=np.full(shape,np.inf)
 for s in shapes:
  if s['label']!='crack_path':continue
  for a,b in zip(s['points'][:-1],s['points'][1:]):
   a,b=np.array(a,float),np.array(b,float);v=b-a;den=float(v@v)
   near=(xx>=min(a[0],b[0])-maximum)&(xx<=max(a[0],b[0])+maximum)&(yy>=min(a[1],b[1])-maximum)&(yy<=max(a[1],b[1])+maximum)
   if not near.any():continue
   t=np.clip(((xx[near]-a[0])*v[0]+(yy[near]-a[1])*v[1])/max(den,1e-12),0,1)
   delta=np.hypot(xx[near]-(a[0]+t*v[0]),yy[near]-(a[1]+t*v[1]));distance[near]=np.minimum(distance[near],delta)
 return distance

def fraction(weights,condition):return float(weights[condition].sum()/weights.sum()) if weights.sum()>0 else None

def render(r,d,z,coverage,dest):
 canvas=Image.new('RGB',(1600,980),'#142331');draw=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
 title=f"{r['dataset_id']} / frame {r['frame_id']} / {role(r['dataset_id'])} / {classify(d)}"
 draw.text((20,15),title,fill='white',font=font);draw.text((20,49),'Frozen outputs + HUMAN annotations / comparison only / no training / gray difference scale 0..80',fill='#ffdc8b',font=small)
 current=z['current'];common=z['common_mask'];roi=z['roi'];sx,sy=z['scale'];panels=[]
 for kind in ['original','labels','mask','E1_FIXED_REF','E2_MATCHED_HISTORY','labels_masked']:
  rgb=np.repeat(current[:,:,None],3,axis=2)
  if kind in ARMS:
   field=kind+'_signed_difference'
   if field in z and common.any():rgb=np.repeat(np.clip(abs(z[field].astype(float))*255/80,0,255).astype(np.uint8)[:,:,None],3,axis=2)
   else:rgb=np.full_like(rgb,45)
   rgb[~common]=[85,50,90]
  if kind in ['mask','labels_masked']:rgb[~common]=(rgb[~common]*.3+np.array([70,30,70])).astype(np.uint8)
  im=Image.fromarray(rgb)
  if kind in ['labels','labels_masked']:
   dr=ImageDraw.Draw(im)
   for s in d['shapes']:
    pts=[((x-roi[0]+.5)*sx-.5,(y-roi[1]+.5)*sy-.5) for x,y in s['points']]
    if s['label']=='crack_path':dr.line(pts,fill='#00ff88',width=2)
    elif s['label']=='crack_tip':
     x,y=pts[0];dr.ellipse((x-4,y-4,x+4,y+4),outline='#ff4444',width=2)
    elif s['label']=='uncertain_region':dr.line(pts+[pts[0]],fill='#ffcc00',width=2)
  panels.append((kind,im))
 for i,(name,im) in enumerate(panels):
  x=20+(i%3)*525;y=100+(i//3)*375;draw.text((x,y),name,fill='white',font=small);im.thumbnail((510,320));canvas.paste(im,(x,y+31))
 pct=lambda v:'N/A' if v is None else f'{100*v:.1f}%'
 draw.text((20,873),'Full labelled path inside ROI: '+pct(coverage['path_in_roi_fraction'])+' | common-valid path: '+pct(coverage['path_common_fraction']),fill='#ffdc8b',font=font)
 draw.text((20,913),'Purple = excluded area. Missing registration is not zero error. Path support is not tip accuracy.',fill='white',font=small)
 canvas.save(dest,quality=89)

def main():
 assert not (OUT/'pre_evaluation_lock.json').exists(),'Use a fresh run; never overwrite a scored validation lock'
 (OUT/'diagnostics').mkdir(exist_ok=True);assert not any((OUT/'diagnostics').iterdir());manifest=rows(PACKAGE/'selection_manifest.csv');active=active_rows(manifest);assert len(active)==120 and {r['dataset_id'] for r in active}=={'group_a','ct2','group_h','ct3','group_c','three_point_bend'}
 rules=json.loads((BASE/'global_rules.json').read_text(encoding='utf8'));threshold=rules['activation_threshold'];assert threshold==25
 # Freeze hashes BEFORE opening any human shapes or computing scores.
 inputs={str(BASE/'global_rules.json'):sha(BASE/'global_rules.json'),str(POLICY_PATH):sha(POLICY_PATH)}
 for name in ['history_reference_selection.csv','difference_comparison.csv','case_registration_details.json']:inputs[str(BASE/name)]=sha(BASE/name)
 for r in active:
  for p in [PACKAGE/r['selected_json'],BASE/'diagnostics'/f"{r['dataset_id']}__frame_{int(r['frame_id']):06d}.npz"]:inputs[str(p)]=sha(p)
 production={str(p):sha(p) for p in (ROOT/'src/cpp/a').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
 for p in [ROOT/'output/build/src/cpp/a/Release/CrackV4.dll',ROOT/'output/releases/A_Win64_OpenCV440/bin/CrackV4.dll']:production[str(p)]=sha(p)
 prior=json.loads((BASE/'frozen_manifest.json').read_text(encoding='utf8'))['protected']
 for p,h in production.items():assert prior[Path(p).relative_to(ROOT).as_posix()]==h,'Production identity changed since prelabel run'
 write(OUT/'pre_evaluation_lock.json',dict(inputs=inputs,production=production,policy=policy(),frozen_rules=rules,tolerances_original_px=[3,5,10],path_sample_step_px=.5,activation_threshold=threshold,label_use='COMPARISON_ONLY',training=False,fitting=False,validation_feedback_changes=False,excluded=['group_x'],scoring='whole labelled path arc-length coverage; pixel-center exact tube geometry; per-frame paired support',original_splits='preserved; group VALIDATION_ONLY overrides legacy development subset'))
 shutil.copyfile(POLICY_PATH,OUT/'dataset_usage_policy.json');shutil.copyfile(BASE/'global_rules.json',OUT/'frozen_algorithm_rules.json')
 cases={(c['dataset_id'],int(c['target_frame'])):c for c in json.loads((BASE/'case_registration_details.json').read_text(encoding='utf8')) if role(c['dataset_id'])!='EXCLUDED'}
 history=[r for r in rows(BASE/'history_reference_selection.csv') if role(r['dataset_id'])!='EXCLUDED'];save(OUT/'history_reference_selection_six_groups.csv',[h for h in history if any(h['dataset_id']==r['dataset_id'] and h['target_frame']==r['frame_id'] for r in active)])
 assert all(not h['selected_order'] or int(h['selected_order'])<int(h['target_order']) for h in history)
 statuses=[];metrics=[];coverage_rows=[];exclusions=[];label_shapes=collections.Counter();current_hashes={}
 with zipfile.ZipFile(OUT/'human_annotations_six_groups_snapshot.zip','w',zipfile.ZIP_DEFLATED) as snapshot:
  for r in active:
   g=r['dataset_id'];require(g,'comparison',uses_annotations=True);p=PACKAGE/r['selected_json'];raw=p.read_bytes();current_hashes[str(p)]=hashlib.sha256(raw).hexdigest();assert current_hashes[str(p)]==inputs[str(p)];snapshot.writestr(r['selected_json'],raw);d=json.loads(raw);validate_label(d,r,PACKAGE)
   image=PACKAGE/r['selected_image'];assert sha(image)==r['source_sha256']
   with Image.open(image) as im:assert im.size==(int(r['image_width']),int(r['image_height']));im.load()
   state=classify(d);assert state in ['VISIBLE','UNCERTAIN','NO_VISIBLE_CRACK'];label_shapes.update(s['label'] for s in d['shapes']);case=cases[g,int(r['frame_id'])];key=f"{g}__frame_{int(r['frame_id']):06d}"
   identity=dict(dataset_id=g,frame_id=int(r['frame_id']),group_role=role(g),original_split=r['split'],annotation_state=state,parameter_tuning_allowed=False,annotation_sha256=current_hashes[str(p)])
   statuses.append(identity)
   with np.load(BASE/'diagnostics'/(key+'.npz')) as z:
    common=z['common_mask'];roi=z['roi'];scale=z['scale'];shape=common.shape;allpix=np.ones(shape,bool);points,weights=sample_paths(d['shapes']);tip=np.array([s['points'][0] for s in d['shapes'] if s['label']=='crack_tip']).reshape(-1,2)
    both=all(case['arms'].get(a,{}).get('valid',False) for a in ARMS[:2])
    if both:assert np.array_equal(common,z['E1_FIXED_REF_valid_mask']&z['E2_MATCHED_HISTORY_valid_mask'])
    else:assert not common.any()
    assert not np.any(common&z['transition_mask'])
    coverage=dict(**identity,full_labelled_path_length_px=float(weights.sum()) if state=='VISIBLE' else None,path_in_roi_fraction=fraction(weights,sample_mask(points,allpix,roi,scale)),path_common_fraction=fraction(weights,sample_mask(points,common,roi,scale)),path_transition_fraction=fraction(weights,sample_mask(points,z['transition_mask'],roi,scale)),tip_in_roi=bool(sample_mask(tip,allpix,roi,scale)[0]) if len(tip)==1 else None,tip_common_valid=bool(sample_mask(tip,common,roi,scale)[0]) if len(tip)==1 else None,common_valid_pixels=int(common.sum()),common_area_fraction=float(common.mean()),paired_registration_valid=both,roi_original=roi.tolist())
    for arm in ARMS:
     result=case['arms'].get(arm);field=arm+'_valid_mask';coverage[arm+'_registration_valid']=bool(result and result['valid']);coverage[arm+'_path_valid_fraction']=fraction(weights,sample_mask(points,z[field],roi,scale)) if result and result['valid'] else (0. if len(weights) else None)
     if not result or not result['valid']:exclusions.append(dict(**identity,arm=arm,reason=result['reason'] if result else 'no_causal_reference_or_all_candidates_rejected'))
    coverage_rows.append(coverage)
    if state=='VISIBLE':
     distances=tube_distance(d['shapes'],shape,roi,scale);ablation=z['ablation_common_mask']
     for comparison,mask,arms in [('PRIMARY_E1_E2',common,ARMS[:2]),('FOUR_ARM_ABLATION',ablation,ARMS)]:
      for tol in [3,5,10]:
       tube=distances<=tol;target=mask&tube;off=mask&~tube
       for arm in arms:
        signed=arm+'_signed_difference';available=bool(signed in z and case['arms'].get(arm,{}).get('valid',False) and mask.any());act=(abs(z[signed])>threshold)&mask if available else None
        metrics.append(dict(**identity,comparison=comparison,tolerance_original_px=tol,arm=arm,paired_area_pixels=int(mask.sum()),path_band_in_roi_pixels=int(tube.sum()),path_band_valid_pixels=int(target.sum()),path_band_coverage_in_roi=float(target.sum()/tube.sum()) if tube.any() else None,path_difference_support=float(act[target].mean()) if available and target.any() else None,off_path_activation_density=float(act[off].mean()) if available and off.any() else None,off_path_is_true_false_positive=False,static_strip_gt_overlap_pixels=int((z['holdout_mask']&tube&mask).sum()),missing_reason='' if available and target.any() else 'NO_COMMON_VALID_AREA' if not mask.any() else 'NO_GT_PATH_PIXELS_IN_COMMON_MASK',tip_localization_error_px=None,tip_error_reason='DIFFERENCE_ARMS_DO_NOT_OUTPUT_TIP_PREDICTIONS',interference_activation=None,interference_reason='NO_HUMAN_INTERFERENCE_LABELS'))
    render(r,d,z,coverage,OUT/'diagnostics'/(key+'.jpg'))
   if len(statuses)%20==0:print('compared',len(statuses),g,flush=True)
 save(OUT/'annotation_status.csv',statuses);save(OUT/'path_coverage.csv',coverage_rows);save(OUT/'difference_label_comparison.csv',metrics);save(OUT/'excluded_or_failed_arms.csv',exclusions)
 save(OUT/'active_selection_manifest.csv',[dict(r,effective_role=role(r['dataset_id']),annotation_use='COMPARISON_ONLY',training_allowed=False) for r in active])
 write(OUT/'comparison_summary.json',dict(groups=sorted({r['dataset_id'] for r in statuses}),count=len(statuses),status_counts=dict(collections.Counter(r['annotation_state'] for r in statuses)),label_counts=dict(label_shapes),production_updated=False,training_performed=False,parameter_fitting=False,excluded_group_x=20,tip_accuracy='NOT_COMPUTED_NO_TIP_PREDICTIONS',negative_metrics='N/A_NO_NO_VISIBLE_CRACK_LABELS',interference_metrics='N/A_NO_INTERFERENCE_LABELS'))
 assert all(sha(p)==h for p,h in inputs.items());assert all(sha(p)==h for p,h in production.items())
 write(OUT/'integrity_check.json',dict(status='PASS',frozen_input_files=len(inputs),production_files=len(production),annotations_unchanged=True,group_x_labels_or_images_opened=False,group_policy_assertions=True))
 print('FROZEN ANNOTATION COMPARISON COMPLETE',len(statuses),flush=True)
if __name__=='__main__':main()
