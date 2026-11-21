# 环境记录

- OS: Windows NT 10.0.26200.0, x64（PowerShell `[Environment]::OSVersion`；CIM 查询在当前受限会话不可用）。
- CPU: `AMD64 Family 25 Model 97 Stepping 2, AuthenticAMD`, logical processor count 32 (`PROCESSOR_IDENTIFIER` / `NUMBER_OF_PROCESSORS`). 这是 AMD，不是用户目标中的 Intel Core i7；因此性能结果按实际机器记录，不能宣称 i7 认证。
- CMake: `D:/CMake/bin/cmake.exe`, Visual Studio 17 2022 generator.
- Compiler: VS2022 v142 toolset（项目 `build.ps1`）；未在当前会话获得独立 `cl.exe` 版本文本。
- Build: Release x64, C++17.
- Native OpenCV: 4.4.0, `third_party/opencv440`.
- Python: 3.12.7; NumPy 1.26.4; OpenCV Python 4.12.0.88.
- Runtime: 4 native threads; flags=3572, policy=SHADOW(1), terminal validation=1, refine=true.
- Candidate DLL: `output/build/src/cpp/a/Release/CrackV4.dll`.
- Candidate DLL SHA-256: `55a0e7a79162da79e691ede9ff58229e59a56fdd1e0b1e3f609dc51128860402`.
- Profiling is disabled in the production DLL; R02 profiling build is separate and diagnostic-only.

CIM/ComputerInfo 查询失败原因：当前 Codex Windows 会话无法访问 CIM 资源；已记录可用环境变量和 OSVersion，未填充不可核实的 CPU 型号/频率字段。
