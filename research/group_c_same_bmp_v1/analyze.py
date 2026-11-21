"""Offline quantitative causal audit; reads completed fixed runs and never selects parameters."""
from core import *
import zipfile,math
from collections import Counter

def load_case(name):
 folder=OUT/'runs'/name
 with np.load(folder/'arrays.npz') as z:arrays={k:z[k] for k in z.files}
 return dict(name=name,folder=folder,arrays=arrays,meta=read(folder/'metadata.json'),observer=read(folder/'observer.json'),init=rows(folder/'initial_candidates.csv'),initial=rows(folder/'track_initialization.csv'),candidates=rows(folder/'column_candidates.csv'),summary=rows(folder/'summary_results.csv'))
def trace(name,mode='joint',thr=10):return rows(OUT/'runs'/name/f'trace_{mode}_T{thr}p0.csv')
def tip(row):return [float(row['tip_x']),float(row['tip_y'])] if row['tip_x'] else None
def brief(name,kind,extra=None):
 folder=OUT/'runs'/name;initial={(r['mode'],float(r['threshold'])):r for r in rows(folder/'track_initialization.csv')};obs=read(folder/'observer.json');output=[]
 for s in rows(folder/'summary_results.csv'):
  mode=s['mode'];thr=int(float(s['threshold']));t=trace(name,mode,thr);seen=[r for r in t if r['is_observed']=='True'];point=tip(s);r=dict(case=name,kind=kind,mode=mode,threshold=thr,reference_points=obs['reference_points'],current_points=obs['current_points'],tip=point,status='PROVISIONAL' if point else 'NO_TIP',approximate_anchor_error=float(np.linalg.norm(np.array(point)-[2423,2344])) if point else None,anchor_kind='offline approximate golden tip; not a frame-specific LabelMe GT',xstart=int(initial[mode,thr]['xstart']),ctr=float(initial[mode,thr]['ctr']),y0=int(initial[mode,thr]['y0']),init_ymin=int(initial[mode,thr]['init_ymin']),init_ymax=int(initial[mode,thr]['init_ymax']),initial_nonzero_scores=int(initial[mode,thr]['nonzero_scores']),all_initial_scores_zero=initial[mode,thr]['all_scores_zero']=='True',first_observed=[int(seen[0]['x']),int(seen[0]['selected_y'])] if seen else None,observed_points=int(s['observed_points']),visited_columns=int(s['visited_columns']),last_visited_x=int(s['last_visited_x']),maximum_missing_run=max(int(x['missing_run']) for x in t),last_missing_run=int(t[-1]['missing_run']),native_stop_reason=s['stop_reason'],actual_loop_end='gap_gt20' if int(t[-1]['missing_run'])>20 else 'ROI_right_boundary',geometry=obs['geometry'],point_translations=obs['point_translations'],alpha_min=obs['fields']['alpha']['min'],alpha_max=obs['fields']['alpha']['max'],alpha_mean=obs['fields']['alpha']['mean'],**(extra or {}));output.append(r)
 return output
def crop_global(case,field,bounds):
 xa,ya,xb,yb=case['arrays']['crop'];x0,y0,x1,y1=bounds;return case['arrays'][field][y0-ya:y1-ya,x0-xa:x1-xa]
def intersection(a,b):
 aa=a['arrays']['crop'];bb=b['arrays']['crop'];return [int(max(aa[0],bb[0])),int(max(aa[1],bb[1])),int(min(aa[2],bb[2])),int(min(aa[3],bb[3]))]
