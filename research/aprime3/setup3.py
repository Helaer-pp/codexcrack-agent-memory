from common3 import *
import platform,zipfile
guard();records=[]
paths=[ROOT/'CrackV4_Aprime3_FailureDriven_Candidate_Reference_Research_Agent_Prompt.md',ROOT/'CrackV4_Aprime2_MultiStop_ValidatedReference_Agent_Prompt.md',
       OLD/'09_reports/development_report.md',OLD/'05_DEV/full_v3/failure_stages.csv',OLD/'05_DEV/full_v3/decision_predictions.jsonl',OLD/'index.html',
       ROOT/'output/aprime_20261105/run01/A_prime_source_results_reports.zip',ROOT/'archive/packages/C2_results_source_reports.zip',
       ROOT/'baseline/frozen_a/bin/CrackV4.dll',ROOT/'output/build/Release/CrackV4AP2Shadow.dll',ROOT/'output/build/Release/AP2DualBench.exe',
       * (ROOT/'research/aprime2').glob('*.py'),* (ROOT/'baseline/frozen_a/src').glob('*')]
for p in paths:
 if p.is_file():records.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size,role='FROZEN_OR_EXPOSED_INPUT',replayable=True))
csvout(RUN/'00_audit/input_manifest.csv',records)
save(RUN/'00_audit/environment.json',dict(python=sys.version,opencv_python=cv2.__version__,numpy=np.__version__,platform=platform.platform(),native_opencv='4.4.0',native_threads=4,gemini_md_available=any(ROOT.rglob('GEMINI.md'))))
fails=rows(OLD/'05_DEV/full_v3/failure_stages.csv');pred=rows(OLD/'05_DEV/full_v3/final_per_frame.csv')
stage=collections.Counter(r['stage'] for r in fails);cross=collections.Counter((r['stage'],r['family'],r['A_stop']) for r in fails)
assert len(fails)==67 and sum(r['observable']=='True' for r in pred)==432 and sum(r['Aprime2_correct']=='True' for r in pred)==365
csvout(RUN/'01_diagnosis/stage_family_stop.csv',[dict(stage=a,family=b,A_stop=c,n=n) for (a,b,c),n in cross.items()])
omit=[r for r in fails if r['stage']=='CANDIDATE_OMISSION_ON_REACHABLE_PATH']
summary=dict(failures=len(fails),observable=432,A_correct=sum(r['A_correct']=='True' for r in pred),research_correct=365,stages=stage,
    omissions=len(omit),path_distance_median=float(np.median([float(r['path_distance']) for r in omit])),oracle_error_median=float(np.median([float(r['oracle_error']) for r in omit])),
    candidate_count_median=float(np.median([int(r['candidate_count']) for r in omit])),omission_temporal_pending=sum(r['A_stop']=='temporal_pending' for r in omit))
save(RUN/'01_diagnosis/recomputed.json',summary)
write(RUN/'01_diagnosis/recomputed_baselines.md','# A′2原始表复算（已曝光）\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n来源和SHA见00_audit；程序GT与物理GT不同。\n')
# Inference-only input and evaluator-only labels, deliberately separate files/processes.
with (RUN/'03_exposed_regression/inference_inputs.jsonl').open('w',encoding='utf8') as inf,(RUN/'03_exposed_regression/evaluator_GT.jsonl').open('w',encoding='utf8') as gt:
 for z in jl(OLD/'05_DEV/full_v3/decision_predictions.jsonl'):
  dump_line(inf,{k:z[k] for k in ['case_id','frame_id','input_image','reference_image','points','reference_points','A','tiles']})
  dump_line(gt,{k:z[k] for k in ['case_id','frame_id','family','pair_id','GT','A_error','A_correct','oracle_error','oracle_correct','metrics','M_GT']})
write(RUN/'00_protocol/preregistered_gates.md','''# A′3 预登记（首次NEW_DEV评估之前）
生产A零修改；flags3572/SHADOW1/terminal1/refine/4线程。K≤12，最多4096路径采样，事件提议而非等距候选。
Gate A：NEW_DEV observable候选正确数相对旧候选器至少增加5帧；强假尾增加>=1、弱裂纹增加>=1；A已确认端点100%保留；不损失任何旧oracle正确帧作为研究目标；无GT输入运行时。
Gate B：与旧v3参考对照，NEW_DEV可信争议覆盖平均严格提高，独立已知运动>1px误接受不增加；分开统计完整争议段与any query。若仍不能跨材料支持，NOT_GENERALIZED。
激活：至少12独立pair/3背景过程，假尾A>32px且真长A<=8px，当前图与锚点完全相同。
Gate C前置DEV：实际正确数严格增加、惩罚损失降低、阴性FP不增加、A_correct_changed_wrong=0，灾难性>160px错改=0，真长/交叉/既有裂纹变暗负控。
旧数据只做曝光诊断；NEW_TEST须全部前置Gate满足且生成前冻结一次。缺完整原生实现即Gate D NOT_TESTED；生产保持A。
无真实物理GT，真实MAE=N/A。单调先验关闭，无未来帧，PHASE_UNKNOWN。
''')
write(RUN/'05_NEW_TEST/NOT_RUN_REASON.md','前置Gate尚未判定；没有生成/读取独立TEST。不得把曝光DEV称为TEST。\n')
print(summary,flush=True)
