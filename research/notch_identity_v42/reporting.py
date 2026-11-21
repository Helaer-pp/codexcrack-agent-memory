"""Tables and paired post-seal audits shared by the two research releases."""
from collections import defaultdict
from pathlib import Path
from statistics import mean
import json,os,re
from zipfile import ZipFile,ZIP_DEFLATED
from research.notch_identity_v31.report import aggregate,NAMES,num
from research.notch_identity_v41.report import coord
from research.v3_labelme_comparison.infer import read_csv
from research.v3_labelme_comparison.compare import table,write_csv

FOCUS={'group_a':[67,366,398,504],'three_point_bend':[1,144,178,215,335,407,503],'group_c':[38,54,69,195,335,347,363,456,469,510,528]}

def pack(batch,name,parts):
    archive=batch.ROOT/'evidence'/batch.new.STAGES[-1]
    archive.mkdir(exist_ok=True)
    text='\n\n'.join(parts)+'\n'
    for folder in (batch.OUT,archive):
        def local(m):
            target=batch.OUT/m[1]
            assert target.is_file(),target
            return ']('+Path(os.path.relpath(target,folder)).as_posix()+')'
        (folder/name).write_text(re.sub(r'\]\(([^)]+)\)',local,text),encoding='utf8')

def collect(b):
    scores={};records={};metrics=[];timings=defaultdict(list)
    lock=b.read(b.OUT/'freeze.json')
    assert lock['sources']==b.sources()
    for field,f in [('group_a','group_a.jsonl'),('dev_scores','group_a_scores.csv'),('events','weak_events.csv'),('paired_probes','paired_probes.csv')]:
        assert b.sha(b.OUT/f)==lock[field]
    for g,n in b.GROUPS.items():
        path=b.OUT/(g+'.jsonl')
        assert b.sha(path)==b.read(b.OUT/(g+'_seal.json'))['predictions']
        for row in read_csv(b.OUT/(g+'_scores.csv')):
            scores[g,int(row['frame']),row['stage'],row['mode']]=row
        with path.open(encoding='utf8') as stream:
            for i,line in enumerate(stream,1):
                rec=json.loads(line)
                assert rec['group']==g and rec['frame']==i
                if len(rec['models'])>1 or i in FOCUS[g]:records[g,i]=rec
                for s,m in rec['models'].items():
                    for mode,field in [('full','seconds'),('raw_only','raw_seconds')]:
                        timings[g,s,mode].append(m[field])
        assert i==n
        for s in b.ALGS:
            for mode in ('full','raw_only'):
                rr=[r for (gg,i,ss,mm),r in scores.items() if (gg,ss,mm)==(g,s,mode)]
                assert len(rr)==20
                t=timings[g,s,mode]
                metrics.append(dict(group=g,stage=s,mode=mode,**aggregate(rr),hit5=sum(r['hit5']=='True' for r in rr),fps=1/mean(t),ms=1000*mean(t),timed=len(t)))
    write_csv(b.OUT/'ablation.csv',metrics)
    return scores,records,metrics

def metric_tables(b,metrics):
    parts=['## 实测消融与速度','每组各有 20 张人工标注，只有可见尖端参与命中分母。Joint 同时要求尖端误差 ≤10 px、10 px 容差内的路径覆盖和精度均 ≥80%。Severe 指有效预测误差 >100 px。无有效坐标按未命中计，中位及最大误差仅统计有效坐标。FPS 由单帧 prepare + predict 耗时算术均值换算；计时不含读图、评分和制图。表内另列实测计时帧数，六进程共享 CPU，跨批次吞吐受并发和首次编译影响。']
    for g in b.GROUPS:
        parts.extend(['### '+NAMES[g],table(['阶段','模式','有效/可见','Hit@5','Hit@10','Joint','Severe','中位 px','最大 px','ms','FPS','计时帧'],[(r['stage'],r['mode'],f"{r['valid']}/{r['visible']}",r['hit5'],r['hit'],r['joint'],r['severe'],num(r['median']),num(r['max']),num(r['ms']),num(r['fps']),r['timed']) for r in metrics if r['group']==g])])
    return parts

