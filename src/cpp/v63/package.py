"""Stage the three-file x64 SDK, then archive the verified artifacts."""
from pathlib import Path
import shutil
from zipfile import ZIP_DEFLATED,ZipFile
from .verify import BUILD,OUT,VERSION,b

SDK=b.ROOT/'output/releases'/('GrayDetectionV2-'+VERSION+'-cmake')
FILES=('GrayDetectionV2.hpp','GrayDetectionV2.lib','GrayDetectionV2.dll')


def stage():
    SDK.mkdir(parents=True,exist_ok=True)
    if any(p.name not in FILES for p in SDK.iterdir()):
        raise RuntimeError(f'Unexpected contents in {SDK}')
    shutil.copy2(BUILD.parent / FILES[0], SDK / FILES[0])
    for name in FILES[1:]:shutil.copy2(BUILD/name,SDK/name)


def finish():
    tested=b.read(OUT/'integration.json')
    expected={name:b.sha(SDK/name) for name in FILES}
    assert expected==tested['files'] and expected['GrayDetectionV2.dll']==b.sha(BUILD/'GrayDetectionV2.dll')
    target=SDK.parent/(SDK.name+'.zip')
    with ZipFile(target.with_suffix('.partial'),'w',ZIP_DEFLATED) as archive:
        for name in FILES:archive.write(SDK/name,name)
    with ZipFile(target.with_suffix('.partial')) as archive:
        assert archive.testzip() is None and archive.namelist()==list(FILES)
    target.with_suffix('.partial').replace(target)


if __name__=='__main__':
    import sys
    if sys.argv[1:] == ['--stage']:stage()
    else:finish()