def divergences(a,b):
 output=[];bounds=intersection(a,b);label=a['name']+' vs '+b['name']
 ga=a['observer']['geometry'];gb=b['observer']['geometry'];output.append(dict(comparison=label,layer='input_ROI_geometry',different=ga!=gb,a=ga,b=gb,interpretation='Geometry is an input intervention, not an image identity error'))
 for field in ['ca','csm','reference_aligned','rsm','newdark','valley','flank_low','roi_mask','valid_material','score']:
  va=crop_global(a,field,bounds).astype(float);vb=crop_global(b,field,bounds).astype(float);d=np.abs(va-vb);coords=np.argwhere(d>.1);point=[int(coords[0,1]+bounds[0]),int(coords[0,0]+bounds[1])] if len(coords) else None
  output.append(dict(comparison=label,layer=field,different=bool(np.any(d>1e-6)),a=None,b=None,common_crop=bounds,mean_abs=float(d.mean()),p95_abs=float(np.percentile(d,95)),max_abs=float(d.max()),pixels_gt_1e_6=int((d>1e-6).sum()),pixels_gt_0p1=int((d>.1).sum()),pixels_gt_1=int((d>1).sum()),first_row_major_gt_0p1=point,interpretation='Common global-pixel statistical difference; first raster pixel is NOT automatically a causal tracking divergence'))
 for mode in ['joint','current']:
  ia=next(r for r in a['initial'] if r['mode']==mode and r['threshold']=='10.0');ib=next(r for r in b['initial'] if r['mode']==mode and r['threshold']=='10.0');output.append(dict(comparison=label,layer=mode+'_initial_y0',different=ia['y0']!=ib['y0'],a=dict(x=int(ia['xstart']),y0=int(ia['y0']),ctr=float(ia['ctr'])),b=dict(x=int(ib['xstart']),y0=int(ib['y0']),ctr=float(ib['ctr'])),interpretation='Different xstart must not be called the same-column comparison'))
  ta=trace(a['name'],mode);tb=trace(b['name'],mode);da={r['x']:r for r in ta};db={r['x']:r for r in tb};shared=sorted(set(da)&set(db),key=int)
  output.append(dict(comparison=label,layer=mode+'_first_selected_ordinal',different=(ta[0]['x'],ta[0]['selected_y'])!=(tb[0]['x'],tb[0]['selected_y']),a=[ta[0]['x'],ta[0]['selected_y']],b=[tb[0]['x'],tb[0]['selected_y']],interpretation='First loop iteration; x may differ'))
  for column in ['selected_y','is_observed','missing_run']:
   first=next((x for x in shared if da[x][column]!=db[x][column]),None);output.append(dict(comparison=label,layer=mode+'_first_shared_x_'+column,different=first is not None,x=int(first) if first else None,a=da[first][column] if first else None,b=db[first][column] if first else None,python_row_a=da[first] if first else None,python_row_b=db[first] if first else None,interpretation='Compared at matching original-image x, not row ordinal'))
  pa=tip(next(r for r in a['summary'] if r['mode']==mode and r['threshold']=='10.0'));pb=tip(next(r for r in b['summary'] if r['mode']==mode and r['threshold']=='10.0'));output.append(dict(comparison=label,layer=mode+'_endpoint',different=pa!=pb,a=pa,b=pb))
 return output

def evidence_swap(cases):
 rates=[];crossings=[]
 for geom in ['A','D']:
  a=cases[f'CF_geometry_{geom}_motion_A'];b=cases[f'CF_geometry_{geom}_motion_D'];assert np.array_equal(a['arrays']['crop'],b['arrays']['crop'])
  for key in ['ca','csm','valley','flank_low','roi_mask','valid_material']:assert np.array_equal(a['arrays'][key],b['arrays'][key]),(geom,key)
  aa=a['arrays'];bb=b['arrays'];xa,ya,xb,yb=aa['crop'];init=next(r for r in a['initial'] if r['mode']=='joint' and r['threshold']=='10.0');xstart=int(init['xstart']);regions=[]
  for n in [1,20,100]:
   mask=np.zeros_like(aa['valid_material']);mask[:,xstart-xa:min(xstart+n,xb)-xa]=True;mask&=aa['roi_mask'];regions.append((f'first_{n}_ROI_columns',mask,'Fixed x region, may extend beyond the executed stopping column'))
  for refname in ['A','D']:
   refmode='joint' if refname=='A' else 'current';mask=np.zeros_like(aa['valid_material'])
   for row in trace(refname,refmode):
    if row['is_observed']!='True':continue
    x=int(row['x'])-xa;y=int(row['selected_y'])-ya
    if 0<=x<mask.shape[1] and 0<=y<mask.shape[0]:mask[max(0,y-3):min(mask.shape[0],y+4),max(0,x-3):min(mask.shape[1],x+4)]=True
   regions.append((f'near_{refname}_{refmode}_trace_3px',mask,'Posthoc computational trace neighborhood, NOT an independent manual crack path'))
  for region,mask,meaning in regions:
   for name,c in [('A',aa),('D',bb)]:
    valid=c['valid_material']&mask;val=valid&(c['valley']>=10);joint=val&(c['newdark']>=10);n=int(mask.sum());rates.append(dict(geometry=geom,motion=name,region=region,region_pixels=n,material_pixels=int(valid.sum()),current_valley_pixels=int(val.sum()),joint_pixels=int(joint.sum()),material_fraction=float(valid.sum()/n),current_fraction=float(val.sum()/n),joint_fraction=float(joint.sum()/n),mean_valley=float(c['valley'][mask].mean()),mean_newdark=float(c['newdark'][mask].mean()),region_meaning=meaning))
  x0=xstart-xa;x1=min(xstart+100,xb)-xa;window=np.zeros_like(aa['roi_mask']);window[:,x0:x1]=True
  down=window&aa['valid_material']&(aa['valley']>=10)&(aa['newdark']>=10)&(bb['newdark']<10)
  up=window&aa['valid_material']&(aa['valley']>=10)&(aa['newdark']<10)&(bb['newdark']>=10)
  for direction,mask in [('A_pass_D_veto',down),('A_veto_D_pass',up)]:
   for y,x in np.argwhere(mask):crossings.append(dict(geometry=geom,direction=direction,x=int(x+xa),y=int(y+ya),valley=float(aa['valley'][y,x]),newdark_A=float(aa['newdark'][y,x]),newdark_D=float(bb['newdark'][y,x]),material=True))
 save(OUT/'reference_evidence_rates.csv',rates);save(OUT/'reference_threshold_crossings.csv',crossings)

