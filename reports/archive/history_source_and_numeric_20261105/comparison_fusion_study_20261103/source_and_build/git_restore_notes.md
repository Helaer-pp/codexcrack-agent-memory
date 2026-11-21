# 离线来源与重放补充

研究代码和报告模板已在 TEST/排除组X新复核前锁定，production A 也未修改。本脚本只复制不可变历史依赖和日志，未修改检测、参数、统计规则或任何测量结果。

Git bundle 恢复时使用 `git -c core.autocrlf=false clone research_frozen.bundle restored_research`，防止 Windows 自动换行改变逐字节源码 SHA。工作区副本按 workspace_layout 保留原相对布局；原始真实 BMP 不重复复制，仍使用 frame_manifest.csv 的授权 F: 数据路径。OpenCV4.4/VS 编译依赖须保留 D: 路径或在新的复现实验中显式登记新路径/哈希。

历史 TipSidecar DLL/LIB/Tests 仅为旧 guard 文件身份核验依赖，放在原 research 路径，未在本轮作为新生产算法调用或发布。真正 A 检测 DLL 的唯一 SHA 为 c23498fcc660469927f63244b8e98e39b1eb86d542ec9a7b069d61fcf813654b。

视频包含参考帧 frame_id=0，后续帧按原编号依次显示；video_frame_zero_based=frame_id。15fps 是演示播放帧率，不是已知相机采样时间或真实加载周期。核心15Hz由独立性能测量判定。

真实图中的 F0/A 原生根部并非由独立物理 GT 校验的同一点；原生弧长保留各自测量起点，不能直接排名物理总长度。共同根部轴投影另列，但它只是统一的程序参考几何，不代表根部已获得物理标定。受控 GT 才具有共同已知根部，并单列根部定位误差。F0 根部邻域25px内的有序路径可用不代表缺失根段已被实测，弧长不补上该缺口。