def probe_tables(tests):
    parts=['## 合成探针','每格为通过数/分母，P1 含 2.5 px 容差下的完整路径覆盖，P6 含预测路径精度 ≥95%，阳性尖端误差按原尺度 ≤10 px。isolated 对照使用恒深裂纹，分离渐隐、散点和外加干扰。']
    for stage,rs in tests:
        matrix=[]
        for case in dict.fromkeys(r['case'] for r in rs):
            line=[case]
            for z in (.5,1,2):
                for ph in ('nominal','dim','bright'):
                    q=[r for r in rs if r['case']==case and float(r['zoom'])==z and r['photo']==ph]
                    line.append(f"{sum(r['passed']=='True' for r in q)}/{len(q)}")
            matrix.append(line)
        parts.extend(['### '+stage,table(['探针']+[f'{z}× {ph}' for z in (.5,1,2) for ph in ('标准','暗','亮')],matrix)])
        for ph in ('nominal','dim','bright'):
            q=[r for r in rs if r['photo']==ph];neg=[r for r in q if r['negative']=='True']
            parts.append(f"{ph} 阴性误报 {sum(r['valid']=='True' for r in neg)}/{len(neg)}；已观测重连 {sum(int(r['accepted']) for r in q)} 次，错接 {sum(int(r['wrong']) for r in q)} 次。")
    return parts

def focus_tables(b,scores,records,stages):
    tables=['## 指定帧','端点为当前原图坐标。验证组C 347 缺少人工端点，仅报告定性坐标。']
    for g,ids in FOCUS.items():
        data=[]
        for i in ids:
            ms=records[g,i]['models'];final=ms[b.new.STAGES[-1]]['full'];d=final['diagnostics'].get('dual',{})
            cells=[]
            for s in stages:
                r=scores.get((g,i,s,'full'),{})
                cells.append((coord(ms[s]['full']['tip'])+' / '+num(r.get('error_px'))) if s in ms else '无同帧记录')
            data.append([f'[{i}](difference_views/frames/{g}/{i:04d}.jpg)',*cells,d.get('decision','—'),d.get('stop',final['status']),d.get('rejections',{})])
        tables.extend(['### '+NAMES[g],table(['帧',*stages,'主选','停止','拒绝'],data)])
    return tables

def failure_list(b,scores,records,comparators,detail,modes=('full',)):
    parts=['# '+b.new.STAGES[-1].replace('_','.').upper()+' 失败与退化帧专项分析','完整模式四栏图对应本版发布结果。统计相对对照版的尖端误差增加、路径覆盖/精度下降，以及缺失有效结果。'];entries=[]
    for g in b.GROUPS:
        parts.append('## '+NAMES[g])
        for (gg,i,s,mode),r in scores.items():
            if gg!=g or s!=b.new.STAGES[-1] or mode not in modes or r['state']!='VISIBLE':continue
            changed=[]
            for v in comparators:
                old=scores[g,i,v,mode]
                for k,sgn,lab in [('error_px',1,'尖端误差'),('precision',-1,'路径精度'),('coverage',-1,'覆盖')]:
                    if old[k] and r[k] and sgn*(float(r[k])-float(old[k]))>1e-9:changed.append(v+'/'+lab)
                if old['error_px'] and not r['error_px']:changed.append(v+'/失去端点')
            if not changed and r['joint']=='True':continue
            m=records[g,i]['models'][s][mode];d=m['diagnostics'].get('dual',{})
            why=detail(g,i,m,r,mode)
            photo=f'difference_views/frames/{g}/{i:04d}.jpg'
            olderr='，'.join(v+' '+num(scores[g,i,v,mode]['error_px']) for v in comparators)
            parts+= [f"### {i} · {mode} · "+('联合失败' if r['joint']!='True' else '命中但局部指标退化'),f"人工 {r['gt']}，预测 {coord(m['tip'])}，误差 {num(r['error_px'])} px（{olderr}）。dx/dy {num(r['dx'])} / {num(r['dy'])}；路径覆盖 / 精度 {num(r['coverage'])} / {num(r['precision'])}。{', '.join(changed)}。",why+f' [完整模式四栏图]({photo})']
            entries.append(dict(group=g,frame=i,mode=mode,error=r['error_px'],gt=r['gt'],tip=m['tip'],stop=d.get('stop'),why=why,image=photo))
    write_csv(b.OUT/'failures.csv',entries)
    return parts,entries
