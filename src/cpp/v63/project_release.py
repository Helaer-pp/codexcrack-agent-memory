"""Export a relocatable VS project and the three files verified for this release."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / 'GrayDetectionV2'
RELEASES = ROOT / 'output/releases'
FILES = ('GrayDetectionV2.hpp', 'GrayDetectionV2.lib', 'GrayDetectionV2.dll')
VERSION = (PROJECT / 'VERSION.txt').read_text(encoding='ascii').strip()
NAME = 'GrayDetectionV2-' + VERSION


def archive(target, entries):
    partial = target.with_suffix('.partial')
    with ZipFile(partial, 'w', ZIP_DEFLATED) as z:
        for path, name in entries:
            z.write(path, name)
    with ZipFile(partial) as z:
        if z.testzip() is not None:
            raise ValueError('Archive verification failed')
    partial.replace(target)


def project_zip():
    entries = [(PROJECT / name, 'GrayDetectionV2/' + name) for name in (
        'VERSION.txt', 'GrayDetectionV2.sln', 'GrayDetectionV2.vcxproj',
        'GrayDetectionV2.rc.in', 'generate_sdk.cmake', 'README.md')]
    cpp = ROOT / 'src/cpp'
    files = [cpp / name for name in (
        'a/CrackV4.cpp', 'a/roi_tip.inc', 'a/segments.inc', 'a/include/CrackV4.h',
        'a/include/CrackV4.hpp', 'a/internal/CrackV4_experiments.h', 'a/internal/CrackV4_v2.h',
        'a/internal/scipy_gaussian_kernels.h', 'v510/registration.cpp', 'v510/internal.hpp',
        'v512/internal.hpp', 'v512/material.cpp', 'v512/exports.def',
        'v63/geometry.cpp', 'v63/mapping.cpp', 'v63/evidence.cpp', 'v63/tracking.cpp',
        'v63/internal.hpp', 'v63/adapter.inc')]
    cv = ROOT / 'third_party/opencv440'
    files += [cv / 'LICENSE', cv / 'bin/opencv_world440.dll', cv / 'lib/opencv_world440.lib']
    files += sorted(p for p in (cv / 'include').rglob('*') if p.is_file())
    entries += [(p, 'GrayDetectionV2/' + p.relative_to(ROOT).as_posix()) for p in files]
    archive(RELEASES / (NAME + '-VS2022-source.zip'), entries)


def sdk_zip(verification):
    sdk = RELEASES / NAME
    expected = json.loads(verification.read_text(encoding='utf8'))
    if expected['build_info'].split('; ')[-1] != 'DLL ' + VERSION:
        raise ValueError('Wrong tested version')
    if set(p.name for p in sdk.iterdir()) != set(FILES):
        raise ValueError('Unexpected SDK contents')
    for name in FILES:
        if hashlib.sha256((sdk/name).read_bytes()).hexdigest() != expected['files'][name]:
            raise ValueError('Untested file: ' + name)
    archive(RELEASES / (NAME + '.zip'),
            [(sdk / name, name) for name in FILES])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--integration', type=Path, help='Verify and archive the binary SDK')
    args = parser.parse_args()
    RELEASES.mkdir(exist_ok=True, parents=True)
    if args.integration:
        sdk_zip(args.integration)
    else:
        project_zip()
