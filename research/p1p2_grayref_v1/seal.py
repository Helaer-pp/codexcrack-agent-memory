"""Seal completed evidence; never changes detector outputs, labels, or original datasets."""
from common import *
import shutil,zipfile,difflib,datetime,re
from validation import verify_lock

def main():
 assert not (OUT/'final_integrity.json').exists(),'Already sealed'
 report=read(OUT/'report_complete.json');media=read(OUT/'media_complete.json');assert report['frames']==2647 and media['frames']==2647 and media['cards']==120
 assert sha(FROZEN)==EXPECTED_SHA;verify_lock(read(OUT/'validation_lock.json'))
 preserved=read(OUT/'validation_io_amendment.json')['preserved_outputs'];assert all(sha(OUT/p)==v for p,v in preserved.items())
 for g in DEV+VAL:
  complete=read(OUT/f'frame_comparisons_complete_{g}.json');assert complete['frames']==len(list((OUT/'galleries/comparison_frames'/g).glob('*.jpg')))
  assert read(OUT/f'media_complete_{g}.json')['full_decode_pass']
 # Check local gallery targets before sealing. Dynamic full-sequence targets are counted above.
 missing=[]
 for file in (OUT/'galleries').glob('*.html'):
  for link in re.findall(r'(?:href|src)="([^"#]+)"',file.read_text(encoding='utf8')):
   if '://' not in link and not (file.parent/link).exists():missing.append(str(file)+': '+link)
 assert not missing,missing
 old=ROOT/'output/runs/uctt_r05h_20261112_r01';old_manifest=read(old/'artifact_manifest.json');old_changed=[]
 for name,record in old_manifest['files'].items():
  p=(old/name).resolve();assert p.is_relative_to(old.resolve())
  if not p.exists() or sha(p)!=record['sha256']:old_changed.append(name)
 assert not old_changed,old_changed
 print('Protected R05H verified',len(old_manifest['files']),flush=True)
 source=ROOT/'research/p1p2_grayref_v1';snap=OUT/'source_snapshot/research';snap.mkdir(parents=True,exist_ok=True);hashes={};patch=[]
 for p in sorted(source.iterdir()):
  if not p.is_file():continue
  target=snap/p.name;shutil.copy2(p,target);hashes[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p);patch.extend(difflib.unified_diff([],p.read_text(encoding='utf8').splitlines(True),fromfile='/dev/null',tofile=str(p.relative_to(ROOT)).replace('\\','/')))
 write(OUT/'new_source_manifest.json',hashes);(OUT/'implementation_additions.patch').write_text(''.join(patch),encoding='utf8')
 sdk=OUT/'sdk';(sdk/'bin').mkdir(parents=True,exist_ok=True);(sdk/'include').mkdir(exist_ok=True)
 for name in ['P1P2GrayRefV1.dll','P1P2GrayRefV1.lib','opencv_world440.dll']:shutil.copy2(BUILD/'Release'/name,sdk/'bin'/name)
 for p in [source/'P1P2GrayRefV1.h',ROOT/'src/cpp/a/include/CrackV4.h']:shutil.copy2(p,sdk/'include'/p.name)
 shutil.copy2(source/'README.md',sdk/'README.md');shutil.copy2(OUT/'build_and_reproduce.md',sdk/'build_and_reproduce.md')
 with zipfile.ZipFile(OUT/'P1P2GrayRefV1_Research_SDK.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sdk.rglob('*'):
   if p.is_file():z.write(p,str(p.relative_to(sdk)))
 acceptance=[('SOURCE_IDENTITY','PASS','Task SHA exact; immutable source_diff empty'),('GOLDEN_SIX_MODES','PASS','Full original six summary rows equal'),('FULL_DEVELOPMENT','PASS','1565 frames;9390 modes'),('DEVELOPMENT_CPP_PARITY','PASS','9390 endpoints/column decisions exact;640 arrays exact'),('LOCKED_VALIDATION_EXECUTED','PASS','1082 frames;6492 modes;metadata-only amendment preserved'),('VALIDATION_CPP_STRICT_PARITY','FAIL','15 current endpoints differ;126 traces;max209.02px'),('CROSS_GROUP_ACCURACY','FAIL','jointT10 development12/76 allCT3;validation5/35'),('PRODUCTION_CONFIRMATION','NOT_IMPLEMENTED','Provisional only;formal0 not safety success'),('ROI_APPLICABILITY','FAIL','CT3 six GT tips outside fixed ROI'),('NEGATIVE_FPR','NOT_MEASURABLE','No NO_VISIBLE_CRACK labels'),('PERFORMANCE_50MS','FAIL','Native six-mode P95 CT2/group_h/group_c/three-point-bend exceed50ms on7950X'),('MEDIA','PASS','6 fully decoded videos;2647 three-panel comparisons;120 detailed cards'),('BASELINE_AND_HISTORY','PASS','Production protected files and R05H sealed files unchanged'),('V2','NOT_IMPLEMENTED','Suggestions only;no V1 rule change')]
 save(OUT/'acceptance_matrix.csv',[dict(requirement=k,status=s,evidence=e) for k,s,e in acceptance])
 final=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_source_sha256=sha(FROZEN),dll_sha256=sha(BUILD/'Release/P1P2GrayRefV1.dll'),development_frames=1565,validation_frames=1082,mode_results_each_implementation=15882,exact_cpp_tips=report['exact_tips'],selected_arrays_exact=report['exact_arrays'],strict_global_parity=False,accuracy_pass=False,production_replacement=False,excluded_groups_read=[],annotations_training=False,annotation_counts=dict(development_visible=76,development_uncertain=4,validation_visible=35,validation_uncertain=5),preserved_first_python_outputs=len(preserved),metadata_amendment_documented=True,protected_production=report['protected_files_unchanged'],previous_R05H_files_checked=len(old_manifest['files']),previous_R05H_changed=old_changed,media=media,source_manifest_sha256=sha(OUT/'new_source_manifest.json'),sdk_sha256=sha(OUT/'P1P2GrayRefV1_Research_SDK.zip'),decision='KEEP_A_RESEARCH_DELIVERED_WITH_ACCURACY_AND_VALIDATION_PARITY_FAILURES')
 write(OUT/'final_integrity.json',final)
 manifest={}
 for p in sorted(OUT.rglob('*')):
  if p.is_file() and p.name not in ['artifact_manifest.json','seal.log'] and 'io_cache' not in p.relative_to(OUT).parts:
   manifest[str(p.relative_to(OUT)).replace('\\','/')]=dict(bytes=p.stat().st_size,sha256=sha(p))
 write(OUT/'artifact_manifest.json',dict(files=manifest,count=len(manifest),excludes=['artifact_manifest.json itself','seal.log open while hashing','io_cache replaceable byte copies'],source_root=str(source)));print('SEALED',len(manifest),'files',flush=True)
if __name__=='__main__':main()
