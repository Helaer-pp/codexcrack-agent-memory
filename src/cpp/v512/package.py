"""Assemble the original ABI SDK using the verified V5.12 build."""
import shutil
import sys
import re
from zipfile import ZipFile, ZIP_DEFLATED
from .verify_abi import BUILD, DEST, batch

root=batch.ROOT
sdk=root/'output/releases/V5_12_CrackV4_Win64_OpenCV440'
src=root/'baseline/frozen_a/src'
def copy(path,rel):
    target=sdk/rel
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,target)
def prepare():
    assert batch.sha(BUILD/'CrackV4.dll')==batch.read(DEST/'freeze.json')['dll']
    for p in ('CrackV4.h','CrackV4.hpp','CrackV4_v2.h','CrackV4_experiments.h'):copy(src/p,'include/'+p)
    for p in ('CrackV4.dll','opencv_world440.dll'):copy(BUILD/p,'bin/'+p)
    copy(BUILD/'CrackV4.lib','lib/CrackV4.lib')
    copy(root/'third_party/opencv440/LICENSE','OpenCV-LICENSE.txt')
    copy(src/'example.cpp','example/main.cpp')
    copy(root/'src/cpp/a/example/SDK.cmake','CMakeLists.txt')
    copy(root/'src/cpp/v512/集成说明.md','集成说明.md')
    copy(batch.POLICY,'profiles/group_c_bright.json')
def finish():
    prepare()
    copy(root/'output/build/v512_sdk_consumer/Release/CrackV4Example.exe','bin/CrackV4Example.exe')
    for p in ('abi_exports.json','existing_client.json','freeze.json','REPORT.md','group_a_all.csv','group_c_all.csv','three_point_bend_all.csv','group_a_path_delta.csv','group_c_path_delta.csv','three_point_bend_path_delta.csv'):
        copy(DEST/p,'verification/'+p)
    entries=sorted(p for p in sdk.rglob('*') if p.is_file() and p.name!='SHA256.txt')
    (sdk/'SHA256.txt').write_text(''.join(f'{batch.sha(p)}  {p.relative_to(sdk).as_posix()}\n' for p in entries),encoding='utf8')
    with ZipFile(sdk.with_suffix('.zip'),'w',ZIP_DEFLATED,compresslevel=5) as z:
        for p in [*entries,sdk/'SHA256.txt']:z.write(p,p.relative_to(sdk.parent))
    with ZipFile(sdk.with_suffix('.zip')) as z:assert z.testzip() is None
def minimal():
    """Package the frozen binaries with one public header for C and C++ callers."""
    out = sdk.with_name('V5_12_CrackV4_minimal')
    out.mkdir(parents=True, exist_ok=True)
    files = ('CrackV4.hpp', 'CrackV4.lib', 'CrackV4.dll')
    if any(p.name not in files for p in out.iterdir()):
        raise ValueError(f'Unexpected file in {out}')
    if batch.sha(BUILD / 'CrackV4.dll') != batch.read(DEST / 'freeze.json')['dll']:
        raise ValueError('V5.12 DLL differs from the verified build')

    # Start with the C declarations used to build the DLL, including segment access.
    base = root / 'src/cpp/a/include/CrackV4.h'
    parts = [base.read_text(encoding='utf8').rstrip()]
    for name, dependency in [('CrackV4_v2.h', 'CrackV4.h'),
                             ('CrackV4_experiments.h', 'CrackV4_v2.h'),
                             ('CrackV4.hpp', 'CrackV4_v2.h')]:
        prefix = f'#pragma once\n#include "{dependency}"\n'
        source = (src / name).read_text(encoding='utf8')
        if not source.startswith(prefix):
            raise ValueError(f'Review the dependencies in {name}')
        body = source[len(prefix):].rstrip()
        if name == 'CrackV4.hpp':
            body = '#ifdef __cplusplus\n' + body + '\n#endif'
        parts.append(body)
    header = '\n\n'.join(parts) + '\n'
    declared = set(re.findall(r'\b(CrackV4\w+)\s*\(', header))
    exports = set(batch.read(DEST / 'abi_exports.json')['release'])
    if not exports.issubset(declared):
        raise ValueError(f'Missing declarations: {sorted(exports - declared)}')
    (out / files[0]).write_text(header, encoding='utf8')
    for name in files[1:]:
        shutil.copy2(BUILD / name, out / name)
    with ZipFile(out.with_suffix('.zip'), 'w', ZIP_DEFLATED) as archive:
        for name in files:
            archive.write(out / name, name)

if __name__ == '__main__':
    if '--minimal' in sys.argv:
        minimal()
    elif '--prepare' in sys.argv:
        prepare()
    else:
        finish()
