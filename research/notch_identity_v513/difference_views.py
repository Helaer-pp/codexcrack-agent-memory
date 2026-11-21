"""Render frozen predictions with native fixed-frame correspondence and signed pixel differences."""
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor
from zipfile import ZipFile, ZIP_STORED

import cv2
import numpy as np
from PIL import Image, ImageDraw

from . import reference_views as v

DEST = v.OUT / 'difference_views'
WIDTH, HEIGHT = 2000, 764
LIMIT = 32
MISSING = (90, 90, 90)

from research.notch_identity_v34.difference_views import difference,rgb_delta

def build_card(rec, meta, raw, fixed, aligned, label, score, output_mode="full"):
    original, row = v.render(rec,meta,raw,fixed,aligned,label,score,include_windows=True,output_mode=output_mode)
    boxes = row.pop('windows')
    same = row['status']=='SAME'
    if same:
        l,t,r,b = rec['box']
        assert np.array_equal(raw, fixed[t:b,l:r])
    delta, origin = difference(raw,aligned,rec['box'][:2],boxes,row['shift'],same)
    if row['status']=='OUTSIDE':
        delta[:] = np.nan
    color = Image.fromarray(rgb_delta(delta))
    card = Image.new('RGB',(WIDTH,HEIGHT),'#f6f6f3')
    card.paste(original,(0,0))
    draw = ImageDraw.Draw(card)
    def text(x,y,words,size=20,fill='#18323e'):
        draw.text((x,y),words,font=v.font(size),fill=fill,anchor='lt')
    text(1498,66,'有符号差分  ·  固定参考减当前')
    for box,y in zip(boxes,[99,376]):
        x0,y0,w,h = box
        l,t = x0-origin[0],y0-origin[1]
        region = color.crop((l,t,l+w,t+h)).resize((v.W,v.H),Image.Resampling.NEAREST)
        card.paste(region,(1498,y))
    draw.rectangle((14,342,1450,373), fill='#f6f6f3')
    text(20,347,'尖端局部放大   ·   同行四图等倍率，差分与当前图逐像素对应',19)
    ramp = np.linspace(-LIMIT,LIMIT,280,dtype=np.float32)[None,:]
    card.paste(Image.fromarray(rgb_delta(ramp)).resize((280,13)),(1500,650))
    text(1498,626,'蓝 · 当前变亮',16,'#1b53a8')
    text(1683,626,'红 · 当前变暗',16,'#b6201b')
    text(1498,670,'−32',15);text(1635,670,'0',15);text(1760,670,'+32 灰度级',15)
    text(1498,712,'灰色为无对应像素，超过色阶按端点显示',17)
    row.update(diff_x=origin[0],diff_y=origin[1],diff_width=color.width,diff_height=color.height,
               valid_pixels=int(np.isfinite(delta).sum()))
    return card,color,row

def source_frames(group,only=None,mode='full',placement=None):
    placement=placement or ('bright' if group=='group_c' else 'original')
    prediction=v.OUT/(group+'.jsonl')
    assert v.sha(prediction)==v.read(v.OUT/(group+'_seal.json'))['predictions']
    scores={int(r['frame']):r for r in v.read_csv(v.OUT/(group+'_scores.csv')) if r['stage']=='S3' and r['mode']==mode and r['placement']==placement}
    roster={int(r['frame_id']):r for r in v.read_csv(v.SELECT) if r['dataset_id']==group}
    ref_sha=None
    with prediction.open(encoding='utf-8') as stream:
        for idx,line in enumerate(stream,1):
            if only is not None and idx not in only:continue
            rec=json.loads(line)
            rec['placement']=placement;rec['models']=rec['placements'][placement]
            cache=v.OLD/'evidence'/group/str(idx)
            meta=v.read(cache/'metadata.json')
            info=meta['input']
            assert (rec['group'],rec['frame'],rec['source_sha'])==(group,idx,info['image_sha'])
            assert v.sha(cache/'arrays.npz')==meta['arrays_sha']
            if ref_sha!=info['ref_sha']:
                fixed=v.current(info['reference'],info['ref_sha'])
                ref_sha=info['ref_sha']
            label=None
            if idx in scores:
                assert roster[idx]['sha256']==rec['source_sha']
                label=v.read(v.PACKAGE/roster[idx]['selected_json'])
            with np.load(cache/'arrays.npz') as z:
                l,t,r,b=rec['box']
                ox,oy=meta['evidence']['scene']['bounds'][:2]
                aligned=z['fixed__aligned'][t-oy:b-oy,l-ox:r-ox]
                yield build_card(rec,meta,z['raw'][t-oy:b-oy,l-ox:r-ox],fixed,aligned,label,scores.get(idx),mode)

