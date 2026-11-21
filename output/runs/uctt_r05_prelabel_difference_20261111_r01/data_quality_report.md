# 原图与点映射盘点

- group_a: 551/551 可解码，唯一哈希 551，尺寸 {'1856x2072': 551}；exact source num match。
- group_c: 562/562 可解码，唯一哈希 562，尺寸 {'5120x5120': 562}；exact source num match。
- ct2: 468/468 可解码，唯一哈希 468，尺寸 {'5120x5120': 468}；exact source num match。
- group_h: 410/410 可解码，唯一哈希 410，尺寸 {'5112x1406': 410}；exact source num match。
- group_x: 524/524 可解码，唯一哈希 524，尺寸 {'3036x4024': 524}；exact source num match。
- three_point_bend: 520/520 可解码，唯一哈希 520，尺寸 {'5120x5120': 520}；exact source num match。
- ct3: 136/136 可解码，唯一哈希 136，尺寸 {'2024x1032': 136}；frozen explicit mapping only。

总计 3171 张，非法点 0，精确重复 0。六组原点文件 num 与 manifest 逐帧一致；CT3 仅冻结 CSV 显式文件名/坐标映射，独立原始跟踪文件 NOT_AVAILABLE。固定参考均是各序列 frame_order=0；后续算法只在 t>0 使用该参考。原文件名数字不直接用作帧号。无物理载荷同步，实际裂纹阶段 UNKNOWN。源数据为供应清单的完整原图，已核对哈希，不声称能从像素证明拍摄前不存在任何预处理。
