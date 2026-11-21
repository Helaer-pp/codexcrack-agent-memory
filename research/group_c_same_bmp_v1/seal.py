"""Read-only integrity verification, source snapshot and evidence manifest."""
from core import *
import datetime,shutil,re,concurrent.futures
from PIL import Image

def main():
 identity=read(OUT/'run_identity.json');assert sha(FROZEN)==SHA
 for path,digest in identity['files'].items():assert sha(path)==digest,path
 for path,digest in identity['protected_production'].items():assert sha(ROOT/path)==digest,path
 for stage in ['primary','controlled','sensitivity','sentinels','analysis','controls_audit','visualization','report']:
  assert (OUT/f'{stage}_complete.json').is_file(),stage
 oldfiles=read(OLD/'artifact_manifest.json')['files']
 def verify_old(item):
  name,entry=item;p=OLD/name
  return name,p.is_file() and p.stat().st_size==entry['bytes'] and sha(p)==entry['sha256']
 mismatches=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for i,(name,ok) in enumerate(pool.map(verify_old,oldfiles.items()),1):
   if not ok:mismatches.append(name)
   if i%10000==0:print('OLD EVIDENCE VERIFIED',i,flush=True)
 assert not mismatches,mismatches
 config=read(OUT/'inputs.json');manifest={int(r['frame_id']):r for r in rows(OLD/'inputs/validation_manifest.csv') if r['group']=='group_c'}
 images=[]
 pairs=[(1,config['reference_original'],config['reference']),(237,config['current_original'],config['current'])]
 pairs += [(r['frame_id'],manifest[r['frame_id']]['current'],str(OUT/'staging'/f"current_{r['frame_id']}.bmp")) for r in read(OUT/'sentinel_plan.json')['additional_visible_frames']]
 for fid,original,staged in pairs:
  original_hash=sha(original);assert original_hash==sha(staged)
  a=cv2.imdecode(np.frombuffer(Path(original).read_bytes(),np.uint8),0);b=cv2.imread(staged,0)
  assert a is not None and np.array_equal(a,b)
  images.append(dict(frame_id=fid,original=original,staged=staged,file_sha256=original_hash,array_sha256=array_sha(a),shape=list(a.shape),dtype=str(a.dtype),equal=True))
 save(OUT/'final_image_identity.csv',images)
 gates={'native_replay_gate':'passed','counterfactual_identity_gate':'passed','column_observer_gate':'matches_original_trace','observer_overlay_gate':'decoded_overlay_pixels_equal','counterfactual_motion_field_gate':'common_global_pixels_exact','current_evidence_common_ROI_gate':'exact','sentinel_replay_gate':'passed'}
 for name,key in gates.items():assert all(r[key]=='True' for r in rows(OUT/f'{name}.csv')),name
 # Zero controls have their own trace/summary assertion when generated.
 zeros=rows(OUT/'sensitivity_zero_control_gate.csv');assert zeros and all(r['passed']=='True' for r in zeros)
 required=['input_provenance','abcd_runs','initial_candidate_audit','first_causal_divergence','geometry_vs_reference_ablation','point_sensitivity','group_sentinels']
 for name in required:assert rows(OUT/f'{name}.csv'),name
 assert len(rows(OUT/'abcd_runs.csv'))==24 and len(rows(OUT/'point_sensitivity.csv'))==606
 observers=[read(p) for p in (OUT/'runs').rglob('observer.json')];clis=[read(p) for p in (OUT/'runs').rglob('cli_identity.json')]
 assert len(observers)==113 and len(clis)==5
 assert all(r['status']=='OK' and r['source_sha256']==SHA for r in observers)
 assert all(r['returncode']==0 and r['source_sha256']==SHA for r in clis)
 assert sum(r['counterfactual'] for r in observers)==4
 source=Path(__file__).resolve().parent;snapshot=OUT/'scripts';snapshot.mkdir(exist_ok=True)
 for p in source.iterdir():
  if p.suffix in ['.py','.ps1','.js','.md']:
   if p.suffix=='.py':compile(p.read_text(encoding='utf8'),str(p),'exec')
   dest=snapshot/p.name
   if p.resolve()!=dest.resolve():shutil.copyfile(p,dest)
 shutil.copyfile(FROZEN,snapshot/'paired_p1p2_roi_V1_FROZEN.py')
 (OUT/'original_source_diff.patch').write_text('',encoding='utf8')
 assert sha(snapshot/'paired_p1p2_roi_V1_FROZEN.py')==SHA
 node=shutil.which('node');assert node,'Node required for exported viewer JS validation'
 result=subprocess.run([node,str(source/'validate_viewer.js'),str(OUT/'trace_audit_A_B_C_D.html')],capture_output=True,text=True,check=True)
 viewer=json.loads(result.stdout);assert viewer['passed'];write(OUT/'viewer_qa.json',viewer)
 html=(OUT/'trace_audit_A_B_C_D.html').read_text(encoding='utf8')
 for link in re.findall(r'(?:href|src)="([^"]+)"',html):
  if not re.match(r'\w+:',link):assert (OUT/link).is_file(),link
 pngs=list((OUT/'figures').glob('*.png'));assert len(pngs)==11
 for p in pngs:
  with Image.open(p) as im:im.verify()
 video=read(OUT/'video_qa.json');assert video['full_decode_pass'] and video['sha256']==sha(OUT/'root_cause_walkthrough.mp4')
 probe=subprocess.run([str(ROOT/'third_party/ffmpeg/ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(OUT/'root_cause_walkthrough.mp4')],capture_output=True,text=True,check=True)
 probe=json.loads(probe.stdout);assert float(probe['format']['duration'])==54 and int(probe['streams'][0]['nb_frames'])==648
 write(OUT/'video_probe.json',probe)
 tools=[Path(sys.executable),Path(node),ROOT/'third_party/ffmpeg/ffmpeg.exe',ROOT/'third_party/ffmpeg/ffprobe.exe']
 identity['tool_sha256']={str(p):sha(p) for p in tools};identity['script_sha256']={p.name:sha(p) for p in snapshot.iterdir() if p.is_file()}
 identity['annotations_read_at_start']=identity.pop('annotations_read',identity.get('annotations_read_at_start',0))
 identity['annotation_members_read_after_inference']=len(rows(OUT/'annotation_access_log.csv'))
 identity['sealed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();write(OUT/'run_identity.json',identity)
 integrity=dict(passed=True,source_sha256=sha(FROZEN),frozen_source_unchanged=True,old_evidence_files_verified=len(oldfiles),old_evidence_mismatches=mismatches,protected_production_files_unchanged=len(identity['protected_production']),native_python_main_runs=114,diagnostic_counterfactual_main_runs=4,auxiliary_cpp_cases=4,abcd_modes=24,sensitivity_cases=101,sensitivity_modes=606,additional_visible_frames=4,figures=11,viewer_logic_passed=True,video_seconds=54,video_frames=648,no_v2=True,no_parameter_selection=True,physical_registration_truth='UNRESOLVED',original_point_semantics='UNRESOLVED',scope='Evidence integrity is PASS; detector accuracy and physical causal truth are not implied',sealed_utc=identity['sealed_utc'])
 write(OUT/'final_integrity.json',integrity)
 files={}
 for p in sorted(OUT.rglob('*')):
  if p.is_file() and p.name not in ['artifact_manifest.json','seal.log']:
   files[p.relative_to(OUT).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
 write(OUT/'artifact_manifest.json',dict(files=files,excluded=['artifact_manifest.json (self)','seal.log (optional open console log)'],sealed_utc=identity['sealed_utc']))
 print('SEALED',len(files),'files; old evidence',len(oldfiles),'unchanged',flush=True)

if __name__=='__main__':main()
