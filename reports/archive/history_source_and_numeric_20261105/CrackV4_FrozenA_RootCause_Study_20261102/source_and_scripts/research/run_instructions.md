# 冻结 A 专项根因诊断复现

这是研究工具包，不是新的生产算法或 DLL。不得把运动替换控制句柄用于软件测量。

原工作目录：`D:/workspace/crack_v4_cpp/rootcause_diagnostic_20261102`。
数据输出：`D:/workspace/CrackV4_FrozenA_RootCause_Study_20261102`。
原始图像和基准点为只读；输入清单保留逐张 SHA256、原图坐标与参考关系。

环境：Windows、MSVC v142、C++17、OpenCV 4.4.0、4线程；Python `D:/ProgramData/anaconda3/python.exe`。
Python诊断环境实际 OpenCV 4.12，与原生DLL的4.4独立。独立材料匹配只与同一Python旧诊断环境逐尝试对照，不将Python计时当DLL性能。

## 构建命令

PowerShell中运行，保持工作目录为原目录。`instrument.py`只写研究副本。

```powershell
$env:PYTHONUTF8='1'
$env:PATH='D:/opencv-4.4.0/build/x64/vc15/bin;'+$env:PATH
& 'D:/ProgramData/anaconda3/python.exe' instrument.py
& 'D:/CMake/bin/cmake.exe' -S . -B build -G 'Visual Studio 17 2022' -A x64 -T v142
& 'D:/CMake/bin/cmake.exe' --build build --config Release
```

`trace_harness.exe`为独立研究可执行文件；`CRACK_V4_EXPORTS`供原ABI源码在该EXE中编译，不意味着发布新的DLL。导出的中间矩阵、每列累积值和控制分支均不连接生产调用入口。

## 本轮实际顺序

1. `audit_replay.py`：前四组文件/基准点审计及冻结DLL回放；1987当前帧另加4参考帧。
2. `run_trace.py`：CT2 refine off原生回放，两个独立状态研究分支，固定14帧同历史正对照及运动替换。
3. `controlled_tests.py`：固定种子20261102，前四组空间分离DEV/TEST数字变换。
4. `diagnose_round.py`：原四组逐尝试重现原材料匹配规则，光度分层与路径只读归因。
5. `supplemental.py`：预选深度矩阵差分、失败类型示例、验证组C99帧门控差异。
   `stop_validate.py`调用`trace_analyze.exe`，仅用保存矩阵调用同一冻结C++ ridge函数，精确核对原DP的终止列和gain，分析逐块停止；不实例化Detector、不重放图像检测。
6. `performance_only.py`：无并发诊断任务时重放原四组完整C++核心；再次校验精确输出。
7. `publish.py`：生成DEV报告模板、唯一优先动作及视频哈希/解码校验。
8. `freeze_protocol.py`：独立Git提交、脚本/研究EXE/旧依赖/冻结源码SHA锁定。
9. `audit_replay.py --holdout`：第五组唯一一次新原生回放；`diagnose_round.py --holdout`：唯一一次新诊断。两者均先验证冻结SHA，已经运行过会拒绝再次执行。
10. `supplemental.py --holdout`：从固定诊断结果制作预定失败类型静态示例，不运行Detector或matcher；`publish.py --all`：合并统一模板，不调参数。
11. `seal_package.py`：检查2510当前帧、5参考帧、视频帧数、HTML相对链接及源码锁定，封存输出SHA。

运行对应Python脚本使用 `& 'D:/ProgramData/anaconda3/python.exe' -u <脚本路径>`。封存包只供核查；若需要从头复现，建立独立新目录并明确标为重复性复核，不能删除本包锁文件后声称第五组仍是首次留出。源码中的原工作区依赖保留实际绝对路径，搬迁时必须显式调整路径并重新声明实验身份。

## 失败预跑与时间口径

CT2最初研究预跑误用clean参考模式，已停止、归档于 `03_CT2_refine/INVALID_mode0`。正式分析改用清单中的auto后，完整验证研究与原DLL各468帧、14正对照零差异。初次汇总还遇到整型仿射矩阵不能求逆的Python类型问题；只改为float64并用 `run_trace.py --reuse-native` 读取已存原生/插桩结果完成分析，没有修改检测器。

原生完整核心含 Process、GetResultV2、CopyPath及必要路径分配，输入已解码；磁盘、解码、JSON、写图/视频和研究埋点不在此口径。没有采集硬件或ETW实测，不将数字扰动当真实曝光，也不猜测包装层停顿来源。

真实裂纹尖端/中心线 GT 不存在，真实误差和precision/recall为N/A；coverage、暗谷支持、版本坐标分歧和已知数字运动误差分别报告。
