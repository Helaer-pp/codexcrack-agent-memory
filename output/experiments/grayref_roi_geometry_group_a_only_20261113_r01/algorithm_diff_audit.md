# 非ROI机制冻结审计

原型依赖当前research目录中已冻结的grayref_simplified_evidence_v0.algorithm，不修改原文件。冻结源码SHA与上一轮source_hashes.json核验。A调用其run_mode(C_FUSION_RAW)原函数；共享缓存由旧逐帧manifest SHA与当前BMP/P SHA确定，同一a对象供三模式使用。

B/C通过AST复制原run_mode，只追加search_mask参数，并在原eligible赋值后插入一行eligible = eligible & search_mask。删除这两个变动并还原函数名后，AST与原函数逐节点一致，运行时断言。其余算术、调用顺序、图/路径、分数、停止函数均为原代码。全安全mask的合成对照与原函数、图数组相同。GROUP_A预定中间帧用原BMP重新提取所有证据，对缓存数组逐项相等；正式30帧（每组10）再次核查。

lineage模块只在原graph_paths AST增加一次ranked读取回调，原返回值不改。额外重放边数组与计数逐模式核对，记录包含去重、未访问的预算尾部及keeper；不是修复去重。稳定节点ID采用原图(x,y)，同时保存三模式节点索引及掩膜成员资格，新增保留节点仅是原强度排序预算释放后的候选。

B/C额外ROI_LIMITED公开边界守卫由任务书要求，原生输出/候选/停止分数同时保留，不修改冻结停止准则。A不应用新的公开守卫，否则不能保持原对照。参考与尖端上下文不变，缩ROI不重新估计noise、threshold、参考质量或归一化。

NOT_IN_SCOPE：包含去重修复、提高路径/前驱预算、改变停止规则、参考权重优化、滤波选择、时间追踪、其他开发组调参、生产替换。

冻结前实现修复记录：无标签冒烟发现走廊缺失分支的Python字典priority重复关键字，改为字典覆盖赋值；纯实现错误，无GT访问。边界审计方向从原生停止trace_index恢复，避免误用另一个末端的斜率。最终版本与完整参数在全量评分前封存。
