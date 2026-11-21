# Reproduction (PowerShell, project root)

The existing run is evidence; do not overwrite it. For a fresh run change OUT and BUILD in research/uctt_r03/prepare.py and PBUILD/SRC in profile.py to new output paths first. All runtime imports are active research/src files, never sealed output sources. The frozen_production copy is restore-only.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Resolve-Path output/cache/tmp).Path
$env:TMP=$env:TEMP
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/prepare.py
& D:/CMake/bin/cmake.exe -S research/uctt_r03 -B output/build/uctt_r03 -G 'Visual Studio 17 2022' -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build/uctt_r03 --config Release -- /m:1 /nodeReuse:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/pilot.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/verify.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/profile.py --generate
& D:/CMake/bin/cmake.exe -S output/build/uctt_r03_profile_source -B output/build/uctt_r03_profile -G 'Visual Studio 17 2022' -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build/uctt_r03_profile --config Release -- /m:1 /nodeReuse:false
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/profile.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r03/report.py
```

Contracts exit2 means safety FAIL (not infrastructure crash); verify.py preserves that result and does not open A3. CMake parallel build hung in this sandbox; serial /nodeReuse:false completed. Failed build logs retained. Any next source change requires rebuilding/replaying affected evidence.
