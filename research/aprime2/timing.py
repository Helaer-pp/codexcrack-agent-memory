from common import *
import subprocess,platform,psutil

guard();mm=rows(ROOT/'data/inputs/six_groups_manifest.csv');allrows=[];summary=[];regression=[]
save(RUN/'07_native_timing/environment.json',dict(platform=platform.platform(),processor=platform.processor(),
    logical_cpus=psutil.cpu_count(),physical_cpus=psutil.cpu_count(logical=False),RAM_bytes=psutil.virtual_memory().total,
    threads=4,compiler='MSVC v142 /O2 /fp:precise',opencv='4.4.0',input='stream decoded before core timer',
    scope='A and A+bounded native observer ONLY; Python candidates/reference/decision excluded; full A-prime-2 NOT_TESTED',
    execution_order='alternating A-first/shadow-first by frame, independent handles, same temporal order',
    production_sha=sha(api.BASE),shadow_sha=sha(ROOT/'output/build/Release/CrackV4AP2Shadow.dll')))
for g in dict.fromkeys(m['dataset_alias'] for m in mm):
    rr=[m for m in mm if m['dataset_alias']==g];p=RUN/f'07_native_timing/{g}'
    write(p.with_suffix('.tsv'),'\n'.join(m['input_image']+'\t'+'\t'.join(str(v) for q in json.loads(m['points']) for v in q) for m in rr))
    args=[str(ROOT/'output/build/Release/AP2DualBench.exe'),str(api.BASE),str(ROOT/'output/build/Release/CrackV4AP2Shadow.dll'),str(p.with_suffix('.tsv')),str(p),'2' if rr[0]['mode']=='auto' else '0']
    with p.with_suffix('.log').open('w') as log:subprocess.run(args,check=True,stdout=log,stderr=subprocess.STDOUT)
    r=rows(p.with_suffix('.csv'));a=list(jl(str(p)+'_A.jsonl'));b=list(jl(str(p)+'_shadow.jsonl'));_,old,_=native(ROOT/f'data/frozen_a_replay/{g}_A')
    assert len(r)==len(rr)
    for i,(x,y,z) in enumerate(zip(a,b,old)):
        assert api.normalized(x)==api.normalized(y)==api.normalized(z),(g,i)
        regression.append(dict(group=g,frame_id=i,full_state_equal=True,path_bitwise_equal=r[i]['path_bytes_equal']=='1'))
    for z in r:allrows.append(dict(group=g,**z))
    q=r[1:];summary.append(dict(group=g,frames=len(q),A=api.stats([float(x['A_complete_core_ms']) for x in q]),
        shadow_observer=api.stats([float(x['shadow_observer_core_ms']) for x in q]),full_Aprime2='NOT_TESTED'))
    csvout(RUN/'07_native_timing/all_frames.csv',allrows);save(RUN/'07_native_timing/summary.json',summary)
    csvout(RUN/'03_A_candidate_audit/Gate0_final_native.csv',regression);print('TIMING',g,summary[-1],flush=True)
guard();save(RUN/'03_A_candidate_audit/Gate0_final_native.json',dict(frames=len(regression),differences=0,shadow_sha=sha(ROOT/'output/build/Release/CrackV4AP2Shadow.dll'),passed=True))
