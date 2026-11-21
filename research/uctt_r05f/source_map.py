from common import *

def main():
 mapping={
 'src/cpp/a/CrackV4.cpp':['struct Detector','Detector(const','Result Detector::process','int CrackV4Create(','int CrackV4Process(','int CrackV4CreateExtended(','d.measureTip(d.last'],
 'src/cpp/a/roi_tip.inc':['cv::Mat1b localReference','Path distalLine','if(shared<4)','void Detector::measureTip','else if(eroded','path=distalLine','r.tip=r.has'],
 'src/cpp/a/include/CrackV4.h':['CrackV4Image','CrackV4Process'],
 'research/uctt_r05f/current.hpp':['struct Config','inline Patch sampleCurrent','inline void addCandidate','inline void findCurrentDarklineSegments','bool anchorsOK','void process'],
 'research/uctt_r05f/runtime.cpp':['std::string describe','void* R05FCreate','int R05FProcess'],
 'research/uctt_r05f/replay.py':['class Native','def main'],
 'research/uctt_r05f/compare.py':['def evaluate']}
 text=['# R05F 实际源码依赖图\n','生产、研究及比较器分开。以下行号在本次封存源码上生成；没有 Git 元数据，版本身份以 SHA256 为准。\n','```text\n生产 A: CreateExtended → Detector → process → measureTip\n  localReference → matchTemplate / 相关票 → aligned / eroded\n  score → distalLine DP → 候选停止审计 / shared<4 → !path.empty() 确认\n研究 B0: R05FCreate → R05FProcess → 小窗口 sampleCurrent\n  多尺度当前暗谷 → NMS ridge → 连通片段 → 结构端点/对比下降端点 → 几何去重\n  每帧探索数据；无 observed 生产者、无可信历史写入\n离线: 已冻结原图输出 + LabelMe 快照 → compare.py → 原图像素距离/路径带覆盖\n```\n','| 文件 | SHA256 | 定位 |\n|---|---|---|']
 for name,keys in mapping.items():
  p=ROOT/name;lines=p.read_text(encoding='utf8').splitlines();loc=[]
  for key in keys:
   found=[str(i+1) for i,line in enumerate(lines) if key in line];loc.append(key+' : '+','.join(found))
  text.append(f'| `{name}` | `{sha(p)}` | '+ '<br>'.join(loc)+' |')
 text.extend(['\n## 基线身份注意事项\n','S0 完整回放使用现有研究基准 `output/build/src/cpp/a/Release/CrackV4.dll`（55a0…）；项目配置指向的发布包 DLL（1c742…）二进制哈希不同，两者分别冻结。不能写成两个文件字节相同。生产输出等价结论以 A0_equivalence.csv 中明确指定的现有基准为准。发布包未经本轮重新部署。','\n## 小窗口与原图映射\n','窗口局部 x 沿 P1→P2 的右法向，y 沿其法向。记录每个窗口 polygon，双线性有效采样的 2×2 原图像素足迹逐窗计数；帧内并集通过原图 visited 位图计数。sum 与 union 不混用。当前实现静态覆盖仅为 B0/S1 对照，尚非 S2 步进。'])
 (OUT/'source_dependency_map.md').write_text('\n'.join(text),encoding='utf8')
if __name__=='__main__':main()
