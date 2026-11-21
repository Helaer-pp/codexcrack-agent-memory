# R05H 完整研究管线

独立 C++17/OpenCV4.4 研究库，生产 A 不变。原图 + 当前 P1/P2 + 初始化参考进入唯一 `r05h::Pipeline::process`；无试件名、文件名、帧号阶段规则或人工标注输入。

构建（项目根目录）：

```powershell
& D:/CMake/bin/cmake.exe -S research/uctt_r05h -B output/build/uctt_r05h -G 'Visual Studio 17 2022' -A x64 -T v142
& D:/CMake/bin/cmake.exe --build output/build/uctt_r05h --config Release -- /m:1 /nr:false
$env:PYTHONPYCACHEPREFIX='./output/pycache'
& D:/ProgramData/anaconda3/python.exe research/uctt_r05h/tests.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05h/replay.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05h/evaluate.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05h/media.py
& D:/ProgramData/anaconda3/python.exe research/uctt_r05h/report.py
```

`replay.py` 拒绝覆盖已经冻结的运行。复现时在 `common.py` 指定一个新的 `output/runs/` 目录，然后重新构建/冻结并回放；不要删除原始封存运行。合成检查脚本写入当前运行，请在封存后同样使用新目录。

原生 API：`R05HCreate(reference, reference_anchors)` 返回句柄；逐帧 `R05HProcess(handle, current, current_anchors, variant)`；`R05HRead` 获取 JSON；`R05HDestroy` 释放。图像/点 ABI 与项目 `CrackV4.h` 相同。JSON 字符串有效期至下一次 Read 或销毁；同一句柄不可并发。当前输入无效时 API 返回负数，几何无效时返回显式 UNOBSERVED / search_complete=false。Python 调用示例见 `native.py`。

变体：0 FULL，1 NO_REFERENCE，2 LAST_ENDPOINT，3 NO_HISTORY。各变体独立初始化并按时间前缀回放；开发组四变体，验证组冻结后仅 FULL 一次。LAST_ENDPOINT 选择最前方的保留 STOP，作为“取远端”对照；不是生产 A。参考关闭变体关闭固定参考打分，但保留相同历史导航机制，因此区分固定参考和历史参考作用。

输出 `observed_tip` 仅正式确认填值；`working_tip` 允许暂定/预测。`main_path` 每点含可见性、强度、尺度和缺失距离；`visible_segments` 与 `inferred_gaps` 分开。STOP 候选含前段支持、后段占比、当前/参考/身份/终止评分、参考每侧匹配质量。预测不写历史，只有 OBSERVED 可写。

采样核心的 `crossSection` 与 R05G 逐字相同，冻结时校验 SHA256。改变自动起源、间隙探索范围、STOP 决策、参考比较和可信历史导航。参考失败为中性；现有真裂纹不会仅因在参考中存在而被删除。当前版本仅局部平移参考，复杂变形、强纹理和形态相似划痕仍可能失败。它是可运行研究基线，不是生产精度或错锁安全保证。

输入策略：GROUP_A/CT2/开发组H/CT3 开发；验证组C/三点弯仅冻结验证；排除组X排除。LabelMe 仅 `evaluate.py` / `media.py` 离线读取，不进入 native/replay。输出目录中的 `freeze.json`、输入访问日志、源码快照和完整性清单用于复核。
