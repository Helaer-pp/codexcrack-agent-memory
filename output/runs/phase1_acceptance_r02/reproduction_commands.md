# R02 复现命令

工作目录：`.`。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
D:/ProgramData/anaconda3/python.exe -B .\output\runs\phase1_acceptance_r02\scripts\r02_reconcile.py
D:/ProgramData/anaconda3/python.exe -B .\output\runs\phase1_acceptance_r02\scripts\r02_t2.py
D:/ProgramData/anaconda3/python.exe -B .\output\runs\phase1_acceptance_r02\scripts\r02_t2_report.py
D:/ProgramData/anaconda3/python.exe -B .\output\runs\phase1_acceptance_r02\scripts\r02_ab_test.py
D:/ProgramData/anaconda3/python.exe -B .\output\runs\phase1_acceptance_r02\scripts\r02_profile.py
D:/ProgramData/anaconda3/python.exe -B .\output\runs\phase1_acceptance_r02\scripts\r02_perf_report.py
$env:CRACK_STRICT_RUN='phase1_acceptance_r02_t1_20261110_r01'; D:/ProgramData/anaconda3/python.exe -B .\tests\strict_anchor_invariance.py
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 check
```

A/B 的 `ab_src_before/after` 与 `ab_build_before/after` 已归档在本目录；构建使用同一 VS2022/v142、Release x64、OpenCV4.4。R02 不覆盖 R01 目录或旧发布包。
