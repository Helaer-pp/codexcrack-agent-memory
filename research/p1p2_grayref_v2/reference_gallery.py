"""Post-inference visualization of saved reference evidence; no detector changes."""
from v2common import *
from PIL import Image,ImageDraw,ImageFont
import numpy as np,html
from media_v2 import FONT

def evidence_card(folder,target,title):
 d=unpack(folder/'result.json.gz');a=np.load(folder/'evidence.npz');g=d['roi'];w=a['csm'].shape[1];h=a['csm'].shape[0]
 canvas=Image.new('RGB',(1400,1370),'#132131');draw=ImageDraw.Draw(canvas);font=ImageFont.truetype(FONT,20);small=ImageFont.truetype(FONT,16)
 draw.text((18,10),title+' | 参考证据审计（显示缩放不参与检测）',font=font,fill='white')
 draw.text((18,43),f"原图裁剪 x=[{g['xa']},{g['xb']}) y=[{g['ya']},{g['yb']}) | 正新增=红，负新增=蓝",font=small,fill='white')
 tile=np.zeros((h,w,3),np.uint8)
 for q in d['reference_quality']:
  lo=max(0,q['x0']-g['xa']);hi=min(w,q['x1']-g['xa']);tile[:,lo:hi]=[(110,110,110),(240,120,55),(45,190,110)][q['code']]
 delta=a['newdark'];signed=np.zeros((h,w,3),np.uint8);signed[:,:,0]=np.clip(delta,0,30)/30*255;signed[:,:,2]=np.clip(-delta,0,30)/30*255
 layers=[('当前平滑灰度 [0,255]',a['csm']),('按V1双点变换对齐的参考灰度 [0,255]',a['reference_aligned']),('当前暗谷 valley [0,40]（显示截断）',np.clip(a['valley']/40*255,0,255)),('带符号 newdark [-30,+30]（显示截断，负值保留）',signed),('参考质量：灰=不可用，橙=不可靠，绿=纹理可靠；绿不等于新增裂纹',tile)]
 for i,(label,v) in enumerate(layers):
  yy=80+i*210;draw.text((18,yy),label,font=font,fill='white');im=Image.fromarray(v.astype(np.uint8)).convert('RGB');im.thumbnail((1364,170));canvas.paste(im,(18,yy+32))
 rp=d['input']['reference_points'];cp=d['input']['current_points'];displacement=[[round(cp[i][j]-rp[i][j],6) for j in range(2)] for i in range(2)]
 draw.text((18,1140),'双点来源变换 dP1/dP2='+str(displacement)+'；上下局部NCC另列，未替换变换。',font=small,fill='white')
 counts={reason:sum(q['reason']==reason for q in d['reference_quality']) for reason in set(q['reason'] for q in d['reference_quality'])}
 draw.text((18,1172),'参考窗失效原因/计数：'+str(counts),font=small,fill='white')
 for i,r in enumerate(d['results']):
  counts=r['reference_status_counts'];text=' / '.join(label+'='+str(counts.get(key,0)) for key,label in [('REFERENCE_UNAVAILABLE','不可用'),('REFERENCE_UNRELIABLE','不可靠'),('EXISTING_DARK_OR_NO_INCREMENT','已有暗线/无增量'),('NEW_DARK_SUPPORTED','可靠新增')]);draw.text((18,1204+i*27),r['mode']+'  轨迹点计数：'+text,font=small,fill='white')
 target.parent.mkdir(parents=True,exist_ok=True);canvas.save(target,quality=92)

