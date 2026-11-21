"""Time the available native V5.12 ABI separately from the V5.14 research runner."""
import ctypes as C
import os
from time import perf_counter
import numpy as np
from src.cpp.v512 import verify_abi as abi
from research.v3_labelme_comparison.compare import write_csv
from .batch import ROOT,OUT,OLD,old,read,sha


def main():
    os.environ.pop('CRACKV4_V512_MATERIAL_POLICY',None)
    lib=abi.load()
    digest=sha(abi.BUILD/'CrackV4.dll')
    assert digest==sha(ROOT/'output/releases/V5_12_CrackV4_minimal/CrackV4.dll')
    rows=[]
    for g,i in [('group_a',398),('three_point_bend',248)]:
        assert read(ROOT/'config/dataset_usage_policy.json')['groups'][g] in ('DEVELOPMENT','VALIDATION_ONLY')
        meta=read(OLD/'evidence'/g/str(i)/'metadata.json')
        info=meta['input'];raw=old.current(info['current'],info['image_sha']);ref=old.read_fixed(info['reference'],info['ref_sha'])
        cp,rp=map(np.array,(meta['current_points'],meta['fixed_points']))
        for repeat in range(4):
            offsets=[0,-50,-100,-150]
            for dx in offsets[repeat:]+offsets[:repeat]:
                tick=perf_counter();h=abi.create(lib,ref,rp+[dx,0]);ms=1000*(perf_counter()-tick)
                try:
                    output=abi.Result(size=C.sizeof(abi.Result))
                    tick=perf_counter()
                    ret=lib.CrackV4Process(h,C.byref(abi.image(raw)),abi.pair(cp+[dx,0]),C.byref(output))
                    elapsed=1000*(perf_counter()-tick)
                    assert ret==0,lib.CrackV4LastJson(h)
                    rows.append(dict(group=g,frame=i,dx=dx,repeat=repeat,create_ms=ms,process_ms=elapsed,
                        tip=[output.tip.x,output.tip.y] if output.tip_ok else None,detector_ms=output.detector_ms,dll_sha=digest))
                finally:lib.CrackV4Destroy(h)
    write_csv(OUT/'v512_dll_left.csv',rows)

if __name__=='__main__':
    main()
    from .legacy_pressure import main as compare_python
    compare_python()
    from .pressure_views import main as render_pressure
    render_pressure()
    from .negative_audit import main as examine_negatives
    examine_negatives()
