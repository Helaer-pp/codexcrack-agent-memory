"""Create the group_c audit from sealed predictions and the same 20 annotations."""
import json
import os
from collections import Counter
from pathlib import Path
from statistics import median
import numpy as np
from research.notch_identity_v58 import batch as r04
from research.notch_identity_v58_bright.run import OUT as R06
from research.notch_identity_v58_bright.evaluate import annotations,load_truth,evaluate
from research.notch_identity_v58_bright.views import card
from research.v3_labelme_comparison.compare import write_csv
from .run import ROOT,OUT,N,read,read_csv,sha,sources,save

EVIDENCE=ROOT/'evidence/v5_8_bright'
def count(rows,key):
    return sum(str(row[key])=='True' for row in rows)

def stats(rows):
    errors=[float(r['error_px']) for r in rows if r['error_px'] not in (None,'')]
    return dict(n=len(rows),tips=len(errors),hit5=sum(e<=5 for e in errors),hit10=sum(e<=10 for e in errors),
                joint=count(rows,'joint'),severe=count(rows,'severe'),median=round(median(errors),2),max=round(max(errors),2))
def metric_row(name,s):
    return '| '+' | '.join(map(str,[name,s['tips'],s['hit5'],s['hit10'],s['joint'],s['severe'],s['median'],s['max']]))+' |'
def link(label,path,folder):
    return '['+label+']('+os.path.relpath(path,folder).replace(os.sep,'/')+')'

def curves(i,mode,gt,model):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    folder=OUT/'failure_curves';folder.mkdir(exist_ok=True)
    with np.load(OUT/'surfaces'/f'{i:04d}_{mode}.npz') as z:
        fig,ax=plt.subplots(figsize=(8.2,3.5),layout='constrained')
        for branch,values in zip(z['branch_ids'],z['curves']):
            values=np.array(values,dtype=float);values[(~np.isfinite(values))|(values<-1e6)]=np.nan
            ax.plot(np.arange(len(values))+z['origin'][0],values,label=f'branch {branch}',lw=1.1)
        ax.axvline(gt[0],label='manual tip x',color='#156fa0',ls='--')
        if model['tip']:ax.axvline(model['tip'][0],label='published tip x',color='#b73529',ls=':')
        ax.set(xlabel='Original image x (px)',ylabel='Accumulated DP score',title=f'group_c  {i}  /  {mode}')
        ax.legend(ncol=2,fontsize=8);ax.grid(alpha=.2)
        path=folder/f'{i:04d}_{mode}.png';fig.savefig(path,dpi=125);plt.close(fig)
        return path

