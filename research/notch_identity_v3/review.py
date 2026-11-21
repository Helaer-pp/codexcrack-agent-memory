"""Render only scored, sealed results with their manual comparison, after regression."""
import csv
import json
import zipfile
from pathlib import Path
import cv2
import numpy as np
from .run import RUN,OLD,ROOT,PREVIOUS,read,sha,save
from .report import rows,stream,write_csv


def render():
    out=RUN/'visible_review'
    out.mkdir(exist_ok=True)
    entries=rows(RUN/'visible_changes.csv')
    visible={(r['group'],int(r['frame'])):r for r in entries if r['stage']=='s3t' and r['mode']=='full'}
    preds={}
    for stage,directory in [('r02',PREVIOUS),('s1',RUN/'s1'),('s2',RUN/'s2'),('s3',RUN/'s3'),('s3t',RUN/'s3t')]:
        for split in ('dev','locked'):
            for r in stream(directory/(split+'.jsonl')):
                key=(r['group'],r['frame'])
                if key in visible:
                    preds[stage,key]=r['full']
    source=ROOT/'output/runs/uctt_r05f_20261111_r01/selected_frames.csv'
    manifest={(r['dataset_id'],int(r['frame_id'])):r for r in rows(source)}
    evidence=[]; html=[]
    with zipfile.ZipFile(ROOT/'output/runs/r05_annotation_validation_20261111_r01/human_annotations_six_groups_snapshot.zip') as z:
        for key,row in visible.items():
            g,f=key
            base=preds['r02',key]; final=preds['s3t',key]
            item=manifest[key]
            label=json.loads(z.read(item['selected_json']))
            folder=OLD/'evidence'/g/str(f)
            scene=read(folder/'metadata.json')
            assert scene['input']['image_sha']==item['sha256']
            origin=np.array(scene['evidence']['scene']['bounds'][:2])
            with np.load(folder/'arrays.npz') as a:
                raw=a['raw']
            paths=[np.array(s['points']) for s in label['shapes'] if s['label']=='crack_path']
            tip=next(s['points'][0] for s in label['shapes'] if s['label']=='crack_tip')
            cloud=np.vstack(paths+[np.array(base['points']),np.array(final['points']),np.array(tip).reshape(1,2)])-origin
            lo=np.maximum(0,np.floor(cloud.min(0)-20).astype(int))
            hi=np.minimum(raw.shape[::-1],np.ceil(cloud.max(0)+21).astype(int))
            crop=raw[lo[1]:hi[1],lo[0]:hi[0]]
            color=cv2.cvtColor(crop,cv2.COLOR_GRAY2BGR)
            def coords(points):
                return np.rint(np.asarray(points)-origin-lo).astype(np.int32)
            def panel(result,title,use_label):
                image=color.copy()
                if use_label:
                    for p in paths:
                        cv2.polylines(image,[coords(p)],False,(250,200,15),1)
                    cv2.drawMarker(image,tuple(coords(tip)),(250,200,15),cv2.MARKER_CROSS,9,1)
                if result:
                    for a,b in zip(result['points'],result['points'][1:]):
                        if b[0]-a[0]==1:
                            cv2.line(image,tuple(coords(a)),tuple(coords(b)),(40,220,60),1)
                    if result['tip']:
                        cv2.circle(image,tuple(coords(result['tip'])),5,(20,35,250),1)
                scale=min(590/image.shape[1],216/image.shape[0])
                scaled=cv2.resize(image,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
                card=np.full((256,608,3),28,np.uint8)
                card[34:34+scaled.shape[0],8:8+scaled.shape[1]]=scaled
                cv2.putText(card,title,(9,23),cv2.FONT_HERSHEY_SIMPLEX,.54,(240,240,240),1,cv2.LINE_AA)
                return card
            image=np.vstack((np.hstack([panel(None,'RAW',False),panel(None,'Manual path and tip (+)',True)]),
                             np.hstack([panel(base,'r02 + manual',True),panel(final,'V3 + manual',True)])))
            name=f'{g}_{f}.png'
            assert cv2.imwrite(str(out/name),image) and cv2.imread(str(out/name)).shape==image.shape
            html.append(f'<a href="{name}">{g} · {f}</a>')
            rec=dict(group=g,frame=f,gt_tip=tip,old_error=row['error_before'],final_error=row['error_after'])
            for stage in ('r02','s1','s2','s3','s3t'):
                r=preds[stage,key]
                rec[stage+'_root']=r['root']
                rec[stage+'_tip']=r['tip']
                rec[stage+'_dx']=r['tip'][0]-tip[0] if r['tip'] else None
                rec[stage+'_coverage']=next(v['coverage_after'] if stage!='r02' else v['coverage_before'] for v in entries
                    if v['group']==g and int(v['frame'])==f and v['mode']=='full' and v['stage']==('s1' if stage=='r02' else stage))
            rec.update(final_untrimmed_x=(final['diagnostics'].get('terminal') or {}).get('untrimmed_x'),review='visible_review/'+name)
            evidence.append(rec)
    assert len(evidence)==54
    write_csv('visible_stage_coordinates.csv',evidence)
    (out/'index.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>人工标注对照</title><style>body{font:18px system-ui;margin:2em}a{display:inline-block;margin:.6em}</style><h1>54 张可见标注对照</h1><p>青色为人工路径及尖端，绿色为实测路径，红圈为检测尖端。</p>'+''.join(html)+'</html>',encoding='utf-8')


if __name__=='__main__':
    render()

