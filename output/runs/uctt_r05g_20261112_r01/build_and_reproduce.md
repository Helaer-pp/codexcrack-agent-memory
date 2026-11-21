# 编译与复现

工作目录：`.`。Python为`D:/ProgramData/anaconda3/python.exe`，CMake为`D:/CMake/bin/cmake.exe`。OpenCV使用项目third_party/opencv440，VS2022生成器、x64、v142、Release /O2 /fp:precise /utf-8。

本run已封存，**不要覆盖它**。完整复现先将research/uctt_r05g/common.py的OUT改为output/runs/下一个未存在的新run目录；仅输出位置变化，原生参数不变。原图F盘只读。

```powershell
$env:PYTHONPYCACHEPREFIX='./output/pycache'
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/prepare.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/baseline_check.py
& D:/CMake/bin/cmake.exe -S research/uctt_r05g -B output/build/uctt_r05g -G 'Visual Studio 17 2022' -A x64 -T v142 -DR05G_ENABLE_BEAM=OFF
& D:/CMake/bin/cmake.exe --build output/build/uctt_r05g --config Release -- /m:1 /nr:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/g1_check.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/seed_sheets.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/diagnostic_seeds.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/g1_seeded.py
# 必须检查G1_gate机制PASS后才启用beam；保持原诊断种子、不要重新择优。
& D:/CMake/bin/cmake.exe -S research/uctt_r05g -B output/build/uctt_r05g -DR05G_ENABLE_BEAM=ON
& D:/CMake/bin/cmake.exe --build output/build/uctt_r05g --config Release -- /m:1 /nr:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/replay.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/seeded_replay.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/contracts.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/evaluate.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/tables.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/evidence_audit.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/full_trace_metrics.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/origin_audit.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/weak_audit.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/profile_plots.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/media.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/weak_display.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/report.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/delivery.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05g/seal.py
```

R03Original对既有fault_seed.txt退出码2是预期复现的已知失败，不应修改原矩阵令它通过。完整原生参数见冻结tracker.hpp，代码新增清单及diff见code_diff.patch。修改后再复现时记录新SHA与新输出目录，不冒充同一冻结实验。
