"""Publish the paired replay with auditable denominators and review links."""
import csv
import html
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from statistics import median
from collections import defaultdict
from six_roi_replay import CASES, DISPLAY, HASH, NAMES, OUT

def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as file:
        return list(csv.DictReader(file))

def save_rows(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)

def number(x):
    return '—' if x is None else f'{x:.2f}'

def main():
    metrics, examples, anchors, differences = [], [], [], []
    for group, title in NAMES.items():
        directory = OUT/group
        summary, manifest, media = [json.loads((directory/f'{key}.json').read_text(encoding='utf8'))
                                    for key in ('summary', 'manifest', 'media')]
        assert manifest['dll'] == HASH and manifest['frames'] == summary['total'] == media['png'] == int(media['nb_read_frames'])
        cohort = [r for r in read_rows(directory/'frames.csv') if r['coverage'] == 'shared']
        strict = [r for r in cohort if r['all_returned_tips_in_all_roi'] == 'True']
        mixed_strict = sum(int(r['confirmed']) < 8 for r in strict)
        moved_strict = sum(float(r['pair_max_px'] or 0) > 0 for r in strict)
        affected = [r for r in cohort if 0<int(r['confirmed'])<8 or float(r['pair_max_px'] or 0)>0]
        metrics.append(dict(组别=title,帧数=summary['total'],无对照点=summary['unknown'],窗口未共同覆盖=summary['outside'],
                            共同覆盖=summary['shared'],全未确认=summary['none'],部分确认=summary['mixed'],
                            八组均确认且同点=summary['same8'],八组均确认但位置不同=summary['all8']-summary['same8'],
                            至少两组确认=summary['co_confirmed'],坐标变化=summary['varying_coordinates'],
                            确认状态或坐标变化=len(affected),最大组间距离_px=number(summary['max_px']),
                            P95组间距离_px=number(summary['p95_frame_span_px']),
                            严格子集帧数=len(strict),严格子集部分确认=mixed_strict,严格子集坐标变化=moved_strict,
                            各选点未确认帧数下限=summary['miss_range'][0],各选点未确认帧数上限=summary['miss_range'][1]))
        differences.extend(dict(组别=title,**r) for r in affected)
        labels = dict(zip(CASES,DISPLAY))
        if group=='group_h':
            labels['longer']='间距 × 1.20'
        anchors.extend(dict(组别=title,选点=labels[r['case']],共同覆盖=r['common'],确认=r['confirmed'],
                            未确认=r['missing']) for r in read_rows(directory/'case_summary.csv'))
        by_case = read_rows(directory/'per_case.csv')
        measured = [r for r in by_case if r['case']=='measured' and r['coverage']=='shared' and r['confirmed']=='1']
        windows = defaultdict(set)
        for r in by_case:
            if r['coverage']=='shared':
                windows[r['frame']].add(r['roi'])
        metrics[-1]['不同实际ROI数最小值'] = min(map(len,windows.values()),default=0)
        metrics[-1]['不同实际ROI数最大值'] = max(map(len,windows.values()),default=0)
        metrics[-1]['实测点确认帧数'] = len(measured)
        metrics[-1]['实测点至旧版对照距离中位数_px'] = number(median(float(r['distance_to_proxy_px']) for r in measured) if measured else None)
        focus = max(affected,key=lambda r:(float(r['pair_max_px'] or 0),r['all_returned_tips_in_all_roi']=='True',
                                           -abs(int(r['confirmed'])-4)),default=None)
        if focus:
            serial = int(focus['frame'])
            cases = [z for z in by_case if int(z['frame'])==serial]
            record = cases[0]
            png = directory/'frames'/f"{serial:04d}_{Path(record['image']).stem}.png"
            assert png.is_file()
            txt = '，'.join(f"{labels[z['case']]} ({z['tip_x']}, {z['tip_y']})" if int(z['confirmed'])
                            else f"{labels[z['case']]} 未确认" for z in cases)
            examples.append((title, serial, record['image'], png.relative_to(OUT).as_posix(), txt))
    assert len(metrics)==len(NAMES) and sum(r['帧数'] for r in metrics)>0
    save_rows(OUT/'七组汇总.csv',metrics)
    save_rows(OUT/'每种选点确认统计.csv',anchors)
    if differences:
        save_rows(OUT/'结果随选点变化的帧.csv',differences)
    with ZipFile(OUT/'逐帧数值及汇总.zip','w',ZIP_DEFLATED,compresslevel=3) as archive:
        for p in OUT.glob('*.csv'):
            archive.write(p,p.name)
        for group in NAMES:
            for filename in ('frames.csv','per_case.csv','common_pairs.csv','manifest.json','case_summary.csv','media.json'):
                p=OUT/group/filename
                archive.write(p,p.relative_to(OUT))
    total=lambda key:sum(r[key] for r in metrics)
    note=(f"共 {total('帧数')} 帧，每帧独立比较八种选点。旧 A 在 {total('无对照点')} 帧没有对照尖端，另外 {total('窗口未共同覆盖')} 帧的对照点位于至少一个 ROI 外。其余 {total('共同覆盖')} 帧进入主比较。"
          f"其中 {total('全未确认')} 帧八组都未确认，{total('部分确认')} 帧只有部分组选点确认，{total('八组均确认且同点')} 帧八组均确认且同点，{total('八组均确认但位置不同')} 帧八组均确认但位置有差异。"
          f"把部分确认与坐标变化合并去重后，共 {total('确认状态或坐标变化')} 帧对选点敏感。")
    strict_note=(f"进一步要求至少有一个新版输出，且当帧所有新版输出点也位于八个 ROI 的交集，共 {total('严格子集帧数')} 帧。"
                 f"其中 {total('严格子集部分确认')} 帧只有部分组确认，{total('严格子集坐标变化')} 帧已返回的坐标有差异。这两项可以重叠。")
    mechanism=("新版 A 在整个 ROI 内比较有图像支持的线段。实现中会检查尾端暗线、前方材料以及竞争路径，遇到两条得分接近且不重合的路径时可以返回未确认。因此，即使尖端像素仍在窗口内部，移动窗口也可能改变进入比较的背景线条。"
               "本轮逐帧记录了窗口和最终输出，可以查实哪些帧发生变化。具体是哪条内部条件否决某一帧，需要候选级日志才能确定。")
    method=("旧 A 实测点回放给出的尖端仅用于筛选和对照，没有传给本次 DLL。尚无逐帧人工尖端标注，因而“全未确认”和“部分确认”是以旧 A 输出为对照的未确认统计，真实漏检率和尖端误差无法据此测定。"
            "同一帧有至少两组选点确认时才计算原图坐标欧氏距离，最大组间距离取八种选点所有已确认组合的最大值。"
            "每组使用第一帧作参考，从同一条实测 P1/P2 轨迹构造原点、右移 5/10/20 px、左移 10 px、上移 10 px、间距 ×0.75、间距 ×1.35 八组。开发组H MT 的放大条件改为 ×1.20，避免点落在图外。"
            "每种选点各自初始化并独立按时序计算，保持原组参考模式与发布参数。ROI 尺寸有上下限，部分组改变间距可能得到相同窗口。“七组汇总.csv”记录可比帧中不同实际 ROI 的个数范围。排除组X为历史回放，三点弯只用于验证。本轮使用修复版 A，并保留逐帧原因。")
    cols=['组别','帧数','共同覆盖','全未确认','部分确认','八组均确认且同点','八组均确认但位置不同','最大组间距离_px']
    def md_table():
        return ['|'+'|'.join(cols)+'|','|'+'|'.join(['---']*len(cols))+'|',*['|'+'|'.join(str(row[c]) for c in cols)+'|' for row in metrics]]
    def h(text):
        return html.escape(str(text))
    table='<table><tr>'+''.join(f'<th>{h(c)}</th>' for c in cols)+'</tr>'
    table+=''.join('<tr>'+''.join(f'<td>{h(r[c])}</td>' for c in cols)+'</tr>' for r in metrics)+'</table>'
    media_links=[f'<p>{h(name)}　<a href="{g}/comparison.mp4">对比视频</a> · <a href="{g}/frames.zip">逐帧 PNG 包</a> · <a href="{g}/frames/">图像目录</a> · <a href="{g}/per_case.csv">逐帧八组选点位置</a></p>' for g,name in NAMES.items()]
    detail=[f'{name} 第 {i} 帧 {image} — {txt}。' for name,i,image,p,txt in examples]
    page=['<!doctype html><html lang="zh"><meta charset="utf-8"><title>七组裂纹尖端选点复核</title><style>body{font:16px/1.7 "Microsoft YaHei",sans-serif;max-width:1150px;margin:32px auto;color:#14212c}table{border-collapse:collapse}td,th{border:1px solid #c9d5df;padding:5px 9px;text-align:center}a{color:#12598d}</style>',
          '<h1>七组裂纹尖端选点复核</h1>',f'<p>{h(note)}</p>',table,f'<p>{h(strict_note)}</p>',
          '<h2>视频和逐帧原图</h2>',*media_links,'<p><a href="逐帧数值及汇总.zip">七组逐帧数值、成对比较和汇总表</a></p>',
          '<h2>复核帧</h2>',*[f'<p><a href="{p}">{h(t)}</a></p>' for t,(_,_,_,p,_) in zip(detail,examples)],
          '<h2>选点如何影响结果</h2>',f'<p>{h(mechanism)}</p>','<h2>比较口径</h2>',f'<p>{h(method)}</p>',f'<p>CrackV4.dll SHA-256　{HASH}</p></html>']
    (OUT/'index.html').write_text('\n'.join(page),encoding='utf8')
    report=['# 七组裂纹尖端选点复核','',note,'',*md_table(),'',strict_note,'','## 复核帧','',*detail,'','## 选点如何影响结果','',mechanism,'','## 比较口径','',method,'',f'发布 DLL SHA-256　{HASH}']
    (OUT/'复核报告.md').write_text('\n'.join(report)+'\n',encoding='utf8')
    print(note,strict_note,sep='\n')

if __name__=='__main__':
    main()
