# P1/P2-GrayRef V1 冻结移植与跨试件评估

实际运行输出：`output/runs/p1p2_grayref_v1_20261112_r01/`。

2647帧 × 6模式已完成Python/C++回放。开发9390组离散结果完全一致；锁后验证current分支15个端点不一致，最大209.02px，原因是线性拟合微差跨过floor/ceil搜索边界。默认joint T10开发12/76、验证5/35命中10px。非生产研究候选，不能替换A。

唯一算法来源是根目录`paired_p1p2_roi_V1_FROZEN.py`，SHA256 `2e2e5ebef80ab33e486c561b6dec09ee15d23033020cc1886a7de24c7ce2baf6`，没有修改。`python_replay.py`仅适配输入和读取返回局部变量；中文路径通过byte-for-byte ASCII staging处理。`detector.hpp`是独立C++镜像，`runtime.cpp`为GrayRef* C ABI，仅复用A的图像/点内存结构，不链接A检测代码。`P1P2GrayRefV1.h`为独立调用声明；`native.py`是实际运行的ctypes调用入口。

`preflight.py`做输入来源核对；`cpp_replay.py`比较逐列trace；`contracts.py`验证错误输入；`parity_gate.py`锁开发结果；`validation.py`在锁后执行验证；`evaluate.py`在推理完成后读标签；`report.py`仅汇总现有输出；`media.py`和`frame_comparisons.py`只生成离线图像视频。

必须遵守`config/dataset_usage_policy.json`：四开发组；验证组C/三点弯仅验证；排除组X排除；标注比较/QC而非训练/参数拟合。不要直接重跑脚本覆盖已封存目录。新复现用独立目录：

```powershell
Set-Location .
$env:PYTHONPYCACHEPREFIX='./output/pycache'
& D:/ProgramData/anaconda3/python.exe research/p1p2_grayref_v1/reproduce.py --output output/runs/p1p2_grayref_v1_reproduction_example --plan
```

去掉`--plan`才开始新目录的全开发复现，默认不进入验证。`--include-validation`显式包含已经曝光的锁后验证，不会成为新的盲测。入口拒绝已有输出目录、项目output外目录和非ASCII路径。新一键编排已检查计划与语法；本轮所有构成阶段已实际执行，一键入口未额外重复整套2647帧。

完整构建参数、数据依赖、错误日志修复记录和读结果方式见运行目录`build_and_reproduce.md`。V2建议仅在报告中，未改变V1规则。
