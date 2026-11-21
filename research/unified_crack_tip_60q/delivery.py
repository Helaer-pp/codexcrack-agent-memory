"""Post-inference reports, conditional ablation comparisons, media and delivery seal."""
import argparse,collections,json,html,shutil,subprocess
from PIL import Image,ImageDraw
from .common import *
from .config import ARMS
from .pipeline import resultdir

def table(rs,keys):
    return '| '+' | '.join(keys)+' |\n|'+'|'.join(['---']*len(keys))+'|\n'+''.join('| '+' | '.join(str(r.get(k,'')) for k in keys)+' |\n' for r in rs)

def overlays(run,split):
    from .offline_evaluate import labels
    gt=labels(run,split);links=[];inputs={(r['group'],r['frame_id']):r for r in inventory(run,split)}
    for (group,fid),label in gt.items():
        r=readgz(resultdir(run,'FULL',group)/(fid+'.json.gz'))['result'];base=run/'galleries/frames'/group/fid
        image=Image.open(base/'raw.png').convert('RGB');draw=ImageDraw.Draw(image);xa,ya,_,_=r['scene']['bounds'];path=label['path']-np.array([xa,ya]);tip=label['tip']
        if len(path)>1:draw.line([tuple(p) for p in path],fill=(0,220,255),width=2)
        for point,color,name in [(tip,(0,220,255),'OFFLINE GT'),(r['tip'],(255,200,0),'OFFICIAL')]:
            if point is not None:
                x,y=np.asarray(point)-[xa,ya];draw.ellipse((x-7,y-7,x+7,y+7),outline=color,width=2);draw.text((x+9,y),name,fill=color)
        inside=bool(tip is not None and xa<=tip[0]<xa+image.width and ya<=tip[1]<ya+image.height)
        header=Image.new('RGB',(image.width,image.height+40),(20,20,20));header.paste(image,(0,40));ImageDraw.Draw(header).text((8,10),f'POST-SEAL LABEL COMPARISON ONLY | {group}/{fid} | {label["visibility"]} | GT tip inside ROI={inside}',fill='white')
        out=run/'offline_evaluation/overlays'/group/(fid+'.png');out.parent.mkdir(parents=True,exist_ok=True)
        if not out.exists():header.save(out)
        full=Image.open(base/'full.jpg').convert('RGB');fd=ImageDraw.Draw(full);scale=min(1.,1400/int(inputs[group,fid]['width']))
        if len(label['path'])>1:fd.line([tuple(p) for p in label['path']*scale],fill=(0,220,255),width=2)
        if tip is not None:
            x,y=np.asarray(tip)*scale;fd.ellipse((x-6,y-6,x+6,y+6),outline=(0,220,255),width=2);fd.text((x+8,y),'OFFLINE GT',fill=(0,220,255))
        full_header=Image.new('RGB',(full.width,full.height+40),(20,20,20));full_header.paste(full,(0,40));ImageDraw.Draw(full_header).text((8,10),f'POST-SEAL FULL-FRAME LABEL DISPLAY | {group}/{fid} | display scale={scale:.5f}',fill='white')
        full_out=out.with_name(fid+'_full.jpg')
        if not full_out.exists():full_header.save(full_out,quality=92)
        links.append(f'<li>{html.escape(group)} / {fid} / {label["visibility"]} / GT tip inside ROI={inside} <a href="{group}/{fid}.png">ROI GT 对比</a> · <a href="{group}/{fid}_full.jpg">全图 GT 定位</a></li>')
    write(run/'offline_evaluation/overlays'/f'{split}_index.html','<!doctype html><meta charset="utf-8"><h1>独立离线标注比较；不参与推理</h1><ul>'+''.join(links)+'</ul>')

