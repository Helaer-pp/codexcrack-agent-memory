from common import *
MODE='B2' if (OUT/'B2_dev_complete.json').exists() else 'B1'
assert read(OUT/f'{MODE}_dev_complete.json')['status']=='PASS'
rule_files=['common.py','baseline.py','replay.py','compare.py','evidence.hpp','evidence_exports.inc','generate.py','CMakeLists.txt']
write(OUT/'validation_freeze.json',dict(mode=MODE,development_gate=read(OUT/f'{MODE}_gate.json'),rule_sources={f'research/uctt_r05e/{n}':sha(ROOT/'research/uctt_r05e'/n) for n in rule_files},generated_sources={str(p.relative_to(ROOT)):sha(p) for p in GEN.glob('*') if p.is_file()},dlls={str(p.relative_to(ROOT)):sha(p) for p in [BUILD/'Release/B1.dll',BUILD/'Release/B2.dll']},validation_groups=VAL,validation_frames=1082,validation_selections=40,labels='comparison only after snapshots',no_adjustments_from_validation=True,b3_b4='BLOCKED unless all prior gates pass; no branch is enabled by this validation'))
print('VALIDATION RULES FROZEN',MODE)