def independent_motion(config,cases):
 R=cv2.imread(config['reference'],0);C=cv2.imread(config['current'],0);p=config['points'];m,_,_,_=module();ncc=[]
 for name in ['G','S']:
  for i,pt in enumerate(p['R_'+name]):
   matched,info=m.track_reference_point(R,C,pt,29,25,.8);given=p['C_'+name][i];ncc.append(dict(pair=name,point=i+1,reference=pt,provided_current=given,independent_frozen_NCC_current=list(matched),ncc=info['ncc'],provided_vs_NCC_distance=float(np.linalg.norm(np.array(given)-matched)),meaning='Checks tracking consistency around each own reference center; does not prove identical physical point semantics between G and S'))
 save(OUT/'point_ncc_audit.csv',ncc)
 # Fixed material-texture candidates based on P geometry only; no GT/chosen detection path.
 mid=int(round(np.mean(p['C_G'],axis=0)[1]));xleft=int(math.ceil(max(v[0] for v in p['C_G'])));patches=[]
 for side,cy in [('upper',mid-60),('lower',mid+60)]:
  for offset in [450,850,1250]:
   cx=xleft+offset;w=160;h=32;search=20;x0=cx-w//2;y0=cy-h//2;refpatch=R[y0:y0+h,x0:x0+w];region=C[y0-search:y0+h+search,x0-search:x0+w+search];response=cv2.matchTemplate(region,refpatch,cv2.TM_CCOEFF_NORMED);_,q,_,loc=cv2.minMaxLoc(response);dx=loc[0]-search;dy=loc[1]-search;central=response.copy();px,py=loc;central[max(0,py-2):py+3,max(0,px-2):px+3]=-np.inf;second=float(central.max());std=float(refpatch.std());curr=C[y0:y0+h,x0:x0+w].astype(np.float32)
   for motion in ['A','D']:
    rp,cp=(p['R_G'],p['C_G']) if motion=='A' else (p['R_S'],p['C_S']);Y,X=np.mgrid[y0:y0+h,x0:x0+w].astype(np.float32);alpha=np.clip((Y-cp[0][1])/(cp[1][1]-cp[0][1]),0,1);d0=np.array(cp[0])-rp[0];d1=np.array(cp[1])-rp[1];mx=(1-alpha)*d0[0]+alpha*d1[0];my=(1-alpha)*d0[1]+alpha*d1[1];aligned=cv2.remap(R,X-mx,Y-my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT_101).astype(np.float32);ac=aligned-aligned.mean();cc=curr-curr.mean();corr=float(np.sum(ac*cc)/(np.linalg.norm(ac)*np.linalg.norm(cc))) if np.linalg.norm(ac)*np.linalg.norm(cc)>0 else None;mean_dx=float(mx.mean());mean_dy=float(my.mean());patches.append(dict(patch=side+'_'+str(offset),side=side,bounds=[x0,y0,x0+w,y0+h],motion=motion,reference_std=std,template_peak_ncc=float(q),runnerup_ncc_excluding_5x5=second,independent_translation=[dx,dy],predicted_translation=[mean_dx,mean_dy],translation_delta=float(np.hypot(mean_dx-dx,mean_dy-dy)),aligned_current_ncc=corr,aligned_current_mae=float(np.mean(np.abs(aligned-curr))),mean_bias=float(np.mean(aligned-curr)),zero_mean_residual_rmse=float(np.sqrt(np.mean((ac-cc)**2))),texture_reliability='LOW_TEXTURE' if std<3 else 'LOW_NCC' if q<.8 else 'AMBIGUOUS_NCC' if q-second<.01 else 'INFORMATIVE',scope='fixed geometrical material-texture candidate; no independently certified crack-free mask; local motion only'))
 save(OUT/'independent_material_motion.csv',patches)

