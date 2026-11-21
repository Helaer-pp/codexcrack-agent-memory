"""New output only, exact-source ABCD first, then predeclared counterfactual/sensitivity audits."""
from core import *
import re,struct,platform,scipy,matplotlib
from PIL import Image

def prepare():
 require('group_c','validation');assert not OUT.exists(),'Use a new output path for a new run';OUT.mkdir(parents=True);assert sha(FROZEN)==SHA
 manifest=[r for r in rows(OLD/'inputs/validation_manifest.csv') if r['group']=='group_c'];target=next(r for r in manifest if Path(r['current']).name=='3 (175).bmp');frame=int(target['frame_id']);entry=next(r for r in rows(ROOT/'data/inputs/six_groups_manifest.csv') if r['dataset_alias']=='group_c' and int(r['frame_id'])==frame-1);assert entry['input_image']==target['current']
 anchor=ROOT/entry['anchor_file'];raw=anchor.read_bytes();text=raw.decode('gb18030');pointmap={}
 for line in text.splitlines():
  values=re.findall(r'[-+]?\d+(?:\.\d+)?',line)
  if len(values)==5:pointmap[int(values[0])]=[list(map(float,values[1:3])),list(map(float,values[3:5]))]
 rp=pointmap[0];cp=pointmap[frame-1];pp=lambda suffix:[[float(target[f'p{i}_{suffix}_{axis}']) for axis in ['x','y']] for i in [1,2]];assert rp==pp('ref') and cp==pp('cur') and cp==json.loads(entry['points'])
 gold=read(OLD/'regression/metadata.json');R_G=gold['reference_points'];C_G=gold['current_points'];ref=stage(target['reference'],'reference.bmp');cur=stage(target['current'],'current.bmp');identity=[]
 for kind,source,staged,fid in [('reference',target['reference'],ref,1),('current',target['current'],cur,frame)]:
  b=Path(source).read_bytes();im=cv2.imdecode(np.frombuffer(b,np.uint8),cv2.IMREAD_GRAYSCALE);imfile=cv2.imread(str(staged),cv2.IMREAD_GRAYSCALE);pil=Image.open(source);pilgray=np.asarray(pil.convert('L'));assert np.array_equal(im,imfile);oldhash=read(OLD/'regression/regression_checks.json')[kind+'_sha256'];assert sha(source)==oldhash
  identity.append(dict(kind=kind,original_path=source,staged_path=str(staged),frame_id=fid,tracking_num=fid-1,filename=Path(source).name,encoding=pil.format,bmp_header_width=struct.unpack_from('<i',b,18)[0],bmp_header_height=struct.unpack_from('<i',b,22)[0],bits_per_pixel=struct.unpack_from('<H',b,28)[0],compression=struct.unpack_from('<I',b,30)[0],shape=list(im.shape),dtype=str(im.dtype),exif_orientation=pil.getexif().get(274),file_sha256=sha(source),stage_sha256=sha(staged),ndarray_sha256=array_sha(im),imread_ascii_sha256=array_sha(imfile),pil_L_sha256=array_sha(pilgray),cv_imdecode_equals_ascii_imread=True,pil_equal=bool(np.array_equal(im,pilgray)),matches_previous_golden_bytes=True,decoder='cv2.IMREAD_GRAYSCALE; ASCII imread same as immutable V1'))
 save(OUT/'input_provenance.csv',identity);pconfig=dict(reference=str(ref),current=str(cur),reference_original=target['reference'],current_original=target['current'],frame_id=frame,reference_frame_id=1,tracking_num=frame-1,tracking_source=str(anchor),tracking_sha256=sha(anchor),points=dict(R_G=R_G,C_G=C_G,R_S=rp,C_S=cp),source_sha256=sha(FROZEN));write(OUT/'inputs.json',pconfig)
 geometry=[]
 for name,pts in pconfig['points'].items():geometry.append(dict(pair=name,p1=pts[0],p2=pts[1],dy_span=pts[1][1]-pts[0][1],midpoint=np.mean(pts,axis=0).tolist(),xright=max(x[0] for x in pts)))
 save(OUT/'point_geometry.csv',geometry);save(OUT/'point_deltas.csv',[dict(coordinates=kind,point=i+1,golden=g,sequence=s,dx=s[0]-g[0],dy=s[1]-g[1]) for kind in ['R','C'] for i,(g,s) in enumerate(zip(pconfig['points'][kind+'_G'],pconfig['points'][kind+'_S']))])
 sources=[FROZEN,ROOT/'group_c_Same_BMP_V1_Root_Cause_Agent_Prompt.md',anchor,ROOT/'data/inputs/six_groups_manifest.csv',OLD/'inputs/validation_manifest.csv',ROOT/'research/p1p2_grayref_v1/python_replay.py',ROOT/'research/p1p2_grayref_v1/validation.py',OLD/'artifact_manifest.json']
 write(OUT/'run_identity.json',dict(task='Exposed group_c same-BMP frozen forensic audit; not training/tuning/independent validation',source_sha256=sha(FROZEN),files={str(p):sha(p) for p in sources},versions=dict(python=sys.version,opencv=cv2.__version__,numpy=np.__version__,scipy=scipy.__version__,matplotlib=matplotlib.__version__,platform=platform.platform()),golden_frame_mapping=frame,point_source_verified=True,annotations_read=0,scope_note='Generated diagnostics inside project output per active project routing; no old run overwritten',protected_production=read(OLD/'preflight_status.json')['protected_production']))
 # Predeclare exact input perturbations before running outcomes. No GT/score-based refinement.
 cases=[]
 for base,r,c in [('A',R_G,C_G),('D',rp,cp)]:
  for scope,values in [('both',[-5,-3,-1,0,1,3,5]),('current',list(range(-5,6))),('reference',list(range(-5,6)))]:
   for dy in values:
    rr=copy.deepcopy(r);cc=copy.deepcopy(c)
    for pts in ([rr,cc] if scope=='both' else [cc] if scope=='current' else [rr]):
     for point in pts:point[1]+=dy
    cases.append(dict(case=f'{base}_{scope}_dy_{dy:+d}',base=base,scope=scope,dy=dy,reference_points=rr,current_points=cc))
  # Explicit single-point vertical offsets, four point identities x four fixed offsets.
  for where in ['reference','current']:
   for i in [0,1]:
    for dy in [-5,-2,2,5]:
     rr=copy.deepcopy(r);cc=copy.deepcopy(c);(rr if where=='reference' else cc)[i][1]+=dy;cases.append(dict(case=f'{base}_{where}_p{i+1}_dy_{dy:+d}',base=base,scope=where+f'_p{i+1}',dy=dy,reference_points=rr,current_points=cc))
 for i in range(11):
  t=i/10;cases.append(dict(case=f'AD_interpolation_{i:02d}',base='A',scope='four_point_linear_interpolation',t=t,reference_points=((1-t)*np.array(R_G)+t*np.array(rp)).tolist(),current_points=((1-t)*np.array(C_G)+t*np.array(cp)).tolist()))
 write(OUT/'sensitivity_plan.json',dict(cases=cases,parameter_selection=False,single_point_axis='y; x unchanged',synthetic_input_sensitivity_not_tracking_noise=True,predeclared_before_abcd=True))
 # Select representative frames from ALREADY EXPOSED fixed T10 report, not GT-guided inference.
 old=[r for r in rows(OLD/'tables/all_results_validation.csv') if r['group']=='group_c' and r['threshold']=='10' and r['visibility']=='VISIBLE'];j={int(r['frame_id']):r for r in old if r['mode']=='joint'};c={int(r['frame_id']):r for r in old if r['mode']=='current'};used={frame};selected=[]
 predicates=[('joint_current_disagree',lambda f:c[f]['error']!='' and float(c[f]['error'])<=10 and (j[f]['error']=='' or float(j[f]['error'])>10)),('joint_NO_TIP',lambda f:j[f]['coverage']=='False'),('joint_far_error',lambda f:j[f]['error']!='' and float(j[f]['error'])>100),('additional_visible_control',lambda f:True)]
 for why,pred in predicates:
  f=next(f for f in sorted(j) if f not in used and pred(f));used.add(f);selected.append(dict(frame_id=f,selection_reason=why))
 write(OUT/'sentinel_plan.json',dict(golden_frame=frame,golden_is_in_20_labeled_selection=frame in j,additional_visible_frames=selected,selection_rule='Four distinct already-exposed visible report records; no parameter changes'))
 print('IDENTITY GATE PASS',frame,len(cases),'predeclared sensitivities',flush=True)
 return pconfig

