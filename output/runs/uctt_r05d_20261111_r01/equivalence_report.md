# A0/D0逐帧严格等价

PASS：2647/2647，同原图SHA、同初始化/当前锚点、同flags3572/SHADOW1/terminal1/refine=true。规范化只删除 *_ms 计时字段；native JSON、geometry JSON及完整formal/raw_path采用精确数值比较，不使用容差。参考查询单列，不作为推断耗时。每组一实例，完整序列无抽帧重置。D1正常输出另与开发组1565条原哈希一致。

D0只读插桩未改变门；D1的CF2固定ROI改动只在R05D_OFFLINE编译分支，D0 DLL保持初次构建不变。见instrumentation_D0_initial.diff及三个replay_lock。
