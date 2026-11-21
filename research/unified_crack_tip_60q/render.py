"""All-frame local diagnostic viewer. No labels in raw rendering."""
import argparse,concurrent.futures as cf,json,html,time,gzip
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont
from .common import *
from .pipeline import load_evidence,resultdir

def png(path,a):
    assert not path.exists();Image.fromarray(a).save(path)
def signed_color(a):
    v=np.clip(np.nan_to_num(a)/40,-1,1);out=np.full((*a.shape,3),255,np.uint8)
    out[:,:,0]=np.where(v>=0,255,255*(1+v));out[:,:,2]=np.where(v<=0,255,255*(1-v));out[:,:,1]=255*(1-np.abs(v));return out
def lines(canvas,pts,color,width=1):
    if len(pts)>1:cv2.polylines(canvas,[np.rint(pts).astype(np.int32)],False,color,width,cv2.LINE_8)
def render_one(args):
    run,row,*options=args;follow=options[0] if options else False;cv2.setNumThreads(1);out=run/'galleries'/'frames'/row['group']/row['frame_id']
    if (out/'done.json').exists():
        entry=get(out/'done.json')
        if 'preferred' not in entry:
            data=json.loads((out/'data.js').read_text(encoding='utf-8').removeprefix('window.frameData=').removesuffix(';window.showFrame();'))
            entry['preferred']=data['preferred_uncertain_tip'] is not None
        return entry
    if follow:
        started=time.monotonic()
        while True:
            try:readgz(resultdir(run,'FULL',row['group'])/(row['frame_id']+'.json.gz'));break
            except (FileNotFoundError,EOFError,gzip.BadGzipFile,json.JSONDecodeError):
                if time.monotonic()-started>3600:raise TimeoutError('Full inference producer did not finish frame within one hour')
                time.sleep(2)
    out.mkdir(parents=True,exist_ok=True);e,m=load_evidence(framedir(run,row));record=readgz(resultdir(run,'FULL',row['group'])/(row['frame_id']+'.json.gz'));r=record['result'];raw=e['raw'];h,w=raw.shape;xa,ya,xb,yb=e['scene']['bounds'];off=np.array([xa,ya]);shape=(h,w,4)
    png(out/'raw.png',raw)
    current=imread(row['current']);scale=min(1.,1400/current.shape[1]);full=cv2.cvtColor(cv2.resize(current,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA),cv2.COLOR_GRAY2RGB)
    cv2.rectangle(full,tuple(np.rint(off*scale).astype(int)),tuple(np.rint(np.array([xb,yb])*scale).astype(int)),(255,190,0),2)
    for p in m['current_points']:cv2.circle(full,tuple(np.rint(np.asarray(p)*scale).astype(int)),5,(0,230,255),2)
    if r['tip']:cv2.drawMarker(full,tuple(np.rint(np.array(r['tip'])*scale).astype(int)),(30,255,30),cv2.MARKER_CROSS,18,2)
    Image.fromarray(full).save(out/'full.jpg',quality=90)
    geom=np.zeros(shape,np.uint8);roi=np.zeros(shape,np.uint8);obs=np.zeros(shape,np.uint8);accepted=np.zeros(shape,np.uint8);rejected=np.zeros(shape,np.uint8);gaps=np.zeros(shape,np.uint8);gaps_verified=np.zeros(shape,np.uint8);tracks=np.zeros(shape,np.uint8)
    for p in e['scene']['points_geometry']:cv2.circle(geom,tuple(np.rint(np.array(p)-off).astype(int)),6,(0,220,255,255),2)
    z=np.array(e['scene']['origin_zone']).reshape(2,2)-off;cv2.rectangle(geom,tuple(z[0].astype(int)),tuple(z[1].astype(int)),(255,190,0,255),2)
    if e['scene']['root']:cv2.drawMarker(geom,tuple(np.rint(np.array(e['scene']['root'])-off).astype(int)),(255,80,200,255),cv2.MARKER_CROSS,14,2)
    with np.load(resultdir(run,'FULL',row['group'])/(row['frame_id']+'_debug.npz')) as z:
        mask=z['mask'];roi[~mask]=(180,0,200,100)
    for event in r['roi_events']:
        if 'bounds' in event:
            b=np.asarray(event['bounds']).reshape(2,2)-off;cv2.rectangle(roi,tuple(b[0].astype(int)),tuple(b[1].astype(int)),(0,180,255,160),1)
    for k in range(len(e['ptr'])-1):lines(obs,e['xy'][e['ptr'][k]:e['ptr'][k+1]]-off,(255,230,0,200))
    # Each segment / gap is rasterized once per semantic layer; shared prefixes do not change its color.
    accepted_ids=set();rejected_ids=set();gap_ids=set();verified_gap_ids=set()
    for p in r['candidates']:
        (accepted_ids if p['verified'] else rejected_ids).update(k for k,entry in p['chain'])
        gap_ids.update(p['edges'])
        if p['verified']:verified_gap_ids.update(p['edges'])
    for ids,canvas,color in [(accepted_ids,accepted,(20,255,80,230)),(rejected_ids,rejected,(255,40,40,140))]:
        for k in sorted(ids):lines(canvas,e['xy'][e['ptr'][k]:e['ptr'][k+1]]-off,color,1)
    endpoints=e['features'][:,11:15].reshape(-1,2)
    for edge in sorted(gap_ids):
        rr=e['edges'][edge]
        if rr[2]<=1.5:continue
        ends=endpoints[rr[:2].astype(int)]-off;a,b=ends;distance=np.linalg.norm(b-a)
        for start in range(0,int(distance),6):
            pts=[a+(b-a)*start/max(1,distance),a+(b-a)*min(start+3,distance)/max(1,distance)]
            lines(gaps,pts,(0,255,255,255),1)
            if edge in verified_gap_ids:lines(gaps_verified,pts,(0,255,255,255),1)
    for t in r['tracks']:
        xy=tuple(np.rint(np.array(t['last_tip'])-off).astype(int));color=(30,255,30,255) if t['state']=='ACTIVE' else (180,180,180,255);cv2.circle(tracks,xy,4,color,1);cv2.putText(tracks,str(t['id'])+' '+t['state'],xy,cv2.FONT_HERSHEY_SIMPLEX,.35,color,1)
    if r['tip']:cv2.drawMarker(tracks,tuple(np.rint(np.array(r['tip'])-off).astype(int)),(255,255,255,255),cv2.MARKER_CROSS,20,2)
    for name,arr in [('geometry',geom),('roi',roi),('observed',obs),('verified',accepted),('rejected',rejected),('gaps',gaps),('tracks',tracks)]:png(out/(name+'.png'),arr)
    overlay=Image.fromarray(raw).convert('RGBA')
    for layer in [geom,accepted,gaps_verified,tracks]:overlay=Image.alpha_composite(overlay,Image.fromarray(layer))
    card=Image.new('RGB',(1800,800),(17,24,39));draw=ImageDraw.Draw(card)
    draw.text((20,16),f"{row['group']} frame {row['frame_id']} | {r['status']} | tip={r['tip']}",fill='white')
    draw.text((20,40),'RAW ROI (original pixel evidence; resized display)',fill='white');draw.text((920,40),'Current verified paths / inferred gaps / tracks (NO GT)',fill='white')
    for x0,img in [(20,Image.fromarray(raw).convert('RGB')),(920,overlay.convert('RGB'))]:
        img.thumbnail((860,210));card.paste(img,(x0,70))
    center=np.asarray(r['tip'] or r['preferred_uncertain_tip'] or e['scene']['root'] or e['scene']['center'])-off
    lx=max(0,min(w-1,int(center[0])-400));ly=max(0,min(h-1,int(center[1])-180));rx=min(w,lx+800);by=min(h,ly+360)
    lx=max(0,rx-800);ly=max(0,by-360);crop=(lx,ly,rx,by);local_bounds=[lx+xa,ly+ya,rx+xa,by+ya]
    local_raw=Image.fromarray(raw).crop(crop);local_result=overlay.convert('RGB').crop(crop)
    local_raw.save(out/'local_raw.png');local_result.save(out/'local_result.png')
    context_type='OFFICIAL OBSERVED TIP' if r['tip'] else 'UNCERTAIN CANDIDATE / ORIGIN (NOT OFFICIAL)'
    draw.text((20,310),'LOCAL RAW '+context_type+' '+str(local_bounds),fill='white');draw.text((920,310),'LOCAL RESULT (same original-coordinate crop)',fill='white')
    for x0,img in [(20,local_raw.convert('RGB')),(920,local_result)]:
        img.thumbnail((860,420));card.paste(img,(x0,340))
    draw.text((20,770),'Green: verified current segments | Cyan dashed: inferred gaps | White cross: official tip | Gray: historical LOST',fill='white')
    card.save(out/'comparison.jpg',quality=90)
    v=np.uint8(np.clip(e['valley']/max(e['threshold']*4,1)*255,0,255));png(out/'valley.png',cv2.cvtColor(cv2.applyColorMap(v,cv2.COLORMAP_VIRIDIS),cv2.COLOR_BGR2RGB))
    for channel in ['fixed','prev']:
        q=e[channel];png(out/(channel+'_signed.png'),signed_color(q['signed']));png(out/(channel+'_valid.png'),q['valid'].astype(np.uint8)*255)
    # Surface is an explicitly sampled view of original uint8 values, never detector input.
    import matplotlib
    matplotlib.use('Agg');import matplotlib.pyplot as plt
    xx=np.linspace(0,w-1,min(w,110),dtype=int);yy=np.linspace(0,h-1,min(h,60),dtype=int);X,Y=np.meshgrid(xx+xa,yy+ya)
    fig=plt.figure(figsize=(8,4.8));ax=fig.add_subplot(projection='3d');ax.plot_surface(X,Y,raw[np.ix_(yy,xx)],cmap='gray',vmin=0,vmax=255,linewidth=0);ax.set(xlabel='original x',ylabel='original y',zlabel='RAW uint8',zlim=(0,255),title='RAW surface (sampled display only)');ax.view_init(45,-75);fig.tight_layout();fig.savefig(out/'surface.png',dpi=100);plt.close(fig)
    candidates=[dict(id=p['id'],endpoint=p['endpoint'],verified=p['verified'],track_id=p.get('track_id'),rejected_reasons=p['rejected_reasons'],evidence=p['evidence'],chain=p['chain']) for p in r['candidates']]
    data=dict(group=row['group'],frame_id=row['frame_id'],status=r['status'],failure=r['failure_reason'],tip=r['tip'],preferred_uncertain_tip=r['preferred_uncertain_tip'],bounds=e['scene']['bounds'],local_bounds=local_bounds,local_context=context_type,shape=[h,w],scene=e['scene'],reference_info=r['reference_info'],roi_events=r['roi_events'],tracks=r['tracks'],rechecks=r['rechecks'],budget=r['budget'],candidates=candidates,threshold=e['threshold'],prepare_seconds=m['prepare_seconds'],engine_seconds=record['engine_seconds'])
    write(out/'data.js','window.frameData='+json.dumps(clean(data),ensure_ascii=False,separators=(',',':'))+';window.showFrame();')
    entry=dict(group=row['group'],frame_id=row['frame_id'],status=r['status'],failure=r['failure_reason'] or 'NONE',budget=r['budget']['exhausted'],jump=bool(r['rechecks']),preferred=r['preferred_uncertain_tip'] is not None,reference_unavailable=any(r['channels'][k]=='UNAVAILABLE' for k in ['fixed','prev']),path='frames/'+row['group']+'/'+row['frame_id']+'/')
    put(out/'done.json',entry);return entry