def main():
 assert (OUT/'validation_evaluation_complete.json').exists();gallery=OUT/'galleries';pages=[];n=0
 for group in DEV+VAL:
  records=[]
  for fid in range(1,COUNTS[group]+1):
   folder=OUT/'frames'/group/str(fid);d=unpack(folder/'result.json.gz');detail=None
   if (folder/'evidence.npz').exists():
    detail=f'reference_evidence/{group}_{fid}.jpg';evidence_card(folder,gallery/detail,f'{group}/{fid}');n+=1
   records.append(dict(frame=fid,roi=d['roi'],reference_points=d['input']['reference_points'],current_points=d['input']['current_points'],quality=d['reference_quality'],independent_audit=d['independent_material_audit'],modes=[dict(mode=r['mode'],state=r['output_state'],reference_status_counts=r['reference_status_counts']) for r in d['results']],detail=detail))
  page='''<meta charset="utf-8"><style>body{font:18px system-ui;margin:25px;background:#eef2f5}table{border-collapse:collapse}td,th{border:1px solid #aaa;padding:5px}img{max-width:100%}pre{white-space:pre-wrap}canvas{max-width:100%;height:50px}select{font:20px system-ui}</style><h1>GROUP 全帧参考质量审计</h1><p><a href="index.html">六组导航</a> · 灰=不可用 / 橙=不可靠 / 绿=纹理可靠。可靠窗还需逐像素正增量才能称 NEW_DARK_SUPPORTED，非增量不等于无裂纹。</p><label>帧 <select id="pick"></select></label><h2 id="heading"></h2><canvas id="strip" width="1200" height="50"></canvas><pre id="points"></pre><div id="detail"></div><img id="overlay"><h2>模式/状态</h2><pre id="modes"></pre><h2>上/下独立材料审计（未应用到检测）</h2><pre id="audit"></pre><h2>逐窗质量与原因</h2><table><thead><tr><th>原图x范围</th><th>质量码</th><th>质量分数</th><th>原因</th><th>上下材料窗实际度量</th></tr></thead><tbody id="quality"></tbody></table><script>const data=DATA;const group=GROUP_JSON;const pick=document.getElementById('pick');data.forEach((r,i)=>pick.add(new Option(r.frame,i)));function show(){const r=data[+pick.value];document.getElementById('heading').textContent=group+'/'+r.frame;document.getElementById('points').textContent=JSON.stringify({roi:r.roi,reference_points:r.reference_points,current_points:r.current_points},null,2);document.getElementById('modes').textContent=JSON.stringify(r.modes,null,2);document.getElementById('audit').textContent=JSON.stringify(r.independent_audit,null,2);document.getElementById('overlay').src=group+'/'+String(r.frame).padStart(6,'0')+'.jpg';const detail=document.getElementById('detail');detail.replaceChildren();if(r.detail){const a=document.createElement('a');a.href=r.detail;a.textContent='打开灰度/暗谷/正负新增/质量五层证据图';detail.append(a);}const tbody=document.getElementById('quality');tbody.replaceChildren();const ctx=document.getElementById('strip').getContext('2d');ctx.fillStyle='#777';ctx.fillRect(0,0,1200,50);r.quality.forEach(q=>{ctx.fillStyle=['#777','#f07837','#2dbe6e'][q.code];ctx.fillRect(1200*(q.x0-r.roi.xleft)/(r.roi.xr-r.roi.xleft),0,1200*(q.x1-q.x0)/(r.roi.xr-r.roi.xleft),50);const tr=document.createElement('tr');[q.x0+'–'+q.x1,q.code,q.quality,q.reason,JSON.stringify(q.sides)].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td)});tbody.append(tr);});}pick.onchange=show;show();</script>'''
  page=page.replace('GROUP_JSON',json.dumps(group)).replace('GROUP',group).replace('DATA',json.dumps(records,ensure_ascii=False,separators=(',',':')));(gallery/f'{group}_reference.html').write_text(page,encoding='utf8');pages.append(f'<li><a href="{group}_reference.html">{group} / {COUNTS[group]}帧</a></li>');print('REFERENCE GALLERY',group,flush=True)
 for case in read(OUT/'perturbation_plan.json')['cases']:
  if case['kind'] not in ['same_BMP_ABCD','predefined_sentinel']:continue
  folder=OUT/'sentinels'/case['name'];target=gallery/'reference_evidence'/f"{case['name']}.jpg";evidence_card(folder,target,case['name']);pages.append(f'<li><a href="reference_evidence/{case["name"]}.jpg">{case["name"]}证据</a></li>');n+=1
 (gallery/'reference_evidence.html').write_text('<meta charset="utf-8"><h1>参考证据与质量全帧查看器</h1><a href="index.html">六组导航</a><ul>'+''.join(pages)+'</ul>',encoding='utf8')
 index=gallery/'index.html';s=index.read_text(encoding='utf8');link='<p><a href="reference_evidence.html">全帧参考状态、质量、变换和失效原因；133张分层证据图</a></p>'
 if 'reference_evidence.html' not in s:index.write_text(s+link,encoding='utf8')
 write(OUT/'reference_gallery_complete.json',dict(full_frame_records=2647,evidence_cards=n,utc=utc()));print('REFERENCE EVIDENCE COMPLETE',n,flush=True)

if __name__=='__main__':main()
