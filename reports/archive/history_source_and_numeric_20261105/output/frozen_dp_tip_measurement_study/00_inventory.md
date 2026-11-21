# Stage0 盘点与冻结基线

真实冻结A：D:/workspace\output\frozen_dp_tip_measurement_study\02_source\binaries\A\CrackV4.dll

SHA256: c23498fcc660469927f63244b8e98e39b1eb86d542ec9a7b069d61fcf813654b；源快照提交：b4531b691ff54e21b77d7cbf8cb5d3aa65b5e6a0。来源为原stable源树和此前冻结稳定二进制，不是上一轮Frangi/STOP研究DLL。A本轮没有重编译，新增旁路将另建DLL。

{
  "platform": "Windows-11-10.0.26200-SP0",
  "CPU": "AMD64 Family 25 Model 97 Stepping 2, AuthenticAMD",
  "logical_cpus": 32,
  "physical_cpus": 16,
  "RAM_bytes": 67768807424,
  "opencv_threads": 4,
  "opencv_native": "4.4.0",
  "SDK": "D:/opencv-4.4.0",
  "compiler": "MSVC v142 x64 C++17 Release /O2 /MD /fp:precise",
  "python_opencv_IO_only": "4.12.0"
}

原接口 Create/Extended 输入GRAY8与两个Point2d；Process输入每帧当前点，NULL表示旧自动配准但主测试不使用；CopyPath(0)为含根部桥接完整折线，CopyPath(1)为observed；GetResultV2只读，SHADOW不替代legacy正式标志。坐标原图x右y下；长度px；旧V2坐标和弧长0.01px取整，CopyPath保留双精度，正式图像必须记录这一表示差异，不能改写A。

- {"group": "group_a", "directory": "D:/datasets\\裂纹数据\\CT裂纹\\开发组A\\测试-1", "reference": "D:/datasets\\裂纹数据\\CT裂纹\\开发组A\\测试-1\\20240328171125068-2.bmp", "images": 551, "current": 550, "reference_shape": [2072, 1856], "native_dtype": "uint8", "current_shape_set": [[2072, 1856]], "per_frame_anchors_present": 551, "missing_anchor_count": 0, "anchor_coordinate_system": "uncropped unscaled original pixels; num0 maps reference, num1 second image; physical point identity fixed per user", "direction": "existing explicit AnchorPositive flag: P1-to-P2 clockwise image normal; dataset configuration, not universal new-project assumption", "timestamp": "filename may encode acquisition clock; not validated loading phase; phase N/A", "exposure": "per-path quality will be audited; whole sequence not labelled no-crack"}
- {"group": "group_c", "directory": "D:/datasets\\1-引伸计\\1-裂纹\\2-验证组C\\1", "reference": "D:/datasets\\1-引伸计\\1-裂纹\\2-验证组C\\1\\1 (1).bmp", "images": 562, "current": 561, "reference_shape": [5120, 5120], "native_dtype": "uint8", "current_shape_set": [[5120, 5120]], "per_frame_anchors_present": 562, "missing_anchor_count": 0, "anchor_coordinate_system": "uncropped unscaled original pixels; num0 maps reference, num1 second image; physical point identity fixed per user", "direction": "existing explicit AnchorPositive flag: P1-to-P2 clockwise image normal; dataset configuration, not universal new-project assumption", "timestamp": "filename may encode acquisition clock; not validated loading phase; phase N/A", "exposure": "per-path quality will be audited; whole sequence not labelled no-crack"}
- {"group": "ct2", "directory": "D:/datasets\\裂纹数据\\CT裂纹\\CT2", "reference": "D:/datasets\\裂纹数据\\CT裂纹\\CT2\\20241101162904251-1864.bmp", "images": 468, "current": 467, "reference_shape": [5120, 5120], "native_dtype": "uint8", "current_shape_set": [[5120, 5120]], "per_frame_anchors_present": 468, "missing_anchor_count": 0, "anchor_coordinate_system": "uncropped unscaled original pixels; num0 maps reference, num1 second image; physical point identity fixed per user", "direction": "existing explicit AnchorPositive flag: P1-to-P2 clockwise image normal; dataset configuration, not universal new-project assumption", "timestamp": "filename may encode acquisition clock; not validated loading phase; phase N/A", "exposure": "per-path quality will be audited; whole sequence not labelled no-crack"}
- {"group": "group_h", "directory": "D:/datasets\\裂纹数据\\CT裂纹\\开发组HMT", "reference": "D:/datasets\\裂纹数据\\CT裂纹\\开发组HMT\\20250314143255927-3304.bmp", "images": 410, "current": 409, "reference_shape": [1406, 5112], "native_dtype": "uint8", "current_shape_set": [[1406, 5112]], "per_frame_anchors_present": 410, "missing_anchor_count": 0, "anchor_coordinate_system": "uncropped unscaled original pixels; num0 maps reference, num1 second image; physical point identity fixed per user", "direction": "existing explicit AnchorPositive flag: P1-to-P2 clockwise image normal; dataset configuration, not universal new-project assumption", "timestamp": "filename may encode acquisition clock; not validated loading phase; phase N/A", "exposure": "per-path quality will be audited; whole sequence not labelled no-crack"}

第五组本阶段只记录用户既有目录和隔离用途；没有打开本轮第五组图像或其历次测量结果，也不统计帧数。51/473历史挑战已在会话曝光，后续不能声称严格盲测。

上轮历史材料仅用前四组部分：CrackV4_V5_ZeroGT_Study/03_experiments 与06_reports中DEV根因；本轮不读取其第五组结果。本轮源码和资源完整可用。历史全媒体的存在与解码不能等同本轮已交付；新视频将在本轮实际生成并独立验收。
