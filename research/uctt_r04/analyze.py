import csv,json,collections,subprocess,math,shutil,struct
import numpy as np
from common import *
def read(name):return list(csv.DictReader((OUT/name).open(encoding='utf-8-sig')))
def stats(values):return dict(zip(['P50','P95','P99','max'],map(float,np.percentile(values,[50,95,99,100])))) if values else dict.fromkeys(['P50','P95','P99','max'])
def yes(v):return str(v) in ['True','1','true']
def table(rows,keys):
 def val(x):return f'{x:.3f}' if isinstance(x,float) else str(x if x is not None else 'N/A')
 return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+'\n'.join('| '+' | '.join(val(r.get(k)) for k in keys)+' |' for r in rows)
def md(name,s):(OUT/name).write_text(s,encoding='utf8')
def main():
 gate0=json.loads((OUT/'gate0_shadow.json').read_text());assert gate0['R03_mismatches']==gate0['shadow_mismatches']==0
 with (OUT/'candidate_paths.jsonl').open(encoding='utf8') as f:original=next(r for r in map(json.loads,f) if r['dataset_id']=='group_a' and r['variant_id']=='measured' and r['frame_id']==241)
 im=api.read(original['input']['image_path']);(OUT/'fixture_image.bin').write_bytes(struct.pack('<ii',im.shape[1],im.shape[0])+im.tobytes())
 pref=original['sidecar']['prefix'];root=original['sidecar']['prefix_root_supported_proxy'];(OUT/'fixture_prefix.txt').write_text(f'{int(root)} {len(pref)}\n'+'\n'.join(f'{x} {y}' for x,y in pref),encoding='ascii')
 fixture=subprocess.run([str(BUILD/'Release/R04Fixture.exe'),str(OUT/'fixture_image.bin'),str(R03/'fault_seed.txt'),str(OUT/'fixture_prefix.txt')],capture_output=True,text=True);assert fixture.returncode==0,fixture.stderr
 (OUT/'original_fixture_r04.csv').write_text(fixture.stdout,encoding='utf-8-sig')
 exact_fixture=list(csv.DictReader(fixture.stdout.splitlines()))
 write('original_fixture_provenance.json',dict(image_sha256=original['image_sha256'],fixture_sha256=sha(R03/'fault_seed.txt'),prefix_source='B1 main-path trace BEFORE measureTip, original GROUP_A frame 241',shift=[-30,-30],real_physical_GT=False,rows=exact_fixture))
 result=subprocess.run([str(BUILD/'Release/R04Contracts.exe'),str(OUT/'synthetic')],capture_output=True,text=True);assert result.returncode==0,result.stderr
 (OUT/'lock_injection_results.csv').write_text(result.stdout,encoding='utf-8-sig')
 faults=read('lock_injection_results.csv');injection=[]
 for method in ['1','2']:
  rr=[r for r in faults if r['method']==method];pos=[r for r in rr if yes(r['expected_observed'])];neg=[r for r in rr if r['label']=='construct_distractor'];wrong=[r for r in rr if r['case_id']=='coherent_wrong_first_lock']
  injection.append(dict(method=method,N=len(rr),constructed_visible_positives=len(pos),true_candidate_retained=sum(yes(r['observed']) for r in pos),constructed_negatives=len(neg),false_candidate_admission=sum(yes(r['observed']) for r in neg),wrong_first_lock=sum(yes(r['history_written']) for r in wrong),contract_failures=sum(not yes(r['pass']) for r in rr),failed_cases=[r['case_id'] for r in rr if not yes(r['pass'])]))
 save('injection_summary.csv',injection)
 write('synthetic_provenance.json',dict(label_source='Analytic line drawings in contracts.cpp; labels evaluated only by harness, not audit/State. Synthetic labels are NOT real physical GT.',prefix_source='Test-only image row search in coarse source corridor, without reading labels; real replay instead uses existing main-path prefix. Not an end-to-end synthetic detector validation.',parameter_revisions=0,images={p.name:sha(p) for p in (OUT/'synthetic').glob('*.png')},limitations='Known construction proves which injected object is intended, not whether physically indistinguishable joined structures can be classified from grayscale alone. Original R03 fixture reproduced separately, not relabeled as physical truth.'))
 rows=read('comparison_results.csv');groups=collections.defaultdict(list)
 for r in rows:groups[r['dataset_id'],r['variant_id'],r['version']].append(r)
 metrics=[];paired=[];div=[];reasons=collections.Counter()
 for (g,v,version),rr in groups.items():
  bb=groups[g,v,'B0_R02_A0']
  for subset in ['chronological_prefix','selected_review']:
   pairs=[(a,b) for a,b in zip(bb,rr) if subset=='chronological_prefix' or yes(a['selected_for_review'])]
   valid=[(a,b) for a,b in pairs if yes(a['visual_confirmed']) and yes(b['visual_confirmed'])];ds=[math.hypot(float(a['tip_x'])-float(b['tip_x']),float(a['tip_y'])-float(b['tip_y'])) for a,b in valid]
   n=len(pairs);c0=sum(yes(a['visual_confirmed']) for a,b in pairs);cn=sum(yes(b['visual_confirmed']) for a,b in pairs)
   metrics.append(dict(dataset_id=g,variant_id=v,version=version,subset=subset,N_total=n,N_executable=n,N_observed_base=c0,N_observed_new=cn,N_both_observed=len(valid),observed_rate_base=c0/n,observed_rate_new=cn/n,coverage_delta_pp=100*(cn-c0)/n,status_disagreement_count=sum(a['visual_confirmed']!=b['visual_confirmed'] for a,b in pairs),source_transition_count=sum(pairs[i][1]['source_type']!=pairs[i-1][1]['source_type'] for i in range(1,n)),recovery_count=sum(yes(pairs[i][1]['visual_confirmed']) and not yes(pairs[i-1][1]['visual_confirmed']) for i in range(1,n)),roi_cutoff_count=sum(yes(b['roi_cutoff']) for a,b in pairs),false_lock_count=None,visible_tip_error_px=None,early_stop_px=None,overshoot_px=None,GT='GT_UNAVAILABLE',**stats(ds)))
  if v=='measured':continue
  control=groups[g,'measured',version];both=[(a,b) for a,b in zip(control,rr) if yes(a['visual_confirmed']) and yes(b['visual_confirmed'])];ds=[math.hypot(float(a['tip_x'])-float(b['tip_x']),float(a['tip_y'])-float(b['tip_y'])) for a,b in both];c0=sum(yes(a['visual_confirmed']) for a in control)
  paired.append(dict(dataset_id=g,variant_id=v,version=version,N=len(rr),C0=c0,Cv=sum(yes(a['visual_confirmed']) for a in rr),Cpair=len(both),Cpair_C0=len(both)/c0 if c0 else None,perturbation_class='stress_10pct' if '10pct' in v else 'normal_2_or_5pct',**stats(ds),worst_frame_id=int(both[int(np.argmax(ds))][0]['frame_id']) if ds else None))
  for kind in ['status_or_coordinate','paired_tip_gt2px']:
   found=None
   for a,b in zip(control,rr):
    mismatch=a['visual_confirmed']!=b['visual_confirmed'];distance=math.hypot(float(a['tip_x'])-float(b['tip_x']),float(a['tip_y'])-float(b['tip_y'])) if yes(a['visual_confirmed']) and yes(b['visual_confirmed']) else None
    if ((mismatch or (distance is not None and distance>2)) if kind=='status_or_coordinate' else (distance is not None and distance>2)):
     found=dict(dataset_id=g,variant_id=v,version=version,kind=kind,frame_id=int(a['frame_id']),paired_distance_px=distance,control_confirmed=a['visual_confirmed'],variant_confirmed=b['visual_confirmed'],source_location='src/cpp/a/roi_tip.inc:146,224; research/uctt_r04/audit.hpp',causality='NOT_PROVEN: E2 gated by attribution/coverage failure');break
   div.append(found or dict(dataset_id=g,variant_id=v,version=version,kind=kind,frame_id=None,causality='NO_MATCHING_DIVERGENCE_WITHIN_EXECUTED_WINDOW'))
 save('metric_summary.csv',metrics);save('perturbation_summary.csv',paired);save('first_divergence_r04.csv',div)
 ce=read('candidate_evidence.csv');save('tip_stop_candidates.csv',[dict(r,new_stop_candidate=False,E3_status='BLOCKED_BY_E1_GATE',meaning='Existing examined DP endpoint; raw-cross-section diagnostics only, NOT E3 new stopping proposal') for r in ce if r['candidate_id']!='-1'])
 # No invented factorial measurements. Record why each requested intervention is gated.
 save('factorial_roi_reference_registration.csv',[dict(dataset_id=g,factor=f,status='BLOCKED_BY_E1_GATE',G=None,M=None,T=None,P=None,tip_difference_px=None,evidence_map_hash=None,reason='E1 source safety / coverage not established. No swaps executed. Trace maps archived in original-coordinate ROI + oriented-map domains.',minimum_instrumentation='Export score/current/registered/prior plus original baseline mask; generated trace now provides these, see map_manifest.json') for g in VARIANTS for f in ['F0','F1','F2','F3','F4','F5']])
 pp=read('performance_scopes.csv');pg=collections.defaultdict(list)
 for r in pp:
  for kind,key in [('dataset',r['dataset_id']),('resolution',r['image_w']+'x'+r['image_h']),('D2_source',r['B2_source'])]:pg[kind,key].append(r)
 ps=[]
 for (kind,key),rr in pg.items():
  for version,col in [('B0_R02_A0','B0_api_ms'),('B1_DIAGNOSTIC','B1_api_ms')]:
   xs=[float(r[col]) for r in rr];ps.append(dict(kind=kind,name=key,version=version,N=len(xs),**stats(xs),timeout_50ms_ratio=sum(x>50 for x in xs)/len(xs)))
 save('performance_summary.csv',ps)
 scopekeys=['main_motion_ms','tip_motion_ms','main_other_ms','local_reference_ms','distal_path_ms','tip_other_and_trace_ms','new_audit_ms','json_and_api_residual_ms'];total=sum(float(r['B1_api_ms']) for r in pp)
 scopes=[dict(scope=k,mean_ms=float(np.mean([float(r[k]) for r in pp])),share=sum(float(r[k]) for r in pp)/total) for k in scopekeys];save('performance_attribution.csv',scopes)
 d2=[r for r in metrics if r['version']=='B2_D2_PREFIX' and r['subset']=='chronological_prefix'];d1=[r for r in metrics if r['version']=='B2_D1_STRUCTURE' and r['subset']=='chronological_prefix']
 c0=sum(r['N_observed_base'] for r in d2);c2=sum(r['N_observed_new'] for r in d2);c1=sum(r['N_observed_new'] for r in d1);n=sum(r['N_total'] for r in d2);delta=100*(c2-c0)/n
 evidence=dict(R04_RESULT='PARTIAL',replace_production=False,N_cases=n,N_unique_frames=gate0['unique_group_frames'],selected_cases=gate0['selected_cases'],N_base_observed=c0,N_D1_observed=c1,N_D2_observed=c2,D2_coverage_delta_pp=delta,synthetic=injection,real_human_label_count=0,GT='GT_UNAVAILABLE',E2='BLOCKED_BY_E1_GATE',E3='BLOCKED_BY_E1_GATE',B3_B4_B5='NOT_EXECUTED',T2_B_REAL='BLOCKED',full_R03_fraction=n/1428,full_R02_fraction=n/15808,full_R02_variants='11 of 112 initializations, truncated windows',video='R04_results.mp4')
 write('result_summary.json',evidence)
 evidence['exact_R03_fixture']=exact_fixture
 write('result_summary.json',evidence)
 accept=[dict(gate='Gate0_reproduction',status='PASS',denominator=n,evidence='baseline_checks.csv / r03_fault_reproduction.csv',reason='Raw JSON and all original 16 injection outcomes reproduced'),dict(gate='B1_output_equivalence',status='PASS',denominator=n,evidence='baseline_checks.csv',reason='Timing excluded; paths/status/coordinates equal'),dict(gate='Gate_A_attribution',status='FAIL' if injection[1]['false_candidate_admission'] else 'NOT_VERIFIED',denominator=injection[1]['N'],evidence='injection_summary.csv / lock_injection_results.csv',reason='Wrong-first detached candidate blocked in constructed component test; broader source identity not certified. Real manually labeled positives=0.'),dict(gate='Gate_B_coverage',status='FAIL' if delta < -5 else 'NOT_VERIFIED',denominator=n,evidence='metric_summary.csv',reason=f'D2 coverage delta {delta:.3f} pp; allowed regression warning is -5 pp'),dict(gate='Gate_C_termination',status='BLOCKED',denominator=0,evidence='tip_stop_candidates.csv',reason='E1 not passed; no independently labeled real terminal GT, E3 not enabled'),dict(gate='Gate_D_initialization',status='FAIL',denominator=n,evidence='perturbation_summary.csv',reason='Baseline sensitivities reproduced; low B2 Cpair is not a stability pass; E2 not run'),dict(gate='Gate_E_CPU',status='FAIL' if any(float(r['B0_api_ms'])>50 for r in pp) else 'PASS',denominator=len(pp),evidence='performance_summary.csv',reason='Full native API timings, not video playback; no B5 claim'),dict(gate='T2_B_REAL',status='BLOCKED',denominator=0,evidence='development_report.md',reason='No real multi-initial external tracker trajectories'),dict(gate='NO_PRODUCTION_CHANGE',status='PASS',denominator=462,evidence='frozen_manifest_r04.json',reason='Frozen hashes reverified during final validation')]
 save('acceptance_matrix.csv',accept)
 save('version_status.csv',[dict(version=v,status=s,meaning=m) for v,s,m in [('B0_R02_A0','EXECUTED','Unchanged native baseline'),('B1_DIAGNOSTIC','EXECUTED','Same output, examined branches and raw transverse evidence'),('B2_D1_STRUCTURE','EXECUTED_SIDECAR','Structure-only component ablation; cannot establish ownership'),('B2_D2_PREFIX','EXECUTED_SIDECAR','Root-supported main path proxy + independent raw sections; no temporal proximity rejection'),('B3_STOP_ONLY','BLOCKED','E1 failed; no newly generated stopping candidates'),('B4_FUSED','BLOCKED','E1/E3 prerequisites unmet'),('B5_LOCAL_COMPUTE','BLOCKED','No verified B4 behavior to preserve')]])
 md('dependency_trace.md','''# Actual dependency trace (production source unchanged)

| Entry | Initial/current anchor dependency | Coordinate/evidence flow |
|---|---|---|
| CrackV4.cpp:509 Detector constructor | Initial P1/P2 validate, midpoint origin, spacing, ordered normal forward | Original image coordinates; brightness side is diagnostic |
| :695 choosePatches / :1102 locateRoot | Initial geometry chooses reference textures/root search | Fixed reference patches; root is an image-derived proxy, not physical GT |
| :911 motion | Current P1/P2 can provide coarse main-path motion prior | Main R,t, distinct from tip motion |
| :748 estimateTipMotion | Immutable reference tip patches, no current-anchor direct ROI | Tip-specific rigid R,t; failure removes endpoint evidence |
| :1205 tile / :1358 seed / :1654 measure | Reference masks, image responses, earlier geometry/causal history | Independent main path; entrance at :1551 supports root proxy; line/terminal evidence can still be wrong |
| roi_tip.inc:8 tipWindow / :146 measureTip | Initial spacing, tipCenter/tipDirection from fixed reference geometry | Original ROI clipped at image boundary; quarter-turn oriented local arrays |
| roi_tip.inc:25 localReference | ROI grid tiles; center-origin rounded drift; reference baseline_mask | Local patch matching; aligned reference/prior in ROI domain, not a dense global rigid warp |
| roi_tip.inc:175–198 response loop | Reference comparison and prior mask | Current/raw-reference Gaussian response, dark-line assumptions remain in B0 |
| roi_tip.inc:68 distalLine | Local score/intensity, no independent root identity | DP can start in any column; top peaks, short gaps, tail and 9-sample ahead audit |
| roi_tip.inc:224 | Nonempty accepted local path sets tip/has/path_valid/terminal together | Correlated flags; root/full length agreement is checked separately, not required for tip |
| CrackV4.cpp:2245 Process | Main process then measureTip, raw output | Legacy output/history unchanged; diagnostic never drives ROI |

Instrumentation generated by research/uctt_r04/prepare.py stores main r.path and r.root BEFORE measureTip overwrites them; records at most five branches actually examined after existing tail/material checks. It does not continue a DP search that B0 would have stopped, and does not claim an exhaustive top-K pool. All branch paths are converted with the exact existing quarter-turn inverse + ROI offset. Map arrays are oriented ROI; baseline_mask is original full image. map_manifest.json stores shapes/dtypes/SHA256 and ROI. No F1–F5 interchange was executed: compatible coordinate export is preparatory instrumentation, not causal proof.

E1 D1 reads current original-resolution transverse samples on each candidate; D2 additionally requires raw-supported main-prefix/root proxy and overlap/tangent consistency. The main prefix is independently computed from the ROI-tip branch, but both image pipelines and initial geometry remain correlated. This is a proxy for source continuity, not independently verified physical ownership. No last-tip proximity gate, frame-number rule, specimen-specific threshold or future-frame input is used. Width, noise and polarity are measured in original pixels; thresholds are frozen globally in audit.hpp, with zero result-driven parameter revisions.
''')
 md('candidate_protocol.md','''# Diagnostic protocol and limits

Candidate -1 is selected B0 path. Nonnegative IDs are examined old DP branches; no new stop proposal is generated. Full original-coordinate paths and pre-overwrite main prefix are in candidate_paths.jsonl. score/current/registered/prior hashes and selected archives are in map_manifest.json/maps. Pixel sampling: tangent from +/-4 path samples; center average at normal offsets -1,0,+1; flank averages at +/-4,+/-6; noise from +/-6 versus +/-7. Both bright and dark polarities are kept. Maximum 256 path samples, so support is a sampled fraction and gap length an approximation. Noise-relative support threshold=max(4 gray levels,2*outer-flank noise); required fraction .7. Width estimated by half-contrast crossing within +/-6 px. No higher real-image accuracy follows from these choices.

D1: raw structural support and no 10 px terminal boundary risk. D2: D1 + independently raw-supported main path with existing root flag; at least half of first 16 candidate samples within max(3,width) of prefix, tangent dot>=.5, unsupported gap<=max(3,2*width). Prefix validity is still a proxy; no confident physical-source assertion is made. S_before is raw last-16-path support; S_ahead is 12 tangent-forward raw samples; S_terminal=before-ahead is NOT independent evidence. S_compete/S_delta are null, reference_usable null; no fabricated six-way fusion. Endpoint acceptance in B2 remains the original terminal flag; new stopping audit is gated off.

State output is diagnostic JSON: observed only on selected B0 tip + corresponding method guard + finite valid image motion. Predicted uses last accepted point in reference coordinates with current tip transform and valid=false; fallback uses bounded search center and valid=false. Neither updates history. All maps are cloned for diagnostics; buffers from R04Map remain borrowed until next process/reset/destroy, consumed immediately by a serial caller. Cached R04Observe is idempotent per detector frame. Legacy exports/layout/length definition are untouched. No production placeholder coordinate is inserted.
''')
 md('performance_report.md',f'''# Full native API performance

{len(pp)} non-reference calls per version; cached GetBaseline excluded, initialization separate. B0 wall includes full original C API. B1 wall includes same detector plus map copies, both E1 methods, branch audits, state/JSON packing, in one R04Process call. B2 methods are jointly evaluated within B1; no fabricated standalone B2/B3/B4/B5 timings. B1 is a diagnostic upper-cost implementation, not optimized deployment. Threads=4 native, AMD Ryzen 9 7950X; OpenCV4.4/MSVC v142 /O2 /fp:precise. Same decoded frame fed in fixed B0 then B1 order; OS/file cache warms during sequential replay, no forced cache flush. Order/cache bias not isolated. Disk decode/hash/map compression/video generation are outside API timers. Video render runs later. SIMD uses the installed OpenCV dispatch; runtime feature toggles unchanged, exact dispatched instruction set NOT_INSTRUMENTED.

Counters reset each frame; direct values read. Only the listed disjoint scope components are summed; old nested timers are not. Residual includes serialization/API overhead and clock measurement error. No 50 ms guarantee. State breakdown groups B1 timings by D2 source, not a newly implemented recovery search.

'''+table(ps,['kind','name','version','N','P50','P95','P99','max','timeout_50ms_ratio'])+'\n\n'+table(scopes,['scope','mean_ms','share']))
 md('development_report.md',f'''# R04 路径归属实验：保留诊断，不替换生产算法

1. **R04_RESULT=PARTIAL；替换 R02 生产算法=NO。** 实际完成冻结、R03原16项注入重现、B0/B1回放、两种E1原生候选验证、真实对照与性能。生产源码/DLL未覆盖。E2、E3、B3–B5因E1证据/覆盖门槛未通过而阻断，不宣称全任务验收通过。用户另要求的结果视频无论成败均交付为 R04_results.mp4。

2. **Q1 首锁根因：** roi_tip.inc:68的局部DP可在任意列起始；:224将非空局部路径同时置为tip/path_valid/terminal，缺少独立主裂纹归属验证。R03原16项结果完全复现，其中自洽错首锁仍写历史。R04 D1用原图横断面复核，D2增加独立主路径/root代理连接。构造标签不送入审计算法，真实人工标签数为0。D2代理仍不是物理归属证明，不能把“有前缀”宣称为真实裂纹。**Q2 停止位置：** 已导出原算法实际检查过的至多5个端点分支和前后截面诊断；E3新停止候选/融合未启用，改善提前停止或过识别=NOT_PROVEN。**Q3 初始化敏感性：** 不同初始化的首分歧可复现，ROI/mask/配准具体因果贡献=NOT_PROVEN。中间数组已导出；F1–F5未执行，不能用“先变ROI”替代因果结论。

3. **结果数字：** 本轮{n}个初始化/帧案例、{gate0['unique_group_frames']}个组帧，{gate0['selected_cases']}个预选审核案例；B0/B1输出差异0/{n}，与R03存档差异0/{n}。B0视觉确认{c0}/{n}；D1={c1}/{n}；D2={c2}/{n}，D2总覆盖变化{delta:.3f}个百分点（预警线-5）。所有“距离”仅是共同确认输出差，非物理误差。完整R03窗口覆盖{n/1428:.2%}，完整R02 15808案例覆盖{n/15808:.2%}；仅11/112个初始化且窗口截短。GROUP_A确认不足，不能以多数未确认计0像素。实验阶段失败后未扩大矩阵。

'''+table(injection,['method','N','constructed_visible_positives','true_candidate_retained','constructed_negatives','false_candidate_admission','wrong_first_lock','contract_failures'])+f'''

注入来源：24种场景，前16种映射R03合同语义；与旧fixture是不同图像构造，旧fixture另行原样复现。表内正负标签仅是synthetic construction，不是实际试件人工GT。完整逐例见lock_injection_results.csv。额外使用同一GROUP_A原图、同一R03路径及(-30,-30)平移做了新方法复核：D1/D2均保留原候选、拒绝平移干扰，后者原图支持率为0；见original_fixture_r04.csv与provenance。这个结果证明新增像素复核能拦住该具体候选注入，并不证明原候选是物理真裂纹。真实可标注样本清单已由frame_manifest和视频提供，但没有伪造双人标注。无独立HOLDOUT，无真实T2-B轨迹；原算法仍主要支持暗线，D1/D2能采样两极性不等于整条算法已支持亮裂纹。

4. **保留/回滚：** 保留旁路候选、原图截面、独立前缀和map hash导出，帮助后续真正隔离G/M/T/P；保留可复跑的失败反例。D1不能单独证明路径身份；D2若大幅降低覆盖或接受相连伪影，均不能推广为生产确认门槛。B2只存在sidecar，不写回原Detector，不控制ROI。未上线步进ROI，未修改长度、ABI或生产DLL。没有用旧尖端附近约束制造稳定。

5. **下一轮最少任务：** (a) 对视频中的首分歧和独立前缀失败制作双人复核标签，真/假/不可辨至少分开，作为归属验证的阻断输入；(b) 改进前缀的证据可用性和歧义处理，在同一构造反例上既保真又拒假，并以真实覆盖下降≤5pp作为预警，未通过则继续阻断E3；(c) E1过关后，用已导出的统一原图域数组逐项交换G/M/T，先定位直接因果再产生新的终止候选。当前不进行无根因参数扫描或B5降采样提速。

## 逐组覆盖（完整执行前缀）

'''+table(d2,['dataset_id','variant_id','N_total','N_observed_base','N_observed_new','coverage_delta_pp'])+'\n\n## 初始化扰动（共同确认，非GT误差）\n\n'+table(paired,['dataset_id','variant_id','version','N','C0','Cv','Cpair','P95','max','worst_frame_id'])+'\n\n## Gate结论\n\n'+table(accept,['gate','status','denominator','reason']))
 md('reproduction_commands.md',r'''# Reproduce in PowerShell from CodexCrack

Use new OUT/BUILD/GEN paths in common.py and matching CMake output source path for a new run. Never overwrite sealed evidence. Active code lives under research/uctt_r04; generated experiment copies derive from active production, never execute sealed snapshots.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Resolve-Path output/cache/tmp).Path
$env:TMP=$env:TEMP
& D:/ProgramData/anaconda3/python.exe research/uctt_r04/prepare.py
& D:/CMake/bin/cmake.exe -S research/uctt_r04 -B output/build/uctt_r04 -G 'Visual Studio 17 2022' -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build/uctt_r04 --config Release -- /m:1 /nodeReuse:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r04/pilot.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r04/analyze.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r04/video.py
./run.ps1 check
& D:/ProgramData/anaconda3/python.exe research/uctt_r04/validate.py
```

R03Reproduce exit2 is the expected reproduced safety failure, not a crashed test. R04Contracts returns0 for completed evaluation; its CSV pass/false admission columns, not exit code, determine safety. Neither failure is silently reclassified as a production pass.
''')
 md('README.md','# R04 stopped research experiment\n\nSee [development_report.md](development_report.md), [result video](R04_results.mp4), [gallery](failure_gallery.html), [acceptance matrix](acceptance_matrix.csv). No production change. New termination/ROI/optimization stages are blocked.\n')
 print(json.dumps(evidence,ensure_ascii=False))
if __name__=='__main__':main()
