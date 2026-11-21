> 用户最新约束：第五组排除组X是独立实验，禁止参与算法调优。v1/v2/v3在澄清前已观察51/473，现全部退出正式候选；其第五组输出仅作排查记录，不能称独立验证。正式独立实验只采用见第五组之前已冻结的旧发布算法。新版本选择仅可依据原四组+合成测试，本轮四组回归未通过，因此不发布算法变更。

# 集成与发布决策

**不替换现有生产DLL；新开关默认关闭，仅离线复核。** 新末端门控降低了部分旧组确认覆盖，尚无人工GT来判定合理性。即使caseB不再输出1084px误长尾，也不足以验收生产。

保持现有ABI的调用：参考原始CV_8UC1+参考两个点创建持久handle，每帧传原始图和对应实测点。不要每帧重新创建；P1在上、P2在下且右法向为预期扩展侧。ratio由外部换算，实验均mm_per_pixel=1只评价px。旧默认Create/配置0与3572行为不变。

如需复现**实验**：CreateExtended flags=15860，SetOptionsV2 policy=1、terminal_validation=1，refine_anchor_motion=1；flags3572即回退旧推荐行为。4096独立路径/末端审计；8192独立历史门控；实验所有支持尺度固定为原图像素，有待跨分辨率验证。

GetResultV2只在tip_confirmed时用tip，complete_length_valid时用complete_length_px。否则数值只作无效输出，不计算到(0,0)距离，不使用历史尖端冒充本帧。CrackV4LastPathAuditJson(handle)返回api_version1、candidate_path、supported_visible_path、截断/局部支撑/独立末端/历史资格。指针立即复制；该查询不推进历史。旧CopyPath在新4096开启时是保留支撑路径，原候选只在新查询，不可把可见前缀当物理完整长度。

旧C struct与PixelV2原样，新增枚举和只读导出。头文件/src和实际dll见交付include/src/bin；build.ps1固定OpenCV4.4.0，scripts/run_all.ps1可重放。每个handle顺序调用；线程与运行库遵守原接口约束。生产禁止启用实验新flags直到人工复核和弱裂纹回归完成。
