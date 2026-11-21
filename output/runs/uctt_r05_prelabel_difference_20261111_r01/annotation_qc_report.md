# LabelMe 标注包 QA

- PASS：140 张原图，7 组各20张，15 development / 5 holdout。
- PASS：源 SHA256 一致、原分辨率不变、主标注图无重复源 SHA；参考副本单独存放。
- PASS：140 个 JSON 的 shapes=[]、flags={}，未预填尖端、路径或无裂纹结论。
- PASS：实际 LabelMe 5.2.1 MainWindow.loadFile + Qt 图像/canvas 加载全部 140 个 JSON；不是仅 JSON 解析。离屏窗口逐组截图在运行目录 labelme_open_*.png，未触发保存。
- PASS：便携 annotation_qc.py 检查所有图像/JSON、尺寸、split 和坐标；当前全部 UNANNOTATED。
- 标注集全部来自曝光序列，holdout 不是独立泛化证据。物理阶段尚待人工确认。
