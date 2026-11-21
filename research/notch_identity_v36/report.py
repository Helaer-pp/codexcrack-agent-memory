"""Post-freeze audit. Reuse sealed outputs and labels solely for scoring and display."""
import json
import re
from collections import Counter
from itertools import zip_longest
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import numpy as np
from .batch import ROOT,OUT,BASE,GROUPS,ALGS,read,save,sha,sources
from . import difference_views as views
from research.notch_identity_v32.audit import signature,selected
from research.notch_identity_v31.report import aggregate,NAMES,num
from research.v3_labelme_comparison.infer import read_csv
from research.v3_labelme_comparison.compare import table,write_csv
MODES=('full','raw_only')
FOCUS={'group_a':[366,398,504],'three_point_bend':[1,144,178,335,407,413],'group_c':[38,54,69,195,335,363,456,510,528]}

def pack(name,parts):
    archive=ROOT/'evidence/v3_6';archive.mkdir(exist_ok=True)
    body='\n\n'.join(parts)+'\n'
    (OUT/name).write_text(body,encoding='utf8')
    prefix='../../'+OUT.relative_to(ROOT).as_posix()+'/'
    (archive/name).write_text(re.sub(r'\]\(([^)]+)\)',lambda m:']('+prefix+m[1]+')',body),encoding='utf8')
    for p in (OUT/name,archive/name):
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf8')):assert (p.parent/link).is_file(),link

def collect():
    lock=read(OUT/'freeze.json');assert lock['sources']==sources()
    for k,name in [('group_a','group_a.jsonl'),('events','paired_events.csv'),('fixtures','fixtures.json'),('paired_probes','paired_probes.csv'),('dev_scores','group_a_scores.csv')]:
        assert sha(OUT/name)==lock[k]
    rows={(g,int(r['frame']),r['stage'],r['mode']):r for g in GROUPS for r in read_csv(OUT/(g+'_scores.csv'))}
    metrics=[];times=[];records={};audits=[]
    for g,n in GROUPS.items():
        for alg in ALGS:
            for mode in MODES:
                stats=aggregate([r for (grp,i,s,m),r in rows.items() if (grp,s,m)==(g,alg,mode)])
                metrics.append(dict(group=g,stage=alg,mode=mode,**stats))
        els=[];anchors=Counter();checks=Counter();seeds=0
        for folder in (OUT,BASE):
            assert sha(folder/(g+'.jsonl'))==read(folder/(g+'_seal.json'))['predictions']
        with (OUT/(g+'.jsonl')).open() as a,(BASE/(g+'.jsonl')).open() as b:
            for i,(s,t) in enumerate(zip_longest(a,b),1):
                rec=json.loads(s);prior=json.loads(t)
                assert i==rec['frame']==prior['frame'] and rec['source_sha']==prior['source_sha']
                m=rec['models']['v3_6'];d=m['full']['diagnostics']
                assert signature(m['raw_only'])==signature(prior['models']['v3_5']['raw_only'])
                els.append(m['seconds']);c=d.get('coarse') or {};anchors[c.get('anchor','NONE') if c.get('status')=='OK' else 'UNAVAILABLE']+=1
                seeds+=int(d.get('added_ridge_seeds',0)>0)
                for cand in d['candidates']:
                    tr=cand.get('trace',{});ref=tr.get('reference',{})
                    if ref:checks[ref['decision']]+=1
                if (g,i,'v3_6','full') not in rows:continue
                records[g,i]=rec
                for alg in ['v3_5']:
                    for mode in MODES:assert signature(rec['models'][alg][mode])==signature(prior['models'][alg][mode])
                for alg in ALGS:
                    for j,ca in enumerate(rec['models'][alg]['full']['diagnostics']['candidates']):
                        trace=ca.get('trace',{})
                        audits.append(dict(group=g,frame=i,stage=alg,index=j,selected=j==rec['models'][alg]['full']['diagnostics'].get('selected'),start=ca['start'],tip=ca['tip'],status=ca['status'],vetoed=ca.get('static_veto',False),positive=trace.get('positive_branch'),static=trace.get('static_branch'),geometry=trace.get('geometry'),waived=trace.get('waived'),lip=trace.get('waived_lip'),ridge=trace.get('red_seed'),extended=trace.get('clean_extension'),rescued=trace.get('rescued_gate'),reference=trace.get('reference'),rank=trace.get('increment_rank')))
        assert len(els)==n
        times.append(dict(group=g,frames=n,mean_ms=1000*float(np.mean(els)),fps=1/float(np.mean(els)),p95_ms=1000*float(np.percentile(els,95)),anchors=dict(anchors),reviews=dict(checks),ridge_seed_frames=seeds))
    assert len(records)==60
    for path,rr in [('ablation.csv',metrics),('timing.csv',times),('candidate_audit.csv',audits)]:write_csv(OUT/path,rr)
    return rows,metrics,times,records

