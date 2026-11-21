# 环境与准确复现命令

工作目录`.`。Python3.12.7 / OpenCV4.12.0 / NumPy1.26.4 / SciPy1.17.1，完整环境和工具SHA见run_identity.json。每次原始CLI/观察器argv及耗时分别在runs/*/cli_identity.json或observer.json；本次原生main耗时包含输出与绘图、观察器开销，不是内核或部署性能基准。

```powershell
Set-Location .
$env:PYTHONPYCACHEPREFIX='./output/pycache'
$env:PYTHONIOENCODING='utf-8'
# 选择全新的ASCII目录；已有目录会被拒绝：
& ./research/group_c_same_bmp_v1/reproduce.ps1 -Output './output/diagnostics/group_c_same_bmp_root_cause_v1_replay01'
```

同一复现脚本随证据复制在scripts/，也可从那里调用。它先校验图片/源身份并执行原生ABCD，再运行纯控制与交叉控制、101个预定义扰动、4个可见代表帧，然后离线标签、图表、报告、封存。不引入GT作为参数；不修改任何冻结规则。脚本默认输出目录指本轮，直接重跑会拒绝覆盖；新复现必须设GROUP_C_AUDIT_OUTPUT或使用上面的-Output。

分步入口：`run.py primary`、`run.py controlled`、`run.py sensitivity`、`run.py sentinels`、`analyze.py`、`controls_audit.py`、`visualize.py`、`report.py`、`seal.py`。当前实际执行中sensitivity与sentinels并行，评分等待两者完成；新编排顺序执行，算法输出应一致，时间不应直接等同。完整新编排仅做语法/安全路径检查，不为检查编排而再重复一次118次执行；各阶段均已真实运行。

输入文件依赖：原始F盘两张主BMP和4张同组已标注代表帧、data/anchors验证组C原始TXT、data/inputs六组manifest（仅选验证组C）、前轮冻结输出作为只读比较、四个人工LabelMe记录作为推理后离线比较。旧代码不作为运行依赖；冻结根源码是唯一算法来源，旧结果只用于核对。

诊断副本由冻结源AST插入一条alpha/dx/dy供体替换，写入scripts/diagnostic_motion_copy.py，供体函数在core.py。没有改滤波、ROI启发式、阈值、初始化或track。该副本不能作为生产V1发布。脚本快照、原源码副本、source_diff.patch与每个产物哈希随最终清单保存。
