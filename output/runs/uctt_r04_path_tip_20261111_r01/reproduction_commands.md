# Reproduce in PowerShell from CodexCrack

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
