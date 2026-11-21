from common import *
import difflib,shutil,platform

def table(records,keys):
    return '| '+' | '.join(keys)+' |\n|'+'|'.join(['---']*len(keys))+'|\n'+''.join('| '+' | '.join(str(r.get(k,'')) for k in keys)+' |\n' for r in records)

def execute():
    guard();coverage=rows(RUN/'04_reference_validity/real_coverage_by_group.csv')
    v2=json.loads((RUN/'05_DEV/full_v2/decision_summary.json').read_text())
    v3=json.loads((RUN/'05_DEV/full_v3/decision_summary.json').read_text())
    stats=json.loads((RUN/'05_DEV/full_v3/DEV_statistics.json').read_text())
    known=json.loads((RUN/'04_reference_validity/known_GT_summary.json').read_text())
    timing=json.loads((RUN/'07_native_timing/summary.json').read_text())
    nativegate=json.loads((RUN/'03_A_candidate_audit/Gate0_final_native.json').read_text());assert nativegate['frames']==3035 and nativegate['passed']
    pre=rows(RUN/'04_reference_validity/prefilter_four_groups_diagnostic.csv');prestats=[]
    for g in dict.fromkeys(x['group'] for x in pre):
        rr=[x for x in pre if x['group']==g and x['frame_id']!='0'];prestats.append(dict(group=g,frames=len(rr),legacy=sum(x['old_joint']=='True' for x in rr),v2=sum(x['v2_joint']=='True' for x in rr),prefilter=sum(x['prefilter_joint']=='True' for x in rr)))
    csvout(RUN/'04_reference_validity/prefilter_summary_by_group.csv',prestats)
    # v1 observer's display-only invalid fraction used 0/255 without normalization.
    # Preserve raw records; export mathematically corrected fractions explicitly.
    tiles=[]
    for z in jl(RUN/'03_A_candidate_audit/native_tile_observer.jsonl'):
        for i,t in enumerate(z['tiles']):
            tiles.append(dict(group=z['group'],frame_id=z['frame_id'],tile_id=i,x=t[0],y=t[1],dx=t[2],dy=t[3],gain=t[4],support=t[5],median=t[6],threshold=t[7],
                invalid_fraction=t[8] if z.get('observer_encoding')=='INVALID_FRACTION_0_1' else (254+t[8])/255,path_size_pre_measure=int(t[9]),dp_size=int(t[10]),raw_observer_invalid_field=t[8]))
    csvout(RUN/'03_A_candidate_audit/native_tile_samples.csv',tiles)
    gates=dict(decision='KEEP_A',research_value='PARTIAL_CANDIDATE_AND_DEV_EVIDENCE',Gate0='PASS_3035_BITWISE_PATH_AND_STATE',
        activation='PASS_12_INDEPENDENT_PAIRS_3_PROCESSES',GateA='PARTIAL_CANDIDATE_RECALL',GateB='REFERENCE_NOT_GENERALIZED',
        GateC='DEV_ONLY_NOT_PASSED_INDEPENDENT_TEST',TEST='NOT_STARTED_GATE_B_FAILED',Gate15Hz='FULL_APRIME2_NATIVE_NOT_TESTED',
        new_production_DLL=False,real_physical_accuracy='N/A',monotonic_prior=False)
    save(RUN/'09_reports/gates.json',gates)
    write(RUN/'00_executive_summary.md',f'''# A′2 本轮结果：KEEP_A

生产 A 保持原样。完成 C++ 旁路、候选生成、参考选块/区间审查、短端/继续延伸研究决策与失败归因。没有通过跨场景参考门槛，因此没有启动独立 TEST，也没有发布 A′2 生产 DLL。

- 最终原生复测 3035/3035：A/旁路的状态、尖端、旧弧长一致，完整 float64 路径逐字节相同；原源码/DLL 哈希不变。
- 新 DEV：180 案例 / 540 帧，432 可观察正例；12 对独立假尾/真长配对、三种材料过程均实际激活，共 36 个配对帧。当前图像及基准点相同，参考不同。
- A 正确 359/432；候选 oracle 379/432；研究决策正确 365/432。6 个修正来自 2 个独立 pair；不是 6 个独立试件。
- v2 改动 6 帧、6 帧达到 ≤8px；选块前置 v3 改动 9 帧，另外 3 帧仍有约 9.74–10.91px 误差，不能算正确修复。
- 两个 DEV 版本均未改错已经正确的 A；36 帧 55°、36 帧 75°、36 帧 S 弯及 36 帧静态划痕交叉保持原结果。弱裂纹仍仅 7/36 正确，不能称已解决弱裂纹。
- 参考同末端审核：旧 A′ 337/3029，v2 为 240/3029。候选多区间 339/3029 是另一口径，不能作为相对 337 的提升。四个原零支持组仍为零。
- 全部 A′2 核心含候选/参考/决策未做原生实现，15Hz = NOT_TESTED。原生旁路库仅是观测工具。

[完整开发报告](09_reports/development_report.md) · [视频/逐帧图](index.html) · [DEV 失败逐帧表](05_DEV/full_v3/failure_stages.csv) · [真实关键失败帧](09_reports/historical_failure_frames.csv)
''')
    write(RUN/'09_reports/development_report.md',f'''# A′2 开发与失败帧报告

本轮结论 **KEEP_A**。H1 有部分候选价值，H3 仅有已曝光 DEV 的有限改善；H2 未泛化，H4 完整原生性能未测。退回 A 本身不构成新算法安全性证明。

## 1. 基线是否守恒
保留生产源码、头文件、DLL、ABI、flags3572 / SHADOW1 / terminal1 / refine / 4线程。最终独立 C++ 双句柄回放 3035 帧，完整路径 memcmp 相同；原生 JSON 去除计时字段后与封存基线全部相同。基线原图 SHA 另见输入审核。初始化一次，参考 GetBaseline 是缓存查询，当前帧按时序和逐帧两点输入。

## 2. 真正触发了什么故障
先试原纹理强度的 DEV v1，再根据材料块信息不足增加背景可观察纹理，形成 v2；二者全部保留，均为 EXPOSED_DEV。新过程为 Poisson 颗粒、分片晶粒、有限核各向异性磨痕，未复制真实图像。程序线端只作为离线 GT。

主 DEV 180 案例/540 帧，432 可观察正例、72 阴性、36 不可观察正例。12 对真假尾、36 配对帧实际同时满足假尾 A 错 >32px、真长 A 正确 ≤8px。真假当前像素 SHA 与锚点完全相同。静态尾的对比度在变形帧变化是有意设置的干扰；它证明的是此受控机制，并不能唯一确定真实材料的物理归属。

## 3. 候选与选择必须分开
K≤12；A 原端点逐位保留。其余来自当前暗谷前后持续变化、几何变化、原生 tile 增益/支持变化；法向有限偏移单独记录 raw_xy。B 竞争次路径、可比历史末端未实现，字段 null。没有第二次全图 DP。

A 正确359，oracle379，最终365。强假尾36帧中仅20帧候选在8px内；候选不是沿路径任意 GT 挑点。DEV v3剩余失败：{stats['failure_stages']}。本集没有出现可量化的路径分叉离轨失败，不代表真实图中不存在；主路径无路径与可达路径候选遗漏另列。

## 4. 参考有效性和失败原因
以下均为变形帧，第一张自比较已排除。

{table(coverage,['group','current_frames','old_joint','fraction_joint','balanced_joint','interval_joint','mean_path_coverage'])}

old/fraction/balanced 为同一个 A 末端的固定审核框；interval 为3个候选查询有效域的并集。339帧只有至少一个局部查询通过，不等于整条争议段可信。

选块退化原因已定位：v2 先在点级灰度 mask 找角点，再筛 patch 有效比例，孔边/饱和边缘可消耗角点预算后被拒绝。前置比例 mask 的诊断不放松后验阈值，DEV平均路径覆盖由20.16%到58.31%，已知刚性几何控制未出现>1px误接受。只在原四组作后续开发诊断，排除组X/三点弯不参与此修正调优。

{table(prestats,['group','frames','legacy','v2','prefilter'])}

开发组A和开发组H局部近饱和/低信息仍缺可用对应；CT2 虽有大量候选材料角点，真正通过 NCC/唯一性、空间 FIT/HOLDOUT 的对应仍不足。验证组C/三点弯主要是局部残差、FIT不一致和有效域不覆盖；不能把局部几块通过当作整条路径归属成立。

## 5. 错配是否被掩盖
132个已知变换控制/方法，覆盖0.5/1/3/5px、光度、仿射、重复纹理、遮挡、压缩、饱和及参考暗线。旧/比例/空间缓存通过数93/93/90，误接受>1px均0；接受最大误差0.113/0.113/0.248px。空间缓存的尾部误差反而较大，有限控制不能宣称泛化无退化。实际图像的错配物理真值仍 N/A。

## 6. 短端与继续延伸如何比较
只在前段有新增暗谷、争议段≥90%可观察且≥85%持续静态参考线、后段没有连续新增信号再出现时形成 H_STOP 模式。还需当前持续支持变化候选、几何±估计残差与光度±2%下保持同一唯一候选，才在 DEV 给出 RESEARCH_RELOCATED。弯曲本身不构成停止依据，多个稳定候选返回歧义。已有参考裂纹变暗依然是归属混淆风险。

v2六帧正确修正；v3九帧改动中仅六帧正确，另三帧虽从约122px降至约10px误差，仍未达到8px标准。不能通过放宽误差阈值包装成功。

## 7. 反例与消融
A_only、candidate_only、reference_only_shadow、candidate+reference_no_select 保持A实际输出；候选oracle只在离线报告。full_decision 有实际6帧正确改动。参考关闭/屏蔽会消除对应修正；交换参考会改变部分结果，说明参考参与决策；这些控制不能代替物理准确性。候选顺序不影响结果，删去每第五个材料块、几何/光度扰动单列逐帧表。ROI固定审核窗口与重跑搜索不是同一件事；冻结公共ABI没有独立ROI覆盖参数，本轮未执行扩大ROI重新搜索，属于未完成的Gate C验证项。

无已正确A改错，无>160px灾难性改错，仅限这批DEV。没有名义TEST目录；不能将已曝光DEV重新命名为TEST。配对聚类bootstrap仅描述DEV：平均惩罚损失下降{stats['mean_loss_reduction']:.4f}px，95%区间{stats['cluster_bootstrap_95']}，包含零，不支持强效果声明。

## 8. 真实失败帧逐项观察
- 排除组X51：A方向歧义，无有效端点；本轮12个候选，三处局部查询FIT/HOLDOUT全为0，覆盖0。图上长橙线不应被当作已确认裂纹。
- 排除组X473：A arc1084.13px、尖端(2344.05,2409.42)，前缀历史hits5、端点hits1；12个候选，但三处查询仍无可用对应。存在靠近路径转向位置的候选，并没有独立物理依据选择其中一个。排除组X仅作历史追因。
- CT2 6/18/84：A约440–442px，候选11/12/11；三个查询各只有0–2个合格对应，远小于6FIT/4HOLDOUT门槛。不是没有尝试短候选，而是参考证据不能验证它。
- 三点弯100：短路径参考覆盖100%；300/519是局部对应数量不足或HOLDOUT残差不通过。仅曝光验证，不调参。

A的measure采用前30点的历史前缀相似来帮助确认，并非整个新尾段的物理身份确认。当前线恢复/增量响应可能在无关暗纹上继续累计；evidence_ended只说明该路径终于缺支持，不说明之前没有跟错。这是源码可直接观察的风险，具体真实短端仍需人工GT或其他独立证据。

## 9. 性能
原生新增固定256条tile记录约20KiB，复用原DP及响应，仅旁路取样；超过预算显式报告。双句柄交替执行排除固定先后偏差，I/O和JSON在计时外，含Process/V2/CopyPath/分配/旁路复制。原生计时与媒体任务有并发，保留实际最慢值，不将其当作隔离机器极限。

{table([dict(group=t['group'],A_max_ms=t['A']['Max'],observer_max_ms=t['shadow_observer']['Max'],A_over=t['A']['over_budget'],observer_over=t['shadow_observer']['over_budget']) for t in timing],['group','A_max_ms','observer_max_ms','A_over','observer_over'])}

候选/参考/最终决策仍为Python研究实现，完整A′2原生核心 NOT_TESTED，不能宣布15Hz。观察到开发组H原A和旁路都有超66.67ms帧，本轮无实时性通过结论。

## 10. 建议与下一步
保持生产A。下一轮先解决“可达路径上的候选遗漏”和“材料块筛选前后的预算顺序”，分别用已曝光DEV开发；加入真实裂纹本已存在而后续变暗的归属反例。需要完整ROI重跑、位深扰动和新的冻结一次TEST后再讨论发布。现有真实组不可用作独立精度测试。新增人工尖端标注将有助于区分真实路径错误与图像不可观察，但不是本轮已掌握的证据。
''')
    write(RUN/'01_protocol_and_freeze/source_audit.md','''# 实际源码与旁路审计

冻结源 baseline/frozen_a/src/CrackV4.cpp：motion约793–939，两点刚性与材料patch refine；tile约1017–1198，配准采样、亮度偏置、blackhat暗谷和参考差异；seed约1200–1495，入口ROI、可起点mask和DP；ridge359–417，逐列累积最佳前驱与端点；measure1496–1586，平滑、根部连接及历史前缀确认；process1589–1775，tile循环、增益/支持不足/缝隙/方向/边界停止；terminalAudit1789–1890，SHADOW不覆盖legacy；Process2055，GetBaseline2100，CopyPath2116，GetV22145。

已复用：tile增益、支持样本、方向、有效像素、现有DP局部路径和当前原图完整路径。旁路仅新增固定AP2Stop[256]和可选CopyStops导出到独立DLL；不写原DP/阈值/历史。
额外计算：ss中位数的<=96元素暂存、有效mask均值；Python法向5点/前后窗，最多4096路径采样，K<=12。参考最多480缓存/3查询×48patch，额外成本有界，但不满足原生2.77ms余量的任何证明。
缺省：竞争第二路径得分B、可比历史末端T未采集，null；未谎称已实现有限分叉DP备选。

Observer v1的invalid字段误用0/255均值，影响诊断显示不影响候选/检测。raw JSON保留；native_tile_samples.csv用(254+raw)/255恢复有效比例，最终C++修正为1-mean/255并再次3035帧原生对照验证。正式原生产DLL和检测过程未修改。

模板选择、局部几何/光度代码直接从本项目可移植A′模块导入；归档只读取失败机制而不作为运行时依赖。C2的第一个归属转折优先覆盖规则未复制。
''')
    write(RUN/'01_protocol_and_freeze/DEV_change_log.md','''# DEV修改记录 / 未进入TEST

1. 新材料DEV v1：目标假长尾已激活，材料纹理信息不足；保存probe/full全部输出。
2. DEV v2：三种背景统一标准差3.2，增加材料可观察性；不放松参考验收阈值。180案例540帧原始图/GT/推断完整保留。
3. 研究决策先仅模式诊断，后加入几何/光度扰动及唯一当前变化候选，在同一已曝光DEV实测6帧正确改动。
4. 选块前置诊断：点mask找角点后筛patch会消耗角点预算。新增prefilter=True只把<=3%坏像素合同前移，不改后验；同批DEV称full_v3，并在原四组做诊断，排除组X/三点弯不用于此项修改。
5. v3新出现3帧约10px的错误短端，不计为成功；保留v2/v3差异。不按这些结果改8px阈值。
6. Gate B不通过；未生成/运行独立TEST；生产不发布。ROI重跑和完整原生实现未进入执行阶段，明确NOT_TESTED。
''')
    write(RUN/'reproduce.md','''# 实际复现命令

工作目录 .。Python D:/ProgramData/anaconda3/python.exe。外部F盘原图只读；所有输出output/runs/<RunId>。

```powershell
$env:PYTHONUTF8='1'
$env:CRACK_AP2_RUN='aprime2_reproduce_new_id'
$py='D:/ProgramData/anaconda3/python.exe'
& $py -B research/aprime2/bootstrap.py
./build.ps1
& $py -B research/aprime2/native_bridge.py
& $py -B research/aprime2/dev.py --probe --v1
& $py -B research/aprime2/dev.py --v1
& $py -B research/aprime2/dev.py
& $py -B research/aprime2/evaluate.py
& $py -B research/aprime2/decision_experiment.py
& $py -B research/aprime2/controls.py
& $py -B research/aprime2/real_audit.py
& $py -B research/aprime2/counterfactuals.py
& $py -B research/aprime2/analyze.py
& $py -B research/aprime2/selector_prefilter_diagnostic.py
& $py -B research/aprime2/evaluate.py --prefilter
& $py -B research/aprime2/decision_experiment.py --prefilter
& $py -B research/aprime2/counterfactuals.py --prefilter
& $py -B research/aprime2/analyze.py --prefilter
& $py -B research/aprime2/contract_tests.py
& $py -B research/aprime2/timing.py
& $py -B research/aprime2/audit_inputs.py
& $py -B research/aprime2/media.py
& $py -B research/aprime2/report.py
& $py -B research/aprime2/finalize.py
```

源码snapshot在02_source，运行研究源在research/aprime2。独立旁路DLL只是取样器，不是A′2生产算法。最终旁路已修正诊断invalid归一化；原始v1取样JSON只保留历史证据，其归一化转换在报告中说明。GT仅生成/离线评价器读取。全新RunId避免覆盖已有证据。
''')
    print('REPORT_READY',flush=True)

if __name__=='__main__':execute()
