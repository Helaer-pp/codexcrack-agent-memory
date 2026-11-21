from common import *
import platform,winreg,shutil

def main():
 OUT.mkdir(parents=True,exist_ok=False)
 for n in ['logs','experiments','traces','tests','galleries/images','galleries/local_frames','seeds','source_snapshot']:(OUT/n).mkdir(parents=True,exist_ok=True)
 protected={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in (ROOT/'src/cpp/a').rglob('*') if p.is_file()}
 for n in ['config/project.json','config/dataset_usage_policy.json','config/datasets.json','output/build/src/cpp/a/Release/CrackV4.dll','output/releases/A_Win64_OpenCV440/bin/CrackV4.dll']:
  protected[n]=sha(ROOT/n)
 for n in ['research/uctt_r05f/current.hpp','research/uctt_r05f/runtime.cpp','output/build/uctt_r05f/Release/R05F.dll']:
  protected[n]=sha(ROOT/n)
 for p in [F/'artifact_manifest.json',F/'baseline_manifest.json',F/'baseline_scope.md',F/'A0_frames.jsonl',F/'traces/B0_frames.jsonl.gz',D/'artifact_manifest.json',LABELS]:
  if p.exists():protected[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
 assert protected['output/build/src/cpp/a/Release/CrackV4.dll'].startswith('55a0')
 assert protected['output/releases/A_Win64_OpenCV440/bin/CrackV4.dll'].startswith('1c742')
 inventory=filter_rows(rows(F/'input_inventory_allowed.csv'),'development');selection=filter_rows(rows(F/'selected_frames.csv'),'development');assert len(inventory)==1565 and len(selection)==80
 save(OUT/'input_inventory.csv',inventory);save(OUT/'selection.csv',selection)
 with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as k:cpu=winreg.QueryValueEx(k,'ProcessorNameString')[0]
 write(OUT/'source_hash_before.json',protected)
 write(OUT/'baseline_manifest.json',dict(protected=protected,baseline_scope='R02/R05D/R05E/R05F research A55a0; historical released1c742 is distinct by design',historical_provenance=['output/runs/phase1_audit_decoupling_20261110_r01/dependency_audit.md:25','output/runs/phase1_acceptance_r02/ab_regression_report.md:3'],cpu=cpu,platform=platform.platform(),native_opencv='4.4.0',threads=4,compiler='MSVC v142 /O2 /fp:precise /utf-8 x64',git_commit=None,git_reason='no Git metadata',labels_use='offline evaluation/diagnosis/display ONLY',validation_access='BLOCKED before G0-G3 freeze',excluded_image_access=0))
 variants=[dict(name='G1_GREEDY',beam=1,gap=True,weak=True,history=False,scope='first compile and selected real mechanism gate'),dict(name='E1_BEAM',beam=4,gap=True,weak=True,history=True,scope='full1565 automatic-prefix'),dict(name='E1_GREEDY',beam=1,gap=True,weak=True,history=True,scope='full1565 same origin seeds and equal sampling budget'),dict(name='E1_NO_GAP',beam=4,gap=False,weak=True,history=True,scope='full1565 gap-only ablation'),dict(name='E1_STRONG',beam=4,gap=True,weak=False,history=True,scope='full1565 strong-only observation ablation'),dict(name='E1_NO_HISTORY',beam=4,gap=True,weak=True,history=False,scope='full1565; history-effect NOT_EXERCISED if safety gate denies writes'),dict(name='E0_GREEDY',beam=1,gap=True,weak=True,history=False,scope='80 selected; isolated seeds; not autonomous'),dict(name='E0_BEAM',beam=4,gap=True,weak=True,history=False,scope='80 selected; same seeds; not autonomous'),dict(name='E0_CAPACITY_GREEDY',beam=1,gap=True,weak=True,history=False,scope='80 selected; diagnostic high cap; not online setting'),dict(name='E0_CAPACITY_BEAM',beam=4,gap=True,weak=True,history=False,scope='80 selected; same high cap; no online claim')]
 write(OUT/'experiments/predeclared_variants.json',dict(variants=variants,no_parameter_search=True,reference='NOT_IMPLEMENTED optional only after G1/G2 evidence',seed_policy='independent current image short start or legal P1P2 origin prior; never LabelMe path/tip',history_safety='no trusted write until independent identity and first-lock safety passed; proposal output separately audited'))
 print('G0 freeze prepared',len(protected),len(inventory),len(selection),flush=True)
if __name__=='__main__':main()
