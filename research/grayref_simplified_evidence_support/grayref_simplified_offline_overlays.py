"""Clearly separate OFFLINE_LABEL_OVERLAY views; never changes GT-free evidence pages."""
import argparse,zipfile,json,hashlib,io,html
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from grayref_simplified_evidence_v0.common import *

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();run=Path(a.run)
    assert (run/'completion_seal.json').exists()
    for role in ['development','exposed_regression']:
        for rel,h in get(run/f'inference_frozen_{role}.json')['files'].items():assert sha(run/rel)==h
    metrics={(r['group'],r['frame_id']):r for r in rows(run/'offline_evaluation.csv') if r['mode']=='C_FUSION_RAW'}
    manifest={(r['group'],r['frame_id']):r for r in safe_manifest(run/'input_manifest.csv')};records=[];out=run/'offline_label_overlays';out.mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
    with zipfile.ZipFile(ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip') as z:
        for row in rows(ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv'):
            group=row['dataset_id'];fid=row['frame_id']
            if group not in GROUPS:continue
            assert row['sha256']==manifest[group,fid]['image_sha']
            b=z.read(row['selected_json']);label=json.loads(b);d=run/'galleries'/group/fid;r=readgz(d/'result.json.gz');g=r['roi'];result=next(v for v in r['results'] if v['mode']=='C_FUSION_RAW');metric=metrics[group,fid]
            with np.load(d/'roi_gray.npz') as q:raw=q['raw']
            image=Image.fromarray(raw).convert('RGB');draw=ImageDraw.Draw(image)
            def xy(p):return p[0]-g['xa'],p[1]-g['ya']
            for shape in label['shapes']:
                if shape['label']=='crack_path' and len(shape['points'])>1:draw.line([xy(p) for p in shape['points']],fill='#ff1aa7',width=3)
                if shape['label']=='crack_tip':
                    x,y=xy(shape['points'][0]);draw.line([x-7,y,x+7,y],fill='#ff1aa7',width=2);draw.line([x,y-7,x,y+7],fill='#ff1aa7',width=2)
            if result['paths']:
                trace=result['paths'][0]['selected_trace']
                for aa,bb in zip(trace,trace[1:]):draw.line([xy(aa),xy(bb)],fill='#00dd55' if aa[2] and bb[2] else '#ff9900',width=1)
            if result['tip']:
                x,y=xy(result['tip']);draw.ellipse([x-6,y-6,x+6,y+6],outline='#00bfff',width=2)
            draw.rectangle([g['xleft']-g['xa'],g['upper']-g['ya'],g['xr']-g['xa'],g['lower']-g['ya']],outline='#39829c',width=1)
            canvas=Image.new('RGB',(max(1200,image.width),image.height+110),'#112431');canvas.paste(image,(0,110));draw=ImageDraw.Draw(canvas)
            draw.text((10,6),f"OFFLINE_LABEL_OVERLAY | {group}/{fid} | {metric['visibility']} | {result['output_state']}",font=font,fill='white')
            draw.text((10,34),'粉色：人工可见路径/尖端；绿色：算法观测段；橙色：假设桥接；蓝圈：公开尖端。标签仅用于事后对比。',font=small,fill='white')
            draw.text((10,60),f"公开端点误差(px): {metric['error'] or 'N/A'}  路径10px覆盖/精度: {metric['coverage10']}/{metric['precision10']}  阶段: {metric['stage']}",font=small,fill='white')
            draw.text((10,85),'保持原始冻结ROI裁剪；ROI外标注不改变推理或裁剪，仍计入全部可见分母。未知标签不是阴性。',font=small,fill='#c2d8e5')
            path=out/group/(fid+'.png');buffer=io.BytesIO();canvas.save(buffer,format='PNG');write_bytes(path,buffer.getvalue())
            with Image.open(path) as check:check.load();assert check.size==canvas.size
            records.append(dict(group=group,frame_id=fid,visibility=metric['visibility'],state=result['output_state'],error=metric['error'],png=str(path.relative_to(out)).replace('\\','/'),png_sha=sha(path),label_member=row['selected_json'],label_sha=hashlib.sha256(b).hexdigest(),default_gallery_unchanged=True))
    assert len(records)==120 and sum(r['visibility']=='VISIBLE' for r in records)==111
    body='<meta charset="utf-8"><title>OFFLINE_LABEL_OVERLAY</title><style>body{font:18px sans-serif;background:#112431;color:#eee;margin:24px}a{color:#81d8ff}img{max-width:100%}details{margin:16px}</style><h1>OFFLINE_LABEL_OVERLAY：仅事后人工对比</h1><p>120张已标注图，其中111可见、9未知；不是全序列阴性真值。默认2647帧图册完全不使用GT。</p><a href="../galleries/index.html">返回2647帧无GT证据图册</a>'
    for group in ['group_c','three_point_bend','group_a','ct2','group_h','ct3']:
        body+='<h2>'+group+'</h2>'
        for r in records:
            if r['group']==group:body+=f'<details><summary>{r["frame_id"]} | {r["visibility"]} | {r["state"]} | error={r["error"] or "N/A"}</summary><a href="{r["png"]}"><img loading="lazy" src="{r["png"]}"></a></details>'
    write_bytes(out/'index.html',body.encode('utf-8'));csvwrite(out/'manifest.csv',records);put(out/'integrity.json',dict(script_sha=sha(__file__),overlays=120,visible=111,unknown=9,GT_free_default_gallery_unmodified=True,images=records));print('Offline label comparisons: 120; visible111 / unknown9')

if __name__=='__main__':main()