def primary():
 config=prepare();ref=Path(config['reference']);cur=Path(config['current']);p=config['points'];checks=[]
 ncc=plain_cli('NCC_recheck',ref,cur,p['R_G'],None);assert read(ncc/'metadata.json')['current_points']==p['C_G'];checks.append(dict(test='NCC_current_points',passed=True,details=read(ncc/'metadata.json')['point_translations']))
 for name,rkey,ckey in [('A','R_G','C_G'),('B','R_G','C_S'),('C','R_S','C_G'),('D','R_S','C_S')]:
  plain=plain_cli(name+'_plain',ref,cur,p[rkey],p[ckey]);observed=execute(name,ref,cur,p[rkey],p[ckey],detailed=True);compare=compare_outputs(plain,observed);checks.append(dict(test=name+'_observer_vs_unobserved_CLI',**compare));assert compare['passed']
  if name in ['A','D']:
   previous=OLD/'regression' if name=='A' else OLD/'py_runs/group_c'/str(config['frame_id']);compare=compare_outputs(previous,observed);checks.append(dict(test=name+'_previous_exact_replay',**compare));assert compare['passed']
 save(OUT/'native_replay_gate.csv',checks);write(OUT/'primary_complete.json',dict(passed=True,source_unchanged=sha(FROZEN)==SHA,additional_annotation_access=0));print('PRIMARY GATE PASS',flush=True)

