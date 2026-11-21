# 未执行硬件验证 NOT_RUN_HARDWARE

最小独立采集：固定原始灰度格式和标定靶，两个曝光条件；独立材料标记至少覆盖裂纹两侧与远场，记录刚体平移/旋转和已知线靶端点。同步保存原图、曝光/增益、硬件触发时间戳、载荷传感器时间戳与采样率、原始P1/P2及质量。先用独立线靶/显微测量标注端点及容差，检测输出不得参与生成GT。至少一个未参与研发的新试件在算法锁定后一次性运行。

schema字段：dataset_id,frame_id,image_sha256,camera_timestamp_ns,trigger_id,load_timestamp_ns,load_N,exposure_us,gain_db,p1_x,p1_y,p2_x,p2_y,mm_per_pixel,independent_gt_tip_x,independent_gt_tip_y,gt_uncertainty_px,phase_source。

验收命令：python validate_capture.py metadata.json。不能用frame_id取模或未标定两点距离替代真实载荷相位。当前硬件/同步数据NOT_AVAILABLE。
