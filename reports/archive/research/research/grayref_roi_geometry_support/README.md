# ROI锁后解释与交付

这组辅助脚本只读取已封存的预测/离线评分，不执行新检测、不改变参数或数据角色；不属于冻结推理模块。

- `case_audit.py`：GROUP_A新增成功及原合格路径的节点/片段存活。
- `regression_case_audit.py`：曝光回归中原合格路径的mask/节点/片段/预算去向。
- `deliver.py`：在核心completion_seal通过后生成final_delivery复核报告，保留原自动报告不变；更正GT尖端未排除与完整路径未裁剪的不同口径。

从项目根目录设置PYTHONPATH为research，使用config/project.json中的Python；各脚本接收`--run output/experiments/运行目录`。同名封存文件内容不一致会拒绝覆盖。主算法和完整运行方法见`../grayref_roi_geometry_ablation/README.md`。截图、手工视觉核验和补充封存为交付记录，不参与算法。
