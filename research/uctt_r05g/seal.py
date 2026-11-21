"""Final protection checks and reproducible evidence sealing; never modifies inputs."""
from common import *
import difflib,shutil,zipfile,platform
import numpy as np,cv2,PIL,matplotlib
def main():
 assert read(OUT/'delivery_qa.json')['video_full_decode_pass'];assert read(OUT/'video_qa.json')[1]['duration']==264.0
 before=read(OUT/'source_hash_before.json');after={rel:sha(ROOT/rel) for rel in before};assert before==after
 prior=read(F/'artifact_manifest.json')['files']
 for i,(rel,v) in enumerate(prior.items()):assert sha(F/rel)==v['sha256'],rel
 oldprotected=read(F/'baseline_manifest.json')['protected']
 for rel,value in oldprotected.items():assert sha(ROOT/rel)==value,rel
 native_lock={k.replace('\\','/'):v for k,v in read(OUT/'E1_pre_run_lock.json')['files'].items()}
 for rel in ['research/uctt_r05g/tracker.hpp','research/uctt_r05g/runtime.cpp','output/build/uctt_r05g/Release/R05G.dll']:assert sha(ROOT/rel)==native_lock[rel],rel
 assert sha(OUT/'seeds/diagnostic_seeds.json')==read(OUT/'seeds/provenance_lock.json')['seed_sha256']
 verified=[]
 for i,r in enumerate(rows(OUT/'input_inventory.csv')):
  require(r['dataset_id'],'development');h=sha(r['source_image']);assert h==r['sha256'],r['source_image'];verified.append(dict(dataset_id=r['dataset_id'],frame_id=r['frame_id'],sha256_before=r['sha256'],sha256_after=h,equal=True))
  if (i+1)%250==0:print('final original-image hash',i+1,flush=True)
 save(OUT/'input_hash_after.csv',verified)
 labels=[]
 with zipfile.ZipFile(LABELS) as z:
  for r in rows(OUT/'selection.csv'):
   require(r['dataset_id'],'development');require(r['dataset_id'],'comparison',uses_annotations=True);label=json.loads(z.read(r['selected_json']));w,h=int(r['width']),int(r['height']);assert (label['imageWidth'],label['imageHeight'])==(w,h)
   for s in label['shapes']:
    p=np.array(s['points']);assert np.isfinite(p).all() and (p[:,0]>=0).all() and (p[:,0]<w).all() and (p[:,1]>=0).all() and (p[:,1]<h).all()
   labels.append(dict(dataset_id=r['dataset_id'],frame_id=r['frame_id'],width=w,height=h,coordinate_space='original image pixels',within_original_bounds=True))
 save(OUT/'tests/annotation_coordinate_audit.csv',labels)
 write(OUT/'source_hash_before_after.json',dict(before=before,after=after,all_equal=True,prior_R05F_artifacts_checked=len(prior),prior_R05F_protected_sources_anchors_configs_checked=len(oldprotected),original_images_checked=len(verified),annotation_members_original_coordinates_checked=len(labels),seed_unchanged=True,native_frozen_after_scoring=True,production_unchanged=True))
 write(OUT/'runtime_environment.json',dict(cpu=read(OUT/'baseline_manifest.json')['cpu'],platform=platform.platform(),python=platform.python_version(),numpy=np.__version__,opencv_python_io=cv2.__version__,opencv_native='4.4.0',pillow=PIL.__version__,matplotlib=matplotlib.__version__,compiler='MSVC v142 x64 /O2 /fp:precise /utf-8',opencv_thread_setting=4,actual_tracker='scalar local sampler',i7='NOT_VERIFIED',memory_peak='NOT_VERIFIED'))
 # Preserve the initial evaluation-lock hash and identify the additional offline metric revision.
 el=read(OUT/'offline_evaluation_lock.json');el.pop('first_label_read_in_this_round',None);el['detector_frozen_before_label_scoring']=True;el['final_evaluation_source_sha256']=sha(ROOT/'research/uctt_r05g/evaluate.py');el['additional_precision_audit']='experiments/additional_metric_scope.json';write(OUT/'offline_evaluation_lock.json',el)
 patch=[];sources={}
 for p in sorted((ROOT/'research/uctt_r05g').glob('*')):
  if not p.is_file():continue
  rel=str(p.relative_to(ROOT)).replace('\\','/');sources[rel]=sha(p);shutil.copy2(p,OUT/'source_snapshot'/p.name)
  if p.suffix in ['.py','.hpp','.cpp','.txt','.md']:patch.extend(difflib.unified_diff([],p.read_text(encoding='utf8').splitlines(True),fromfile='/dev/null',tofile=rel))
 (OUT/'code_diff.patch').write_text(''.join(patch),encoding='utf8');write(OUT/'research_source_hashes.json',sources)
 section='''## R05G：横截面逐步机制通过，归属/终止与首次锁定仍失败

隔离实现位于 `research/uctt_r05g/`，结果 `output/runs/uctt_r05g_20261112_r01/`。真实C++/OpenCV方向横截面、最近当前观测方向拟合、最多3局部极值、有限束、显式缺失与重捕获已编译回放。G0身份/旧B0选帧复现通过，G1机制通过；G2实际归属/终止FAIL，G3首次锁定FAIL；G4参考与可信历史导航NOT_IMPLEMENTED。G5全回放/证据交付完成，不代表准确率通过或可部署。

四开发组1565帧×4自动变体=6260次调用；80选帧76 VISIBLE+4 UNCERTAIN。独立当前原图短种子E0与AUTO严格分离，标签只在冻结后离线比较。E0贪心/束暂定端点10px为12/76、14/76；束人工路径覆盖均值98.56%，但可见轨迹精度均值63.98%，大量经过真实尖端后继续追纹理。AUTO贪心/束暂定10px为10/76、9/76；强观测消融29/76但开发组H弱末端丢失，不能按这一列升级。正式observed全部0、trusted_history为空，这是功能未通过的守卫，不是全拒绝安全成功。

开发组H78原两列弱片段在AUTO束第123/124步附近接入，暂定端点误差6.22px；GROUP_A504 AUTO贪心1.73px而束523.11px；CT2/395束401.42px。CT3全136帧AUTO无起点，选帧最长合格起源连续性≤2未达3；诊断轨迹又有末端过冲，正回归守卫失败。合成34项31通过，连贯旧划痕误锁/平行划痕束误接仍在，参考辨别未实现；原R03错首锁继续失败。

AUTO束原生P50/P95=6.170/17.331ms，>50ms为0；但353/1565搜索不完整且192无起点，不能声称完整检测已达标。完整debug导出P95约69.19ms，I/O解码哈希约183.55ms，不能混成内核时间。i7/内存峰值NOT_VERIFIED。全1565帧4695对消融起源逐字段一致；640详细trace、672948个依赖截面核验通过。AUTO贪心首轮最多3起点，此后宽1；严格单种子宽1对照是E0。

交付1565张逐帧局部图、80详细卡、9哨兵放大/截面响应、原像素弱裂纹证据、完整视频与慢速证据视频、逐帧图ZIP。生产/配置/原图/标签/旧468件R05F产物未改。验证组C/三点弯本轮新图像/标注读取0，排除组X排除。下一步优先独立起源身份、保留早期停止候选与后续探索的竞争；不扩大候选/预算、不用GT选阈值或历史最长端点兜底。读development_report、failure_first_divergence、origin_candidate_audit与group_h78_short_fragment_audit后再开发。

'''
 state=ROOT/'docs/CURRENT_STATE.md';s=state.read_text(encoding='utf8');title='# 当前开发状态\n\n'
 if '## R05G：横截面逐步机制通过' not in s:s=s.replace(title,title+section,1);state.write_text(s,encoding='utf8')
 readme=ROOT/'README.md';s=readme.read_text(encoding='utf8');new='最新R05G见 [开发报告](output/runs/uctt_r05g_20261112_r01/development_report.md)、[1565帧局部对比](output/runs/uctt_r05g_20261112_r01/galleries/all_frames.html)、[80选帧图册](output/runs/uctt_r05g_20261112_r01/galleries/index.html)、[完整序列视频](output/runs/uctt_r05g_20261112_r01/R05G_All_Development_Frames.mp4) 和 [慢速证据视频](output/runs/uctt_r05g_20261112_r01/R05G_Selected_Evidence.mp4)。G1真实横截面机制通过，G2归属/终止与G3错首锁失败；诊断束暂定端点10px14/76，AUTO9/76，正式observed未启用。原生P95约17.33ms但353帧搜索不完整，不能认定部署达标。生产未改，验证组未准入。\n\n'
 if '最新R05G见' not in s:s=s.replace('最新一轮见 [R05F','上一轮见 [R05F',1).replace('# CodexCrack\n\n','# CodexCrack\n\n'+new,1);readme.write_text(s,encoding='utf8')
 agents=ROOT/'AGENTS.md';s=agents.read_text(encoding='utf8');new='- Latest round is R05G isolated native research in `research/uctt_r05g/`, output `output/runs/uctt_r05g_20261112_r01/`. G0/G1 PASS; G2 actual attribution/termination FAIL, G3 first-lock safety FAIL, reference/history navigation NOT_IMPLEMENTED; G5 replay/evidence complete only. Full1565 x4 AUTO calls;80 diagnostic selections,76 VISIBLE/4 UNCERTAIN. E0 greedy/beam tentative10=12/14 of76; beam path coverage98.56% but path precision63.98% from overrun. AUTO tentative10=10/9; observed0 is an isolation guard, NOT safety success. group_h78 two-column evidence joins beam steps123/124, tentative error6.22px. GROUP_A504 AUTO beam523.11px versus greedy1.73px; CT2/395 beam401.42px; CT3 all136 AUTO seed_missing and diagnostic overrun. Native beam P95=17.331ms but353/1565 incomplete; debug exportP95=69.19ms separate. AUTO greedy bootstrap may expand3 origin seeds once before width1; strict width1 comparison is single-seed E0. Original R03 coherent_wrong_first_lock still FAIL. No production/config/label/original/old-result modifications, no validation-only images/labels, group_x excluded. Delivered1565 local comparison JPGs,80 detailed cards,9 sentinel zooms/profiles and2 videos. Next work: independent origin identity and credible stopping-candidate competition before trusting distal explorations; do not enlarge beam/budget or fit thresholds to GT. Read report and first-divergence/origin/weak-fragment audits.\n\n'
 if '- Latest round is R05G' not in s:s=s.replace('- Latest work is R05F','- Previous round is R05F',1).replace('Continue within S1 with a separate weak-fragment evidence representation and shared structural control, not per-case thresholds, label fitting, or all-fallback safety claims.','The R05F-era recommendation was separate weak-fragment representation; it is superseded by the R05G evidence above. Retain prohibitions on per-case thresholds, label fitting and all-fallback safety claims.').replace('## Current algorithm and evidence\n\n','## Current algorithm and evidence\n\n'+new,1);agents.write_text(s,encoding='utf8')
 write(OUT/'final_integrity.json',dict(status='PASS',production_unchanged=True,protected_files=len(before),R05F_sealed_artifacts_unchanged=len(prior),historical_sources_anchors_configs_unchanged=len(oldprotected),original_images_unchanged=1565,annotation_zip_unchanged=True,research_core_unchanged_since_E1=True,seed_file_unchanged=True,all_outputs_inside_output=True,policy='DEVELOPMENT4 only; validation and excluded members never parsed',updated_project_navigation=['AGENTS.md','README.md','docs/CURRENT_STATE.md']))
 excluded={'artifact_manifest.json','logs/seal.log'};files={str(p.relative_to(OUT)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in OUT.rglob('*') if p.is_file() and str(p.relative_to(OUT)).replace('\\','/') not in excluded};write(OUT/'artifact_manifest.json',dict(files=files,excluded=sorted(excluded),status='SEALED',run_id=OUT.name))
 print('SEALED',len(files),'artifacts; production,originals,labels,prior results unchanged',flush=True)
if __name__=='__main__':main()