def attribution(r,model,mode):
    t=selected(model);q=t.get('reference',{});rk=t.get('increment_rank',{})
    if not model['tip']:return '所有候选均未完成资格与末端认证；应按逐候选表核对最早的拒绝门。'
    if mode=='full' and r['group']=='group_c' and int(r['frame'])==7:
        return '尖端坐标相同，但补种路线的起点移动到更靠右、靠上的 (2255,2333)，输出点数从 21 减至 19，近口覆盖下降。'
    if mode=='full' and r['group']=='group_c' and int(r['frame'])==363:
        return '既有暗谷查重原已限制到 x=2474，新增回溯收至 x=2471，再认证停于 x=2470。人工端点在右侧，回溯在原本提前的路径上增加了短截误差。'
    if r['joint']=='True':return '尖端和路径仍联合命中；下表列出引起坐标或路径变化的首个消融阶段。'
    if r['hit10']=='True':return '尖端命中，但覆盖或预测点精度低于 80%，应按缺口两唇分别检查路径归属。'
    if mode=='full':
        g,i=r['group'],int(r['frame'])
        if g=='three_point_bend' and i==1:
            return '当前与固定参考为同一张图，所选路径没有新增暗线证据；预存裂纹与背景暗缘只能由灰度分支竞争，静态兜底选错了路径。'
        if g=='three_point_bend' and i==144:
            veto=sum(bool(c.get('static_veto')) for c in model['diagnostics']['candidates'])
            return f"同帧竞争淘汰 {veto} 条静态候选，胜出根点 {model['root']}，主干净增暗 {num(q.get('body_net'))}，几何终止 {t.get('geometry')}，参考复核 {q.get('decision')}。下一次独立检验应分别检查候选是否覆盖人工尖端以及进场后排名。"
        if g=='three_point_bend' and i==407:
            return f"几何豁免列为 {t.get('waived')}。最终认证在 {model['tip']}，观察续接点数 {t.get('clean_extension',0)}。应核对灰度末端认证对已获豁免的区域是否仍然提前回退。"
        if g=='group_c' and i in (38,54,69):
            d=model['diagnostics'];cs=d['candidates'];reds=[c for c in cs if c.get('trace',{}).get('red_seed')]
            return f"全口门提出 {d.get('whole_mouth_seeds',0)} 个种子，差分种子候选最终状态 {dict(Counter(c['status'] for c in reds))}。胜出候选为{'差分' if t.get('red_seed') else '原灰度'}种子。核对新增种子的根连接、是否追到人工尖端及同侧分支身份。"
        if g=='group_c' and i==335:
            return f"尖端相对人工位置 dx/dy 为 {num(r['dx'])}/{num(r['dy'])} px。形状核验给出 {q.get('prior_cut',q.get('cut'))}，最终裁剪列 {q.get('cut')}。需要分开检查首次沿背景斜纹偏航的位置与重新认证产生的回退。"
        if g=='group_c' and i in (195,456,510,528):
            return f"末端/主干 {num(q.get('tail_body_ratio'))}，当前门 {q.get('decision')}，豁免列 {t.get('waived')}。人工端点之后的连续低增暗列数和噪声阈值见开发报告的水平过冲表。"
    if mode=='full' and q.get('decision')=='NO_SUPPORTED_BOUNDARY':
        return '该候选缺少连续新增暗线边界。核对近口两唇是否都进入竞争，以及主干是否具有可认证正增暗。'
    if mode=='full' and q.get('cut') is not None:
        return f"参考复核 {q['decision']} 在 x={q['cut']} 施加上限；重新灰度认证后需核对回剪与人工尖端的距离。"
    if float(r['dx'])<0:
        return f"预测提前。最终几何门 {t.get('geometry')}，拟截断列 {t.get('geometry_cut')}，末端认证 {t.get('gate')}。应先区分轨迹没有到达、以及到达后失去认证。"
    if float(r['dy']) < -10:
        return '预测向右上偏离。需核对偏航前后背景是否出现相同倾角的暗线及有符号差分的双极边缘。'
    return f"末端越过人工端点，最后获 {t.get('gate')} 认证。逐列比较末端是否仍有与主干一致的新增暗线。"

