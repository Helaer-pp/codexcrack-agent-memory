"""Replay selected groups with the repaired A build."""
import argparse
import ctypes as C
from pathlib import Path
import six_roi_replay as s
from all_groups import ROOT, api

BUILD=ROOT/'output/build/src/cpp/a/Release/CrackV4.dll'
OUT=ROOT/'output/runs/roi_repair_20261108_r01'

def setup():
    api.BASE=BUILD
    api.EXPECTED_BASE=api.sha(BUILD)
    runtime=C.CDLL(str(BUILD.with_name('opencv_world440.dll')))
    lib=api.base_library()
    lib.CrackV4LastDebugJson.argtypes=[C.c_void_p]
    lib.CrackV4LastDebugJson.restype=C.c_char_p
    lib.CrackV4SegmentCount.argtypes=[C.c_void_p]
    lib.CrackV4CopySegment.argtypes=[C.c_void_p,C.c_int,C.POINTER(api.Point),C.c_int]
    return lib,runtime

def run(group):
    s.OUT=OUT
    s.setup=setup
    return s.run(group)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('groups',nargs='+')
    p.add_argument('--out',default=None)
    args=p.parse_args()
    if args.out:
        OUT=ROOT/'output/runs'/args.out
    for group in args.groups:
        run(group)
