from common_ap import *
import platform,subprocess,shutil
identity=guard()
for d in ['00_protocol','01_audit','02_source/aprime_cpp','02_source/tests','03_reference_validity','04_candidate_evidence','05_locked_test','06_real_regression','07_performance/native','08_media/key_cases','09_reports']:(O/d).mkdir(parents=True,exist_ok=True)
assert not (O/'00_protocol/baseline_identity_and_hashes.json').exists(),'New run required'
identity['round_created_utc']=utc();identity['python']=sys.version;identity['opencv_python']=cv2.__version__;identity['platform']=platform.platform()
identity['task_document_sha256']=sha(ROOT/'docs/specifications/CrackV4_Aprime_ReferenceDeformed_TraditionalTip_Agent_Prompt.md')
identity['api_header_sha256']={str(p):sha(p)for p in (ROOT/'baseline/frozen_a/src').glob('*.h')}
save(O/'00_protocol/baseline_identity_and_hashes.json',identity)
shutil.copy2(ROOT/'docs/specifications/CrackV4_Aprime_ReferenceDeformed_TraditionalTip_Agent_Prompt.md',O/'00_protocol/task_document.md')
rr=rows(ROOT/'data/inputs/six_groups_manifest.csv')
csvout(O/'00_protocol/inputs_manifest.csv',rr)
csvout(O/'00_protocol/data_roles_and_leakage_controls.csv',[dict(group=g,role='RETIRED_EXPOSED_HISTORY_ONLY'if g=='group_x'else'EXPOSED_DIAGNOSTIC_NOT_TUNING',frames=sum(r['dataset_alias']==g for r in rr),physical_GT='N/A')for g in dict.fromkeys(r['dataset_alias']for r in rr)])
write(O/'00_protocol/task_scope_and_exclusions.md','''# A′ scope
Production A, its ABI, flags3572, SHADOW policy1, terminal validation1, refine=true, four native threads and old outputs remain unchanged. All original six groups are exposed diagnostics; 排除组X is retired history, 三点弯 is exposed validation, neither tunes parameters. No real physical endpoint GT is available. No future frames, phase assumptions, monotonic growth, specimen labels, DIC, flow, DL, full-image second detector.
Stage1 is adaptive sparse reference comparability, before endpoint modifications. Current-image morphology and reference ownership are distinct. The endpoint pool always retains the exact A double tip. Output projection is (tip-current anchor midpoint) dot ordered right normal; invalid anchor order fails. Unknown is not no-crack. No mm calibration is assumed.
''')
write(O/'00_protocol/preregistered_metrics_and_gates.md','''# Pre-DEV protocol, 2026-11-05
Gate0: all3035 fresh native states, V2 coordinates/valid bits/lengths and float64 full paths must exactly match the prior frozen replay. Original DLL/source/header hashes must remain fixed. Diagnostic tracing3573 is separate and compared to3572, never enabled in formal baseline.
Gate1: adaptive material feature patches outside dilated A path; no fixed24 macro grid. Cache reference features. Choose simplest sparse NCC with a gradient-NCC engineering alternative. FIT/HOLDOUT separated by image-space blocks, no patch used for both. At least6 FIT and4 HOLDOUT, robust translation, holdout residual P90<=1px, valid spatial polygon covers each audited candidate's fixed window. Photometry on FIT, holdout independently tests robust residual/noise. No relaxation by specimen. Near-all-UNKNOWN is operationally defined BEFORE runs as joint local support<5% of non-reference frames or zero support in3 or more active groups. This is an information-availability stop, not an accuracy certificate. If failed, no automatic endpoint replacement, no new confirmatory TEST or production DLL. Independent controlled engineering/DEV failure tests and all real media still delivered.
Candidate ceiling K=12, always reserve one bitwise A tip. No candidate rule may privilege first reference transition. Stage2/3 only if gate1 passes; all prospective native stop instrumentation must be separate. Correct counts at<=8px, rejection penalty32px and confirmed error cap64px; observable positives, negatives and unobservables distinct. Cluster bootstrap unit independent case/shared-current pair,95% CI,10000 resamples seed2026110519. Safety: zero correct A revoked/changed wrong; zero>=160px catastrophic changes; weak/55/75/S counts no decrease; FP<=A; absolute correct count strictly>A; matched pairs both correct nonzero. No late TEST retuning.
Gate4: lock generator, detector, evaluator, limits and protocol BEFORE generating fresh independent-background TEST; seal all inputs and GT before one execution. Gate5 only after research gates: C++17/OpenCV4.4 independent artifacts, full Process+GetResultV2+CopyPath+all A′ modules+allocations<=66.67ms every frame. Python timings never native performance. Real physical MAE N/A. No clean new real holdout available.
ROI contract: candidate audit windows sample original pixels at1px, independent of search ROI; increasing search ROI with fixed candidates is distinct from rerunning search. No history extension with PHASE_UNKNOWN.
''')
write(O/'00_protocol/deviations_and_errata.md','No deviations at creation. Ordered gates may stop progression; unexecuted stages must be explicitly marked NOT_EXECUTED rather than populated with invented results.\n')
print('SETUP',O,flush=True)
