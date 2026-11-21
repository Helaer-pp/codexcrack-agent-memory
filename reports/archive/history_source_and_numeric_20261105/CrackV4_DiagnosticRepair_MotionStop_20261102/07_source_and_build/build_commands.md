# 构建与复现

工作目录 D:/workspace/crack_v4_cpp/diagnostic_repair_motionstop_20261102，Python D:/ProgramData/anaconda3/python.exe。

```powershell
$env:PYTHONUTF8='1'
python instrument.py
D:/CMake/bin/cmake.exe -S . -B build -G "Visual Studio 17 2022" -A x64 -T v142 -DOpenCV_DIR=D:/opencv-4.4.0/build
D:/CMake/bin/cmake.exe --build build --config Release --parallel 4
python register_protocol.py
python audit_replay.py
python known_gt.py
python logo.py
python diagnostic_v2.py
python run_motion.py
python regression.py
python photometric_controls.py
python known_motion_dp.py
python performance_only.py
python report_round.py
python qa_round.py
python freeze_round.py
# 第五单次锁，重复运行会拒绝：
python audit_replay.py --holdout
python diagnostic_v2.py --holdout
python report_round.py --all
python qa_round.py --all
python seal_round.py
```

以上命令在新的输出根目录重放；不要删除已完成的第五单次锁。已交付目录直接浏览结果，不需要重新消耗第五验证。

本轮 trace_harness/trace_analyze 为独立 INSTRUMENTED_DIAGNOSTIC EXE，原始A DLL仍由a_bench加载；没有构建/发布新生产DLL。source_patch.diff只在复制的原源上加追踪与研究EXE运动介入钩子。注入从不进入生产DLL。build.log记录v142/OpenCV4.4成功构建。

common_rc引用上轮common_diag/diagnostic_methods及冻结ctypes wrapper，所有外部源码依赖在source_hashes中列hash，package_dependencies中保存可复现副本。原数据仍需manifest中的只读F盘路径；复制源码不复制原始试验图片。