def videos(run,split,groups=None):
    rs=inventory(run,split);checks=[];(run/'videos').mkdir(exist_ok=True)
    if groups is not None:
        rs=[r for r in rs if r['group'] in groups]
        assert rs and set(groups)=={r['group'] for r in rs}
    for group in dict.fromkeys(r['group'] for r in rs):
        part=[r for r in rs if r['group']==group];dest=run/'videos'/(group+'.mp4')
        if not dest.exists():
            partial=run/'videos'/(group+'_encoding.mp4');assert not partial.exists(),'Preserve and inspect interrupted encoding before retry'
            with open(run/'videos'/(group+'_encoder.log'),'wb') as log:
                writer=subprocess.Popen([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-hide_banner','-loglevel','warning','-n','-f','rawvideo','-pix_fmt','bgr24','-s','1800x800','-r','10','-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','21','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(partial)],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
                for row in part:
                    b=np.frombuffer((run/'galleries/frames'/group/row['frame_id']/'comparison_clean.jpg').read_bytes(),np.uint8);image=cv2.imdecode(b,cv2.IMREAD_COLOR);assert image.shape[:2]==(800,1800);writer.stdin.write(image.tobytes())
                writer.stdin.close();assert writer.wait()==0,'FFmpeg failed: inspect encoder log'
            assert partial.resolve().is_relative_to(run) and dest.resolve().is_relative_to(run);partial.rename(dest)
        cap=cv2.VideoCapture(str(dest));count=0
        while True:
            ok,image=cap.read()
            if not ok:break
            assert image.shape[:2]==(800,1800);count+=1
        cap.release();assert count==len(part)
        probe=json.loads(subprocess.check_output([str(ROOT/'third_party/ffmpeg/ffprobe.exe'),'-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height','-of','json',str(dest)]))['streams'][0];assert probe['codec_name']=='h264'
        checks.append(dict(group=group,frames=count,fps=10,seconds=count/10,sha=sha(dest),full_decode=True,codec=probe))
    suffix='_'+'_'.join(groups) if groups is not None else ''
    put(run/'videos'/f'{split}{suffix}_verification.json',checks)

def ablation_report(run):
    metrics=get(run/'offline_evaluation/DEV_summary.json');frame=rows(run/'offline_evaluation/DEV_frames.csv');lookup={(r['group'],r['frame_id'],r['arm']):r for r in frame};paired=[]
    for r in frame:
        if r['arm']=='FULL' or r['visibility']!='VISIBLE':continue
        full=lookup[r['group'],r['frame_id'],'FULL'];a=r['hit10']=='True';b=full['hit10']=='True'
        paired.append(dict(group=r['group'],frame_id=r['frame_id'],arm=r['arm'],full_hit10=b,arm_hit10=a,full_only_hit=b and not a,ablation_only_hit=a and not b,full_error=full['error'],arm_error=r['error'],full_status=full['status'],arm_status=r['status'],full_over100=full['over100'],arm_over100=r['over100'],interpretation='PAIRED_CONDITIONAL_SWITCH_EFFECT_NOT_UNIQUE_PHYSICAL_CAUSE'))
    csvwrite(run/'ablations/ablation_summary.csv',metrics);csvwrite(run/'ablations/paired_visible_frames.csv',paired)
    deltas=[]
    for group in ['group_a','three_point_bend']:
        f=next(m for m in metrics if m['group']==group and m['arm']=='FULL')
        for m in metrics:
            if m['group']!=group or m['arm']=='FULL':continue
            pp=[p for p in paired if p['group']==group and p['arm']==m['arm']]
            deltas.append(dict(group=group,arm=m['arm'],FULL_minus_arm_hit10=f['hit10']-m['hit10'],FULL_minus_arm_valid=f['valid']-m['valid'],FULL_minus_arm_over100=f['over100']-m['over100'],full_only_frames=','.join(p['frame_id'] for p in pp if p['full_only_hit']),arm_only_frames=','.join(p['frame_id'] for p in pp if p['ablation_only_hit'])))
    csvwrite(run/'ablations/paired_summary.csv',deltas)
    write(run/'reports/ABLATION_REPORT.md','# 开发组预注册消融\n\n11模式×1071帧，正式主结果固定FULL。两组合计34张可见GT，按组19/15固定分母，不以拒绝率降低冒称准确率提高。所有模式同一配置和预算，历史状态独立，公共图像证据只读。\n\n'+table(metrics,['group','arm','visible','valid','hit10','over100','oracle_hit10','full_sequence_budget'])+'\n\n'+table(deltas,['group','arm','FULL_minus_arm_hit10','FULL_minus_arm_valid','FULL_minus_arm_over100','full_only_frames','arm_only_frames'])+'\n固定参考关闭仅移除变化证据，初始缺口几何保留；NO_TRACKING仍使用实际前一帧；NO_MULTITRACK确实损失其他分支覆盖。开口仅用于不确定候选的弱平局信息，因此正式指标零变化不证明开口物理信息无效，只说明当前集成不能贡献正式结果。动态工作ROI不减少完整安全区RAW scout成本。共享预计算耗时应与每arm引擎耗时分列，不能把缓存复用当算法提速。\n\n同帧差异只能归因于该条件开关与其时序反馈整体，不证明唯一物理机制；S5是反馈而非严格流水阶段，Oracle不能替代正式tip。组合不是验证后选优。另见[预标注轨迹预算定位](PRELABEL_TRACK_BUDGET_FINDING.md)，其中三点弯FULL的93次预算失败全部来自轨迹上限；不能把它们归咎于RAW或图边预算。\n')
    return metrics

def reports_dev(run):
    metrics=ablation_report(run);full=[m for m in metrics if m['arm']=='FULL'];stages=rows(run/'diagnostics/DEV_failure_stages.csv');counter={g:dict(collections.Counter(r['earliest_observable_loss'] for r in stages if r['group']==g and r['arm']=='FULL')) for g in ['group_a','three_point_bend']}
    write(run/'reports/DEVELOPMENT_REPORT.md','# 开发组完整结果\n\nGROUP_A551+三点弯520全部保留；标注34张VISIBLE，6张UNKNOWN，仅离线比较，无训练/GT参数搜索。新算法未依据验证组C像素/P/GT修改规则；但冻结前误运行通用旧A检查，读取了验证组C原图/P点，严格输入隔离不通过。详见PROTOCOL_DEVIATION.md，不能宣称本轮完全未接触验证组C输入。\n\n'+table(full,['group','frames','visible','valid','null','hit3','hit5','hit10','hit20','coverage','over100','over500','mean_error','median_error','p95_error','max_error','oracle_hit10','preferred_uncertain_hit10','passes_frozen_thresholds'])+'\n\n最早可观测丢失（不是因果结论；BUDGET_INCOMPLETE为审计优先状态，不表示已经排除更早灰度/片段损失，S1–S5覆盖另列）：\n\n```json\n'+json.dumps(counter,ensure_ascii=False,indent=2)+'\n```\n\n合成工程检查成功不等于真实跨试件准确率通过。保留所有预算耗尽与错误端点，不调小分母、不按组修参数、不把preferred/Oracle补入正式输出。候选词典序搜索仍可能失去不同前驱的路径身份，结构门可能保留纹理、丢失细线；需结合逐帧血缘和配对消融进一步定位。\n')
    overlays(run,'DEV');videos(run,'DEV')
    write(run/'reports/ENGINEERING_REPORT.md','# 工程交付\n\n新实现位于research/unified_crack_tip_60q，旧生产和研究源码没有就地修改。15项合成合同通过：RAW1/2px、分支最右、后退与大跳跃同帧复查、LOST恢复和过期重建、暗划痕/孤点、P互换/降级、参考独立不可用、gap观测端点、平局不确定、预算null及无GT接口。结果文件见synthetic_tests.txt及engineering_preflight.json。另有5个追加风险探针：4通过、1失败；static_detached_dark_stroke_near_origin错误输出VALID(240,115)。该图中靠近不确定起源的静态独立暗线被当作裂纹，证明当前身份条件不足；不能把15个基本合同通过称为所有安全测试通过。完整图和原生结果见synthetic_risk_probes_extended/及synthetic_risk_probes_extended.json。\n\n开发组全量证据/11模式/离线分母/顺序重放已执行，以manifests/DEV_inference_seal.json和diagnostics/DEV_determinism_and_source.csv为机器证据。验证组C尚须预验证冻结后执行；最终状态见FINAL_DECISION.md。仅Python实现，无C++ parity。数值在numpy/scipy/OpenCV/numba当前环境核验，不承诺其他平台位级一致。git目录不存在，environment.json记录真实错误。\n\n无标签冒烟先发现方向联合导致纹理碎片爆炸、路径重复扩展；以方向估计、组件结构、词典序有向段搜索修正，RAW数值仍保留。预声明只使用GROUP_A276、三点弯260，smoke历史产物不覆盖。资源上限调整发生在全量注册/标签评价前。独立消融先增加并发，随后将剩余GROUP_A模式拆为三个执行批次，另改gzip压缩级别，仅影响调度/IO；调度中断的未完成文件在orchestration_interrupted_attempt*隔离，完整帧恢复，原四模块hash不变。随后在独立engine_fast.py中批量计算相同采样点的历史KDTree查询及布尔计数；133个跨模式真实检查点和15项合成测试的全部原生结果、状态、调试掩膜及血缘一致后，才恢复剩余计算。原engine.py未改，已完成结果不覆盖；新增结果带五文件hash，旧结果保留四文件hash，兼容核对仅接受这两套准确来源。参数/判定未变，无GT读取。注册与断点见DEV_execution_backend_registration.json、worker_reschedule4.json和qa/batch_backend_*；耗时按两后端分列，不能混为同一性能基准。\n\n内存受输入ROI/骨架/段与图上限约束，但邻居枚举发生于图边截断之前，尚无操作系统级硬内存上限保证。此为高密度极端输入的明确工程局限；生产批准还需有界流式边提案与资源压力测试，不能仅凭本数据未OOM认定完全通过。配准窗口数量单独有界；无效引用不进入证据。原生holdout_ncc实际为拟合后的交错子集一致性，子集已参与整块模板匹配，不是独立留出验证；不能扩大为物理配准真实性证据。\n\n图册已通过Node DOM加载、8图层、候选分页/筛选和空选择合同，对比图经逐帧视频编码/解码检查，部分图像已抽样查看；全部PNG与数值完整性以最终final_integrity记录为准。实际浏览器尝试因内置浏览器不能连到本地服务、且工具策略禁止file://而受阻；没有绕过策略，也不声称完成真实浏览器交互验收，见qa/browser_interaction_attempt.json。\n')

def full_diagnostics(run):
    summaries=[];references=[];budgets=[];jumps=[];lines=[];all_stages=[]
    stage_rows=rows(run/'diagnostics/DEV_failure_stages.csv')+rows(run/'diagnostics/LOCKED_failure_stages.csv')
    stages={(r['group'],r['frame_id']):r for r in stage_rows if r['arm']=='FULL'}
    evaluated=rows(run/'offline_evaluation/DEV_frames.csv')+rows(run/'offline_evaluation/LOCKED_frames.csv')
    visibility={(r['group'],r['frame_id']):r['visibility'] for r in evaluated if r['arm']=='FULL'}
    for row in inventory(run):
        group=row['group'];fid=row['frame_id'];d=readgz(resultdir(run,'FULL',group)/(fid+'.json.gz'));r=d['result'];identity=dict(group=group,frame_id=fid,role=row['role'])
        stage=stages.get((group,fid))
        all_stages.append(dict(**identity,status=r['status'],native_termination=r['failure_reason'] or 'OFFICIAL_OUTPUT',budget=r['budget']['exhausted'],visibility=visibility[group,fid],offline_earliest_observable_loss=stage['earliest_observable_loss'] if stage else 'UNASSESSABLE_NO_VISIBLE_GT',causal_claim=False,unlabeled_is_negative=False))
        summary={**identity,**{k:v for k,v in r.items() if k not in ['candidates','tracks','roi_events','reference_info','scene','budget','rechecks','track_transitions']},'candidate_count':len(r['candidates']),'raw_result':f'FULL/{group}/{fid}.json.gz','raw_lineage':f'FULL/{group}/{fid}_lineage.json.gz','evidence':f'../evidence/{group}/{fid}/arrays.npz'}
        lines.append(json.dumps(clean(summary),ensure_ascii=False,separators=(',',':')));summaries.append(dict(**identity,status=r['status'],tip_x=r['tip'][0] if r['tip'] else None,tip_y=r['tip'][1] if r['tip'] else None,failure=r['failure_reason'],budget=r['budget']['exhausted'],candidates=len(r['candidates']),prepare_seconds=d['prepare_seconds'],engine_seconds=d['engine_seconds']))
        budgets.append({**identity,**{k:v for k,v in r['budget'].items() if not isinstance(v,dict)},**{'raw_'+k:v for k,v in r['budget']['raw'].items()},**{'graph_'+k:v for k,v in r['budget']['graph_counts'].items() if not isinstance(v,dict)}})
        audit_text=(run/'galleries/frames'/group/fid/'audit.js').read_text(encoding='utf-8')
        lineage_audit=json.loads(audit_text.removeprefix('window.receiveAudit(').removesuffix(');'))
        budgets[-1].update(candidate_budget_omissions=len(lineage_audit['omitted_candidates']),unvisited_route_states=lineage_audit['lineage_summary']['unvisited_states'],roots_total=lineage_audit['lineage_summary']['roots_total'],roots_explored=lineage_audit['lineage_summary']['roots_explored'])
        for channel in ['fixed','prev']:
            q=r['reference_info'][channel];references.append(dict(**identity,channel=channel,status=q['status'],reason=q.get('reason'),valid_fraction=q['valid_fraction'],windows=len(q['windows']),budget=q['budget_exhausted']))
        for j in r['rechecks']:jumps.append(dict(**identity,**j))
    csvwrite(run/'raw_inference/all_frames.csv',summaries);write(run/'raw_inference/all_frames.jsonl','\n'.join(lines)+'\n');csvwrite(run/'diagnostics/reference_quality.csv',references);csvwrite(run/'diagnostics/budget_audit.csv',budgets)
    csvwrite(run/'diagnostics/abnormal_jump_audit.csv',jumps or [dict(note='No anomaly-triggered rechecks in this frozen run')])
    csvwrite(run/'diagnostics/failure_stages.csv',stage_rows);csvwrite(run/'diagnostics/all_frame_failure_index.csv',all_stages)
    cost=[]
    for group in GROUPS:
        for arm in ARMS if group!='group_c' else ['FULL']:
            part=rows(resultdir(run,arm,group)/'summary.csv')
            cost.append(dict(group=group,arm=arm,frames=len(part),engine_p50=float(np.median([float(r['engine_seconds']) for r in part])),engine_p95=float(np.percentile([float(r['engine_seconds']) for r in part],95)),prepare_p50=float(np.median([float(r['prepare_seconds']) for r in part])),candidates_mean=float(np.mean([int(r['candidates']) for r in part])),tracks_mean=float(np.mean([int(r['tracks']) for r in part])),fixed_fraction_mean=float(np.mean([float(r['fixed_valid_fraction']) for r in part])),prev_fraction_mean=float(np.mean([float(r['prev_valid_fraction']) for r in part])),null=sum(r['status']!='VALID' for r in part)))
            cost[-1]['fixed_effective_fraction_mean']=0. if 'fixed' in ARMS[arm] else cost[-1]['fixed_fraction_mean']
            cost[-1]['prev_effective_fraction_mean']=0. if 'prev' in ARMS[arm] else cost[-1]['prev_fraction_mean']
            cost[-1]['main_identity_changes']=sum(bool(a['main_track']) and bool(b['main_track']) and a['main_track']!=b['main_track'] for a,b in zip(part[:-1],part[1:]))
            cost[-1]['official_track_changes']=sum(bool(a['selected_track']) and bool(b['selected_track']) and a['selected_track']!=b['selected_track'] for a,b in zip(part[:-1],part[1:]))
            cost[-1]['anomaly_rechecks']=sum(int(r['jump_rechecks']) for r in part)
            for backend in ['ORIGINAL_SCALAR','BATCH_EQUIVALENT']:
                times=[float(r['engine_seconds']) for r in part if r.get('engine_backend','ORIGINAL_SCALAR')==backend]
                cost[-1][backend+'_frames']=len(times);cost[-1][backend+'_p50']=float(np.median(times)) if times else None;cost[-1][backend+'_p95']=float(np.percentile(times,95)) if times else None
    csvwrite(run/'diagnostics/cost_and_channels.csv',cost)

def historical(run):
    # Only final post-locked delivery reads historical exposed result values.
    check_freeze(run);assert (run/'offline_evaluation/LOCKED_evaluation_seal.json').exists();old=[]
    for label,path in [('V1','output/runs/p1p2_grayref_v1_20261112_r01/tables/group_summary.csv'),('V2','output/experiments/p1p2_grayref_v2_20261112_r01/group_summary.csv')]:
        for r in rows(ROOT/path):
            if r['group'] not in GROUPS:continue
            if label=='V1' and (r['mode']!='joint' or float(r['threshold'])!=10):continue
            if label=='V2' and r['mode'] not in ['V2_COMBINED','COMBINED']:continue
            old.append(dict(version=label,group=r['group'],visible=r['visible'],valid=r.get('error_n'),hit10=r['hit10'],over100=r['over100'],semantics='HISTORICAL_PROVISIONAL_NOT_NEW_FORMAL_OBSERVATION',new_detector_execution=False,source=path,source_sha=sha(ROOT/path)))
    assert all(sum(r['version']==v for r in old)==3 for v in ['V1','V2']), 'Historical baseline mode mapping incomplete'
    csvwrite(run/'offline_evaluation/historical_reference_comparison.csv',old)
    write(run/'reports/HISTORICAL_BASELINE_SCOPE.md','# 冻结基线对照边界\n\n旧 A 的正式观测与 GrayRef 暂定端点、新规则VALID并非同一物理认证等级。本对照表未重新执行旧A/V1/V2，也未以其候选Oracle代替正式结果。此前误运行通用检查中的旧A少量回放另记于PROTOCOL_DEVIATION.md，不属于此全序列对照。下表只读取原封存汇总，明确是历史比较；不能当本轮公平重测或新盲测。A不提供语义匹配的新1633帧正式统计，记NOT_RERUN而非虚造指标。\n\n'+table(old,['version','group','visible','valid','hit10','over100','semantics'])+'\n旧源码、DLL、原输出全部hash核对见final_integrity.json。\n')

def final(run):
    check_freeze(run);assert get(run/'reports/final_integrity.json')['protected_changed']==[]
    locked=get(run/'offline_evaluation/LOCKED_summary.json');dev=get(run/'offline_evaluation/DEV_summary.json');full=[r for r in dev if r['arm']=='FULL']+locked
    overlays(run,'LOCKED');videos(run,'LOCKED');full_diagnostics(run);historical(run)
    integrity=get(run/'reports/final_integrity.json');gate=all(r['passes_frozen_thresholds'] for r in full)
    acceptance=[
        dict(requirement='1633 complete frames and 12343 mode outputs',status='PASS',evidence='manifests/*inference_seal.json; reports/final_integrity.json'),
        dict(requirement='RAW1px/2px, current max-x branch, retreat, jump review, independent reference masks',status='PASS_SYNTHETIC_CONTRACTS',evidence='reports/synthetic_tests.txt'),
        dict(requirement='Original-source numeric replay and deterministic sequence state',status='PASS_CHECKED_SAMPLES',evidence='diagnostics/*determinism_and_source.csv; 30 source frames + 9 sequential replay frames'),
        dict(requirement='Independent batch execution matches original scalar semantics',status='PASS_133_NATIVE_CHECKPOINTS_AND_15_SYNTHETIC',evidence='qa/batch_backend_contract.json; qa/batch_backend_native_parity.csv; reports/EXECUTION_BACKEND_EQUIVALENCE.md'),
        dict(requirement='Physical crack identity / detached dark stroke safety',status='FAIL',evidence='synthetic_risk_probes_extended/static_detached_dark_stroke_near_origin/result.json.gz'),
        dict(requirement='Strict pre-freeze group_c input isolation',status='FAIL_WITH_DISCLOSED_DEVIATION',evidence='reports/PROTOCOL_DEVIATION.md'),
        dict(requirement='Budget exhaustion never promoted to an official endpoint',status='PASS_CHECKED_FRAMES',evidence='diagnostics/all_frame_integrity.csv'),
        dict(requirement='Hard worst-case memory guarantee before neighbor proposal enumeration',status='NOT_PROVEN',evidence='graph.py enumerates spatial neighbor pairs before the final pair budget cap'),
        dict(requirement='Three-group frozen accuracy gates',status='PASS' if gate else 'FAIL',evidence='offline_evaluation/DEV_metrics.csv; LOCKED_metrics.csv'),
        dict(requirement='C++ parity',status='NOT_IMPLEMENTED_NOT_CLAIMED',evidence='Python-only implementation permitted by task'),
        dict(requirement='Registration quality proxy interpretation',status='POST_FIT_SUBSET_CHECK_ONLY',evidence='holdout_ncc is a post-fit interleaved subset consistency check, not independent holdout'),
        dict(requirement='Physical notch and deformation-field ground truth',status='UNRESOLVED',evidence='Image hypotheses / local texture quality only'),
        dict(requirement='Batch evidence adapter for invalid current P1/P2',status='FAIL_FAST_ADAPTER_LIMITATION',evidence='Engine supports historical-geometry degradation in synthetic tests; stateless pipeline.prepare_one rejects invalid real P instead of adapting it'),
        dict(requirement='Real-browser interactive viewer verification',status='NOT_VERIFIED_TOOL_POLICY_BLOCK',evidence='qa/browser_interaction_attempt.json; Node DOM contracts and image inspection passed separately'),
        dict(requirement='Preserve historical source, DLL and sealed results',status='PASS' if not integrity['protected_changed'] else 'FAIL',evidence='reports/final_integrity.json')]
    csvwrite(run/'reports/acceptance_matrix.csv',acceptance)
    write(run/'reports/IMPLEMENTATION_BOUNDARIES.md','# 实际实现与验收边界\n\n'+table(acceptance,['requirement','status','evidence'])+'\nM4的图首先提出当前RAW/方向/间断支持的几何连接，参考变化在整条候选路径身份验证中消费；不声称边提案本身具有独立参考分类器。每个有向段保留词典序最优前驱，其他前驱保存为拒绝血缘；这不是所有路径的穷举。开口只作用于不确定候选弱平局，未影响正式结果时如实报告。动态工作掩膜仍需完整安全区RAW scout，因此不能声称减少全部特征成本。核心Engine.process具备P点降级与历史几何支持，但当前无历史批量证据缓存入口prepare_one遇非法P会明确停止；不能将核心合成测试等同批入口已覆盖所有异常输入。当前三组是否存在此类输入，以实际prepare完成记录为准。\n\n“完成研究代码和实验交付”不等于全部规范验收通过。独立暗线误输出、隔离执行偏差、极端内存保证和物理真值缺口均保留，禁止发布为生产替代。\n')
    # The measured engineering limitation is an independent release blocker.
    production=False;decision='PRODUCTION_NO_GO'
    write(run/'reports/LOCKED_VALIDATION_REPORT.md','# 冻结验证组C验证\n\n新算法在prevalidation_freeze.json生成后才读取验证组C原图和实际P；但通用旧A检查已在冻结前读取过该组，严格数据隔离审计FAIL，详见PROTOCOL_DEVIATION.md。只执行一轮562帧FULL正式序列；结果封存后独立读取20张可见GT。额外原图重算和首3帧确定性检查属于固定结果审计，不选参数、不产生替换成绩。该组历史已曝光，且本轮有隔离执行偏差，明确非新盲测或隔离流程完全合格的锁定验证。\n\n'+table(locked,['group','frames','visible','valid','null','hit3','hit5','hit10','hit20','coverage','over100','over500','mean_error','median_error','p95_error','max_error','oracle_hit10','preferred_uncertain_hit10','passes_frozen_thresholds'])+'\n冻结后不按验证组C调整任何算法/配置/评价逻辑，不筛掉预算耗尽或错误输出帧。\n')
    stages=rows(run/'diagnostics/failure_stages.csv');counts={g:dict(collections.Counter(r['earliest_observable_loss'] for r in stages if r['group']==g and r['arm']=='FULL')) for g in GROUPS}
    write(run/'reports/FINAL_DECISION.md','# 最终验收：'+decision+'\n\n本轮已完成独立主链、DEV两组全量11模式、锁定验证组C单轮FULL、分离的GT评价和1633帧诊断/三组视频。研究实现不替换旧A。必须同时阅读[协议偏差](PROTOCOL_DEVIATION.md)：严格冻结前验证组C数据隔离未完全遵守，不能将完成实验等同规范全部验收通过。\n\n'+table(full,['group','frames','visible','valid','null','hit3','hit5','hit10','hit20','coverage','over100','over500','mean_error','median_error','p95_error','max_error','oracle_hit10','preferred_uncertain_hit10','passes_frozen_thresholds'])+'\n正式分母固定19/15/20。阈值：GROUP_A hit10≥14/valid≥16/>100=0；三点弯11/12/0；验证组C14/16/≤1。分组准确率门整体='+str(gate)+'。另有冻结前通用旧A检查读取验证组C原图/P点的隔离偏差（DATA_ISOLATION_AUDIT=FAIL_WITH_DISCLOSED_DEVIATION），以及高密度边枚举尚无OS硬内存保障的工程局限，不能批准生产。null保留分母，Oracle和preferred不并入正式命中，未标注帧不是负例、真实FPR=N/A。\n\n## RESEARCH_RESULT\n\n原始细线保真、两路独立引用、动态工作掩膜、多轨迹与大跳跃证据复查已连通，15项基本合成合同通过，但追加5项风险探针有1项静态独立暗线误输出；真实序列指标和条件消融在DEVELOPMENT_REPORT/ABLATION_REPORT中完整披露。工程通过项不能证明裂纹身份。验证组C是已曝光固定回归，不是新盲测。新算法源码和参数在验证组C新算法运行前冻结；旧A通用检查的预冻结读图偏差单独披露。标注不训练，r01没有GT参数搜索。\n\n最早可观测失败阶段（非物理因果）：\n\n```json\n'+json.dumps(counts,ensure_ascii=False,indent=2)+'\n```\n\n## 后续建议\n\n1. 优先解决已有合成反例：在缺口根部不确定时，附近静态独立暗线仍输出VALID(240,115)。保持RAW/参考输入，单独研究物理起源关联及身份不确定性的传播，不能以参考零差分否决所有旧裂纹。此安全反例在任何指标改善前都须明确保留。\n2. 针对候选预算与纹理图的传播范围做受控实验：固定RAW、参考和身份规则，比较有界流式边提案/候选终点保留，证明减少的是冗余而不是正确尾端；不能仅持续加预算或缩ROI。\n3. 依据配对消融和候选Oracle，区分候选不可达、身份拒绝、端点竞争；逐帧核对反例再改变单模块。覆盖率本身不证明路径正确，部分GT路径不能认证gap物理连接。\n4. 建立独立缺口/材料纹理配准真实性检查和划痕阴性集，验证物理身份与局部参考有效性。当前局部NCC通过不等于真实变形场。下一轮若开发，使用新实验版本；不能利用本次验证组C成绩回调同一冻结版本。\n\n## 完整性与复现\n\n全部1633帧保留；DEV11781+LOCKED562=12343条完整模式预测（不把中断尝试、合成、无标签smoke或固定审计重放计入完整预测数）。保护历史'+str(integrity['protected_files'])+'文件，变动'+str(len(integrity['protected_changed']))+'。仅Python，C++未实现。源代码hash、运行环境、清单和原始TXT配对见manifests；实际命令见源码README。原四模块和参数未变；中途增加经133例全原生一致性核对的批量执行副本，来源hash分别保留，见执行副本注册。验证组C全部使用冻结批量副本；开发耗时按旧/新执行版本分列。调度中断的未完成文件隔离，完整历史结果未覆盖。\n\n图册：[全帧交互平台](../galleries/index.html)；视频：[GROUP_A](../videos/group_a.mp4)、[三点弯](../videos/three_point_bend.mp4)、[验证组C](../videos/group_c.mp4)。独立GT：[开发](../offline_evaluation/overlays/DEV_index.html)、[验证组C](../offline_evaluation/overlays/LOCKED_index.html)。\n')
    write(run/'reports/BLOCKERS_FINAL.md','# 最终阻塞/局限\n\n数据处理和证据交付无待运行帧。初始BLOCKERS.md保留作为盘点时快照；当前最终状态见本文件与FINAL_DECISION.md。生产批准仍阻塞于已披露的冻结前旧A验证组C读图隔离偏差、静态独立暗线误输出反例、分组实测门槛与高密度边提案硬内存保障、物理身份/配准真实性等已披露限制。没有C++实现，不能声称parity。没有真实阴性标注，FPR不能估计。\n')
    put(run/'manifests/code_config_hashes.json',dict(source=source_hashes(),freeze=sha(run/'manifests/prevalidation_freeze.json')))
    write(run/'DELIVERABLE_INDEX.md','# 交付索引\n\n- [最终结论](reports/FINAL_DECISION.md) / [协议执行偏差](reports/PROTOCOL_DEVIATION.md)\n- [工程](reports/ENGINEERING_REPORT.md) / [开发](reports/DEVELOPMENT_REPORT.md) / [消融](reports/ABLATION_REPORT.md) / [锁定验证](reports/LOCKED_VALIDATION_REPORT.md)\n- [全1633帧交互图册](galleries/index.html)\n- [GROUP_A视频](videos/group_a.mp4) / [三点弯视频](videos/three_point_bend.mp4) / [验证组C视频](videos/group_c.mp4)\n- [全部原生结果索引](raw_inference/all_frames.csv) / [JSONL索引](raw_inference/all_frames.jsonl)；各FULL与消融逐帧完整JSON、NPZ和lineage在raw_inference/，公用数值证据在evidence/\n- [开发指标](offline_evaluation/DEV_metrics.csv) / [锁定指标](offline_evaluation/LOCKED_metrics.csv) / [可见标注阶段表](diagnostics/failure_stages.csv) / [1633帧状态阶段索引](diagnostics/all_frame_failure_index.csv) / [预算](diagnostics/budget_audit.csv) / [参考](diagnostics/reference_quality.csv) / [异常重查](diagnostics/abnormal_jump_audit.csv)\n- [开发失败定位](reports/DEV_FAILURE_INTERPRETATION.md) / [独立执行副本一致性](reports/EXECUTION_BACKEND_EQUIVALENCE.md) / [预标注轨迹预算定位](reports/PRELABEL_TRACK_BUDGET_FINDING.md) / [离线评价读取核对](reports/EVALUATOR_IO_EQUIVALENCE.md)\n- [冻结历史保护和全帧完整性](reports/final_integrity.json) / [最终局限](reports/BLOCKERS_FINAL.md)\n')
    paths=[p for sub in ['reports','diagnostics','offline_evaluation','ablations','videos','manifests','galleries','qa','logs','synthetic_risk_probes_extended'] for p in (run/sub).rglob('*') if p.is_file() and p.name!='final_delivery.log']
    put(run/'final_delivery_seal.json',dict(time=utc(),files={str(p.relative_to(run)).replace('\\','/'):sha(p) for p in sorted(paths)},production=decision,research='COMPLETED_WITH_MEASURED_LIMITATIONS',frames=1633,predictions=12343))
    print(decision,json.dumps(full,ensure_ascii=False),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--phase',choices=['DEV','FINAL'],required=True);a=ap.parse_args();run=Path(a.run).resolve()
    if a.phase=='DEV':reports_dev(run)
    else:final(run)
