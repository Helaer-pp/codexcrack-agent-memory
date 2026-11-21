# 实际复现命令

工作目录 .。Python D:/ProgramData/anaconda3/python.exe。外部F盘原图只读；所有输出output/runs/<RunId>。

```powershell
$env:PYTHONUTF8='1'
$env:CRACK_AP2_RUN='aprime2_reproduce_new_id'
$py='D:/ProgramData/anaconda3/python.exe'
& $py -B research/aprime2/bootstrap.py
./build.ps1
& $py -B research/aprime2/native_bridge.py
& $py -B research/aprime2/dev.py --probe --v1
& $py -B research/aprime2/dev.py --v1
& $py -B research/aprime2/dev.py
& $py -B research/aprime2/evaluate.py
& $py -B research/aprime2/decision_experiment.py
& $py -B research/aprime2/controls.py
& $py -B research/aprime2/real_audit.py
& $py -B research/aprime2/counterfactuals.py
& $py -B research/aprime2/analyze.py
& $py -B research/aprime2/selector_prefilter_diagnostic.py
& $py -B research/aprime2/evaluate.py --prefilter
& $py -B research/aprime2/decision_experiment.py --prefilter
& $py -B research/aprime2/counterfactuals.py --prefilter
& $py -B research/aprime2/analyze.py --prefilter
& $py -B research/aprime2/contract_tests.py
& $py -B research/aprime2/timing.py
& $py -B research/aprime2/audit_inputs.py
& $py -B research/aprime2/media.py
& $py -B research/aprime2/report.py
& $py -B research/aprime2/finalize.py
```

源码snapshot在02_source，运行研究源在research/aprime2。独立旁路DLL只是取样器，不是A′2生产算法。最终旁路已修正诊断invalid归一化；原始v1取样JSON只保留历史证据，其归一化转换在报告中说明。GT仅生成/离线评价器读取。全新RunId避免覆盖已有证据。
