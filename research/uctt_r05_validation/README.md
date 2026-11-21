# R05 人工标注对照验证：用途受限、无训练

本目录是R05人工标签回传后的验证入口。旧 `research/uctt_r05_prelabel_difference/` 及其输出作为冻结历史来源，不重跑七组旧算法。人工作业目录不被覆盖。

用途规则以 `config/dataset_usage_policy.json` 为准：开发GROUP_A/CT2/开发组H/CT3，验证专用验证组C/三点弯，排除组X完全排除。人工标注只允许QC与comparison，不允许训练、参数拟合、自动阈值搜索或在线参考选择。角色是数据用途权限，不是检测器内部的按材料分支阈值。

在项目根运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$py='D:/ProgramData/anaconda3/python.exe'
& $py research/uctt_r05_validation/test_validation_contracts.py
& $py research/uctt_r05_validation/validate_annotations.py
& $py research/uctt_r05_validation/replay_production.py
& $py research/uctt_r05_validation/summarize_validation.py
& $py research/uctt_r05_validation/render_delivery.py
& $py research/uctt_r05_validation/seal_delivery.py
```

当前输出为 `output/runs/r05_annotation_validation_20261111_r01`。重跑必须把脚本中的OUT改为新的唯一目录并预先创建，不能覆盖已有评分锁定文件。第一次运行前，配置变更前的文件已保存在policy_before。先锁定规则与输入哈希，然后读标签并评分；不能看验证分数再改规则。

`validate_annotations.py` 仅读取120个允许组的标签及冻结NPZ；人工标签只用于掩膜覆盖、路径容差带、可见性分母及渲染。路径完整弧长包含ROI外部分，不能用裁后路径作全长分母。3/5/10px容差全部在原图像素中计算。失败差分与无标签不作零误差。

`replay_production.py` 不打开任何标注JSON，只接受原图、原始P1/P2和预先选帧清单。严格按时间顺序回放至各组最后一个选中帧；冻结生产A，flags3572/SHADOW1/terminal1/refine=true/native4线程。一次初始化；首帧GetBaseline只是缓存读取。输出完成后，独立比较器才打开冻结人工JSON快照计算欧氏误差。

`summarize_validation.py` 分组级开发/验证角色、旧development/holdout子划分出表；验证组C/三点弯旧development子划分仍不允许开发。小样本和历史曝光状态不变。没有独立新TEST，没有训练或调参，生产DLL不变。

基础设施回归 `./run.ps1 check` 也已过滤排除组X，现有冒烟数据中只对其余五组执行，不假称包含CT3。历史结果的七组表不被改写。新的数据读取应调用 `crackv4.dataset_policy.require` 或 `filter_rows`；不要直接迭代旧manifest全部组。

`render_delivery.py` 仅在评分完成后渲染全部120帧人工/算法尖端叠图及视频，青色十字为生产A确认输出，红圈为人工尖端；显示裁剪不改变误差坐标。`seal_delivery.py` 最后检查原标注、原图和18个生产文件不变，归档本次评价源代码与回归检查结果，并生成交付哈希清单。更新项目状态文档后才执行封存。
