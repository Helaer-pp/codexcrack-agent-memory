# 复现命令

工作目录必须是 CodexCrack；复现请先把common.py中OUT/GEN/BUILD设为新的未存在目录，不覆盖本次封存目录。PowerShell设置PYTHONPYCACHEPREFIX到output/pycache。

```powershell
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/freeze.py
& D:/CMake/bin/cmake.exe -S research/uctt_r05e -B output/build/uctt_r05e -G "Visual Studio 17 2022" -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build/uctt_r05e --config Release --target B0 R03Original EvidenceContracts -- /m:1 /nodeReuse:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/baseline.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/generate.py
& D:/CMake/bin/cmake.exe -S research/uctt_r05e -B output/build/uctt_r05e
& D:/CMake/bin/cmake.exe --build output/build/uctt_r05e --config Release --target B1 B2 EVIDENCE_DP_PROBE -- /m:1 /nodeReuse:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/checks.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/replay.py B1 dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/compare.py B1 dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/diagnose.py
# Only if B1_gate PASS:
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/replay.py B2 dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/compare.py B2 dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/freeze_validation.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/replay.py B1 val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/compare.py B1 val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/replay.py B2 val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/compare.py B2 val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/budget_diagnose.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/replay.py B2 perf
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/benchmark.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/input_contract.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/report.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/media.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05e/seal.py
```

B2 FAIL即停止B3/B4，不执行新输出融合。冻结后验证只观察已冻结阶段；不能凭验证结果继续改预算。
