"""Seal this completed comparison, preserving user annotations and production."""
from validate_annotations import *

def main():
 lock=json.loads((OUT/'pre_evaluation_lock.json').read_text(encoding='utf8'))
 changed=[]
 for section in ['inputs','production']:
  for name,expected in lock[section].items():
   p=Path(name)
   if not p.is_absolute():p=ROOT/p
   if sha(p)!=expected:changed.append(str(p))
 assert not changed,changed
 manifest=rows(OUT/'active_selection_manifest.csv')
 for r in manifest:
  require(r['dataset_id'],'comparison',uses_annotations=True)
  assert sha(PACKAGE/r['selected_image'])==r['source_sha256']
 complete=json.loads((OUT/'production_replay_complete.json').read_text(encoding='utf8'));assert complete['status']=='PASS' and complete['frames']==2576
 assert json.loads((OUT/'video_qa.json').read_text(encoding='utf8'))['full_decode']=='PASS'
 checks=json.loads((ROOT/'output/checks/latest.json').read_text(encoding='utf8'));assert checks['passed'] and checks['excluded_groups']==['group_x']
 shutil.copy2(ROOT/'output/checks/latest.json',OUT/'project_check_snapshot.json')
 sources=[ROOT/'AGENTS.md',ROOT/'README.md',ROOT/'docs/CURRENT_STATE.md',ROOT/'config/datasets.json',POLICY_PATH,ROOT/'src/python/crackv4/dataset_policy.py']
 sources+=list((ROOT/'research/uctt_r05_validation').glob('*.py'))+[ROOT/'research/uctt_r05_validation/README.md']
 sources+=[ROOT/f'tests/{name}.py' for name in ['check_project','check_anchor_invariance','check_invalid_current_anchor']]
 sources+=[ROOT/f'research/annotation_tools/{name}.py' for name in ['audit_annotations','launch_labelme']]
 with zipfile.ZipFile(OUT/'evaluation_source_snapshot.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sources:z.write(p,p.relative_to(ROOT).as_posix())
 write(OUT/'final_integrity.json',dict(status='PASS',locked_inputs_unchanged=len(lock['inputs']),production_files_unchanged=len(lock['production']),selected_images_unchanged=len(manifest),human_annotations_unchanged=True,group_x_images_or_annotations_used=False,validation_used_for_tuning=False,model_training=False,production_algorithm_modified=False,source_hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sources}))
 files=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='final_artifact_manifest.json')
 write(OUT/'final_artifact_manifest.json',dict(status='SEALED',files={p.relative_to(OUT).as_posix():sha(p) for p in files}))
 print('SEALED',len(files),'artifacts; all locked inputs and production files unchanged')
if __name__=='__main__':main()