def main():
    os.environ.setdefault('MPLCONFIGDIR',str(OUT/'plot_cache'))
    assert sources()==read(OUT/'freeze.json')['sources']
    seal=read(OUT/'seal.json')
    assert sha(OUT/'group_c.jsonl')==seal['predictions'] and sha(OUT/'freeze.json')==seal['freeze']
    assert sha(OUT/'control_predictions.json')==read(OUT/'control_seal.json')['predictions']
    roster=annotations()
    records={r['frame']:r for r in map(json.loads,(OUT/'group_c.jsonl').open())}
    scores=read_csv(OUT/'scores.csv');old=read_csv(r04.OUT/'group_c_scores.csv');early=read_csv(R06/'scores.csv')
    sets=[('V5.7 r03','v5_7',old),('V5.8 r04','v5_8',old),('r05 原输入复算','r05_unrestricted',scores),('r06 逐帧行亮度裁剪','bright',early),('r07 外边界随动＋亮区点','bright',scores)]
    table={name+' / '+mode:stats([r for r in data if r['stage']==stage and r['mode']==mode]) for name,stage,data in sets for mode in ('full','raw_only')}
    controls=[]
    for r in read(OUT/'control_predictions.json'):
        i=r['frame'];gt,paths=load_truth(roster[i])
        if r['area']=='material' and r['anchors']=='cur_points':
            model=records[i]['models']['bright']['full']
            assert model['points']==r['points'] and model['tip']==r['tip']
        controls.append(dict(frame=i,area=r['area'],anchors=r['anchors'],**evaluate(dict(r,status='VALID' if r['tip'] else 'no_tip'),paths,gt)))
    write_csv(OUT/'control_scores.csv',controls)
    lengths=read_csv(OUT/'crack_lengths.csv');anchors=read_csv(OUT/'anchor_audit.csv');jitter=read_csv(OUT/'jitter.csv')
    assert len(anchors)==4*N and all(float(r['patch_min'])>=float(r['floor']) for r in anchors)
    jitter_rows=[];paired=[float(r['drift_px']) for r in jitter if r['drift_px']]
    for kind,delta in dict.fromkeys((r['kind'],r['requested']) for r in jitter):
        rs=[r for r in jitter if (r['kind'],r['requested'])==(kind,delta)]
        err=[float(r['drift_px']) for r in rs if r['drift_px']]
        jitter_rows.append(f"| {kind} | {delta} | {sum(float(r['max_clip_px'])>.70711 for r in rs)}/20 | {len(err)} | {median(err):.2f} | {max(err):.2f} | {count(rs,'joint')}/20 |")
    scored=[r for r in scores if r['stage']=='bright']
    fails=[];rawdir=OUT/'visuals/raw_failures';rawdir.mkdir(exist_ok=True,parents=True)
    for r in scored:
        if r['joint']=='True':continue
        i=int(r['frame']);mode=r['mode'];rec=records[i];model=rec['models']['bright'][mode];dual=model['diagnostics']['dual']
        gt,paths=load_truth(roster[i]);bs=dual['branches'];tip=model['tip'];e=r['error_px']
        curve=curves(i,mode,gt,model);picture=OUT/'visuals/frames'/f'{i:04d}.jpg'
        if mode=='raw_only':
            picture=rawdir/picture.name
            card(rec,gt,paths,r,OUT,'r07',mode)[0].save(picture,quality=91)
        if not tip:
            nearest=min((np.linalg.norm(np.subtract(b['tip'],gt)) for b in bs),default=None)
            reason=f"候选未发布，终止码 {dual['stop']}。"+(f"最近分支候选距标注 {nearest:.2f} px。" if nearest is not None else "没有候选分支。")
        else:
            winner=next(b for b in bs if 'BRANCH_'+str(b['id'])==dual['pick'])
            reason=f"选中分支 {winner['id']}，尖端横向偏差 {float(r['dx']):+.1f}、纵向偏差 {float(r['dy']):+.1f} px。"
            if winner['bridge']['accepted']:
                reason+=f"桥接前尖端 {winner['base_tip']}，距标注 {np.linalg.norm(np.subtract(winner['base_tip'],gt)):.1f} px；桥接后 {tip}。"
            else:
                reason+=('在标注前提前终止。' if float(r['dx'])<-10 else '终点越过标注。' if float(r['dx'])>10 else '路径与标注重合不足。')
        fails.append((i,mode,e,reason,picture,curve,[(b['id'],b['reason'],b['tip']) for b in bs]))
    full=[r for r in scored if r['mode']=='full'];ins=0
    for r in full:
        i=int(r['frame']);gt,_=load_truth(roster[i]);l,t,h,b=records[i]['geometry']['box'];ins+=l<=gt[0]<h and t<=gt[1]<b
    assert ins==20
    lengths_full=[r for r in lengths if r['mode']=='full' and r['path_length_px']]
    used_bridge=sum(any(('BRANCH_'+str(b['id'])==d['pick'] and b['bridge']['accepted']) for b in d['branches']) for d in (rec['models']['bright']['full']['diagnostics']['dual'] for rec in records.values()))
    rates={mode:N/sum(rec['models']['bright'][field] for rec in records.values()) for mode,field in [('full','seconds'),('raw_only','raw_seconds')]}
    freeze=read(OUT/'freeze.json')
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    for dest in [OUT,EVIDENCE]:
        def url(label,p):return link(label,p,dest)
        def asset(label,path):return url(label,OUT/path)
        failures=['# 验证组C V5.8 r07 失败帧分析','',
            'full 共 12 个联合失败帧，raw_only 共 11 个。每一行使用该模式自己的预测图和分支累计得分曲线。横坐标使用原图像素。仅用于离线归因。','',
            '| 帧 | 模式 | 误差 px | 判断依据 | 分支候选（编号、状态、端点） | 证据 |','|---:|---|---:|---|---|---|']
        for i,mode,e,reason,pic,curve,branches in fails:
            failures.append(f"| {i} | {mode} | {float(e):.2f} | {reason} | {branches} | {url('四栏图',pic)} · {url('累计曲线',curve)} |" if e else f"| {i} | {mode} | 无输出 | {reason} | {branches} | {url('四栏图',pic)} · {url('累计曲线',curve)} |")
        (dest/'FAILURES_AUDIT.md').write_text('\n'.join(failures)+'\n','utf8')
        lines=['# V5.8 验证组C亮材料带验证报告','',
         '按用户截图重跑验证组C 562 帧。20 个可见人工标注中，主模式 full 的尖端和路径联合通过 8 帧。5 帧出现超过 100 px 的严重误差，验证组C验收门要求至少 17/20 且严重误差为零，本轮未通过。','',
         asset('562 帧视频','visuals/group_c.mp4')+' · '+asset('逐帧图册与独立差分','visuals/index.html')+' · '+url('逐帧失败分析',dest/'FAILURES_AUDIT.md')+' · '+asset('逐帧裂纹长度','crack_lengths.csv'),'',
         '## 亮区和基准点','',
         f"将红框配准到固定参考原图，77 对匹配中有 {freeze['inliers']} 对一致，重投影残差中位数 {freeze['median_residual']:.2f} px。原图红框为 {freeze['reference_box']}，固定材料带为 {freeze['fixed_band']}，坐标顺序为左、上、右、下，右和下开区间。原始跟踪点保留作位移来源。首帧虚拟测量点为 P1 (2248,2278)、P2 (2263,2423)。",
         '固定参考确定外边界，每帧用原点位移传递，再取参考与当前可用带的交集。每个新点在两幅图各自的 9×9 邻域内逐像素通过亮度检查，同时保留原点记录的相对位移并取整。这样不要求裂纹自身变亮。新点属于虚拟测量坐标，未独立测定材料点运动。每帧都保存新旧坐标、最低灰度和阈值。20 个人工尖端均落在有效框内。',
         f"562 帧的参考和当前图共 {len(anchors)} 个名义点邻域通过检查。"+asset('点位检查表','anchor_audit.csv')+' · '+asset('用户原始红框','user_region.png')+' · '+asset('冻结记录','freeze.json'),'',
         '## 同帧对照','',
         '各行分母均为同一批 20 个标注。联合通过要求尖端误差 ≤10 px、路径覆盖率和精确率均 ≥0.8，路径容差 10 px。严重误差为 >100 px。中位数与最大值只统计已输出的尖端。full 使用原灰度与参考辅助，raw_only 的裂纹检测只用当前灰度，两者共享亮区输入几何。','',
         '| 版本与模式 | 有尖端 | ≤5 px | ≤10 px | 联合 | 严重 | 中位误差 px | 最大误差 px |','|---|---:|---:|---:|---:|---:|---:|---:|',*[metric_row(name,s) for name,s in table.items()],'',
         'r06 把每帧局部暗行当成材料边界。第 335 帧上界收缩至 y=2343，无可达分支。r07 沿固定外边界传递，该帧上界 y=2281，尖端误差 0.30 px。r06 结果已保留。'+url('r06 逐帧图册',R06/'visuals/index.html'),'',
         '### 将搜索范围和点位分开比较','',
         '以下四组均以 P1/P2 中点初始化同一个冻结检测器，仅切换搜索范围与输入点。表中的原点位用于归因。上表的 r05 原输入另沿用了历史初始化位置。','',
         '| 范围与点位 | 有尖端 | ≤5 px | ≤10 px | 联合 | 严重 | 中位误差 px | 最大误差 px |','|---|---:|---:|---:|---:|---:|---:|---:|']
        for area,scope in [('original','原范围'),('material','亮材料带')]:
            for key,pt in [('original_cur','原点位'),('cur_points','亮区点')]:
                lines.append(metric_row(scope+' / '+pt,stats([r for r in controls if r['area']==area and r['anchors']==key])))
        lines+=['','原搜索范围下，只移动点位仍为 0/20。固定亮材料带后，原点位与亮区点分别为 12/20 和 8/20。限制搜索范围和改变检测器初始化位置均会影响表现，亮区点约束本身不能保证精度。'+asset('四组逐帧对照','control_scores.csv'),'',
            '## 基准点敏感性','',
            '以各帧已通过检查的点为起点，同时改变参考和当前点。axis 表示沿基准线移动，normal 表示沿法向移动，单位 px；span_pct 表示点距缩放百分比。表中“修正”指至少一点的请求坐标与实际坐标相差超过像素取整上限 0.70711 px。漂移只统计名义与扰动后都输出尖端的情况。','',
            '| 方向 | 请求幅度 | 位置经修正 | 有成对尖端 | 中位漂移 px | 最大漂移 px | 联合通过 |','|---|---:|---:|---:|---:|---:|---:|',*jitter_rows,'',
            f"共 200 次，{len(paired)} 次有成对尖端，中位漂移 {median(paired):.2f} px，最大 {max(paired):.2f} px。原来无尖端而扰动后有尖端 {sum(r['base_valid']=='False' and r['valid']=='True' for r in jitter)} 次。实际点位有 183 次因亮区或邻域约束被修正。每个扰动都使用名义结果作配对对照。"+asset('实际坐标及尖端漂移','jitter.csv'),'',
            '## 失效位置与长度','',
            'full 的前四个标注帧（1、7、38、54）在预存裂纹确认处未发布尖端。第 69、95 帧提前终止。第 345、363、456、469、480 帧均选中了发生前向桥接的分支，其终点到达上边界附近；逐帧分析记录了桥接前后的端点。第 510 帧未触发桥接，终点越过标注约 14 px。亮区只约束搜索范围，边界附近的背景结构仍可能被连接。',
            f"全序列 full 有 {len(lengths_full)}/{N} 帧输出长度，主分支采用桥接 {used_bridge} 帧。弧长取识别根部到尖端的折线总长，投影长度以实际新点中点为零点，单位均为 px。没有有效识别时留空。错误桥接同样会高估长度，未标注帧仅能确认输出完整性。检测器计时 full {rates['full']:.2f} FPS、raw_only {rates['raw_only']:.2f} FPS，不含图像读取、亮区选点、评分及渲染。",
            '',asset('第 221 帧','visuals/frames/0221.jpg')+' · '+asset('第 335 帧','visuals/frames/0335.jpg')+' · '+asset('第 335 帧差分','visuals/differences/0335.png')+' · '+asset('第 456 帧错误桥接','visuals/frames/0456.jpg')+' · '+asset('四栏失败帧及差分压缩包','visuals/failure_views.zip'),'',
            '## 数据使用与复现','',
            '本轮只运行验证组C。沿用 V5.8 r05 已冻结的检测源码与参数，人工标注在结果封存后用于误差、路径对照和可视化。r07 的外边界处理是在检查 r06 验证组C表现时修正的，因此这是已暴露验证组的复核。排除组X未参与；开发组A、三点弯及其他组未重跑。既有三组合成与消融结果见前版报告。后续桥接诊断宜在开发组或合成边界样例上验证。','',
            url('前版三组与消融报告',ROOT/'evidence/v5_8/REPORT.md')+' · '+asset('离线评分明细','scores.csv')+' · '+asset('结果封存','seal.json')+' · '+url('推理入口',ROOT/'research/notch_identity_v58_material/run.py')+' · '+url('亮区几何',ROOT/'research/notch_identity_v58_material/region.py')]
        (dest/'REPORT.md').write_text('\n'.join(lines)+'\n','utf8')
    save(EVIDENCE/'latest_metrics.json',dict(frames=N,comparison=table,anchor_checks=len(anchors),paired_jitter=len(paired),max_drift=max(paired),valid_lengths=len(lengths_full),detector_fps=rates))
    print('Wrote reports and failure evidence',len(fails))


if __name__=='__main__':main()