def sensitivity_table():
 plan=read(OUT/'sensitivity_plan.json');output=[]
 for c in plan['cases']:
  name='sensitivity/'+c['case'];rr=brief(name,'native_frozen_input_perturbation',dict(base=c['base'],scope=c['scope'],dy=c.get('dy'),t=c.get('t'),synthetic_not_measured_tracking_error=True))
  for r in rr:
   base=trace(c['base'],r['mode'],r['threshold']);now=trace(name,r['mode'],r['threshold']);dd={v['x']:v for v in base};first=next((row for row in now if row['x'] in dd and (row['selected_y'],row['is_observed'])!=(dd[row['x']]['selected_y'],dd[row['x']]['is_observed'])),None);r['first_shared_x_divergence']=int(first['x']) if first else None
   miss=next((row for row in now if row['is_observed']=='False'),None);r['first_unsupported_x']=int(miss['x']) if miss else None;r['first_unsupported_selected_valley']=float(miss['current_contrast']) if miss else None;r['first_unsupported_selected_delta']=float(miss['reference_new_darkening']) if miss else None;r['support_failure_note']='Selected best rejected pixel below valley threshold' if miss and float(miss['current_contrast'])<r['threshold'] else 'Selected best rejected pixel below delta threshold' if miss and r['mode']=='joint' and float(miss['reference_new_darkening'])<r['threshold'] else 'Material or another candidate constraint; full native trace retained' if miss else 'No missing columns';output.append(r)
 save(OUT/'point_sensitivity.csv',output)
 # Zero-offset controls must match their base, even when repeated as different planned families.
 zeros=[]
 for c in plan['cases']:
  if c.get('dy')==0 or c.get('t') in [0,1]:
   base='D' if c.get('t')==1 else c['base'];comp=compare_outputs(OUT/'runs'/base,OUT/'runs/sensitivity'/c['case']);assert comp['passed'];zeros.append(dict(case=c['case'],base=base,**comp))
 save(OUT/'sensitivity_zero_control_gate.csv',zeros)

