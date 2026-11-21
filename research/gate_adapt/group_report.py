"""Build a local review page for seven completed, verified runs."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
GROUPS={'group_a':'开发组A','group_c':'验证组C','ct2':'CT2','group_h':'开发组H MT','three_point_bend':'三点弯','ct3':'CT3 白色喷漆','group_x':'排除组X白板'}
ROLE={'group_a':'开发回归','group_c':'开发回归','ct2':'开发回归','group_h':'开发回归','three_point_bend':'验证专用','ct3':'已用于研发','group_x':'退役历史回放'}


def neighbor_audit(folder,rows):
    """Retrospective triage only. Never used for detection or tuning."""
    with (folder/'paths.jsonl').open(encoding='utf8') as f:
        anchors=[json.loads(line)['anchors'] for line in f]
    reference_spacing=np.linalg.norm(np.diff(anchors[0],axis=0))
    def local(i):
        p1,p2=np.asarray(anchors[i]); v=p2-p1
        basis=np.array([[v[1],-v[0]],v])
        tip=np.array([float(rows[i]['tip_x']),float(rows[i]['tip_y'])])
        return basis@(tip-(p1+p2)/2)*reference_spacing/(v@v)
    limit=max(12.,.08*reference_spacing)
    reviewed=[]
    for i,r in enumerate(rows):
        if r['source'] not in ('gap','adapt'):continue
        before=next((k for k in range(i-1,max(-1,i-6),-1) if rows[k]['source']=='A'),None)
        after=next((k for k in range(i+1,min(len(rows),i+6)) if rows[k]['source']=='A'),None)
        if before is None or after is None:continue
        a,b=local(before),local(after)
        if np.linalg.norm(a-b)>limit:continue
        p=local(i)
        delta=min(np.linalg.norm(a-p),np.linalg.norm(b-p))
        reviewed.append(dict(group=folder.name,frame=i+1,image=r['image'],source=r['source'],before=before+1,after=after+1,
                             distance_px=round(float(delta),2),threshold_px=round(limit,2),flag=bool(delta>limit),png=r['png']))
    return sorted(reviewed,key=lambda x:-x['distance_px'])


def build(out):
    sets=[];examples=[];table=[];audit=[];flaglist=[]
    for key,name in GROUPS.items():
        folder=out/key
        s=json.loads((folder/'summary.json').read_text())
        with (folder/'results.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
        assert len(rows)==s['frames']==s['verified_video_frames']
        table.append(f"<tr><th>{name}</th><td>{ROLE[key]}</td>"+''.join(f"<td>{s[k]}</td>" for k in ['frames','A','V1','latest','missing','complete_lengths'])+f"<td><a href='{key}/result.mp4'>视频</a> · <a href='{key}/results.csv'>CSV</a> · <a href='{key}/frames/'>逐帧图</a></td></tr>")
        sets.append(dict(key=key,name=name,rows=[[r['png'],r['image'],r['source'],r['tip_x'],r['tip_y'],r['length_px'],r['action']] for r in rows]))
        checks=neighbor_audit(folder,rows);audit.extend(checks)
        flagged=[r for r in checks if r['flag']]
        if flagged:
            r=flagged[0]
            flaglist.append(f"<li>{name}：{len(flagged)} 帧超过复核线。最大偏移见 <a href='{key}/frames/{r['png']}'>第 {r['frame']} 帧</a>（{r['distance_px']} px）。</li>")
        for kind in ('gap','adapt','none'):
            candidates=[r for r in rows if r['source']==kind]
            if candidates:
                r=candidates[len(candidates)//2]
                examples.append(dict(group=key,category=kind,frame=r['frame'],image=r['image'],path=str(folder/'frames'/r['png'])))
    review_text=f"<p>在各新增帧前后各 5 帧以内寻找 A 已确认尖端；只有两侧尖端彼此接近才纳入。将坐标转换到随基准点移动的坐标系，新增尖端到两侧的距离均超过 max(12 px, 0.08 × 首帧基准点间距) 时标记供复核。{len(audit)} 帧满足对照条件，{sum(r['flag'] for r in audit)} 帧超过复核线。该筛选只用于找跳点，不能覆盖没有邻帧参照的错误或稳定误跟踪。</p><ul>"+''.join(flaglist)+"</ul>"
    if audit:
        with (out/'neighbor_review.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=audit[0]);w.writeheader();w.writerows(audit)
    html=PAGE.replace('{{TABLE}}','\n'.join(table)).replace('{{REVIEW}}',review_text).replace('{{DATA}}',json.dumps(sets,ensure_ascii=False).replace('<','\\u003c'))
    (out/'index.html').write_text(html,encoding='utf8')
    (out/'review_examples.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2),encoding='utf8')
    print('Report verified:',len(sets),'groups,',sum(len(g['rows']) for g in sets),'frames')


PAGE="""<!doctype html><html lang="zh"><meta charset="utf-8"><title>七组裂纹回放</title>
<style>
*{box-sizing:border-box}body{max-width:1440px;margin:auto;padding:28px;color:#162934;background:#fbfaf6;font:15px/1.5 "Microsoft YaHei",sans-serif}
h1,h2{margin:.65em 0}td,th{text-align:left;padding:7px 12px;border-bottom:1px solid #ccd1cc}table{border-collapse:collapse;width:100%;background:white}
a{color:#076465}select,input,button{padding:5px;font:inherit}label,button{margin-right:10px}#frame,video{display:block;max-width:100%;margin-top:8px}video{width:min(100%,900px)}#frame{width:100%}#readout{min-height:24px}section{margin:24px 0}p{max-width:1050px}
</style>
<h1>七组裂纹逐帧回放</h1>
<p>每组按时序使用首帧和逐帧基准点。表中 A、断点恢复版和最新适配版的数字都是输出尖端的帧数，含参考帧。完整长度只计根部和尖端都确认的帧。各组缺少人工尖端真值，真实定位误差与误识别率暂不可计算。</p>
<table><thead><tr><th>试验组</th><th>用途</th><th>帧数</th><th>冻结 A</th><th>断点恢复</th><th>最新适配</th><th>未确认</th><th>有完整长度</th><th>文件</th></tr></thead><tbody>{{TABLE}}</tbody></table>
<section><h2>新增尖端复核</h2>{{REVIEW}}</section>
<section><h2>查看逐帧 ROI</h2>
<label>试验组 <select id="group"></select></label><label>结果来源 <select id="filter">
<option value="">全部</option><option value="adapt">最新适配新增</option><option value="gap">断点恢复新增</option><option value="A">冻结 A 已确认</option><option value="none">尖端未确认</option></select></label>
<button id="prev">上一张</button><button id="next">下一张</button><label>跳到帧号 <input id="num" type="number" min="1" style="width:85px"></label>
<p id="readout"></p><a id="full"><img id="frame" alt="左侧原图 ROI，右侧同一区域的检测结果"></a>
</section><section><h2>本组视频</h2><video id="video" controls preload="metadata"></video><button id="locate">查看视频当前帧的结果图</button><p>15 FPS 演示回放。红线为已输出路径，黄圈为尖端；坐标单位为原图像素，图中不跨断点补线。</p></section>
<script>const groups={{DATA}}, el=id=>document.getElementById(id), group=el('group'), filter=el('filter'), num=el('num');
const labels={A:'冻结 A',gap:'断点恢复新增',adapt:'最新适配新增',none:'尖端未确认'};
for (const g of groups) group.add(new Option(g.name,g.key));
let indexes=[],pos=0; function current(){return groups.find(g=>g.key===group.value)}
function render(){let i=indexes[pos],g=current(),ok=i!==undefined;
el('prev').disabled=!ok||pos===0;el('next').disabled=!ok||pos>=indexes.length-1;
el('frame').hidden=!ok;el('frame').style.display=ok?'block':'none';num.max=g.rows.length;
if(!ok){el('readout').textContent='本组没有符合筛选条件的帧。';return}
let [png,file,source,x,y,len,reason]=g.rows[i];num.value=i+1;
let url=g.key+'/frames/'+encodeURIComponent(png);el('full').href=url;el('frame').src=url;
el('readout').textContent='第 '+(i+1)+' / '+g.rows.length+' 帧 · '+file+' · '+labels[source]+(x?' · 尖端 ('+Number(x).toFixed(2)+', '+Number(y).toFixed(2)+') px':'')+(len?' · 完整弧长 '+Number(len).toFixed(2)+' px':' · 完整长度未确认')+' · 当前筛选 '+indexes.length+' 帧';}
function reset(){indexes=current().rows.map((r,i)=>(!filter.value||r[2]===filter.value)?i:-1).filter(i=>i>=0);pos=0;render()}
group.onchange=()=>{el('video').src=current().key+'/result.mp4';reset()};filter.onchange=reset;
el('prev').onclick=()=>{pos--;render()};el('next').onclick=()=>{pos++;render()};
num.onchange=()=>{let i=Number(num.value)-1;if(!Number.isInteger(i)||i<0||i>=current().rows.length){render();return}if(!indexes.includes(i)){filter.value='';reset()}pos=indexes.indexOf(i);render()};
el('locate').onclick=()=>{let v=el('video');v.pause();num.value=Math.min(current().rows.length,1+Math.floor(v.currentTime*15));num.onchange();el('readout').scrollIntoView()};
group.onchange();</script></html>"""


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('run_id');args=parser.parse_args()
    if Path(args.run_id).name!=args.run_id:raise ValueError(args.run_id)
    build(ROOT/'output/runs'/args.run_id)

