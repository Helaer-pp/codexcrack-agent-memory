"""Compile and run C and C++ consumers linked against the released GrayDetectionV2 SDK."""
import ctypes as C
import math
import os
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np
from .verify import OUT,Point,Image,Config,Result,copy_path,image,pair,library,b,inputs
from .package import FILES,SDK


def command(args,**kwargs):
    return subprocess.check_output(list(map(str,args)),encoding='utf8',errors='replace',**kwargs)


def test_api(lib,im,ref,cp,rp):
    tests={}
    for mode in (0,1,2):
        config=Config();lib.GrayDetectionV2DefaultConfig(C.byref(config));config.mode=mode;config.ratio=.025
        h=C.c_void_p();message=C.create_string_buffer(1024)
        rc=lib.GrayDetectionV2Create(C.byref(image(ref)),pair(rp),C.byref(config),C.byref(h),None,message,len(message))
        if rc:
            assert mode==1 and not h.value and message.value
            tests[f'mode_{mode}']='missing reference crack explicitly rejected'
            continue
        try:
            baseline=Result(size=C.sizeof(Result));again=Result(size=C.sizeof(Result))
            assert lib.GrayDetectionV2GetBaseline(h,C.byref(baseline))==0
            result=Result(size=C.sizeof(Result))
            assert lib.GrayDetectionV2Process(h,C.byref(image(im)),pair(cp),C.byref(result))==0
            path=copy_path(lib,h)
            assert lib.GrayDetectionV2GetBaseline(h,C.byref(again))==0 and bytes(baseline)==bytes(again)
            assert copy_path(lib,h)==path
            assert result.tip_ok and math.isclose(result.mm,.025*result.length,abs_tol=1e-8)
            storage=np.zeros((im.shape[0],im.shape[1]+37),dtype=np.uint8)
            storage[:,:im.shape[1]]=im
            padded=storage[:,:im.shape[1]]
            assert lib.GrayDetectionV2Process(h,C.byref(image(padded)),pair(cp),C.byref(result))==0 and copy_path(lib,h)==path
            bad=Result(size=1)
            assert lib.GrayDetectionV2Process(h,C.byref(image(im)),pair(cp),C.byref(bad))!=0
            invalid=image(im);invalid.stride=im.shape[1]-1
            assert lib.GrayDetectionV2Process(h,C.byref(invalid),pair(cp),C.byref(result))!=0
            assert lib.GrayDetectionV2Process(h,C.byref(image(im)),None,C.byref(result))==0
            tests[f'mode_{mode}']='loaded, cached baseline, padded GRAY8, bad size/stride, NULL tracked points and mm conversion checked'
        finally:lib.GrayDetectionV2Destroy(h)
    cracked=Config()
    lib.GrayDetectionV2DefaultConfig(C.byref(cracked))
    cracked.mode=1
    h=C.c_void_p()
    err=C.create_string_buffer(512)
    assert lib.GrayDetectionV2Create(C.byref(image(im)),pair(cp),C.byref(cracked),C.byref(h),None,err,len(err))==0,err.value
    try:
        baseline=Result(size=C.sizeof(Result))
        assert lib.GrayDetectionV2GetBaseline(h,C.byref(baseline))==0
        assert baseline.tip_ok and baseline.length_ok and baseline.length>0
        assert copy_path(lib,h)[-1]==[baseline.tip.x,baseline.tip.y]
        tests['precracked_mode_1']='confirmed precracked reference returned with positive baseline arc and path'
    finally:
        lib.GrayDetectionV2Destroy(h)
    return tests