def sentinels_table():
 import datetime
 assert read(OUT/'sentinels_complete.json')['passed'] and read(OUT/'sensitivity_complete.json')['cases']==101
 selection={int(r['frame_id']):r for r in rows(ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv') if r['dataset_id']=='group_c'};archive=ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip';output=[];access=[]
 with zipfile.ZipFile(archive) as z:
  for item in read(OUT/'sentinel_plan.json')['additional_visible_frames']:
   f=item['frame_id'];require('group_c','comparison',uses_annotations=True);raw=z.read(selection[f]['selected_json']);label=json.loads(raw);points=[s['points'][0] for s in label['shapes'] if s['label']=='crack_tip'];assert len(points)==1;gt=points[0];access.append(dict(frame_id=f,member=selection[f]['selected_json'],sha256=hashlib.sha256(raw).hexdigest(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),usage='after_all_native_inference_offline_comparison'));case=load_case('sentinel_'+str(f));write(case['folder']/'offline_label.json',label)
   for mode in ['joint','current']:
    r=next(r for r in brief(case['name'],'same_input_visible_sentinel',dict(frame_id=f,selection_reason=item['selection_reason'])) if r['mode']==mode and r['threshold']==10);r.pop('approximate_anchor_error');r.pop('anchor_kind');r['GT_tip']=gt;r['offline_error']=float(np.linalg.norm(np.array(r['tip'])-gt)) if r['tip'] else None
    init=[v for v in case['init'] if v['mode']==mode];winner=next(v for v in init if v['selected']=='True');other=next(v for v in case['init'] if v['mode']=='current' and v['selected']=='True');r['winner_valley']=float(winner['valley']);r['winner_newdark']=float(winner['newdark']);r['current_winner_y']=int(other['y']);r['current_winner_joint_accept']=other['accept_joint_T10']=='True';r['current_winner_newdark']=float(other['newdark']);r['winner_vs_current_y']=abs(r['y0']-int(other['y']))
    from scipy.spatial import cKDTree
    dense=[]
    for shape in label['shapes']:
     if shape['label']!='crack_path':continue
     for aa,bb in zip(shape['points'][:-1],shape['points'][1:]):
      aa=np.array(aa);bb=np.array(bb);n=max(1,int(np.ceil(np.linalg.norm(bb-aa))));dense.extend(aa+(bb-aa)*np.arange(n)[:,None]/n)
    observed=[(int(t['x']),int(t['selected_y'])) for t in trace(case['name'],mode) if t['is_observed']=='True'];dist=cKDTree(np.asarray(dense)).query(observed)[0] if dense and observed else [];r['first_observed_distance_manual_path']=float(dist[0]) if len(dist) else None;r['observed_within5_fraction']=float(np.mean(np.asarray(dist)<=5)) if len(dist) else None
    r['evidence_tags']=['MULTIFACTOR','ROI/INIT_GEOMETRY','REFERENCE_REMAP/DELTA_VETO'] if mode=='joint' and r['winner_vs_current_y']>7 else ['REFERENCE_REMAP/DELTA_VETO'] if mode=='joint' and not r['current_winner_joint_accept'] else ['TRACKING_GAP_OR_JUMP'] if r['offline_error'] is not None and r['offline_error']>10 and len(dist) and dist[0]<=5 else ['ROI/INIT_GEOMETRY','UNRESOLVED'] if r['offline_error'] is not None and r['offline_error']>10 else ['WITHIN_10_PROVISIONAL'] if r['offline_error'] is not None else ['UNRESOLVED'];r['independent_material_distortion']='UNRESOLVED';r['GT_kind']='VISIBLE_manual_LabelMe';output.append(r)
 for r in brief('D','same_BMP_golden_file_in_formal_sequence',dict(frame_id=read(OUT/'inputs.json')['frame_id'],selection_reason='golden BMP is NOT in the existing20 annotated selections',GT_kind='approximate regression anchor only',evidence_tags=['MULTIFACTOR','ROI/INIT_GEOMETRY','REFERENCE_REMAP/DELTA_VETO'])):
  if r['threshold']==10:output.append(r)
 save(OUT/'annotation_access_log.csv',access);save(OUT/'group_sentinels.csv',output)

def main():
 assert read(OUT/'primary_complete.json')['passed'] and read(OUT/'controlled_complete.json')['passed']
 cases={name:load_case(name) for name in ['A','B','C','D']+[f'CF_geometry_{g}_motion_{m}' for g in ['A','D'] for m in ['A','D']]}
 save(OUT/'abcd_runs.csv',[r for name in 'ABCD' for r in brief(name,'native_frozen')]);save(OUT/'initial_candidate_audit.csv',[r for name in 'ABCD' for r in cases[name]['init']]);save(OUT/'first_causal_divergence.csv',[r for name in 'BCD' for r in divergences(cases['A'],cases[name])]);save(OUT/'geometry_vs_reference_ablation.csv',[r for name in cases if name.startswith('CF_') for r in brief(name,'counterfactual_diagnostic_only')]);save(OUT/'controlled_first_divergence.csv',divergences(cases['CF_geometry_D_motion_A'],cases['CF_geometry_D_motion_D'])+divergences(cases['CF_geometry_A_motion_A'],cases['CF_geometry_A_motion_D']));evidence_swap(cases);independent_motion(read(OUT/'inputs.json'),cases);sensitivity_table();sentinels_table();write(OUT/'analysis_complete.json',dict(native_abcd_modes=24,counterfactual_modes=24,sensitivity_cases=101,sensitivity_modes=606,visible_sentinels=4,source_unchanged=sha(FROZEN)==SHA));print('ANALYSIS COMPLETE',flush=True)

if __name__=='__main__':main()
