# 复现（在 CodexCrack 根目录执行）

Python环境路径见config/project.json。新实验必须新RunId，不覆盖封存证据。

```powershell
$env:PYTHONUTF8='1'
$env:CRACK_AP3_RUN='aprime3_new_unique_id'
$env:TEMP="$PWD/output/cache/tmp"
$env:TMP=$env:TEMP
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/setup3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/make_observer3.py
& D:/CMake/bin/cmake.exe -S . -B output/build -G 'Visual Studio 17 2022' -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build --config Release --target CrackV4AP3Observer AP2DualBench -- /m:1 /nodeReuse:false
# 原生计时必须独占，先完成，再做以下DEV和媒体。
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/native_audit3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/diagnose3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/seed_audit3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/generate3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/infer3.py exposed
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/evaluate3.py exposed
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/infer3.py new
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/evaluate3.py new
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/controls3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/counterfactual3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/real3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/real_reference_compare3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/refresh_history3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/postprocess3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/contracts3.py
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/media3.py exposed
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/media3.py new
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/media3.py real
& D:/ProgramData/anaconda3/python.exe -B research/aprime3/report3.py
```

setup和原生计时读取已封存AP2结果做回归证据，运行代码来自活动research目录。外部原图F盘路径及逐帧坐标由data/inputs/six_groups_manifest.csv定义；不写外部数据。
新DEV输入与GT分文件，运行infer3不读取GT。评测器使用8px程序真值容差，损失=正例min(error,64)/漏检32、阴性误确认32；不可观察正例不计入损失。真实无物理GT。
此复现脚本不会生成独立TEST。前置失败不能调用新TEST，未提供可被误用为通过的TEST数据。
完整A′3原生未实现；CrackV4AP3Observer.dll只是诊断旁路，不能拿它替换生产DLL。
