# 原灰度缺口追踪 V2 r02

detector.py实现当前帧缺口边界定位、原灰度暗谷追踪与终止。experiment.py从UCTIP-60Q的不可变证据缓存读取原始像素、几何和两路注册差分。evaluate.py进行封存后LabelMe评价。deliver.py导出全帧局部图册和三组视频。

从CodexCrack项目根目录运行，每次指定新的空输出目录。使用项目Anaconda Python，设置PYTHONDONTWRITEBYTECODE=1。把下列RUN替换为该目录，CLI均位于本目录。

1. python check.py
2. python experiment.py dev RUN
3. python evaluate.py dev RUN
4. python experiment.py freeze RUN
5. python experiment.py locked RUN
6. python evaluate.py locked RUN
7. python deliver.py RUN

发布的实际参数和Python文件哈希记录在运行目录freeze.json。逐帧坐标和观测点在dev.jsonl和locked.jsonl中，使用原图坐标。研究版只跟踪从缺口向右的一条路径，全部三组门槛尚未通过。
