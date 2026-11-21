# 实际执行勘误与封存范围

最终冻结 A：2510 当前帧及 5 参考帧，**2515/2515 全状态与双精度 CopyPath 零差异**。原 A 源码、参数和 DLL 未修改。源码主锁 commit c13d3712d620b4c1dc860a32b2ca29632894fcc3；其所有哈希仍通过。下面的调用与计算实现勘误分别封存，不能声称整个执行过程没有任何协议偏差。

1. 第一次封存尝试因报告归档目标目录未创建而失败，发生在 TEST/排除组X执行前。补建目录后形成正式主锁；没有根据 TEST 调参。见 00_manifest/protocol_freeze_erratum.json。
2. 排除组X A 首次调用误传参考模式 Clean(0)，从参考帧状态即触发等价性失败。历史已封存 manifest_final5_sealed.json 明确为 Auto(2)。修复仅恢复历史调用参数，原失败全序列文件保存于 00_manifest/invalid_CF_clean_invocation；更正后一次有效全序列回放与历史完全相同。未来必须使用 source_and_build/replay_A_holdout_historical_config.py --holdout，不能照旧驱动的 Clean 调用。见 reference_mode_invocation_erratum.json。
3. 排除组X F-WIDE 原实现因逐连通域反复全图扫描过慢，在保存 12 条完整行后中断。为完成全量对照，增加单独封存的等价枚举实现：只在该连通域的精确 bounding box 内做 np.where，再加偏移；每次断言像素数量等于连通域面积。全局像素集合和 row-major 顺序与原实现完全相同，其他响应、阈值、掩膜、距离、闭运算、骨架、尖端选择不变。原 F0 窄 ROI 仍执行原始完整计算片段，没有使用该加速器。总计 29 项一致性记录涵盖 12 个程序标签场、既有开发组H宽 ROI 非空路径及所有中断排除组X缓存行，结果相同。之后仅完成一次全量 Frangi 排除组X复核，没有按结果改参数。原部分输出在 CF_slow_enumeration_aborted_partial，源码/驱动/等价报告均在 component_enumeration_* 清单中逐字节封存。**这是一项主锁后的计算实现偏差，不将它描述成 TEST 前已锁定源码；不据此宣称新精度收益。**
4. 逐帧图集、三种长度导出、A/F 相邻帧与双侧时序表属于只读报告补全，单独登记 packaging_freeze_addendum / dynamics_reporting_addendum。它们没有更改确认、路径、评分和 DEV 准入选择。时序表仍使用先定的范数/长度差、40帧块及标距代理分箱，不引入物理相位判据。
5. 三长度补充导出在参考帧的整数 JSON 单位矩阵上触发 OpenCV 类型错误；仅在该只读导出中显式转为 float 后求逆，数值矩阵未改变。原补充脚本/日志及修复前后 SHA 在 export_dtype_failure 和 export_dtype_erratum.json；不是检测或原始指标计算变更。
6. 首次媒体导出因 Windows 沙箱拒绝 os.link 硬链接而中断。该轮部分媒体全部移至 failed_media_hardlink_attempt，明确不是有效交付；正式目录从同一锁定缓存重新完整渲染。仅把两处硬链接操作替换为逐字节复制，并校验F1/F0 SHA相同；不改渲染公式、确认规则或检测。见 media_filecopy_erratum.json，F1复用说明明确为文件副本，不是假称硬链接或复用旧轮视频。

所有最终 TEST 与排除组X数据均无反馈调参。原 F0 ZIP 文件及 A 主锁始终原样保留。Frangi 为 Python 原型，**NOT_TESTED_IN_CPP**，本轮不生成替代 DLL。CF F-WIDE 的 Python 时延采用上述等价实现，其他组保留原枚举，不把跨组时延当作同实现速度排名，详见 07_performance/timing_implementation_map.csv。

冻结 A 完整原生核心本机单次回放最大 **61.5841 ms**，超过 66.67ms 的当前帧 **0/2510**。不含采集、原图解码、基准点跟踪、渲染编码；不是硬实时最坏上界。Frangi 的 Python 播放视频 15FPS 仅是演示帧率。

第五组排除组X是已曝光材料，51/473 是历史已知风险；不是新材料盲测。真实尖端/物理长度精度 N/A。受控 GT、缓存算法间差异、原视频的视觉偏好均不能取代真实物理 GT。工程决策仍为 KEEP_A。

本研究统一以原图 px 输出，没有为不同材料猜测新的 mm/px 标定。A0_path_fraction_outside_F_ROI 是路径采样点的范围外比例，不是弧长加权比例；A 自适应多 tile 搜索区域的精确面积交集未导出，已明确 NOT_AVAILABLE，不能把路径域覆盖代理当成完整搜索域交集。

补充源码属性审计 source_direction_audit.md：原 Frangi 的方向向量可能退化为(0,0)，理想竖向条纹在35°和90°门下均得到约0.999949中心响应。因此35°并非严格排除所有竖线的保证。本审计在 TEST 后进行，只说明原公式的可复现数值属性；未参与选参或改公式，也不能据此断言某张真实图的异常原因。
