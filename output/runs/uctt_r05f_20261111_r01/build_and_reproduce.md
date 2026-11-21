# 构建与复现

工作目录：`.`。Python3 / OpenCV native4.4；MSVC v142 x64、VS17生成器，/O2 /fp:precise /utf-8、4 native threads。不存在Git commit，身份见hash清单。输入F盘只读。

```powershell
$env:PYTHONPYCACHEPREFIX='./output/pycache'
& 'D:/CMake/bin/cmake.exe' -S research/uctt_r05f -B output/build/uctt_r05f -G 'Visual Studio 17 2022' -A x64 -T v142
& 'D:/CMake/bin/cmake.exe' --build output/build/uctt_r05f --config Release -- /m:1 /nodeReuse:false
```

封存目录不可覆盖。新全程复现前将 `common.py` 中 `OUT` 改为新的 `output/runs/<unique_r05f_id>`，GEN/BUILD也建议设置新output/build子目录，并同步CMake生成源/产物目录；新目录必须为空。prepare.py主动拒绝覆盖旧OUT。算法参数仍使用已封存current.hpp，不从标注选参。再依次执行：

```powershell
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/prepare.py
# prepare生成A0插桩源后执行上面的configure/build
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/baseline.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/contracts.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/replay.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/compare.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/diagnose_budget.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/diagnose_compare.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/pixel_audit.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/benchmark_release.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/release_details.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/audit_media.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/media.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/video_qa.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/tables.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/source_map.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/report.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/postprocess_gallery.py
& 'D:/ProgramData/anaconda3/python.exe' research/uctt_r05f/seal.py
```

原图回放器不接受GT输入；只读策略在读取每张图前验证。单帧失败诊断由pixel_audit.py复现实际访问窗口的native数组，明确是stateless/offline，不替代全前缀评估。独立计时期间不得同时运行其他实验/渲染。全部CSV可直接重算分母；压缩轨迹按JSONL流式读取，不能一次性解压到内存。

S0 A_FROZEN使用55a0…构建DLL；发布DLL1c742…单独完整验证，文件字节不同但行为对照另有证据。R05F研究DLL的新接口不宣称与生产ABI可直接替换。R03Original退出码2是原有错锁失败复现，不能篡改为0。
