# 基线、身份与清理

第五组历史上已被观察，本轮冻结前未读取第五组输入或结果。本轮只能称有历史预暴露的操作性留出验证。

稳定基线为 flags3572 / Shadow1 / refine1 / terminal1，非撤回v3，也非上轮32244恢复方案。默认行为未替换。旧v3 flags15860。

{
  "baseline_flags": 3572,
  "candidate_flags": 888308,
  "production_flags": 364020,
  "source_workspace": "D:/workspace\\crack_v4_cpp\\local_tip_20261030",
  "dll_sha256": "d63f4bdacf7f4b9646b16eba0de74fef068e34cf9cd3c46d47227e49197a776b",
  "stable_dll_sha256": "c23498fcc660469927f63244b8e98e39b1eb86d542ec9a7b069d61fcf813654b"
}

稳定源提交 d485fe25deb7d68056d5bfc9e0a3cc97aea3847a。旧v3源提交1535019d494b7e7b1e560ee786c3bb0f57b7b74c。本轮源码/脚本提交见freeze_manifest.json。关闭新特性与两影子模式逐帧复现稳定输出，详见各summary。

项目只删除可再生编译中间件和Python缓存，保留原图、坐标、算法历史、DLL和既有交付。清理清单位于 D:/workspace/project_maintenance_20261030/cleanup_manifest.json。


当前项目上一轮完整代码与交付也原地保留，未被清理删除：
D:/workspace/crack_v4_cpp/four_group_recovery_20261030
上一轮算法源提交872510984a16658284ce7e6457bfdd366a5ec37b，DLL SHA256为52ae56280a38122fea7ac267de7a6758f7b379eb820d58dbe6adcbe1bb0f8ba1。
本轮按开发文档指定，从稳定3572作为评估基线，单独建立local_tip_20261030研究工作区，没有覆盖上一轮32244实现或原项目使用中的DLL。
