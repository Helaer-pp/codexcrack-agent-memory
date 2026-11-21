# 本项目本地依赖

- `opencv440/`：从用户指定的D:/opencv-4.4.0/build复制的4.4.0 Release运行库、导入库、头文件及原许可证；正式C++和本项目构建均使用此版本，不依赖旧工程目录。
- `ffmpeg/`：原已安装FFmpeg/FFprobe的项目内副本及许可证，用于离线媒体导出和核验。

Python、Visual Studio编译器、Windows SDK和系统中文字体仍由当前Windows环境提供。可配置工具路径在config/project.json，实际Python包版本在requirements-lock.txt。没有下载或切换OpenCV版本。