def controlled():
 assert read(OUT/'primary_complete.json')['passed'];config=read(OUT/'inputs.json');p=config['points'];ref=Path(config['reference']);cur=Path(config['current']);checks=[]
 for geom,gr,gc in [('A','R_G','C_G'),('D','R_S','C_S')]:
  for motion,mr,mc in [('A','R_G','C_G'),('D','R_S','C_S')]:
   name='CF_geometry_'+geom+'_motion_'+motion;folder=execute(name,ref,cur,p[gr],p[gc],detailed=True,donor=(p[mr],p[mc]))
   if geom==motion:
    comp=compare_outputs(OUT/'runs'/geom,folder);assert comp['passed']
    with np.load(folder/'arrays.npz') as a,np.load(OUT/'runs'/geom/'arrays.npz') as b:arr={key:bool(np.array_equal(a[key],b[key])) for key in ARRAYS}
    assert all(arr.values());checks.append(dict(test=name+'_pure_control',**comp,arrays_exact=arr))
 save(OUT/'counterfactual_identity_gate.csv',checks);write(OUT/'controlled_complete.json',dict(passed=True,diagnostic_only=True));print('CONTROLLED GATE PASS',flush=True)

def sensitivity():
 config=read(OUT/'inputs.json');ref=Path(config['reference']);cur=Path(config['current']);plan=read(OUT/'sensitivity_plan.json');assert read(OUT/'controlled_complete.json')['passed']
 for i,c in enumerate(plan['cases']):
  execute('sensitivity/'+c['case'],ref,cur,c['reference_points'],c['current_points'])
  if (i+1)%10==0:print('SENSITIVITY',i+1,'/',len(plan['cases']),flush=True)
 write(OUT/'sensitivity_complete.json',dict(cases=len(plan['cases']),all_native=True,gt_in_inference=False))

def sentinels():
 config=read(OUT/'inputs.json');manifest={int(r['frame_id']):r for r in rows(OLD/'inputs/validation_manifest.csv') if r['group']=='group_c'};checks=[]
 for c in read(OUT/'sentinel_plan.json')['additional_visible_frames']:
  f=c['frame_id'];r=manifest[f];cur=stage(r['current'],f'current_{f}.bmp');points=lambda kind:[[float(r[f'p{i}_{kind}_{axis}']) for axis in ['x','y']] for i in [1,2]];folder=execute('sentinel_'+str(f),Path(config['reference']),cur,points('ref'),points('cur'),detailed=True);comp=compare_outputs(OLD/'py_runs/group_c'/str(f),folder);assert comp['passed'];checks.append(dict(frame_id=f,selection_reason=c['selection_reason'],**comp))
 save(OUT/'sentinel_replay_gate.csv',checks);write(OUT/'sentinels_complete.json',dict(frames=len(checks),passed=True,labels_not_read=True))

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['primary','controlled','sensitivity','sentinels']);a=parser.parse_args();globals()[a.mode]()