def group_views(group):
    checkpoint=DEST/(group+'_views.json')
    if checkpoint.exists():
        record=json.loads(checkpoint.read_text(encoding='utf8'))
        if record['sha']==v.sha(v.OUT/(group+'.jsonl')):
            return record['rows']
    cv2.setNumThreads(1)
    folder=DEST/'frames'/group
    diffs=DEST/'differences'/group
    folder.mkdir(parents=True,exist_ok=True)
    diffs.mkdir(parents=True,exist_ok=True)
    rows=[]
    for card,delta,row in source_frames(group):
        stem=f"{row['frame']:04d}"
        card.save(folder/(stem+'.jpg'),quality=93,subsampling=0)
        delta.save(diffs/(stem+'.png'),compress_level=3)
        row.update(image=f'frames/{group}/{stem}.jpg',difference=f'differences/{group}/{stem}.png')
        rows.append(row)
    n=v.GROUPS[group]
    assert len(rows)==n
    video=DEST/(group+'.mp4')
    subprocess.run([str(v.ROOT/'third_party/ffmpeg/ffmpeg.exe'),'-v','error','-y','-framerate','10','-start_number','1','-i',str(folder/'%04d.jpg'),'-frames:v',str(n),'-c:v','libx264','-threads','3','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
    cap=cv2.VideoCapture(str(video))
    for _ in range(n):
        ok,frame=cap.read()
        assert ok and frame.shape[:2]==(HEIGHT,WIDTH)
    assert not cap.read()[0]
    cap.release()
    checkpoint.write_text(json.dumps(dict(sha=v.sha(v.OUT/(group+'.jsonl')),rows=rows),ensure_ascii=False),encoding='utf8')
    return rows

def main():
    for g in v.GROUPS:
        for sub in ('frames','differences'):
            (DEST/sub/g).mkdir(parents=True,exist_ok=True)
    with ProcessPoolExecutor(3) as pool:
        rows=sum(pool.map(group_views,v.GROUPS),[])
    assert len(rows)==sum(v.GROUPS.values())
    for r in rows:
        for key in ('image','difference'):
            with Image.open(DEST/r[key]) as im:
                im.verify()
    v.write_csv(DEST/'coordinates.csv',rows)
    failures=[r for r in rows if r['failure']]
    assert len(failures)==sum(r['state']=='VISIBLE' and (r['joint']!='True') for g in v.GROUPS for r in v.read_csv(v.OUT/(g+'_scores.csv')) if r['stage']=='S3' and r['mode']=='full' and r['placement']==('bright' if g=='group_c' else 'original'))
    with ZipFile(DEST/'failure_views.zip','w',ZIP_STORED) as z:
        for r in failures:
            for key in ('image','difference'):
                z.write(DEST/r[key],r[key])
    with ZipFile(DEST/'failure_views.zip') as z:assert z.testzip() is None
    page="""<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>V5.13 裂纹参考差分</title><style>body{font:17px/1.55 system-ui,sans-serif;max-width:1920px;margin:2vw;color:#18323e}button,select{font:inherit;margin:.2em}a{color:#006858}img{width:100%;height:auto}p{max-width:76em}</style><h1>裂纹与参考背景差分</h1><p>左侧方框标记预测尖端在固定参考原图中的对应位置。最右列显示对齐参考灰度减当前灰度，红为当前变暗，蓝为当前变亮，浅色接近零，深灰为无对应数据。所有帧共用 ±32 灰度级色阶。粗定位和上游映射只给出近似位置，邻接的红蓝条纹可能来自残余错位。</p><select id="group"><option value="group_c">验证组C</option><option value="three_point_bend">三点弯</option><option value="group_a">开发组A</option></select><select id="filter"><option value="all">全部帧</option><option value="failure">尖端或路径失败帧</option><option value="manual">人工标注帧</option></select><button id="prev">上一帧</button><select id="frame"></select><button id="next">下一帧</button>　<a id="video">整组视频</a>　<a id="diff">单独差分 PNG</a>　<a href="failure_views.zip">失败帧图包</a>　<a href="coordinates.csv">对应坐标</a>　<a href="../crack_lengths.csv">逐帧裂纹长度 CSV</a><p id="status"></p><a id="large"><img id="pic" alt="固定参考、当前灰度、识别叠图与有符号差分"></a><script>const rows=DATA,$=id=>document.getElementById(id);let group=[];function show(){$('prev').disabled=$('next').disabled=!group.length;$('diff').hidden=$('large').hidden=!group.length;if(!group.length){$('pic').removeAttribute('src');$('status').textContent='此组没有匹配帧';return}let i=$('frame').selectedIndex,r=group[i];$('pic').src=$('large').href=r.image;$('diff').href=r.difference;$('prev').disabled=i===0;$('next').disabled=i===group.length-1;$('status').textContent='参考图 '+r.reference+'　·　'+r.label+ (r.error?'　·　误差 '+Number(r.error).toFixed(2)+' px':'')+'　·　缺口根点至尖端弧长 '+(r.path_length_px==null?'—':Number(r.path_length_px).toFixed(2)+' px')+'　·　锚点中点投影 '+(r.projected_length_px==null?'—':Number(r.projected_length_px).toFixed(2)+' px');}function fill(initial){group=rows.filter(r=>r.group===$('group').value&&($('filter').value==='all'||($('filter').value==='failure'?r.failure:r.state!=='UNLABELED')));$('frame').replaceChildren(...group.map(r=>new Option('第 '+r.frame+' 帧',r.frame)));if(initial)$('frame').value='335';$('video').href=$('group').value+'.mp4';show()}$('prev').onclick=()=>{$('frame').selectedIndex--;show()};$('next').onclick=()=>{$('frame').selectedIndex++;show()};$('frame').onchange=show;$('group').onchange=$('filter').onchange=()=>fill(false);fill(true)</script></html>"""
    payload=[{**{k:r[k] for k in ('group','frame','image','difference','failure','state','reference','error','path_length_px','projected_length_px')},'label':v.MODE[r['status']]} for r in rows]
    (DEST/'index.html').write_text(page.replace('DATA',json.dumps(payload,ensure_ascii=False)),encoding='utf-8')
    print('Verified',len(rows),'comparisons and PNGs;',len(failures),'failures',flush=True)

if __name__=='__main__':main()
