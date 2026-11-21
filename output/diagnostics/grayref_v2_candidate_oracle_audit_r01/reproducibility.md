# 实际执行与复现

工作目录：`.`。所有新数据和审计代码仅在本轮output/diagnostics目录内；冻结算法从活动research/p1p2_grayref_v2/只读加载并核对SHA，不执行旧封存算法副本。没有训练、优化器、新C++或新主路径模型。

实际执行顺序（每个脚本均已执行成功，日志在logs）：

```powershell
Set-Location .
$env:PYTHONPYCACHEPREFIX='./output/pycache'
$env:PYTHONIOENCODING='utf-8'
D:/ProgramData/anaconda3/python.exe output/diagnostics/grayref_v2_candidate_oracle_audit_r01/audit_source/prepare.py
D:/ProgramData/anaconda3/python.exe output/diagnostics/grayref_v2_candidate_oracle_audit_r01/audit_source/observe.py
D:/ProgramData/anaconda3/python.exe output/diagnostics/grayref_v2_candidate_oracle_audit_r01/audit_source/evaluate.py
D:/ProgramData/anaconda3/python.exe output/diagnostics/grayref_v2_candidate_oracle_audit_r01/audit_source/causal_details.py
D:/ProgramData/anaconda3/python.exe output/diagnostics/grayref_v2_candidate_oracle_audit_r01/audit_source/verify.py
D:/ProgramData/anaconda3/python.exe output/diagnostics/grayref_v2_candidate_oracle_audit_r01/audit_source/galleries.py
D:/ProgramData/anaconda3/python.exe output/diagnostics/grayref_v2_candidate_oracle_audit_r01/audit_source/report.py
D:/ProgramData/anaconda3/python.exe output/diagnostics/grayref_v2_candidate_oracle_audit_r01/audit_source/seal.py
```

以上是原执行命令记录，**不要在已封存目录再次覆盖运行**。完整新复现请用：

```powershell
& ./output/diagnostics/grayref_v2_candidate_oracle_audit_r01/audit_source/reproduce.ps1 -Output './output/diagnostics/grayref_v2_candidate_oracle_audit_replay01'
```

该编排先复制审计源码到全新同级目录再执行；原输出只读保留。编排做语法/路径检查，各实际阶段已运行，但未为了验证包装器再重复全部实验。外部F盘原图、原点文件、V2冻结结果与LabelMe快照仍须存在；所有路径由现有manifest确定。环境完整版本见environment.json，不自动安装库。

补充执行：evaluate最终版将E4得分复算从±1微分容差检查收紧为原有确定性量化后的整数严格相等，完整150输入全部评分重跑并通过，未改变匹配参数、候选或统计口径；evaluate01.log与evaluate_final.log均保留。图册补了原可见段放大，galleries01.log与galleries_final.log保留。没有算法调参或验证驱动模型修复。

耗时：每个无GT观察输入的总秒数在candidates/*/*/freeze.json的elapsed_seconds（含解码、两次原检测、诊断延伸及导出）；全离线评分用时在evaluation_complete.json。这些是审计成本，不是冻结DLL实时性能。Python采用3个观察worker；GT只在全部候选冻结后读取。影子轨迹缓存同一输入/同一原始种子/M2设置，绝不混入原Oracle。

源码及输入SHA：identity_before.json、observer_source_lock.json、audit_plan_sha.json、candidates_frozen.json、source_manifest.json。完整旧V2的39734份文件已复核，后续所有阶段不写旧目录；旧源码/点源/标注归档期末再核对。新的全部文件散列在artifact_manifest.json，自身和正在写入的seal日志排除。
