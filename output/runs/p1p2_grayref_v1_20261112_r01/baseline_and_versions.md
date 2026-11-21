# 基线身份与版本

完整包：`.\P1P2_GrayRef_V1_Frozen_B7E784AAE881BCE5918C%85.zip`，SHA256 `71385d946d6b1e3bcc56cde60d186853e9a5c770bf44940be6ef42a777010a9c`。配套README、batch、六行golden均可用，package_identity.json逐件记录。preflight_status.json中缺资料状态是历史启动快照，已由package_identity与本报告解决，不能抹掉当时记录。

冻结Python SHA256 `2e2e5ebef80ab33e486c561b6dec09ee15d23033020cc1886a7de24c7ce2baf6`；所有2647帧按此源执行，source_snapshot byte-for-byte相同，source_diff.patch为空。C++候选DLL SHA256 `58e073e7830ccccba77e6cea48e1c33d0977317ed896d1b535d0def7f9d93ef1`。MSVC v142 / C++17 / OpenCV4.4 / O2 / fp:strict，原生和Python不同库版本通过实际parity，不宣称因版本号相同而一致。

Python环境：`{"python": "3.12.7 | packaged by Anaconda, Inc. | (main, Oct  4 2024, 13:17:27) [MSC v.1929 64 bit (AMD64)]", "opencv": "4.12.0", "numpy": "1.26.4", "scipy": "1.17.1", "pandas": "2.2.2", "matplotlib": "3.10.9", "platform": "Windows-11-10.0.26200-SP0"}`。包中原运行环境另见input_package/requirements_tested.txt和freeze_manifest.json；当前环境六档golden仍完全一致。

研究A：R02/R05D build55a0，历史发布：A1c742，两种身份不同，准确率只从研究A55封存dev_frames/val_frames读取。生产源码和两个DLL共19个保护文件的原SHA均保持；详见最终完整性。复用旧结果不是本轮重新验证旧A算法。

严格数据隔离：开发4组1565帧/80标签（76可见），验证2组1082帧/40标签（35可见），排除组X0。标签只在完成推理之后作离线对比，不作训练、伪标签、参数搜索、参考选择、ROI或路径指导。解码/移植未读取GT。验证规则锁与metadata修复amendment分别保留。
