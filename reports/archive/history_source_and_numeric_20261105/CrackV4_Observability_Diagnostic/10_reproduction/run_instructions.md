# 复现与隔离

独立工具目录：D:/workspace\crack_v4_cpp\observability_diagnostic_20261102
冻结工具Git：45a20cbf24934fedad24f47ee0c102ffe7e3b59c
生产DLL：D:/workspace\output\frozen_dp_tip_measurement_study\02_source\binaries\A\CrackV4.dll

在PowerShell设 `$env:PYTHONUTF8="1"`；Python为D:/ProgramData/anaconda3/python.exe，NumPy/OpenCV/Pillow/Matplotlib；原生caller用 C++17/v142/OpenCV4.4。

顺序：

```powershell
cd "D:/workspace\crack_v4_cpp\observability_diagnostic_20261102"
# 新实验须改输出根目录并复制冻结代码，切勿覆盖现有已完成实验
python stage0.py
D:/CMake/bin/cmake.exe -S . -B build -G "Visual Studio 17 2022" -A x64 -T v142
D:/CMake/bin/cmake.exe --build build --config Release
python native_benchmark.py
python tests_diag.py
python run_diagnostics.py
python controls.py
python reports.py
python render.py render
python render.py validate
python freeze.py
python holdout.py
python run_diagnostics.py --holdout
python render.py render --holdout
python render.py validate --holdout
python reports.py --all
python finalize.py
```

本轮以上步骤已实际执行。第五组ATTEMPT_STARTED.json防止重复评测；仅重新渲染缓存不调用A。原四组不可变快照与A源码在既有目录，guard_A逐文件SHA复核。

无有效尖端时正式视频只显示原图；诊断PNG是原图、冻结A、诊断文字分栏。固定裁剪只用于显示，检测没有裁剪变更。单位为原图px；无本组标定不输出mm。

离线诊断不属于实时生产链；新exe只是加载既有A的独立计时调用器，不是新生产DLL。
