# 复现命令

在项目根运行，Python D:/ProgramData/anaconda3/python.exe。原运行已封存，复跑先在common.py将OUT/GEN/BUILD设为新唯一output目录，不覆盖本轮。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/prepare.py
& D:/CMake/bin/cmake.exe -S research/uctt_r05d -B output/build/uctt_r05d -G "Visual Studio 17 2022" -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build/uctt_r05d --config Release -- /m:1 /nodeReuse:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/contracts.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/replay.py dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/analyze.py dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/local_audit.py dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/analyze.py dev
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/replay.py cf
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/evidence_probe.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/initialization_probe.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/counterfactuals.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/replay.py val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/local_audit.py val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/analyze.py val
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/geometry_completion.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/deliver.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05d/crossgroup.py
```

重点帧不能单图重置：复现所属完整组后查看traces/<group>__<frame:06d>.json。只看已有重点帧可直接打开R05D_G0_G5_Failure_Gallery.html#ct2__000395、#group_h__000078、#group_a__000504、#ct3__000065。全部候选在JSON中；NPZ原数组供进一步离线审计。
