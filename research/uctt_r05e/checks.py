from common import *
import ast,subprocess,numpy as np
from compare import original,local
from crackv4.dataset_policy import allowed
def main():
 checks=[]
 def check(name,passed,scope):checks.append(dict(test=name,status='PASS' if passed else 'FAIL',scope=scope));assert passed,name
 for turn in range(4):
  for roi in [[0,0,121,85],[13,27,121,85],[480,900,242,170],[0,350,40,32]]:
   t=dict(roi=roi,turn=turn);p=np.array([[roi[0],roi[1]],[roi[0]+roi[2]-1,roi[1]+roi[3]-1],[roi[0]+.17*roi[2],roi[1]+.63*roi[3]]])
   check(f'coordinate_roundtrip_turn{turn}_{roi}',np.max(np.abs(original(local(p,t),t)-p))<1e-10,'quadrants, border crop, resolution; original pixel coordinates')
 check('excluded_group_all_uses',not allowed('group_x','validation') and not allowed('group_x','development'),'policy before image/label opens')
 check('validation_groups_not_development',all(not allowed(g,'development') for g in VAL),'group-level policy')
 check('human_annotations_not_training',all(not allowed(g,'model_training',uses_annotations=True) for g in DEV+VAL),'no fitting/search/training')
 native='\n'.join((ROOT/'research/uctt_r05e'/n).read_text(encoding='utf8') for n in ['evidence.hpp','evidence_exports.inc'])
 check('native_no_sample_identity',not any(s in native.lower() for s in ['crack_tip','human_tip','dataset_id','group_a','group_h','ct2','ct3','group_c']),'native signatures and rules source inspection')
 runner=(ROOT/'research/uctt_r05e/replay.py').read_text(encoding='utf8')
 check('raw_runner_no_annotation_reader',not any(s in runner for s in ['ZipFile','selected_json','human_tip','crack_tip']),'offline comparator separate from runtime')
 for p in (ROOT/'research/uctt_r05e').glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
 check('python_syntax',True,'all research Python modules')
 seed=ROOT/'output/runs/phase1_r03_dynamic_roi_20261110_r01/fault_seed.txt';exe=BUILD/'Release/R03Original.exe'
 result=subprocess.run([str(exe),str(seed)],capture_output=True,text=True);(OUT/'tests/r03_original.csv').write_text(result.stdout,encoding='utf8');assert result.returncode==2
 original_rows=rows(ROOT/'output/runs/phase1_r03_dynamic_roi_20261110_r01/fault_injection_results.csv');current=rows(OUT/'tests/r03_original.csv')
 check('unchanged_r03_fixture_reproduced',current==original_rows,'16 original cases; 15 pass and coherent_wrong_first_lock fails; reproduction PASS is not safety PASS')
 write(OUT/'tests/r03_provenance.json',dict(seed_sha=sha(seed),source_sha=sha(ROOT/'research/uctt_r03/contracts.cpp'),state_sha=sha(ROOT/'research/uctt_r03/state.hpp'),exe_sha=sha(exe),provenance=read(seed.with_name('fault_seed_provenance.json')),returncode=result.returncode,safety_status='FAIL'))
 result=subprocess.run([str(BUILD/'Release/EvidenceContracts.exe')],capture_output=True,text=True);(OUT/'tests/native_evidence.csv').write_text(result.stdout,encoding='utf8');check('native_evidence_properties',result.returncode==0,'10 C++ constructed channel/candidate properties, no physical GT')
 save(OUT/'tests/contracts.csv',checks)
 print('CHECKS',len(checks),'PASS; R03 safety remains FAIL',flush=True)
if __name__=='__main__':main()
