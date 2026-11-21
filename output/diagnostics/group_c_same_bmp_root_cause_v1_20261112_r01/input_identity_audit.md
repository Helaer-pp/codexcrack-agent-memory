# 输入身份与调用链审计

| 角色 | 完整原图路径 | 文件SHA256 | 解码uint8数组SHA256 | shape/bpp |
|---|---|---|---|---|
| reference | D:/datasets\1-引伸计\1-裂纹\2-验证组C\1\1 (1).bmp | cfe718b7a6e4f255e999a00bba270a619576c8c62bc969d9f21edc912fb80862 | 700542e546cd7b25c0a9843e62a1d2f6ecd37b069e61263c54a0fc6739c01f44 | [5120, 5120]/8 |
| current | D:/datasets\1-引伸计\1-裂纹\2-验证组C\1\3 (175).bmp | cc9584ce44e5ebbe601d63decbbf91ecdd564a7ba009994317d8c551eebda5c4 | f588fcce606de63311b6937100ae6cf3be84d56e88edfe9c8199dd6ce145874d | [5120, 5120]/8 |

| 点集 | P1 | P2 | 来源 |
|---|---|---|---|
| R_G | [2243.75, 2247.5] | [2260.0, 2431.25] | task frozen reference defaults |
| C_G | [2242.75, 2252.5] | [2259.0, 2435.25] | saved original NCC; independently rerun exact |
| R_S | [2248.46, 2250.77] | [2244.49, 2439.53] | original tracking TXT num record |
| C_S | [2248.22, 2256.98] | [2243.74, 2442.37] | original tracking TXT num record |

| 参考/当前 | 点 | S−G dx | S−G dy |
|---|---|---|---|
| R | 1 | 4.71000 | 3.27000 |
| R | 2 | -15.51000 | 8.28000 |
| C | 1 | 5.47000 | 4.48000 |
| C | 2 | -15.26000 | 7.12000 |

原始记录采用GB18030读取，四个坐标保留原精度；源TXT没有图像文件名，映射沿用已记录的num=项目零基frame_id，正式评估frame_id=num+1。对照项目manifest中对应图片完整路径、filename和图像SHA逐一一致。来源行、manifest、旧adapter/worker版本均在run_identity记录。没有独立采集日志可额外认证上游num语义；本轮未发现执行层映射不一致。

旧黄金与新NCC重跑/current显式传入彼此一致。A/D重新执行旧summary与完整trace完全一致。所有原生调用只传reference/current、P点和输出路径；没有gt-tip、right-edge或阈值覆盖参数。模板29、search25、NCC0.8和所有检测常量均来自冻结源。

BMP存储高度正值，解码器按正常BMP方向恢复；无EXIF方向字段。OpenCV imdecode原始字节、ASCII staging imread和Pillow L数组逐像素一致。灰度读入不会改变原文件；没有翻转、旋转、重采样或截取后作为输入。更多字段见input_provenance.csv。读取路径与数组hash只说明同输入身份，不能证明物理点语义相同。
