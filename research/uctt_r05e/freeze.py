from common import *
import platform,winreg
OUT.mkdir(parents=True,exist_ok=False)
for p in ['traces','maps','images','logs','tests','research_source_patch']:(OUT/p).mkdir()
protected={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'src/cpp/a').rglob('*') if p.is_file()}
for n in ['output/build/src/cpp/a/Release/CrackV4.dll','output/releases/A_Win64_OpenCV440/bin/CrackV4.dll','config/dataset_usage_policy.json']:
 protected[n]=sha(ROOT/n)
assert protected['output/build/src/cpp/a/Release/CrackV4.dll']=='55a0e7a79162da79e691ede9ff58229e59a56fdd1e0b1e3f609dc51128860402'
prior={}
for p in [PRE/'input_inventory.csv',R05/'active_selection_manifest.csv',R05/'human_annotations_six_groups_snapshot.zip',D/'dev_frames.jsonl',D/'val_frames.jsonl',ROOT/'research/uctt_r03/contracts.cpp',ROOT/'research/uctt_r03/state.hpp']:
 prior[str(p.relative_to(ROOT))]=sha(p)
for p in D.glob('*.json'):prior[str(p.relative_to(ROOT))]=sha(p)
inventory=filter_rows(rows(PRE/'input_inventory.csv'),'validation');assert len(inventory)==2647
save(OUT/'input_inventory_allowed.csv',inventory)
selection=filter_rows(rows(R05/'active_selection_manifest.csv'),'validation');assert len(selection)==120
save(OUT/'selected_frames.csv',selection)
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as k:cpu=winreg.QueryValueEx(k,'ProcessorNameString')[0].strip()
write(OUT/'frozen_manifest_r05e.json',dict(protected=protected,prior_inputs=prior,cpu=cpu,platform=platform.platform(),flags=3572,policy=1,terminal=1,refine=True,threads=4,policy_file=read(POLICY_PATH),annotation_use='offline comparison only',development=DEV,validation_only=VAL,excluded=['group_x']))
print('FROZEN',OUT,flush=True)
