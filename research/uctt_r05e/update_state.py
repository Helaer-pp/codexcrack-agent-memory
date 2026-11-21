"""Record completed findings in active project routing docs; preserve history."""
from common import *
def main():
 assert read(OUT/'final_integrity.json')['status']=='PASS'
 data=read(OUT/'group_summary.json');val=[r for r in data if r['dataset_id'] in VAL];vraw=sum(r['raw10'] for r in val);vkeep=sum(r['retained10'] for r in val);vlost=sum(r['capacity_lost10'] for r in val)
 rel=OUT.relative_to(ROOT).as_posix()
 block=f'''## R05E：当前证据解耦通过，空间桶候选安全失败

真实隔离C++17代码`research/uctt_r05e/`，产物`{rel}/`。生产源码/DLL未改。B0完整开发1565帧与冻结A/R05D非计时输出一致；B1/B2完整开发1565及冻结后验证1082帧均保持原输出/ROI/长度/状态，选帧legacyScore逐位一致。B1恢复全部50个R05D G1当前响应；开发76 VISIBLE中current10=74，raw10=67。B2固定4×4桶、每桶4个、K64压缩后retained10=55，12例近端候选被桶内容量误删，Gate FAIL；B3/B4/B5 BLOCKED，不得生产替换。

四哨兵B2最近保留候选：CT2/395 8.31px、开发组H/78 12.15px、GROUP_A/504 7.12px、CT3/65 1.64px；这些不是新的确认输出，原A大偏差仍在。GROUP_A/398原本0.96px近端raw722被桶10删除。76个原生DP重算控制与B1 current-source峰完全一致；开发组H/41、78、115当前支持像素的gain不足12，CT2/196、338、431及开发组H/304不满足向前停止极值。不要用调整10px容差或降低阈值宣布修复。

原始R03同一fixture仍15/16通过，coherent_wrong_first_lock失败；不能把旁路无输出/无历史写入称为锁定安全通过。冻结后验证组C/三点弯35 VISIBLE raw10={vraw}、retained10={vkeep}、预算误删{vlost}；5 UNCERTAIN不评分。验证数据没有参与改规则。排除组X完全排除，人工标注仅对比/QC，不训练、不拟合。无真实阴性标签，真实FP NOT_VERIFIED。目标i7及新初始点扰动稳定性NOT_VERIFIED，完整原生计时见报告，K64不等于CPU达标。

下一轮优先研究开发组中结构链/停止位置的预算保留，随后区分弱累积支持与非停止极值两类G2；两关通过才允许新归属/终止。禁止据验证组调参。保留所有R05E失败证据和旧输出。

[问题结论](../{rel}/problem_findings.md) · [完整报告](../{rel}/development_report.md) · [120帧图册](../{rel}/R05E_Failure_And_Improvement_Gallery.html) · [结果视频](../{rel}/R05E_Validation_Results.mp4) · [验收门](../{rel}/gate_matrix.csv)。

'''
 p=ROOT/'docs/CURRENT_STATE.md';s=p.read_text(encoding='utf8');assert '## R05E：' not in s;p.write_text(s.replace('# 当前开发状态\n\n','# 当前开发状态\n\n'+block,1),encoding='utf8')
 p=ROOT/'README.md';s=p.read_text(encoding='utf8');intro=f'最新诊断见 [R05E问题结论]({rel}/problem_findings.md)、[完整报告]({rel}/development_report.md)、[图册]({rel}/R05E_Failure_And_Improvement_Gallery.html) 和 [结果视频]({rel}/R05E_Validation_Results.mp4)。B1证据解耦通过，B2候选预算误删12个开发可见案例，B3/B4停止；生产仍为A。\n\n';s=s.replace('最新诊断见 [R05D报告]','上一轮诊断见 [R05D报告]',1);p.write_text(s.replace('# CodexCrack\n\n','# CodexCrack\n\n'+intro,1),encoding='utf8')
 p=ROOT/'AGENTS.md';s=p.read_text(encoding='utf8');s=s.replace('- Latest work is R05D diagnostic research','- Previous work is R05D diagnostic research',1)
 bullet=f'- Latest work is R05E research in `research/uctt_r05e/`, results `{rel}/`. Production unchanged. B0 1565 development frames exact; B1/B2 all2647 frames preserve original outputs and selected legacyScore. B1 restores all50 former G1 responses; development76 VISIBLE: current10=74, raw10=67. B2 K64/4x4 buckets/4 per bucket retains55/76 and loses12 true-near candidates by bucket capacity (GROUP_A398 raw722 was0.96px from label). B3/B4/B5 BLOCKED; original R03 coherent_wrong_first_lock still FAIL. group_h78 has current response but supported pixels fail gain12; CT2 several cases fail forward-stopping maximum. Read problem_findings/development_report and retain frozen evidence. Next research: structure/stop-aware candidate retention on DEVELOPMENT only, then attribution/terminal only after gates pass; never interpret shadow candidates as observed accuracy. Validation-only35 VISIBLE raw10={vraw}, retained10={vkeep}; no tuning from it. No production merge, no label training, no group_x use.\n\n'
 p.write_text(s.replace('## Current algorithm and evidence\n\n','## Current algorithm and evidence\n\n'+bullet,1),encoding='utf8')
 print('ACTIVE STATE UPDATED; production routing remains A')
if __name__=='__main__':main()