def failure_report(rows,records):
    entries=[];doc=['# V3.6 失败帧与受损帧专项分析',
      '覆盖所有可见标注。尖端误差 >10 px、路径未联合命中、或相对 V3.5 误差增加/精度下降/覆盖下降的帧逐项记录。位置为当前原图像素，dx/dy 为预测减人工。未标注及不确定帧可在全序列图册查看。']
    raw_images={}
    for g in GROUPS:
        for mode in MODES:
            subset=[]
            for (grp,i),rec in records.items():
                if grp!=g:continue
                r=rows[g,i,'v3_6',mode];old=rows[g,i,'v3_5',mode]
                if r['state']!='VISIBLE':continue
                losses=[lbl for k,sgn,lbl in [('error_px',1,'误差增加'),('coverage',-1,'覆盖下降'),('precision',-1,'精度下降')] if r[k] and old[k] and (float(r[k])-float(old[k]))*sgn>1e-9]
                if r['joint']=='True' and not losses:continue
                m=rec['models']['v3_6'][mode];d=m['diagnostics'];t=selected(m);q=t.get('reference',{});cr=d.get('coarse') or {}
                path=(f'difference_views/frames/{g}/{i:04d}.jpg' if mode=='full' else f'failure_raw/{g}/{i:04d}.jpg')
                if mode=='raw_only':raw_images.setdefault(g,set()).add(i)
                category='尖端超差或缺测' if r['hit10']!='True' else '路径失分' if r['joint']!='True' else '仍命中但退化'
                caused=attribution(r,m,mode)
                changes=[]
                for a,b in zip(ALGS[:-1],ALGS[1:]):
                    ma,mb=rec['models'][a][mode],rec['models'][b][mode]
                    if signature(ma)!=signature(mb):changes.append(f"{b} 起点 {mb['root']}、尖端 {mb['tip']}")
                entries.append(dict(group=g,frame=i,mode=mode,category=category,changes=losses,gt=r['gt'],prediction=m['tip'],old_error=old['error_px'],error=r['error_px'],dx=r['dx'],dy=r['dy'],coverage=r['coverage'],precision=r['precision'],coarse=cr,reference=q,reason=caused,image=path,transitions=changes))
                subset.extend([f"### 第 {i} 帧 · {category}",f"人工 {r['gt']}，预测 {m['tip']}。误差 {num(old['error_px'])} → {num(r['error_px'])} px，dx/dy 为 {num(r['dx'])} / {num(r['dy'])}。覆盖 {num(r['coverage'])}，精度 {num(r['precision'])}。"+'、'.join(losses)+'。',
                   (f"粗定位 {cr.get('status')}（{cr.get('anchor')}），平移 {cr.get('shift')}；尾部 {q.get('source')}，净积分 {num(q.get('net'))}，负正比 {num(q.get('ratio'))}，主干 {num(q.get('body_net'))}，尾/干 {num(q.get('tail_body_ratio'))}。形状匹配 {q.get('shape_match')}，参考判定 {q.get('decision')}，裁剪列 {q.get('cut')}。全口门新种子 {d.get('whole_mouth_seeds',0)}，淘汰静态候选 {sum(bool(c.get('static_veto')) for c in d['candidates'])}，回溯前裁剪列 {q.get('prior_cut')}，低谷连续列 {q.get('low_run','—')}，选中候选近口豁免 {t.get('waived_lip')}，平坦区续接点数 {t.get('clean_extension',0)}。" if mode=='full' else '纯原灰度独立运行；图中固定参考与差分用于离线比对。'),
                   caused+' '+(' → '.join(changes) if changes else '各消融阶段的公开路径与端点一致。'),f'[四栏叠图]({path})'])
            doc.extend([f'## {NAMES[g]} · {mode}',*(subset or ['本项 0 帧。'])])
    for g,ids in raw_images.items():
        for card,diff,r in views.source_frames(g,ids,'raw_only'):
            dest=OUT/f"failure_raw/{g}/{r['frame']:04d}.jpg";dest.parent.mkdir(parents=True,exist_ok=True);card.save(dest,quality=94,subsampling=0)
    write_csv(OUT/'failures.csv',entries);pack('FAILURES_AUDIT.md',doc)
    with ZipFile(OUT/'failure_audit.zip','w',ZIP_DEFLATED) as z:
        for p in ['FAILURES_AUDIT.md','failures.csv',*[r['image'] for r in entries]]:z.write(OUT/p,p)
    with ZipFile(OUT/'failure_audit.zip') as z:assert z.testzip() is None
    return entries
