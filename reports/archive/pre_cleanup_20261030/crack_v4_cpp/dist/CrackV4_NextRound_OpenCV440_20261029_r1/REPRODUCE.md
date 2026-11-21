# 复现与交付目录

SDK `bin/` 是已验证的生产 Release DLL 和三个示例，`include/` 和 `lib/` 可直接集成。`baseline/bin/`、`baseline/source/` 保存上一轮版本；`history.bundle` 保存本轮分步提交，`baseline/history_previous.bundle` 是上一轮交付历史。不要把 profiling DLL 用于生产测速。

## 已验证环境

- CMake `D:/CMake/bin/cmake.exe`，VS2022 Community 的 v142 工具链；C++17、x64、/MD、/O2、/fp:precise。
- OpenCV **4.4.0**，配置在 `D:/opencv-4.4.0/build`；生产DLL链接opencv_world440。
- Python 3.12、NumPy 1.26、Python cv2 4.12、psutil。Python图像工具与DLL内的OpenCV分开，原生计算使用4.4.0。
- 四组原始BMP目录及顺序记录在 `tests/datasets.json`。这些原始文件没有装进SDK；移动数据时修改directory并保持文件顺序。

## 常用命令

PowerShell在项目根目录运行：

```powershell
./build.ps1
./validate.ps1
# 完整序列/240扰动/驻留内存基准；约需14GiB以上可用内存
./validate.ps1 -Full
```

`validate.ps1`重新测试会写同名结果；发布结果的原始副本已在ZIP和SHA256清单中。常规测试15项+扩展5项；合成和自动配准反例是报告用例，保留失败输出，不以“没有异常退出”代表精度全部通过。ABI测试会把冻结SDK编译好的LegacyExample.exe与新DLL放在隔离目录执行。

关键根因及消融可独立重放：

```powershell
python tests/replay_cases.py --dll bin --flags 3 --name diagnostic
python tests/replay_cases.py --dll bin --flags 7 --name direction_ablation
python tests/photo_causality.py --dll bin
python tests/probe_registration.py --dll bin
python tests/replay_errors.py --dll bin --flags 245
python tests/key_figures.py
```

工作源码目录尚无bin时，将以上bin换成build_final/Release。flags3记录原行为，flags7只加方向消融；245为生产实验244再加数值诊断。诊断只用于分析，不用于主速度结论。

完整旁路数值与审核材料可重建：

```powershell
python tests/audit_sequence.py --dll bin --name diagnostic_full --flags 1
python tests/prepare_review.py --final --images
python tests/review_browser.py
```

`prepare_review.py`产生结果表数据 `results/audit_tables.json`。当前三份CSV已通过电子表格运行时生成并逐单元格校验；相同环境可用 `tests/export_audits.mjs` 重建（需要Codex附带@oai/artifact-tool，文件首部标明解析位置）。普通集成软件不依赖Python、Node或该工具。

阶段分析需单独启用编译开关：

```powershell
./build.ps1 -BuildDir build_profile -Profile
python tests/profile_cases.py --dll build_profile/Release
```

主基准始终用关闭profiling的DLL。所有帧含错误与fallback均保留；初始化、LastJson、CopyPath另列，读图/解码不计入算法调用。

`review/index.html`可离线打开。所有人工真值初始为空，建议先核对32个恢复帧、两例开发组H方向扰动及CT2过曝例。页面坐标为原图像素；包内raw.png是保留原分辨率的局部裁剪，原图链接指向用户F盘。人工标注请导出JSON留存，不能以程序路径替代真值。
