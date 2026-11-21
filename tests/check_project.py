"""Infrastructure migration verification, no algorithm changes or new GT claims."""
from pathlib import Path
import sys,os,json,csv,struct,hashlib,subprocess,datetime,runpy
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/python'));sys.path.insert(0,str(ROOT/'research/aprime/experiments'))
run='check_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
os.environ['CRACK_RUN_ID']=run
from crackv4 import frozen_a as api
from crackv4.dataset_policy import filter_rows
from common_ap import rows,jl,native,anchors,guard,read,sha
import numpy as np,cv2
cv2.setNumThreads(1)
OUT=ROOT/'output/checks'/run;OUT.mkdir(parents=True)
identity=guard();mm=filter_rows(rows(ROOT/'data/smoke/manifest.csv'),'validation',dataset_key='dataset_alias');checks=[]
for g in dict.fromkeys(x['dataset_alias']for x in mm):
 rr=[x for x in mm if x['dataset_alias']==g];nr,nj,pp=native(ROOT/f'data/frozen_a_replay/{g}_A');rp=json.loads(rr[0]['points']);ref=read(ROOT/rr[0]['input_image']);engine=api.Baseline(ref,rp,mode=rr[0]['mode'])
 for i,m in enumerate(rr):
  im=read(ROOT/m['input_image']);assert sha(ROOT/m['input_image'])==m['input_sha256'];assert hashlib.sha256(im.tobytes()).hexdigest()==m['decoded_pixel_sha256']
  a=engine.run(im,json.loads(m['points']),is_reference=i==0);p=np.array(a['formal']['raw_path'],dtype='<f8').reshape(-1,2)
  same=api.normalized(a['native'])==api.normalized(nj[i])and p.tobytes()==pp[i].astype('<f8').tobytes()
  assert same,(g,i,'PYTHON_PORT_CHANGED_NATIVE_OUTPUT');checks.append(dict(group=g,frame_id=i,caller='local_python_bridge',native_state_and_bitwise_path_equal=True))
 engine.close()
bench=ROOT/'output/build/Release/CrackReadOnlyBench.exe'
assert bench.exists(),'Run build.ps1 first'
env=os.environ.copy();env['PATH']=str(ROOT/'third_party/opencv440/bin')+';'+env['PATH']
for g in dict.fromkeys(x['dataset_alias']for x in mm):
 rr=[x for x in mm if x['dataset_alias']==g];prefix=OUT/g;tsv=prefix.with_suffix('.tsv');tsv.write_text('\n'.join(str(ROOT/m['input_image'])+'\t'+'\t'.join(str(v)for p in json.loads(m['points'])for v in p)for m in rr),encoding='utf8')
 subprocess.run([str(bench),str(api.BASE),str(tsv),str(prefix),'2'if rr[0]['mode']=='auto'else'0','1','0'],check=True,env=env,stdout=subprocess.DEVNULL)
 nr,nj,pp=native(prefix);pr,pj,pold=native(ROOT/f'data/frozen_a_replay/{g}_A')
 for i in range(len(rr)):
  assert api.normalized(nj[i])==api.normalized(pj[i])and pp[i].tobytes()==pold[i].tobytes(),(g,i,'NATIVE_BUILD_CHANGED_OUTPUT')
  checks.append(dict(group=g,frame_id=i,caller='rebuilt_project_read_only_bench',native_state_and_bitwise_path_equal=True))
os.environ['CRACK_RUN_ID']=run
runpy.run_path(str(ROOT/'research/aprime/tests/test_contracts.py'),run_name='__main__')
bad=[]
for name,module in list(sys.modules.items()):
 p=getattr(module,'__file__',None)
 if p:
  p=Path(p).resolve()
  if p.is_relative_to(ROOT.parent)and not p.is_relative_to(ROOT):bad.append((name,str(p)))
assert not bad,('LEGACY_IMPORT',bad)
guard()
sys.path.insert(0,str(ROOT/'src/cpp/a'))
from check_example import check as check_a
official=ROOT/'output/build/src/cpp/a/Release'
for group in dict.fromkeys(m['dataset_alias'] for m in mm):
    sample=[m for m in mm if m['dataset_alias']==group]
    gold=ROOT/'output/runs/ct3_roi_tip_r01/smoke_expected.json'
    expected=json.loads(gold.read_text(encoding='utf8'))[group]
    assert all(e['image']==m['filename'] and e['anchors']==json.loads(m['points']) for e,m in zip(expected,sample))
    check_a(official/'CrackV4Example.exe',expected,[ROOT/m['input_image'] for m in sample],
            {'auto':2,'clean':0,'cracked':1}[sample[0]['mode']])
result=dict(passed=True,production_DLL_sha256=sha(official/'CrackV4.dll'),production_example_frames=len(mm),historical_frozen_DLL_sha256=sha(api.BASE),python_bridge_frames=len(mm),rebuilt_native_benchmark_frames=len(mm),frame_checks=checks,research_contract_tests=9,anchor_invariance_groups=len({r['dataset_alias'] for r in mm}),excluded_groups=['group_x'],anchor_invariance_variants=['measured','bounded_translation_scale_rotation'],no_legacy_workspace_imports=True,requires_external_real_images_for_smoke=False,opencv_native='4.4.0',python_opencv=cv2.__version__,native_Aprime_accuracy_or_speed_claim=False,output_directory=str(OUT))
subprocess.run([sys.executable,'-B',str(ROOT/'tests/check_roi_terminal.py')],check=True)
subprocess.run([sys.executable,'-B',str(ROOT/'tests/check_anchor_invariance.py')],check=True)
subprocess.run([sys.executable,'-B',str(ROOT/'tests/check_invalid_current_anchor.py')],check=True)
(OUT/'check_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');(ROOT/'output/checks/latest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(f'PROJECT CHECK PASSED: {len(mm)} production A frames, {len(checks)} historical replay checks; group_x excluded',flush=True)
