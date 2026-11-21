# 复现与范围

执行入口在01_source/build_and_run.md。所有算法、生成器、指标与报告代码在 NEW_TEST 生成前锁定；检查00_protocol/protocol_frozen.json和hashes.sha256。图像清单与GT先封存，再运行TEST。正式历史A视频/PNG是鲜明标注的字节复用：先从2515张原始图重新执行A并验证状态/尖端/弧长/double CopyPath一致，再复制上轮媒体，来源与SHA见07_media/official_reuse_provenance.csv。诊断视频和逐帧对比图由本轮新计算的DG结果重绘，原图完整视野单独显示。15 FPS只表示演示播放速度。

物理长度比例本轮仍使用1px单位；没有新标定信息，不把程序像素误差转换为实测物理精度。原始五组数据、生产源码及DLL不写入。第五组从未用于当前阈值选择。新增源数据/TEST不允许覆盖重用。
