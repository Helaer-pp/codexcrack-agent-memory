from common import *
import shutil
target=OUT/'aborted_debug_compression_attempt';target.mkdir(exist_ok=False)
paths=[OUT/'B0_lock.json',OUT/'logs/B0_replay.log',*sorted((OUT/'traces').glob('B0*'))]
for p in paths:
 assert p.resolve().is_relative_to(OUT.resolve()) and target.resolve().is_relative_to(OUT.resolve())
 shutil.move(str(p),str(target/p.name))
write(target/'reason.json',dict(status='ABORTED_NOT_EVALUATED',reason='gzip level9 debug serialization too slow; switched to level1 without changing native algorithm, parameters or comparator; full chronological replay restarts from frame1',native_sha=sha(BUILD/'Release/R05F.dll')))
print('archived',len(paths),'partial outputs')
