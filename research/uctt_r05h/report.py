from common import *
import numpy as np,collections,datetime,shutil
def table(rr,fields):
 return '| '+' | '.join(fields)+' |\n| '+' | '.join('---' for _ in fields)+' |\n'+''.join('| '+' | '.join(str(r.get(k,'')) for k in fields)+' |\n' for r in rr)
def main():
 assert read(OUT/'media_complete.json')['videos']==6
 summary=read(OUT/'evaluation_summary.json');stats=read(OUT/'full_sequence_stats.json');dev=next(r for r in summary if r['dataset_id']=='DEVELOPMENT' and r['variant']=='FULL');val=next(r for r in summary if r['dataset_id']=='VALIDATION_ONLY' and r['variant']=='FULL');selected=rows(OUT/'experiments/selected_evaluation.csv');sent=rows(OUT/'experiments/sentinels.csv');regs=rows(OUT/'experiments/registration_quality.csv');synthetic=rows(OUT/'tests/synthetic_matrix.csv');safety=rows(OUT/'tests/frozen_safety_checks.csv');lock=read(OUT/'freeze.json')
 assert all(sha(ROOT/p)==s for p,s in lock['files'].items());assert all(sha(ROOT/p)==s for p,s in lock['protected'].items())
 old={(r['dataset_id'],int(r['frame_id'])):r for r in rows(G/'experiments/selected_visible_eval.csv') if r['variant']=='E1_BEAM'}
 ct=[r for r in selected if r['dataset_id']=='ct2' and r['variant']=='FULL' and r['visibility']=='VISIBLE'];improved=sum(bool(r['working_error']) and bool(old.get(('ct2',int(r['frame_id'])),{}).get('tracking_error_px')) and float(r['working_error'])<float(old['ct2',int(r['frame_id'])]['tracking_error_px']) for r in ct);near=sum(r['correct_stop_preserved']=='True' for r in ct);lost=sum(r['correct_stop_preserved']=='True' and r['working_error'] and float(r['working_error'])>10 for r in ct)
 ct3=next(r for r in stats if r['dataset_id']=='ct3');valid=sum(r['state']=='VALID' for r in regs);new=sum(r['classification']=='NEW' for r in regs);total=len(regs)
 report=f'''# R05H 完整算法与六组验证报告

1. **已有完整可调用、已编译并实际执行的 C++ 算法。** `research/uctt_r05h/detector.hpp` 的 `Pipeline::process`，C ABI 在 `runtime.cpp`，DLL 在 `output/build/uctt_r05h/Release/R05H.dll`。完整回放2647张原图，开发4变体6260次 + 验证1082次 =7342次调用。运行命令见源码 README / tests/repro_commands.md。生产 A 没有替换。
2. **开发76张可见标注：正式确认 {dev['observed']}/76；正式≤3/5/10px={dev['observed_hit3']}/{dev['observed_hit5']}/{dev['observed_hit10']}；正式>100/500px={dev['observed_over100']}/{dev['observed_over500']}。** 工作端点 {dev['working']}/76，≤3/5/10px={dev['working_hit3']}/{dev['working_hit5']}/{dev['working_hit10']}；>100/500px={dev['working_over100']}/{dev['working_over500']}。拒绝{dev['rejected']}/76。不是只统计正确确认子集。
3. **CT2 可见选帧 {len(ct)} 张，相对 R05G AUTO BEAM 工作误差下降 {improved} 张。** 距GT≤10px STOP保留{near}张，其中{lost}张仍选择错误位置。误差下降不等于进入10px。多个哨兵从旧版过冲变为本轮提前停止：CT2/431、457、GROUP_A504、开发组H78的有符号前向误差均为负。正确STOP未被覆盖，却被较早高分STOP击败；CT2/395没有保留10px正确STOP。逐候选分数与失败阶段见 candidate_stop_audit.csv / error_attribution.csv。
4. **参考模块真实执行：全六组候选/历史参考尝试{total}次，有效{valid}次（{100*valid/max(1,total):.2f}%），NEW票{new}次。** 其余为UNCERTAIN/UNAVAILABLE；有效注册不等于正确身份。开发组启用固定参考使工作10px命中19→17，正式10px命中7→7，没有测得精度增益。开发真实序列历史导航VALID=0，故FULL与NO_HISTORY结果相同；验证组C历史导航实际有效208次。相同图像不产生NEW票的合同检查已执行。
5. **CT3自动起源：{136-ct3['seed_missing']}/136帧获得起点；旧R05G为0/136。** 路径和端点精度仍须看下表。原始R03 coherent_wrong_first_lock依然FAIL，并会错误写历史；这是旧候选注入状态机，不能把它的失败掩盖成新算法通过。R05H原图划痕负例另行运行，见测试表；真实被误确认的帧仍会写入R05H历史，无法宣称首次锁定安全已解决。
6. **建议冻结为可正常输出、但不达生产精度的研究工程基线。** 正式远错误、弱末端漏选及STOP歧义仍存在。完整模块交付不代表算法验收成功；不得部署替换A。后续如继续研发，保留这次验证结果，不能把验证组变成调参集。

## 验证组优先结论

验证组C、三点弯在源码/DLL/规则冻结后各一次性只读回放，共1082帧。35张VISIBLE、5张UNCERTAIN。正式确认{val['observed']}/35，正式≤10px {val['observed_hit10']}/35，正式>100/500px {val['observed_over100']}/{val['observed_over500']}；工作≤10px {val['working_hit10']}/35，>100/500px {val['working_over100']}/{val['working_over500']}。验证结果未用于修改参数或选择版本；两组已历史曝光，不能称独立未见TEST。

'''
 report+=table([r for r in summary if r['variant']=='FULL'],['dataset_id','visible','uncertain','observed','observed_hit3','observed_hit5','observed_hit10','observed_over100','observed_over500','working_hit10','working_over100','working_over500'])
 report+='\n## 路径覆盖、精度与同条件消融\n\n可见折线按1原像素加密；推断间隙不计为观察路径。所有可见标注共同分母；无输出路径计0。合取要求recall10、precision10都≥0.9且工作端点≤10px。GT为人工路径，间隙本身的可见性未逐像素标注，覆盖率存在该标注限制。\n\n'
 report+=table([r for r in summary if r['dataset_id'] in ['DEVELOPMENT','VALIDATION_ONLY']],['dataset_id','variant','visible','observed','observed_hit10','working_hit10','working_over100','working_over500','path_recall5','path_recall10','path_precision5','path_precision10','path_and_endpoint10'])
 report+='\nNO_REFERENCE关闭固定参考评分，仍保留同一历史导航机制；NO_HISTORY关闭历史导航及写入；LAST_ENDPOINT选择最前方保留STOP作为远端策略。各变体独立状态，输入顺序和采样规则相同，因决策反馈导致历史不同是消融结果的一部分。验证组不运行消融以避免版本选择。\n\n## 全序列状态与实际耗时\n\n'
 report+=table(stats,['dataset_id','frames','states','seed_missing','incomplete','history_writes','history_navigation_valid','p50','p95','p99','max','over50','over500','reference_attempts','reference_valid','reference_new'])
 timings=rows(OUT/'experiments/runtime_breakdown.csv');timing_summary=[]
 for g in ALL:
  part=[r for r in timings if r['dataset_id']==g and r['variant']=='FULL'];row={'dataset_id':g}
  for field in ['io_decode_hash_ms','debug_export_ms','root_ms','tracking_ms','terminal_ms','reference_ms','state_ms']:row[field+'_p95']=float(np.percentile([float(r[field]) for r in part],95))
  timing_summary.append(row)
 report+='\n'+table(timing_summary,list(timing_summary[0]))
 report+='\n单位ms，CPU为本机Ryzen7950X；未验证i7部署。预处理为8bit Mat视图，灰度解码在Python IO项；native含root/tracking/terminal/reference/state，debug JSON导出另计。跟踪研究预算350ms，STOP循环450ms后标为不完整，最多12个候选参考注册在其后执行，因此总耗时并非硬保证≤500ms。参考细分匹配与暗谷比较合记reference_ms；没有虚构不可测分项。视频8fps不是算法吞吐。\n\n'
 report+='## 特殊哨兵\n\n负的signed_forward_error表示提前停止，正值表示前向超出；不能把所有大误差都归因为过冲。\n\n'+table(sent,['dataset_id','frame_id','R05G_auto_beam_error','status','working_error','observed_error','signed_forward_error','stop_nearest','correct_stop_preserved','first_failure','reason'])
 report+='\n## 合成与安全检查\n\n'+table(synthetic,['test','expected','status','error','passed','history_written','reason'])+'\n'+table(safety,['test','passed','status','history_written','error'])
 report+='\n12/24/40px间隙的工作端点与正式确认分别考察；40px可以到达但确认歧义仍失败。2/3列弱响应采样没有被旧最短片段门删除，最终主路径弱片段保留测试仍失败，不能声称弱尖端问题解决。原始R03测试16项15通过，coherent_wrong_first_lock失败，完整原输出见tests/R03_original.csv。原图合成负例不能替代真实阴性FPR；真实阴性GT不足，FPR=N/A。未标注起始帧均已回放，仍不可把它们擅自当无裂纹真值。\n\n'
 report+='''## 实现与已知限制

- 自动起源使用宽松P1/P2几何、宽暗缺口结构、弱暗谷备选，不再要求三个连续强截面。仍只按有序P1/P2右法向展开，未覆盖物理前向不确定时的双向识别。
- R05G `crossSection` 原样保留；缺失点不更新方向；间隙上限48–64像素；保留所有有意义支持下降/缺失STOP。STOP评分由有界当前支持、前后证据、身份、覆盖/间隙与有效参考组成，没有无限长度奖励。每候选沿向前3–50尺度像素探测；预算不足显式标注。
- 两侧各2个材料块分别NCC匹配，纹理、唯一性、正反一致、侧内位移残差和边界共同质控。只有两侧可靠才用于NEW/OLD判断；单侧UNCERTAIN和不可用均为中性。仅局部平移模型，无法保证复杂形变。只审查排名前12个STOP的参考，未审查候选不能称参考支持。
- 起源缺口与过去可信材料导航提供身份。历史导航使用以前OBSERVED路径的起始点和局部双侧映射，并重新读取当前横截面；未实现整条历史曲线形变模型。只有正式OBSERVED写历史，但开发19张、验证2张正式误差>100px的标注帧都写入了历史。因此错误历史写入并未解决；开发导航VALID=0使本次错误存储尚未产生可测导航效应，不能将此误称为安全通过。
- 局部末端0.5像素步进补扫，仅接受实际当前暗谷；path末节点和精定位working_tip可能相差≤3像素。预算边界或图像边界不直接变正式尖端。搜索完成只指当前有限假设搜索，不代表全局最优或无歧义。
- 图像边界会抑制相关STOP确认，但冻结版本未把任何分支触边都提升为全局search_complete=false；需结合STOP的boundary/reason审查。完整逐帧日志保留主路径与全部STOP，未导出每个未选beam节点和原始截面数组。
- 部分TENTATIVE帧因最少当前支持条件未满足，其reason仍为current_identity_terminal_supported：这是冻结版本原因字符串不够细的缺陷；status/observed/历史写入字段才是实际状态，未在验证后改算法掩盖。
- 完整结果中的失败阶段是离线直接可见的首类失败，不是未经测量的因果结论；原图和局部对比保留供审查。未实施GT拟合、自动阈值搜索、训练或未来帧读取。

## 视频、每帧对比与复现

[六组视频索引](galleries/index.html) · [2647帧局部对比](galleries/all_frames.html)。验证组C/三点弯视频置顶，每组包括4秒指标卡及全部原帧；不丢弃失败帧。左列原图，右列输出，两个局部视野分别显示整条路径与末端放大。有人工标注时放大中心可用GT，仅影响离线裁切；算法在这之前已完成并冻结。

```
videos/R05H_group_c.mp4
videos/R05H_three_point_bend.mp4
videos/R05H_group_a.mp4
videos/R05H_ct2.mp4
videos/R05H_group_h.mp4
videos/R05H_ct3.mp4
```

原研究基线55a0与历史发布1c742保持独立身份；本轮视频蓝色点来自旧A55a0已冻结逐帧结果，不重新编译A冒充新算法进步。源文件、配置、原DLL、标注快照均hash核对。全部2647输入原图读取时SHA256核对，排除组X图像/标签打开数0。
'''
 (OUT/'development_report.md').write_text(report,encoding='utf8');shutil.copy2(ROOT/'research/uctt_r05h/README.md',OUT/'tests/repro_commands.md')
 for p in (ROOT/'research/uctt_r05h').glob('*'):
  if p.is_file() and not (OUT/'source_snapshot'/p.name).exists():shutil.copy2(p,OUT/'source_snapshot'/p.name)
 integrity=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_source_dll_unchanged=True,production_config_annotations_unchanged=True,original_frames_hash_verified=2647,validation_frames=1082,excluded_images_opened=0,files=lock['files'],protected=lock['protected'],reference_hashes=lock['references'],opencv='4.4.0',compiler='MSVC19.29 v142 C++17 /O2 /fp:precise /utf-8',video_count=6,local_comparison_images=2647)
 write(OUT/'source_integrity.json',integrity)
 print('REPORT COMPLETE',flush=True)
if __name__=='__main__':main()
