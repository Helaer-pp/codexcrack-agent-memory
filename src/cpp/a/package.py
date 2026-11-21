"""Assemble the verified native SDK without touching previous releases."""
import hashlib
import json
import shutil
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

SRC=Path(__file__).resolve().parent
ROOT=SRC.parents[2]
build=ROOT/'output/build/src/cpp/a/Release'
validation=ROOT/'output/runs/ct3_roi_tip_r01'
releases=ROOT/'output/releases'
pkg=releases/'A_Win64_OpenCV440'
def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()
def put(path,rel):
    dest=pkg/rel
    dest.parent.mkdir(exist_ok=True,parents=True)
    shutil.copyfile(path,dest)

manifest=json.loads((validation/'manifest.json').read_text(encoding='utf8'))
assert manifest['frames']==136 and len(manifest['summary'])==8
assert sha(build/'CrackV4.dll')==manifest['dll']
assert sha(build/'opencv_world440.dll')==sha(Path('D:/opencv-4.4.0/build/x64/vc15/bin/opencv_world440.dll'))
identity=json.loads((ROOT/'baseline/frozen_a/identity.json').read_text(encoding='utf8'))
for name,digest in identity['source_hashes'].items(): assert sha(ROOT/name)==digest,name
put(build/'CrackV4.dll','bin/CrackV4.dll')
put(build/'CrackV4.lib','lib/CrackV4.lib')
put(build/'opencv_world440.dll','bin/opencv_world440.dll')
put(build/'CrackV4Example.exe','bin/CrackV4Example.exe')
for name in ['CrackV4.h','CrackV4.hpp']: put(SRC/'include'/name,'include/'+name)
put(SRC/'example/main.cpp','example/main.cpp')
put(SRC/'INTEGRATION.md','集成说明.md')
put(ROOT/'third_party/opencv440/LICENSE','OpenCV-LICENSE.txt')
put(SRC/'example/SDK.cmake','CMakeLists.txt')
for name in ['per_frame.csv','summary.csv','frame_comparison.csv','pairwise.csv','manifest.json','验证报告.md']:
    put(validation/name,'verification/'+name)
entries=sorted(p for p in pkg.rglob('*') if p.is_file() and p.name!='SHA256.txt')
(pkg/'SHA256.txt').write_text('\n'.join(f'{sha(p)}  {p.relative_to(pkg).as_posix()}' for p in entries)+'\n',encoding='utf8')
with ZipFile(pkg.with_suffix('.zip'),'w',compression=ZIP_DEFLATED,compresslevel=3) as z:
    for p in sorted(pkg.rglob('*')):
        if p.is_file():z.write(p,Path(pkg.name)/p.relative_to(pkg))
with ZipFile(pkg.with_suffix('.zip')) as z:
    assert z.testzip() is None
print(pkg.with_suffix('.zip'))
