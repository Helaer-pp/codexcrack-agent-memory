# GROUP_A-only ROI几何因果实验

仅GROUP_A551开发，验证组C562和三点弯520锁后回归，1633帧×A/B/C=4899。CT2/开发组H/CT3/排除组X不加载图像、结果或标签进入本轮。全局数据用途政策不变，本轮进一步缩小研发范围。标签只事后比较，不训练、不选宽度。生产与旧原型不改。

从项目根目录启动全新输出路径：

```powershell
./research/grayref_roi_geometry_ablation/run_group_a.ps1 -RunId grayref_roi_geometry_group_a_only_NEW -Workers 12
./research/grayref_roi_geometry_ablation/run_regression.ps1 -RunId grayref_roi_geometry_group_a_only_NEW -Workers 12
```

第二条需要第一条完成冻结与评分；它完成两组回归、全1633帧绘图、完整性检查、报告和三组视频。或者设置PYTHONPATH为项目research目录后运行`python -m grayref_roi_geometry_ablation.run --run-id UNIQUE --phase all --workers 12 --render`。Python路径从config/project.json读取，不硬编码机器路径在脚本中。

参数：`--run-id`必需且只含字母数字下划线短横；`--group-manifest`可选，省略时筛选上一轮清单，指定时必须恰好三组1633且不含排除组；`--mode ALL`默认正式三模式，A/B/C单模式值仅用于dry-run说明，不允许冒充正式实验；`--workers`默认12；`--dry-run`只检查清单数量并展示计划，不打开图像/GT；`--resume`核对冻结源码与已有工件后恢复，不能覆盖不同内容；`--render`在完整回归后生成所有图像/核验/报告/视频；`--phase group_a|regression|all`默认all。只跑group_a时不加render，全部图像在三组推理锁后生成。

源码检查：`python -m grayref_roi_geometry_ablation.tests --run output/experiments/UNIQUE_PREFLIGHT`；图像可单独恢复：`python -m grayref_roi_geometry_ablation.render --run output/experiments/RUN --workers 12`。同名已封存有效文件只校验，不覆盖。故障保留原目录和异常日志。

读`roi_geometry_spec.md`和`algorithm_diff_audit.md`。config_frozen.yaml采用JSON语法（有效YAML子集）并与Python CONFIG逐项验证。实际环境、耗时、worker峰值内存保存在运行结果；路径引擎计时不含缓存特征计算，不能将旧缓存当成ROI速度改进。

主要交付：REPORT.md、ROI_CAUSAL_FINDINGS.md、galleries/index.html、每帧5张图与mask/节点/边/血缘数组，三组ABC视频（6FPS是播放速度）。数值证据大数组通过旧只读缓存相对项目路径+SHA引用，需保留该缓存目录；PNG不可代替signed差分。旧V1/V2本轮NOT_REPLAYED，上一轮简化A逐帧重新执行。
