from v2common import *
from replay import locked,parse_manifest,read_image
from algorithm import detect
from parity import difference
from evaluate_v2 import getlabels
from media_v2 import card
from PIL import Image
import numpy as np,shutil,subprocess,zipfile,random,io,re,importlib.metadata as metadata,platform,concurrent.futures
def normalize(v):
 if isinstance(v,dict):return {k:normalize(x) for k,x in v.items() if not k.endswith('_ms')}
 if isinstance(v,list):return [normalize(x) for x in v]
 return v
def main():
 locked();assert (OUT/'report_complete.json').exists();identity=read(OUT/'baseline_identity.json');assert sha(FROZEN)==SHA
 for path,digest in identity['protected'].items():assert sha(ROOT/path)==digest,path
 for path,digest in identity['point_sources'].items():assert sha(path)==digest,path
 for path,digest in identity['old_manifests'].items():assert sha(path)==digest,path
 assert sha(OUT/'experiment_manifest.csv')==identity['manifest_sha']
 entry=read(OUT/'validation_entry_lock.json');assert entry['algorithm']==read(OUT/'config_v2_locked.json');assert entry['dev_summary_sha']==sha(OUT/'group_summary_dev.csv')
 for stage in ['gate0','gate1','development_inference','development_evaluation','sentinels','validation_inference','validation_evaluation','native_parity','aggregate','media','reference_gallery','failure_audit','report']:assert (OUT/f'{stage}_complete.json').exists(),stage
 native_identity=read(OUT/'native_port_identity.json');assert sha(OUT/'cpp_build/Release/GrayRefV2.dll')==native_identity['dll_sha']
 for name,digest in native_identity['source_sha'].items():assert sha(Path(__file__).parent/name)==digest,name
 assert read(OUT/'numeric_kernel_audit.json')['records'][-1]['equal']
 baseline_checks=[]
 for old in [OLD,AUDIT]:
  files=read(old/'artifact_manifest.json')['files'];bad=[]
  def check(item):
   name,r=item;p=old/name;return name,p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
   for i,(name,ok) in enumerate(pool.map(check,files.items()),1):
    if not ok:bad.append(name)
    if i%15000==0:print('OLD SEALED FILES CHECKED',old.name,i,flush=True)
  assert not bad,bad;baseline_checks.append(dict(path=str(old),files=len(files),mismatches=bad))
 records=rows(OUT/'all_results.csv');assert len(records)==2647*6;keys={(r['group'],r['frame_id'],r['mode']) for r in records};assert len(keys)==len(records)
 for g in DEV+VAL:
  for m in ['V1_LOCKED']+MODES:assert sum(r['group']==g and r['mode']==m for r in records)==COUNTS[g]
 manifest=parse_manifest();state_checks=0
 for row in manifest:
  g=row['group'];f=row['frame_id'];data=unpack(OUT/'frames'/g/str(f)/'result.json.gz');assert data['input']['image_sha']==row['image_sha'] and data['input']['ref_sha']==row['ref_sha'];assert data['input']['current_points']==row['current_points'] and data['input']['reference_points']==row['reference_points'];assert not data['gt_accessed_at_inference']
  for result in data['results']:
   assert (result['tip'] is not None)==(result['output_state']=='PROVISIONAL_OBSERVED');assert len(result['trace'])==result['observed_path_count']+result['predicted_gap_count']
   if result['tip'] is not None:assert 0<=result['tip'][0]<int(row['width']) and 0<=result['tip'][1]<int(row['height'])
   for t in result['paths']:
    for v in t['trace']:assert v[5]<=v[1]<v[6] and np.isfinite(v[7]) and np.isfinite(v[8])
   state_checks+=1
  combined=next(r for r in data['results'] if r['mode']=='V2_COMBINED');terminal=next(r for r in data['results'] if r['mode']=='V2_TERMINAL')
  for field in ['seeds','paths','chosen_seed','chosen_path_id']:assert combined[field]==terminal[field],(g,f,field)
  imagepath=OUT/'galleries'/g/f'{f:06}.jpg';assert imagepath.exists()
  with Image.open(imagepath) as im:assert im.size==(1600,1320);im.verify()
 # Recompute predetermined random samples, including failed/empty outputs.
 labels,_=getlabels(DEV+VAL);rng=random.Random(20261112);qa=[]
 for group in DEV+VAL:
  for fid in sorted(rng.sample(range(1,COUNTS[group]+1),2)):
   row=next(r for r in manifest if r['group']==group and r['frame_id']==fid);R=read_image(row['reference'],row['ref_sha']);C=read_image(row['current'],row['image_sha']);d=unpack(OUT/'frames'/group/str(fid)/'result.json.gz');new,a=detect(R,C,row['reference_points'],row['current_points']);diff=difference(normalize(new['results']),normalize(d['results']));assert diff is None,diff
   im=card(d,R,C,f'{group} / {fid}   单帧无历史 · V1与独立V2消融',labels.get((group,fid)));b=io.BytesIO();im.save(b,format='JPEG',quality=88);equal=hashlib.sha256(b.getvalue()).hexdigest()==sha(OUT/'galleries'/group/f'{fid:06}.jpg');assert equal;qa.append(dict(group=group,frame_id=fid,complete_five_mode_recompute=True,overlay_bytes_reproducible=equal))
 save(OUT/'random_recompute_overlay_qa.csv',qa)
 # Exercise the independent public Python CLI with the predeclared A input.
 cli=OUT/'cli_smoke';source=Path(__file__).resolve().parent;case=read(OUT/'sentinels/A/case.json')['row']
 if not cli.exists():
  args=[sys.executable,str(source/'cli.py'),'--reference',case['reference'],'--current',case['current'],'--output',str(cli)]
  for name,pts in [('ref',case['reference_points']),('cur',case['current_points'])]:
   for i,p in enumerate(pts,1):args += [f'--p{i}-{name}',','.join(map(str,p))]
  run=subprocess.run(args,capture_output=True,text=True,errors='replace');write(OUT/'cli_smoke_command.json',dict(argv=args,returncode=run.returncode));(OUT/'logs/cli_stdout.txt').write_text(run.stdout,encoding='utf8');(OUT/'logs/cli_stderr.txt').write_text(run.stderr,encoding='utf8');assert run.returncode==0
 assert difference(normalize(read(cli/'result.json')['results']),normalize(unpack(OUT/'sentinels/A/result.json.gz')['results'])) is None
 videos=[]
 for g in DEV+VAL:
  p=OUT/'galleries'/f'{g}_V1_V2.mp4';qa_video=read(OUT/'galleries'/f'{g}_video_qa.json');assert qa_video['sha']==sha(p) and qa_video['full_decode'];r=subprocess.run([str(ROOT/'third_party/ffmpeg/ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,text=True,check=True);probe=json.loads(r.stdout);assert int(probe['streams'][0]['nb_frames'])==COUNTS[g];videos.append(dict(group=g,frames=COUNTS[g],duration=probe['format']['duration'],sha=sha(p),decode_pass=True))
 save(OUT/'video_final_qa.csv',videos)
 # Snapshot all sources together so the copied one-command runner remains usable.
 for name in ['python_v2','cpp_v2']:(OUT/name).mkdir(exist_ok=True)
 for p in source.iterdir():
  if p.is_file() and p.suffix in ['.py','.hpp','.cpp','.h','.ps1','.md','.txt']:
   if p.suffix=='.py':compile(p.read_text(encoding='utf8'),str(p),'exec')
   dest=OUT/'python_v2'/p.name
   if p.resolve()!=dest.resolve():shutil.copyfile(p,dest)
   if p.suffix in ['.hpp','.cpp','.h','.ps1'] or p.name in ['CMakeLists.txt','README.md']:shutil.copyfile(p,OUT/'cpp_v2'/p.name)
 shutil.copyfile(FROZEN,OUT/'python_v2/paired_p1p2_roi_V1_FROZEN.py');(OUT/'original_v1_source_diff.patch').write_text('',encoding='utf8')
 sdk=OUT/'GrayRefV2_Research_SDK';sdk.mkdir(exist_ok=True)
 for src in [OUT/'cpp_build/Release/GrayRefV2.dll',OUT/'cpp_build/Release/GrayRefV2.lib',OUT/'cpp_build/Release/opencv_world440.dll',source/'GrayRefV2.h',source/'README.md'] :shutil.copyfile(src,sdk/src.name)
 shutil.copyfile(ROOT/'third_party/opencv440/LICENSE',sdk/'OpenCV_LICENSE.txt')
 with zipfile.ZipFile(OUT/'GrayRefV2_Research_SDK.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sdk.iterdir():z.write(p,p.name)
 packages={name:metadata.version(name) for name in ['numpy','scipy','opencv-python','pandas','matplotlib','Pillow','psutil']};env=dict(python=sys.version,platform=platform.platform(),packages=packages,opencv_declared_numpy_requires=[r for r in metadata.requires('opencv-python') if 'numpy' in r],cpu='AMD Ryzen 9 7950X 16-Core Processor',cpu_source='Windows registry inspected during original run',fresh_environment_install_verified=False);write(OUT/'environment_versions.json',env)
 (OUT/'reproduce.md').write_text(f'''# 构建与复现

工作目录 `{ROOT}`。已实际执行的各阶段日志在logs/，V1原生每帧CSV/stdout/stderr在frames/*/*/v1/，G0未修改CLI输出在gate0/。完整新编排仅做语法和路径检查；没有为测试编排再重复全部2647帧，但每个实际阶段均已执行，独立Python CLI另有cli_smoke/与命令日志。

```powershell
Set-Location .
& ./research/p1p2_grayref_v2/reproduce.ps1 -Output './output/experiments/p1p2_grayref_v2_replay01'
```

源码快照python_v2/包含完整脚本及其C++构建依赖，也可从该目录调用reproduce.ps1。输出必须为全新ASCII项目output子目录。python_v2/和cpp_v2/的C++文件是相同源码副本；活动源码在research/p1p2_grayref_v2/。不执行旧封存代码；旧结果只供身份/回放比较。不要指向本轮封存目录。

实际构建：`build.ps1 -Output <新目录>/cpp_build`，内部调用CMake、Visual Studio17 2022、x64、v142。真正DLL是cpp_build/Release/GrayRefV2.dll；GrayRefV2_Research_SDK.zip包含DLL/导入库/头文件/OpenCV依赖及许可。native_v2.py是C ABI调用桥，不承担检测计算。

算法推理接口`detect(R,C,rp,cp)`只接收原始uint8图像和四点。无标签、组名、帧名或历史参数。独立CLI参数见python_v2/cli.py --help；P1/P2必须是实际当前帧点。C接口GrayRefV2Create/Process/Read/Array/Destroy，线程与指针寿命见README及头文件。

依赖使用config/project.json现有Python和工具链；完整实测版本见environment_versions.json。requirements.txt是现有环境快照，不是已验证的全新pip解析锁：OpenCV4.12轮子声明NumPy>=2，而本机1.26.4组合已经完成全部实测；不自动安装或覆盖现有环境。字体使用Windows微软雅黑。新机器环境重建与目标i7性能未验证。

原始F盘图像、逐帧点、旧V1回放、标签快照必须仍可读；不写回原图/标签。开发组和验证组顺序固定，标签仅分组全部推理后读取。新跑仍属已曝光回归，不自动变为盲测。单次API调用耗时、Python桥耗时和视频8fps不是同一个指标。
''',encoding='utf8')
 required=['V2_DEVELOPMENT_REPORT.md','V2_EXPERIMENT_PLAN.md','V2_IMPLEMENTATION_AUDIT.md','V2_ABLATION_REPORT.md','V2_FAILURE_ANALYSIS.md','V2_NUMERIC_PARITY_REPORT.md','baseline_identity.json','experiment_manifest.csv','config_v2_locked.json','all_results.csv','group_summary.csv','init_candidates.csv','path_hypotheses.csv','reference_quality.csv','first_divergence_vs_v1.csv','perturbation_robustness.csv','runtime_performance.csv','reproduce.md']
 for name in required:assert (OUT/name).stat().st_size>0,name
 (OUT/'DELIVERABLE_INDEX.md').write_text('# 交付索引\n\n'+''.join(f'- [{n}]({n})\n' for n in required)+'\n- [六组完整视频与每帧对比](galleries/index.html)\n- [ABCD和代表帧](galleries/same_bmp_ABCD_v1_v2.html)\n- [Python/完整复现源码](python_v2/README.md)\n- [C++源码](cpp_v2/v2_detector.hpp)\n- [独立研究SDK](GrayRefV2_Research_SDK.zip)\n- [最终完整性](final_integrity.json)\n',encoding='utf8')
 sources={p.relative_to(OUT).as_posix():sha(p) for name in ['python_v2','cpp_v2'] for p in (OUT/name).iterdir() if p.is_file()};write(OUT/'source_manifest.json',sources)
 for page in (OUT/'galleries').glob('*.html'):
  for link in re.findall(r'(?:href|src)="([^"]+)"',page.read_text(encoding='utf8')):
   if not re.match(r'\w+:',link):assert (page.parent/link).is_file(),(page,link)
 report=read(OUT/'report_complete.json');parity=read(OUT/'native_parity_complete.json');final=dict(utc=utc(),engineering_complete=report['engineering_complete'],algorithm_accuracy_accepted=report['algorithm_accuracy_accepted'],py_cpp_parity_passed=parity['passed'],production_release_approved=False,gate0_identity=True,gate1_module_contracts=True,gate2_locked_before_scoring=True,gate3_complete_development_frames=1565,gate4_cases=136,gate5_complete_exposed_validation_frames=1082,gate6_native_mode_cases=parity['mode_cases'],gate7_integrity=True,all_result_rows=15882,v1_six_mode_rows=15882,v2_inference_state_checks=state_checks,full_frame_comparison_images=2647,full_videos=6,old_sealed_checks=baseline_checks,protected_files_unchanged=len(identity['protected']),frozen_v1_sha=SHA,point_sources_unchanged=True,image_hash_verification='All2647 at Gate0; all original replay/port reads verified against same SHA; native final replay after Python rules locked',random_recompute_cases=12,standalone_cli=True,original_annotations_unchanged_by_code=True,ct3_original_tracking_txt='UNAVAILABLE_USE_EXPLICIT_HISTORICAL_COORDINATE_CSV',physical_registration_truth='UNRESOLVED',physical_crack_identity_certification='NOT_ESTABLISHED',new_blind_holdout='NOT_AVAILABLE',real_FPR='N/A')
 write(OUT/'final_integrity.json',final)
 files={}
 for p in sorted(OUT.rglob('*')):
  if p.is_file() and p.name!='artifact_manifest.json' and not (p.suffix=='.log' and p.name.startswith('seal')):files[p.relative_to(OUT).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
 write(OUT/'artifact_manifest.json',dict(files=files,excluded=['artifact_manifest.json self','logs/seal*.log optional live sealing console'],utc=utc()));print('SEALED',len(files),'files',flush=True)
if __name__=='__main__':main()