def main(sdk, verification):
    verification.mkdir(parents=True,exist_ok=True)
    os.environ.pop('CRACKV4_V512_MATERIAL_POLICY',None)
    build=b.ROOT/'output/build/v63_release'
    cache=(build/'CMakeCache.txt').read_text(encoding='utf8')
    vs=Path(re.search(r'CMAKE_GENERATOR_INSTANCE:INTERNAL=(.+)',cache)[1])
    dumpbin=sorted((vs/'VC/Tools/MSVC').glob('*/bin/Hostx64/x64/dumpbin.exe'))[-1]
    def exports(dll):
        return {name:int(n) for n,name in re.findall(r'^\s*(\d+)\s+[0-9A-F]+\s+[0-9A-F]+\s+(\w+)',command([dumpbin,'/exports',dll]),re.M|re.I)}
    before=b.ROOT/'output/releases/V5_12_CrackV4_minimal'
    prev=exports(before/'CrackV4.dll')
    expected_exports={key.replace('CrackV4','GrayDetectionV2'):ordinal for key,ordinal in prev.items()}
    actual=exports(sdk/'GrayDetectionV2.dll')
    assert actual==expected_exports and len(actual)==21,actual
    dll=library(sdk)
    for symbol in actual:
        assert getattr(dll,symbol)
    for old_name in prev:
        assert not hasattr(dll,old_name)
    header=(sdk/'GrayDetectionV2.hpp').read_text(encoding='utf8')
    assert all(re.search(r'\b'+name+r'\s*\(', header) for name in actual)
    assert 'class GrayDetectionV2 {' in header and 'CrackV4' not in header
    deps=[s.strip() for s in command([dumpbin,'/dependents',sdk/'GrayDetectionV2.dll']).splitlines() if s.strip().lower().endswith('.dll')]
    assert 'opencv_world440.dll' in [s.lower() for s in deps] and not any('python' in s.lower() for s in deps)
    m=inputs.metadata('group_a',299);src=m['input']
    im=b.old.current(src['current'],src['image_sha']);ref=b.old.read_fixed(src['reference'],src['ref_sha'])
    tests=test_api(library(sdk),im,ref,m['current_points'],m['fixed_points'])
    croot=verification/'consumer';croot.mkdir(exist_ok=True)
    root=b.ROOT.as_posix();pack=sdk.as_posix()
    cmake=f'''cmake_minimum_required(VERSION 3.20)
project(Smoke LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
add_executable(cpp_client cpp_client.cpp)
add_executable(legacy_client legacy_client.cpp)
target_include_directories(legacy_client PRIVATE "{pack}" "{root}/third_party/opencv440/include")
target_link_libraries(legacy_client PRIVATE "{pack}/GrayDetectionV2.lib" "{root}/third_party/opencv440/lib/opencv_world440.lib")
target_include_directories(cpp_client PRIVATE "{pack}" "{root}/third_party/opencv440/include")
target_link_libraries(cpp_client PRIVATE "{pack}/GrayDetectionV2.lib" "{root}/third_party/opencv440/lib/opencv_world440.lib")
add_executable(c_client check.c)
target_include_directories(c_client PRIVATE "{pack}")
target_link_libraries(c_client PRIVATE "{pack}/GrayDetectionV2.lib")
'''
    (croot/'CMakeLists.txt').write_text(cmake,encoding='utf8')
    for name,path in [('cpp_client','baseline/frozen_a/src/example.cpp'),('legacy_client','src/cpp/a/example/main.cpp')]:
        source=(b.ROOT/path).read_text(encoding='utf8')
        (croot/(name+'.cpp')).write_text(source.replace('CrackV4Detector','GrayDetectionV2').replace('CrackV4','GrayDetectionV2'),encoding='utf8')
    (croot/'check.c').write_text('#include "GrayDetectionV2.hpp"\n#include <string.h>\nint main(void){GrayDetectionV2Config c; GrayDetectionV2DefaultConfig(&c);return !(c.struct_size==sizeof(c) && strstr(GrayDetectionV2BuildInfo(),"V6.3 S2"));}\n',encoding='ascii')
    cm=b.read(b.ROOT/'config/project.json')['cmake_executable']
    cb=b.ROOT/'output/build'/(verification.name+'_consumer')
    command([cm,'-S',croot,'-B',cb,'-G','Visual Studio 17 2022','-A','x64'])
    command([cm,'--build',cb,'--config','Release','--target','c_client','cpp_client','legacy_client','--parallel','1','--','/nr:false'])
    release=cb/'Release'
    shutil.copy2(sdk/'GrayDetectionV2.dll',release)
    shutil.copy2(b.ROOT/'third_party/opencv440/bin/opencv_world440.dll',release)
    imports={}
    linked_symbols={}
    for name in ('c_client','cpp_client','legacy_client'):
        imports[name]=[s.strip() for s in command([dumpbin,'/dependents',release/(name+'.exe')]).splitlines() if s.strip().lower().endswith('.dll')]
        assert 'graydetectionv2.dll' in [s.lower() for s in imports[name]]
        assert 'crackv4.dll' not in [s.lower() for s in imports[name]]
        imported_symbols=command([dumpbin,'/imports:GrayDetectionV2.dll',release/(name+'.exe')])
        # MSVC import libraries can encode the stable explicit DEF ordinals.
        ordinals={int(v) for v in re.findall(r'^\s*Ordinal\s+(\d+)\s*$',imported_symbols,re.M|re.I)}
        named={name for name in actual if name in imported_symbols}
        assert 'CrackV4' not in imported_symbols and (ordinals or named)
        assert ordinals.issubset(actual.values())
        linked_symbols[name]=sorted(named|{symbol for symbol,n in actual.items() if n in ordinals})
    command([release/'c_client.exe'],cwd=release)
    args=[src['reference'],src['current'],*np.asarray(m['fixed_points']).flatten(),*np.asarray(m['current_points']).flatten()]
    expected=next(r for r in b.read_csv(b.OUT/'group_a_lengths.csv') if int(r['frame'])==299)
    import json
    tip=json.loads(expected['tip'])
    clients={}
    for name in ('legacy_client','cpp_client'):
        if name=='legacy_client':
            legacy_args=[2,.025,src['reference'],*np.asarray(m['fixed_points']).flatten(),
                         src['current'],*np.asarray(m['current_points']).flatten()]
            log=command([release/(name+'.exe'),*legacy_args],cwd=release).strip()
            fields=log.splitlines()[-1].split()
            assert fields[1:3]==['1','1'] and math.dist(tip,list(map(float,fields[3:5])))<1e-8
            assert abs(float(fields[5])-float(expected['path_length_px']))<1e-8
            assert math.isclose(float(fields[6]),.025*float(fields[5]),abs_tol=1e-8)
        else:
            log=command([release/(name+'.exe'),*args],cwd=release).strip()
            assert 'valid=1' in log and 'length_valid=1' in log,log
            match=re.search(r'tip=\[([\d.]+),\s*([\d.]+)\]',log)
            assert match and math.dist(tip,list(map(float,match.groups())))<.0001,log
            assert abs(float(re.search(r'length_px=([\d.]+)',log)[1])-float(expected['path_length_px']))<.0001
        clients[name]=log
    b.save(verification/'integration.json',dict(files={name:b.sha(sdk/name) for name in FILES},exports=actual,
           dependencies=deps,build_info=library(sdk).GrayDetectionV2BuildInfo().decode(),api=tests,client_imports=imports,linked_symbols=linked_symbols,linked_clients=clients,c_header=True))
    print('Verified native dependencies, 21 GrayDetectionV2 exports, C/C++ clients and GrayDetectionV2 import descriptors.')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--sdk',type=Path,default=SDK)
    parser.add_argument('--out',type=Path,default=OUT)
    args=parser.parse_args()
    main(args.sdk.resolve(),args.out.resolve())
