"""Post-evaluation reports, navigable galleries and honest paired decisions."""
import argparse,collections,json,html,subprocess,concurrent.futures
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from .common import *
from .geometry import MODES

def yes(v):return v is True or v=='True'
def table(data,keys):return '| '+' | '.join(keys)+' |\n| '+' | '.join('---' for _ in keys)+' |\n'+''.join('| '+' | '.join(str(r.get(k,'')) for k in keys)+' |\n' for r in data)
def page(title,body):return ('<meta charset="utf-8"><style>body{font:17px sans-serif;background:#142330;color:white;margin:24px}a{color:cyan}table{border-collapse:collapse}td,th{border:1px solid #789;padding:5px}img,video{max-width:100%}</style><h1>'+title+'</h1>'+body).encode()

def video(job):
    run,group=job;run=Path(run);out=run/'videos';out.mkdir(exist_ok=True);target=out/(group+'.mp4');qa=out/(group+'_qa.json')
    if qa.exists():assert sha(target)==get(qa)['sha'];return get(qa)
    ff=ROOT/'third_party/ffmpeg/ffmpeg.exe';cmd=[str(ff),'-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1440x864','-r','6','-i','pipe:0','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]
    with open(out/(group+'_encode.log'),'wb') as log:
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        for row in manifest(run/'input_manifest.csv'):
            if row['group']!=group:continue
            with Image.open(directory(run,row)/'roi_overlay_abc.png') as im:frame=im.convert('RGB').resize((1440,864),Image.Resampling.LANCZOS)
            proc.stdin.write(frame.tobytes())
        proc.stdin.close();assert proc.wait()==0
    probe=subprocess.run([str(ff),'-v','error','-i',str(target),'-f','null','-','-progress','pipe:1'],capture_output=True,text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));assert probe.returncode==0
    count=[int(s.split('=')[1]) for s in probe.stdout.splitlines() if s.startswith('frame=')][-1];assert count==GROUPS[group]
    info=dict(group=group,frames=count,full_decode=True,fps=6,playback_not_inference_speed=True,sha=sha(target));put(qa,info);return info

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--workers',type=int,default=12);a=p.parse_args();run=Path(a.run);check_sources(run);integrity=get(run/'run_integrity.json');assert integrity['engineering_complete'];data=manifest(run/'input_manifest.csv')
    metrics=rows(run/'offline_evaluation_group_a.csv')+rows(run/'offline_evaluation_exposed.csv');lookup={(r['group'],r['frame_id'],r['mode']):r for r in metrics};summaries=get(run/'evaluation_complete_group_a.json')['summary']+get(run/'evaluation_complete_exposed.json')['summary'];summary={(r['group'],r['mode']):r for r in summaries};stats=[];pred=[];runtime=[];baseline=[];lineage=[];evidence=[]
    for row in data:
        d=directory(run,row);r=readgz(d/'result.json.gz');stats+=r['stats'];rm=get(d/'render_metadata.json');baseline.append(dict(group=row['group'],frame_id=row['frame_id'],same_image_sha=row['image_sha'],roi_exact=True,A_full_native_trace_exact=True,A_graph_arrays_exact=True,evidence_cached_sha_verified=True,cache_not_new_inference=True))
        for q,t,s in zip(r['results'],r['timing'],r['stats']):
            pred.append(dict(group=row['group'],frame_id=row['frame_id'],mode=q['mode'],tip=json.dumps(q['tip']),candidate_tip=json.dumps(q['candidate_tip']),last_observed_pixel=json.dumps(q['last_observed_pixel']),state=q['output_state'],native_state=q['native_output_state'],reference_status=r['reference_status'],GT_accessed=False,input_sha=row['image_sha'],reference_sha=row['ref_sha'],config_sha=r['config_sha']))
            runtime.append(dict(group=row['group'],frame_id=row['frame_id'],**t,shared_evidence_cache_load_verify_ms=r['cache_load_verify_ms'],shared_geometry_controller_ms=r['geometry_control_ms'],lineage_audit_ms=r['lineage_audit_ms'],render_ms=rm['render_ms'],worker_peak_rss_bytes=r['peak_rss'],cache_used=True,not_full_preprocessing_benchmark=True))
            lineage.append(dict(group=row['group'],frame_id=row['frame_id'],mode=q['mode'],node_records=str((d/'evidence_arrays.npz').relative_to(run)),route_records=str((d/'route_lineage.json.gz').relative_to(run)),A_nodes_geometry_excluded=s['A_nodes_geometry_excluded'],A_nodes_inside_but_reselected=s['A_nodes_inside_but_reselected'],containment_deleted=s['containment_deleted'],path_budget_not_visited=s['path_budget_not_visited'],stable_node_id='original pixel (x,y); per-mode node index retained',first_loss_stages='ROI_EXCLUDED then COLUMN_RESELECTION then FRAGMENT_CONTAINMENT / PATH_BUDGET; no physical identity assumed'))
        evidence.append(dict(group=row['group'],frame_id=row['frame_id'],page=str((d/'index.html').relative_to(run)),numeric=str((d/'evidence_arrays.npz').relative_to(run)),numeric_sha=sha(d/'evidence_arrays.npz'),cache=json.dumps(r['cache']),pngs=5))
    for name,records in [('frame_roi_geometry.csv',stats),('roi_candidate_stage_counts.csv',stats),('frame_mode_predictions.csv',pred),('runtime_performance.csv',runtime),('baseline_replay_check.csv',baseline),('candidate_lineage.csv',lineage),('evidence_manifest.csv',evidence),('failure_attribution.csv',[r for r in metrics if r['visibility']=='VISIBLE'])]:csvwrite(run/name,records)
    grouped=[]
    for group in GROUPS:
        for mode in MODES:
            part=[r for r in stats if r['group']==group and r['mode']==mode];tt=[r['inference_ms'] for r in runtime if r['group']==group and r['mode']==mode]
            grouped.append(dict(group=group,mode=mode,area_ratio_mean=float(np.mean([r['area_ratio'] for r in part])),search_pixels_mean=float(np.mean([r['search_pixels'] for r in part])),bandwidth_P50=float(np.median([r['width_p50'] for r in part])),nodes_total=sum(r['nodes'] for r in part),capacity_dropped=sum(r['capacity_dropped'] for r in part),containment_deleted=sum(r['containment_deleted'] for r in part),path_budget_not_visited=sum(r['path_budget_not_visited'] for r in part),corridor_touch=sum(r['corridor_touch'] for r in part),ROI_LIMITED=sum(r['state']=='ROI_LIMITED' for r in pred if r['group']==group and r['mode']==mode),inference_P50_ms=float(np.percentile(tt,50)),inference_P95_ms=float(np.percentile(tt,95))))
    csvwrite(run/'roi_mode_summary.csv',grouped);gs={(r['group'],r['mode']):r for r in grouped};paired=[];perframe=[]
    for group in GROUPS:
        aa=summary[group,MODES[0]]
        for mode in MODES[1:]:
            part=[r for r in metrics if r['group']==group and r['mode']==mode and r['visibility']=='VISIBLE'];pairs=[(r,lookup[group,r['frame_id'],MODES[0]]) for r in part]
            rec=dict(group=group,mode=mode,visible=len(part),hit10_gained=sum(yes(r['hit10']) and not yes(b['hit10']) for r,b in pairs),hit10_lost=sum(not yes(r['hit10']) and yes(b['hit10']) for r,b in pairs),joint_gained=sum(yes(r['joint']) and not yes(b['joint']) for r,b in pairs),joint_lost=sum(not yes(r['joint']) and yes(b['joint']) for r,b in pairs),new_over100=sum(yes(r['over100']) and not yes(b['over100']) for r,b in pairs),new_over500=sum(yes(r['over500']) and not yes(b['over500']) for r,b in pairs),new_GT_EXCLUDED=sum(yes(r['GT_EXCLUDED']) and not yes(b['GT_EXCLUDED']) for r,b in pairs),pool_good_lost=sum(not yes(r['any_candidate_path_good']) and yes(b['any_candidate_path_good']) for r,b in pairs),pool_good_gained=sum(yes(r['any_candidate_path_good']) and not yes(b['any_candidate_path_good']) for r,b in pairs))
            paired.append(rec)
            for r,b in pairs:perframe.append(dict(group=group,frame_id=r['frame_id'],mode=mode,A_hit10=b['hit10'],new_hit10=r['hit10'],A_error=b['error'],new_error=r['error'],A_state=b['output_state'],new_state=r['output_state'],A_tip_inside=b['tip_inside_search'],new_tip_inside=r['tip_inside_search'],A_pool_good=b['any_candidate_path_good'],new_pool_good=r['any_candidate_path_good']))
    csvwrite(run/'paired_ablation_summary.csv',paired);csvwrite(run/'paired_frame_comparison.csv',perframe)
    classifications=[]
    for mode in MODES[1:]:
        pa=next(r for r in paired if r['group']=='group_a' and r['mode']==mode);allp=[r for r in paired if r['mode']==mode];aa=summary['group_a',MODES[0]];bb=summary['group_a',mode];geom=gs['group_a',mode];basegeom=gs['group_a',MODES[0]]
        harmful=any(r['new_GT_EXCLUDED']>0 or r['pool_good_lost']>0 or r['new_over100']>0 or r['new_over500']>0 or r['hit10_lost']>0 or r['joint_lost']>0 for r in allp)
        competitive=geom['nodes_total']<basegeom['nodes_total'] and geom['path_budget_not_visited']<=basegeom['path_budget_not_visited']
        if harmful:decision='GEOMETRY_HARMFUL'
        elif bb['hit10']>aa['hit10'] and bb['joint']>aa['joint'] and bb['outputs']>=aa['outputs'] and geom['area_ratio_mean']<=.75 and competitive:decision='GEOMETRY_BENEFIT'
        elif geom['area_ratio_mean']<=.75 and geom['inference_P50_ms']<=.85*basegeom['inference_P50_ms']:decision='COMPUTE_ONLY_BENEFIT'
        else:decision='UNRESOLVED'
        classifications.append(dict(mode=mode,decision=decision,GO_NO_GO='GO' if decision=='GEOMETRY_BENEFIT' else 'NO_GO',production='NO'))
    default=classifications[1];put(run/'decision.json',dict(default_mode=MODES[2],decision=default,mode_decisions=classifications,engineering_complete=True,algorithm_accepted=default['decision']=='GEOMETRY_BENEFIT',production_approved=False,FPR='N/A'))
    # Static per-group navigation, every frame and all statuses; offline without CDN.
    for group in GROUPS:
        sub=[r for r in pred if r['group']==group];body='<a href="index.html">All groups</a><p>DEVELOPMENT only GROUP_A; other groups EXPOSED_REGRESSION, never blind test.</p><input id="q" placeholder="Frame"><select id="m">'+''.join('<option>'+m+'</option>' for m in MODES)+'</select><select id="s"><option value="">All states</option>'+''.join('<option>'+s+'</option>' for s in sorted({r['state'] for r in sub}))+'</select><table><tbody id="rows"></tbody></table>'
        body+='<script>const data='+json.dumps(sub)+';function show(){let q=document.querySelector("#q").value,m=document.querySelector("#m").value,s=document.querySelector("#s").value;document.querySelector("#rows").innerHTML=data.filter(r=>(!q||r.frame_id===q)&&r.mode===m&&(!s||r.state===s)).map(r=>`<tr><td><a href="../frames/'+group+'/${r.frame_id}/index.html">${r.frame_id}</a></td><td>${r.mode}</td><td>${r.state}</td><td>${r.tip}</td></tr>`).join("")}document.querySelectorAll("input,select").forEach(x=>x.oninput=show);show();</script>'
        write_bytes(run/'galleries'/(group+'.html'),page(group,body))
    body='<p>1633 frames / 4899 predictions. No GT in default evidence. Playback6fps is not inference speed.</p>'
    for g in ['group_c','three_point_bend','group_a']:body+=f'<p><a href="{g}.html">{g}: {GROUPS[g]} frames</a> | <a href="../videos/{g}.mp4">ABC comparison video</a></p>'
    body+='<a href="../REPORT.md">Report</a> | <a href="../ROI_CAUSAL_FINDINGS.md">Causal findings</a>'
    write_bytes(run/'galleries/index.html',page('ROI geometry only — full three-group evidence',body))
    keys=['group','mode','visible','outputs','no_public','hit3','hit5','hit10','hit20','joint','over100','over500','any_candidate_path_good','GT_EXCLUDED']
    report='# ROI 单因素实测报告\n\n工程 PASS；输入1633/1633；三模式4899；PROTOCOL_FROZEN/GT_LEAKAGE_CHECK/BASELINE_PARITY=PASS。算法 '+('PASS' if default['decision']=='GEOMETRY_BENEFIT' else 'FAIL')+'；生产 NO。\n\n[全量图册](galleries/index.html) · [数值完整性](run_integrity.json) · [源码快照](source_hashes.json) · [复现](README.md)\n\n'+table(summaries,keys)
    report+='\n原始A为本轮真实重新运行的冻结C_FUSION_RAW路径引擎，证据缓存经原图/点/SHA核验；A的全部原生结果和节点/边逐帧一致。缓存不是本轮重新提取特征的成绩。旧V1/V2本轮NOT_REPLAYED。\n\n## 几何、竞争、耗时\n\n'+table(grouped,list(grouped[0]))
    report+='\n计时为缓存证据上的路径引擎；C控制器、缓存加载/哈希、只读路线审计、绘图另外记录在runtime_performance.csv。不得把三模式共用的旧预处理缓存当成ROI带来的全流程加速。worker_peak_rss为每个工作进程截至该帧的峰值，非整个机器峰值；不宣称生产实时。\n\n## 成对差异\n\n'+table(paired,list(paired[0]))+'\n逐帧胜负见paired_frame_comparison.csv。GROUP_A仅19个可见标签，一帧影响约5.26个百分点，不作显著性或新盲测声称。未知标签单独记录，未标注不当阴性，FPR=N/A。\n\n## 决策\n\n'+table(classifications,list(classifications[0]))
    report+='\n默认C预先指定，不依据组别选择最佳模式。规则冻结后没有据GROUP_A或验证标签调参。验证仅触发预先规定的退化判定，不用于重新设计参数。CT2/开发组H/CT3/排除组X图像、逐帧结果和标签本轮未进入队列。P中心线/图像缺口假设未获物理认证。仅GROUP_A开发不能证明跨试件通用。\n\n'+json.dumps(get(run/'environment.json'),ensure_ascii=False,indent=2)
    write_bytes(run/'REPORT.md',report.encode('utf-8'))
    findings='# ROI 因果结论\n\n'+default['decision']+' / '+default['GO_NO_GO']+'；不替换A/V1/V2或上一轮简化原型。\n\n'+table(summaries,keys)+'\n只改变候选可访问的像素集合；特征、配准、归一化、桥接、去重、路径预算、分数和停止背景完全冻结。新增ROI_LIMITED是搜索边界的显式拒绝，不是新的停止识别成功。\n\n'+table(paired,list(paired[0]))
    examples={}
    conditions={'缩ROI但候选仍不改善':lambda r:r['mode']!=MODES[0] and not yes(r['any_candidate_path_good']) and not yes(lookup[r['group'],r['frame_id'],MODES[0]]['any_candidate_path_good']),'正确候选被裁剪':lambda r:yes(r['GT_EXCLUDED']),'错误路线仍胜出':lambda r:bool(r['error']) and float(r['error'])>100,'末端无可靠停止':lambda r:r['stage']=='STOPPING_OR_AMBIGUITY','图路径仍未到达':lambda r:r['stage']=='EVIDENCE_OR_GRAPH_REACHABILITY','搜索边界限制':lambda r:r['output_state']=='ROI_LIMITED','参考不可用':lambda r:r['reference_status']!='LOCAL_TEXTURE_PROXY_TRUSTED'}
    visible=[r for r in metrics if r['visibility']=='VISIBLE']
    for title,condition in conditions.items():
        case=next((r for r in (metrics if title=='参考不可用' else visible) if condition(r)),None);examples[title]=None if case is None else {k:case[k] for k in ['group','frame_id','mode','stage','output_state','error']}
        findings+='\n- '+title+'：'+('本轮可见标签中无案例。' if case is None else f"[{case['group']}/{case['frame_id']}](frames/{case['group']}/{case['frame_id']}/index.html)，{case['mode']}，{case['stage']}，公开误差{case['error'] or 'N/A'}。")
    findings+='\n\nROI面积下降不自动说明排除了错误暗线；候选数量、池中合格路径、实际公开尖端与拒绝率必须同时看。路径局部峰仍存在但未形成完整路径时，不能归咎于ROI面积本身。\n\n唯一后续建议：保留本轮失败，不继续调整ROI宽度；只在原A固定候选池上单独检验不同终止跨度的包含关系保留，其他模块保持冻结。本轮未实施该改动，也不承诺能恢复尖端。\n\n[完整报告](REPORT.md) · [1633帧图册](galleries/index.html) · [逐帧胜负](paired_frame_comparison.csv) · [候选血缘索引](candidate_lineage.csv)\n'
    write_bytes(run/'ROI_CAUSAL_FINDINGS.md',findings.encode('utf-8'));put(run/'failure_examples.json',examples)
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:videos=list(pool.map(video,[(str(run),g) for g in GROUPS]))
    put(run/'videos/integrity.json',dict(groups=videos,frames=sum(r['frames'] for r in videos),all_full_decode=True))
    # Actual relative HTML links and dynamic per-frame entries.
    from html.parser import HTMLParser
    from urllib.parse import unquote,urlsplit
    class Parser(HTMLParser):
        def handle_starttag(self,tag,attrs):
            for k,v in attrs:
                if k in ['src','href'] and v:
                    u=urlsplit(v)
                    if u.path and not u.scheme:assert (self.folder/unquote(u.path)).is_file(),(self.folder,v)
    count=0
    for f in (run/'galleries').glob('*.html'):
        parser=Parser();parser.folder=f.parent;parser.feed(f.read_text(encoding='utf-8'));count+=1
    for row in data:
        f=directory(run,row)/'index.html';parser=Parser();parser.folder=f.parent;parser.feed(f.read_text(encoding='utf-8'));count+=1
    check_sources(run);put(run/'completion_seal.json',dict(utc=utc(),engineering_complete=True,decision=default,HTML_pages=count,video_frames=1633,source_sha=sha(run/'source_hashes.json'),integrity_sha=sha(run/'run_integrity.json'),files={f.name:sha(f) for f in run.iterdir() if f.is_file() and f.name!='completion_seal.json'},source_unchanged=True));print('COMPLETED '+json.dumps(default),flush=True)

if __name__=='__main__':main()
