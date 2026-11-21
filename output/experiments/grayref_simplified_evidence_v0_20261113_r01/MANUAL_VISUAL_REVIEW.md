# 交付图像抽查与严重失败实例

这是代理实际打开本地 PNG 后的视图复核，不能替代逐帧解码、数组比较、哈希检查或物理裂纹真值认证。所有推理保持冻结。

## 实际打开的证据

- [GROUP_A 视频第 10 秒预览](videos/preview_group_a_10s.png)：对应第 61 帧，标题、观测/桥接图例、原灰度三维曲面及有符号差分均可辨识。
- [验证组C视频第 50 秒预览](videos/preview_group_c_50s.png)：对应第 301/562 帧，明确显示 TIP_UNCERTAIN 和“已曝光验证组、不调参”；图像具有坐标、灰度单位与固定差分色阶。播放 6 FPS 不表示算法性能。
- [三点弯视频第 25 秒预览](videos/preview_three_point_bend_25s.png)：对应第 151/520 帧，主图及两个证据面板完整，明确保留 TIP_UNCERTAIN，未将无输出替换为虚构尖端。
- [三点弯 148 原灰度曲面](galleries/three_point_bend/148/gray_surface_raw.png)：X/Y 为原图像素，Z 是实际灰度 0–255；没有把暗谷响应误标为原灰度。规则采样曲面不能保证显示 1px 细线，应结合全分辨率二维灰度/暗谷及 NPZ。
- [三点弯 148 差分面板](galleries/three_point_bend/148/roi_difference_panel.png)：原始有符号、正向、绝对和局部补偿差分分开；warp 与材料遮罩分开。纹理可信图只在右侧出现窄条，因此“至少一个局部窗口可信”绝非整幅 ROI 或裂纹区域物理配准正确。
- [开发组H 317 无 GT 路径覆盖](galleries/group_h/317/overlay_path_tip.png)：绿色选中段沿上方圆形暗标记外侧轮廓，紫色候选尖端在该轮廓末端；预制缺口右方的细暗线位于更下方。
- [开发组H 317 独立人工对比](offline_label_overlays/group_h/317.png)：实际打开检查后确认粉色人工路径位于预制缺口右方，绿色算法路径位于上方圆形标记，二者分离。页首明确标为 OFFLINE_LABEL_OVERLAY，路径覆盖/精度均 0；蓝圈只是原有公开尖端，未按人工标注修改。

## 开发组H 317 的原生数值

默认 C_FUSION_RAW 的公开尖端为 (2568,296)，离线误差 565.35833164px，状态 PROVISIONAL_TIP。自动缺口假设为 (2643,751.5)，身份未认证；选中路径起点到该假设约 432.824px，观测点 80、推断缺口 0，平均证据约 1.993，起源加分约 0.0593。

该错误轨迹末端仍满足停止条件：后方材料可观测比例 1、可观测负证据比例 1、停止分数 2.2。因此这是“选错暗线也能满足停止条件”的实际反例，不能仅归因于停止阈值，也不能用全序列多数拒绝输出来宣称主裂纹身份安全。

## 可复核性

核心完整性见 [run_integrity.json](run_integrity.json)。最后的辅助交付签名和全部本地链接核验见 [supplemental_delivery_seal.json](supplemental_delivery_seal.json)，环境、磁盘与从冻结到交付的总耗时见 [delivery_cost.json](delivery_cost.json)。后两份由最终交付检查生成；耗时包含绘图和审计，不是单帧推理延迟。
