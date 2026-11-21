# R05F 实际源码依赖图

生产、研究及比较器分开。以下行号在本次封存源码上生成；没有 Git 元数据，版本身份以 SHA256 为准。

```text
生产 A: CreateExtended → Detector → process → measureTip
  localReference → matchTemplate / 相关票 → aligned / eroded
  score → distalLine DP → 候选停止审计 / shared<4 → !path.empty() 确认
研究 B0: R05FCreate → R05FProcess → 小窗口 sampleCurrent
  多尺度当前暗谷 → NMS ridge → 连通片段 → 结构端点/对比下降端点 → 几何去重
  每帧探索数据；无 observed 生产者、无可信历史写入
离线: 已冻结原图输出 + LabelMe 快照 → compare.py → 原图像素距离/路径带覆盖
```

| 文件 | SHA256 | 定位 |
|---|---|---|
| `src/cpp/a/CrackV4.cpp` | `1496c5d1aab92f189e0240d134173582516e8a810e615f1c3cab849dbab809aa` | struct Detector : <br>Detector(const : 509<br>Result Detector::process : 1745<br>int CrackV4Create( : 2209<br>int CrackV4Process( : 2245<br>int CrackV4CreateExtended( : 2389<br>d.measureTip(d.last : 2277 |
| `src/cpp/a/roi_tip.inc` | `82864e96cbbb6ea7ee056fba56fc93bc2ae3bfd808cd1a036cad40f69b8d443a` | cv::Mat1b localReference : 25<br>Path distalLine : 68<br>if(shared<4) : 139<br>void Detector::measureTip : 146<br>else if(eroded : 185<br>path=distalLine : 193<br>r.tip=r.has : 149,224 |
| `src/cpp/a/include/CrackV4.h` | `6944fbc6a905b54c96ab9f070dd974da3aeead24f6db97170637a84f0d775a79` | CrackV4Image : 19,23,40,50<br>CrackV4Process : 50 |
| `research/uctt_r05f/current.hpp` | `b04480f1f949f10fc11fa33ea0a83f16a63c793182ec2560bd9fbf53b02d78f3` | struct Config : 18<br>inline Patch sampleCurrent : 37<br>inline void addCandidate : 57<br>inline void findCurrentDarklineSegments : 69<br>bool anchorsOK : 105<br>void process : 106 |
| `research/uctt_r05f/runtime.cpp` | `8e9bcfcbee879420f31114686dbc755a730488e73a7ae4f04fcfce576c7042ba` | std::string describe : 6<br>void* R05FCreate : 16<br>int R05FProcess : 17 |
| `research/uctt_r05f/replay.py` | `d96a63cfdbf81ca48ed419b8ac5bfcabc56b6f5aab775805266472f8d62ec024` | class Native : 7<br>def main : 31 |
| `research/uctt_r05f/compare.py` | `da2587d6f499b463b1eb39ceea357bc4a3f7af273f2f5cbfb8a5c6cbbae6ee48` | def evaluate : 16 |

## 基线身份注意事项

S0 完整回放使用现有研究基准 `output/build/src/cpp/a/Release/CrackV4.dll`（55a0…）；项目配置指向的发布包 DLL（1c742…）二进制哈希不同，两者分别冻结。不能写成两个文件字节相同。生产输出等价结论以 A0_equivalence.csv 中明确指定的现有基准为准。发布包未经本轮重新部署。

## 小窗口与原图映射

窗口局部 x 沿 P1→P2 的右法向，y 沿其法向。记录每个窗口 polygon，双线性有效采样的 2×2 原图像素足迹逐窗计数；帧内并集通过原图 visited 位图计数。sum 与 union 不混用。当前实现静态覆盖仅为 B0/S1 对照，尚非 S2 步进。