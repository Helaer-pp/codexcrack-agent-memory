from common import *
import shutil
records=rows(OUT/'tests/G1_contracts.csv');real=rows(OUT/'experiments/G1_mechanism.csv');assert len(real)==80
passed=all(r['passed']=='True' for r in records[:2]) and all(any(r['dataset_id']==g and int(r['visible_centers'])>=20 and float(r['visible_travel'])>=30 and int(r['dependent_scanlines'])>=20 for r in real) for g in DEV)
write(OUT/'G1_gate.json',dict(status='PASS' if passed else 'FAIL',meaning='dependent local tracking mechanism only; no identity/accuracy acceptance',synthetic=records,real_frames=80,supported_trajectories=sum(int(r['visible_centers'])>=20 and float(r['visible_travel'])>=30 for r in real),labels_opened=0,serialization_recovery='completed raw traces and CSV retained; repaired numpy.bool_ JSON serialization only; no algorithm rerun/selection'))
dest=OUT/'g1_build';dest.mkdir(exist_ok=True)
for p in [ROOT/'research/uctt_r05g/tracker.hpp',ROOT/'research/uctt_r05g/runtime.cpp',BUILD/'Release/R05G.dll']:shutil.copy2(p,dest/p.name)
print('G1 gate',passed,'supported trajectories',read(OUT/'G1_gate.json')['supported_trajectories'])
