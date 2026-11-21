"""Validate all cards and prediction rows, encode videos, and index each frame."""
import json,subprocess
from pathlib import Path
import cv2
from .batch import ROOT,OUT,GROUPS,read,save,sha
from research.v3_labelme_comparison.infer import read_csv
from research.v3_labelme_comparison.compare import write_csv

def deliver():
    frames=[];videos=[]
    for g,n in GROUPS.items():
        p=OUT/(g+'.jsonl')
        assert sha(p)==read(OUT/(g+'_seal.json'))['predictions']
        scores={int(r['frame']):r for r in read_csv(OUT/(g+'_scores.csv')) if r['mode']=='full' and r['stage']=='v3_2'}
        for i,line in enumerate(p.open(),1):
            rec=json.loads(line);assert rec['group']==g and rec['frame']==i
            m=rec['models']['v3_2'];a=m['full'];s=scores.get(i,{})
            jpg=f'frames/{g}/{i}.jpg';assert sha(OUT/jpg)==rec['card_sha'] and cv2.imread(str(OUT/jpg)).shape==(490,1280,3)
            d=a['diagnostics'];sel=d.get('selected');c=d['candidates'][sel] if sel is not None else {}
            reason=s.get('failure') or (a['status'] if a['tip'] is None else 'UNLABELED')
            png=f'labels/{g}/{i}.png' if s else ''
            if png:assert (OUT/png).is_file()
            frames.append(dict(group=g,frame=i,status=a['status'],root=a['root'],tip=a['tip'],points=len(a['points']),
                               raw_only_tip=m['raw_only']['tip'],seconds=m['seconds'],stop=c.get('trace',{}).get('stop'),
                               gate=c.get('trace',{}).get('gate'),reason=reason,error_px=s.get('error_px',''),
                               coverage=s.get('coverage',''),precision=s.get('precision',''),image=jpg,manual_comparison=png))
        assert i==n
        mov=OUT/(g+'.mp4')
        if not mov.exists():
            subprocess.run([str(ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-n','-framerate','10',
                '-start_number','1','-i',str(OUT/'frames'/g/'%d.jpg'),'-frames:v',str(n),'-c:v','libx264',
                '-pix_fmt','yuv420p','-crf','19','-threads','3','-movflags','+faststart',str(mov)],check=True)
        cap=cv2.VideoCapture(str(mov));count=0
        while True:
            ok,img=cap.read()
            if not ok:break
            assert img.shape[:2]==(490,1280);count+=1
        cap.release();assert count==n
        videos.append(dict(group=g,frames=count,sha256=sha(mov)))
    write_csv(OUT/'frames.csv',frames)
    data=[{k:r[k] for k in ('group','frame','status','reason','error_px','coverage','image','manual_comparison')} for r in frames]
    page="""<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V3.2 逐帧复查</title><style>body{background:#191c20;color:white;font:17px system-ui;margin:2vw}a{color:#9df}button,input,select{font:inherit;margin:.3em}img{max-width:100%;display:block;margin-top:.8em}</style><h1>V3.2 裂纹识别逐帧对比</h1><select id="g"><option value="group_a">开发组A</option><option value="three_point_bend">三点弯</option><option value="group_c">验证组C</option></select><select id="f"><option value="all">全序列</option><option value="ann">人工标注帧</option><option value="miss">可见标注未联合命中</option></select><button id="prev">上一帧</button><select id="n"></select><button id="next">下一帧</button> <a id="v">整组视频</a> <a href="frames.csv">逐帧表格</a><p id="s"></p><p>全序列图左为原灰度，右为算法路径与尖端。有人工标注时，下方另附同坐标叠图，青色十字为人工尖端，绿色为算法路径，红圈为算法尖端，黄色为不确定区。</p><img id="p" alt="原图和识别结果"><img id="m" alt="人工标注对比"><script>const d=DATA;const $=id=>document.getElementById(id);let a=[];function show(){const i=$('n').selectedIndex,r=a[i];$('prev').disabled=i<=0;$('next').disabled=i<0||i>=a.length-1;for(const id of ['p','m'])$(id).style.display='none';if(!r){$('s').textContent='无匹配帧';return}$('p').src=r.image;$('p').style.display='block';if(r.manual_comparison){$('m').src=r.manual_comparison;$('m').style.display='block'}$('s').textContent=r.status+'　'+r.reason+(r.error_px?'　尖端误差 '+Number(r.error_px).toFixed(2)+' px，覆盖 '+Number(r.coverage).toFixed(2):'')}function fill(){const g=$('g').value,f=$('f').value;a=d.filter(r=>r.group===g&&(f==='all'||r.manual_comparison&&(f==='ann'||!['JOINT_HIT','UNCERTAIN_LABEL'].includes(r.reason))));$('n').replaceChildren(...a.map(r=>new Option('第 '+r.frame+' 帧')));$('v').href=g+'.mp4';show()}$('prev').onclick=()=>{$('n').selectedIndex--;show()};$('next').onclick=()=>{$('n').selectedIndex++;show()};$('f').onchange=$('g').onchange=fill;$('n').onchange=show;fill()</script></html>"""
    (OUT/'index.html').write_text(page.replace('DATA',json.dumps(data)),encoding='utf-8')
    save(OUT/'delivery_check.json',dict(cards=len(frames),manual=sum(bool(r['manual_comparison']) for r in frames),videos=videos))

if __name__=='__main__':deliver()