VIEWER=r'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>UCTIP 60Q 全帧证据</title>
<style>body{font:15px system-ui;background:#111827;color:#e5e7eb;margin:18px}select,button,input{margin:5px;padding:5px}img{max-width:100%;background:#222}#stage{position:relative;display:inline-block;max-width:100%;overflow:auto}#stage img{display:block;max-width:none}#stage img.layer{position:absolute;inset:0;pointer-events:none}pre{white-space:pre-wrap;max-height:420px;overflow:auto;background:#1f2937;padding:10px}details{margin:12px 0}a{color:#93c5fd}.row{display:flex;gap:12px;flex-wrap:wrap}.card{flex:1;min-width:340px}canvas{background:white;max-width:100%}#stage{max-height:700px;max-width:100%}</style>
<h1>UCTIP-60Q · 全帧诊断</h1><p>原始推理，无 GT。绿=已验证片段；红=拒绝路径；青虚线=推断 gap；灰=历史 LOST。参考图红正蓝负（±40 灰度）；有效掩膜白色才可作为参考证据。不能将无效区域的显示颜色当作零差分。研究原型，非生产批准。</p>
<p><a href="../reports/ABLATION_REPORT.md">开发消融报告</a> · <a href="../diagnostics/all_frame_failure_index.csv">全帧状态/阶段索引（最终交付后；无GT不判正确性）</a> · <a href="../diagnostics/DEV_failure_stages.csv">开发阶段审计</a> · <a href="../diagnostics/LOCKED_failure_stages.csv">验证组C阶段审计（最终运行后）</a> · <a href="../reports/FINAL_DECISION.md">最终验收（交付后）</a></p>
<div><select id="group"><option value="">全部组</option></select><select id="status"><option value="">全部状态</option></select><select id="failure"><option value="">全部失败原因</option></select><select id="extra"><option value="">全部条件</option><option value="budget">预算耗尽</option><option value="preferred">有不确定首选端点</option><option value="jump">异常跳跃复查</option><option value="reference_unavailable">参考不可用</option></select><input id="number" placeholder="帧号"><button onclick="filter()">筛选</button><span id="count"></span></div>
<button onclick="move(-1)">上一帧</button><select id="frames" onchange="loadFrame()"></select><button onclick="move(1)">下一帧</button><h2 id="title"></h2><p id="links"></p>
<div id="layers"></div><p>ROI 保持原始像素，可滚动；点击灰度图获取原图坐标、RAW 灰度和纵向截线。按住 Ctrl 滚轮可用浏览器缩放。</p><div id="stage"></div><p id="probe"></p><canvas id="profile" width="900" height="150"></canvas>
<details><summary>完整原图定位（展示缩略图）</summary><img id="full"></details>
<div class="row"><div class="card"><h3>局部原图（无正式端点时为候选/起源区）</h3><img id="local_raw"></div><div class="card"><h3>同坐标局部结果</h3><img id="local_result"></div></div>
<div class="row"><div class="card"><h3>RAW 多尺度暗谷响应</h3><img id="valley"></div><div class="card"><h3>原始灰度表面（采样展示）</h3><img id="surface"></div></div>
<div class="row"><div class="card"><h3>固定参考有符号差分 / 有效掩膜</h3><img id="fixed_signed"><img id="fixed_valid"></div><div class="card"><h3>实际上一帧有符号差分 / 有效掩膜</h3><img id="prev_signed"><img id="prev_valid"></div></div>
<details open><summary>候选、拒绝原因和段血缘</summary><input id="candidateQuery" placeholder="候选 ID / 拒绝原因" oninput="candidateTable()"><button onclick="candidatePageMove(-1)">候选上一页</button><button onclick="candidatePageMove(1)">候选下一页</button><span id="candidateCount"></span><pre id="candidates"></pre></details>
<details open><summary>主轨迹/正式轨迹、状态转换、预算删去的端点与前驱裁剪计数</summary><pre id="lineageAudit">加载当前帧身份审计</pre></details>
<details><summary>缺口、P 点及 ROI 扩张/回滚</summary><pre id="geometry"></pre></details><details><summary>独立参考配准窗口与失效原因</summary><pre id="refs"></pre></details><details><summary>轨迹、异常复查和预算</summary><pre id="audit"></pre></details>
<script>const entries=__ENTRIES__;let filtered=entries,selected=null,script=null,rawCanvas=null,candidatePage=0;
const el=id=>document.getElementById(id);for(let k of ['group','status','failure'])for(let v of [...new Set(entries.map(x=>x[k]))].sort()){let o=document.createElement('option');o.value=v;o.textContent=v;el(k).append(o)}
function filter(){filtered=entries.filter(x=>['group','status','failure'].every(k=>!el(k).value||x[k]===el(k).value)&&(!el('extra').value||x[el('extra').value])&&(!el('number').value||x.frame_id===el('number').value));el('frames').innerHTML='';filtered.forEach((x,i)=>{let o=document.createElement('option');o.value=i;o.textContent=x.group+' / '+x.frame_id+' / '+x.status;el('frames').append(o)});el('count').textContent=filtered.length+'/'+entries.length;loadFrame()}
function move(d){el('frames').selectedIndex=Math.max(0,Math.min(filtered.length-1,el('frames').selectedIndex+d));loadFrame()}
function loadFrame(){if(!filtered.length){selected=null;window.frameData=null;window.lastAcceptedFrame=null;rawCanvas=null;el('title').textContent='没有匹配帧';for(let k of ['stage','layers','links','candidates','lineageAudit','geometry','refs','audit'])el(k).innerHTML='';for(let n of ['full','local_raw','local_result','valley','surface','fixed_signed','fixed_valid','prev_signed','prev_valid'])el(n).hidden=true;return}selected=filtered[Number(el('frames').value)];if(script)script.remove();script=document.createElement('script');script.src=selected.path+'data.js';document.body.append(script)}
window.receiveAudit=function(d){if(!selected||d.group!==selected.group||d.frame_id!==selected.frame_id)return;el('lineageAudit').textContent=JSON.stringify(d,null,2)};
window.showFrame=function(){const d=window.frameData;if(!selected||!d)return;if(d.group!==selected.group||d.frame_id!==selected.frame_id){window.frameData=window.lastAcceptedFrame;return}window.lastAcceptedFrame=d;rawCanvas=null;let p=selected.path;el('lineageAudit').textContent='加载当前帧身份审计（完整记录另见血缘文件）';if(window.auditScript)window.auditScript.remove();window.auditScript=document.createElement('script');window.auditScript.src=p+'audit.js';document.body.append(window.auditScript);el('title').textContent=d.group+' · '+d.frame_id+' · '+d.status+' · tip '+JSON.stringify(d.tip);el('links').innerHTML='<a href="'+p+'raw.png">原始 ROI PNG</a> | <a href="../../raw_inference/FULL/'+d.group+'/'+d.frame_id+'.json.gz">完整推理 JSON.gz</a> | <a href="../../raw_inference/FULL/'+d.group+'/'+d.frame_id+'_lineage.json.gz">完整候选/前驱血缘</a> | <a href="../../evidence/'+d.group+'/'+d.frame_id+'/arrays.npz">数值证据 NPZ</a>';
// index lives in galleries/, so machine-readable links are one level above.
el('links').innerHTML=el('links').innerHTML.replaceAll('../../','../');
for(let n of ['full','local_raw','local_result','valley','surface','fixed_signed','fixed_valid','prev_signed','prev_valid'])el(n).hidden=false,el(n).src=p+(n==='local_result'?'local_result_clean':n)+(n==='full'?'.jpg':'.png');el('stage').innerHTML='';el('layers').innerHTML='';let base=document.createElement('img');base.src=p+'raw.png';base.width=d.shape[1];base.height=d.shape[0];el('stage').append(base);
base.onload=()=>{if(window.lastAcceptedFrame!==d)return;rawCanvas=document.createElement('canvas');rawCanvas.width=base.naturalWidth;rawCanvas.height=base.naturalHeight;rawCanvas.getContext('2d').drawImage(base,0,0)};
base.onclick=ev=>{if(!rawCanvas)return;let x=Math.floor(ev.offsetX),y=Math.floor(ev.offsetY);try{let ctx=rawCanvas.getContext('2d'),v=ctx.getImageData(x,y,1,1).data[0];el('probe').textContent='原图 ('+(x+d.bounds[0])+','+(y+d.bounds[1])+') RAW='+v;let c=el('profile').getContext('2d');c.clearRect(0,0,900,150);c.strokeStyle='#111';c.beginPath();for(let j=-45;j<=45;j++){let yy=Math.max(0,Math.min(rawCanvas.height-1,y+j)),g=ctx.getImageData(x,yy,1,1).data[0];let xx=(j+45)*10,py=145-g/255*135;j===-45?c.moveTo(xx,py):c.lineTo(xx,py)}c.stroke()}catch(e){el('probe').textContent='浏览器限制本地像素读取：请用 README 中的本地 http.server 命令；原始 PNG/NPZ 可直接打开。'}};
for(let n of ['geometry','roi','observed','verified','rejected','gaps','tracks','official']){let img=document.createElement('img');img.src=p+n+'.png';img.className='layer';let on=['verified','official'].includes(n);img.style.display=on?'block':'none';el('stage').append(img);let label=document.createElement('label'),box=document.createElement('input');box.type='checkbox';box.checked=on;box.onchange=()=>img.style.display=box.checked?'block':'none';label.append(box,n+' ');el('layers').append(label)}
el('geometry').textContent=JSON.stringify({scene:d.scene,roi_events:d.roi_events},null,2);el('refs').textContent=JSON.stringify(d.reference_info,null,2);el('audit').textContent=JSON.stringify({preferred_uncertain_tip:d.preferred_uncertain_tip,tracks:d.tracks,rechecks:d.rechecks,budget:d.budget,prepare_seconds:d.prepare_seconds,engine_seconds:d.engine_seconds},null,2);candidateTable()};
function candidatePageMove(delta){candidatePage+=delta;candidateTable(false)}
function candidateTable(reset=true){if(reset)candidatePage=0;let d=window.frameData;if(!d)return;let q=el('candidateQuery').value;let matches=d.candidates.filter(x=>!q||String(x.id)===q||x.rejected_reasons.some(r=>r.includes(q)));let pages=Math.max(1,Math.ceil(matches.length/50));candidatePage=Math.max(0,Math.min(pages-1,candidatePage));el('candidateCount').textContent='匹配 '+matches.length+' / 全部 '+d.candidates.length+'；第 '+(candidatePage+1)+' / '+pages+' 页，每页50条（全部可翻页）';el('candidates').textContent=JSON.stringify(matches.slice(candidatePage*50,(candidatePage+1)*50),null,2)}filter();</script></html>'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--split',choices=['DEV','LOCKED','ALL'],required=True);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--follow',action='store_true');a=ap.parse_args();run=Path(a.run).resolve()
    if a.follow:assert a.split=='DEV'
    if a.split in ['LOCKED','ALL']:check_freeze(run);assert (run/'manifests/LOCKED_inference_seal.json').exists()
    rs=inventory(run,None if a.split=='ALL' else a.split);entries=[]
    with cf.ProcessPoolExecutor(a.workers) as pool:
        for i,entry in enumerate(pool.map(render_one,[(run,r,a.follow) for r in rs])):
            entries.append(entry)
            if (i+1)%25==0:print('RENDER',a.split,i+1,len(rs),flush=True)
    filename='index.html' if a.split=='ALL' else a.split+'_index.html';write(run/'galleries'/filename,VIEWER.replace('__ENTRIES__',json.dumps(entries)))
    put(run/'galleries'/f'{a.split}_render_seal.json',dict(frames=len(entries),index_sha=sha(run/'galleries'/filename),entries=entries))

if __name__=='__main__':main()
