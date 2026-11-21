# 清单与一致性

input_manifest.csv为实际文件、原图BMP头、SHA256和逐帧原图P1/P2；原始文件均未改写。DEV1987帧先完成快照比较，随后才运行DEV实验；第五组为遵守隔离，在完整协议冻结后才做输入读取和全组回放。最终覆盖5参考+2510当前。

生产源码/DLL身份见 frozen_a_identity.json；replay_diffs.csv保存每个参考/当前帧的差异数和双精度路径hash。
