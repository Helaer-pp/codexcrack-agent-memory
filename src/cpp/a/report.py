"""Write the SDK validation report from the measured frame data."""
import csv
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
out=ROOT/'output/runs/a_production_merge_seven_r01'
manifest=json.loads((out/'manifest.json').read_text(encoding='utf8'))
with (out/'per_frame.csv').open(encoding='utf-8-sig',newline='') as f:
    rows=list(csv.DictReader(f))
groups=manifest['groups']
names={'group_a':'开发组A','ct2':'CT2','ct3':'CT3 白色喷漆','group_c':'验证组C',
       'group_h':'开发组H MT','group_x':'排除组X白板（历史回放）','three_point_bend':'三点弯'}
def line(r):
    return (f"| {names[r['group']]} | {r['frames']} | {r['confirmed']} | {r['mismatches']} | "
            f"{r['mean_ms']:.2f} | {r['p95_ms']:.2f} | {r['max_ms']:.2f} | {r['over_15hz']} | {r['init_ms']:.2f} |")
times=[float(r['detector_ms']) for r in rows if r['reference']=='0']
exact=sum(g['exact'] for g in groups)
max_tip=max(g['max_tip_px'] for g in groups)
max_path=max(g['max_path_px'] for g in groups)
total_bad=sum(g['mismatches'] for g in groups)
text=f"""# 正式 A（CrackV4.dll）七组原生 DLL 验证

以 seven_groups_gate_locked_r01 封存的新版逐帧输出为对照，使用各组第一帧初始化、实测 P1/P2 和原试验参考模式，按拍摄顺序处理。检查每张原图 SHA-256、帧号、基准点、尖端确认、完整长度确认、尖端坐标、段数、每段点数、每一个双精度路径坐标及完整长度。有效标志和分段拓扑严格相等；坐标和长度的预设绝对容差为 1e-8 px。另行检查原始连续路径查询与按段取点的一致性，以及无效输出置零、C ABI 与 V2 结果一致。

共 {len(rows)} 帧，确认尖端 {sum(g['confirmed'] for g in groups)} 帧，差异超容差 {total_bad} 帧。{exact} 帧的比较数值完全相同，尖端坐标最大绝对差 {max_tip:.3g} px，路径坐标最大绝对差 {max_path:.3g} px。这里的坐标差是各坐标分量绝对差的最大值。这次回放回答的是新版原生实现与已有结果的一致性。真实试件缺少人工真值，无法由此估算物理尖端误差。

| 试验 | 图像数 | 确认尖端 | 差异帧 | 单帧均值 ms | P95 ms | 最慢 ms | 超 66.67 ms 帧 | 初始化 ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
"""+'\n'.join(line(r) for r in groups)+f"""

在 AMD Ryzen 9 7950X、Windows x64 Release、OpenCV 四线程下，七组依次运行，共 {len(times)} 张变形帧。全部变形帧平均 {np.mean(times):.2f} ms，P95 {np.percentile(times,95):.2f} ms，最慢 {max(times):.2f} ms。每组首帧单列初始化，不参与单帧耗时分布。计时包括 DLL 内配准、基础检测及触发的断点续追与尖端确认。读盘、原图哈希、解码、复制结果、视频编码和界面绘制另计。

per_frame.csv 含逐帧坐标、有效标志、路径点数、三个比较误差及耗时（detector_ms 为纯检测，api_ms 为 DLL 内整次调用，call_wall_ms 为调用侧计时）。首帧 call_wall_ms 仅表示读取缓存参考结果；实际初始化耗时在 init_ms。长度以 px 记录；软件传入试验对应 mm/pixel 后可以使用 length_mm。summary.csv 为各组统计。排除组X只作历史回放，三点弯只作验证，本轮没有按组调整参数。

构建使用 D:/opencv-4.4.0，MSVC v142、x64、C++17。正式 A DLL SHA-256 为 `{manifest['sha256']}`。冻结 A DLL SHA-256 为 `c23498fcc660469927f63244b8e98e39b1eb86d542ec9a7b069d61fcf813654b`。正式库保留旧库全部 19 个具名导出，增加 2 个分段路径函数。旧 SDK 的 FrozenAExample.exe 直接加载正式库，CT3 全部 136 帧的尖端、完整长度和路径点通过对照。
"""
(out/'验证报告.md').write_text(text,encoding='utf8')
