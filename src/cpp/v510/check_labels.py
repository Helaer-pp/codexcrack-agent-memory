"""Post-freeze score of DLL paths on the 54 visible annotated frames (60 selected frames)."""
import csv
import ctypes as C
import json
import numpy as np
from research.notch_identity_v510.batch import SELECT, read_csv
from research.v3_labelme_comparison.compare import evaluate, PACKAGE
from .parity import BUILD, RESULTS, ROOT, OLD, OUT, POLICY, libs, read, old, image, pair, Point, Config, Box, Result, sha


def main():
    dll=libs()
    dll.Crack510SetNumThreads(4)
    assert sha(BUILD/'CrackV510.dll')==read(RESULTS/'freeze.json')['dll_sha256']
    roles=read(ROOT/'config/dataset_usage_policy.json')['groups']
    selected=read_csv(SELECT)
    all_scores=[]
    for group in ('group_a','three_point_bend','group_c'):
        assert roles[group] in ('DEVELOPMENT','VALIDATION_ONLY')
        inputs=sorted((r for r in selected if r['dataset_id']==group),key=lambda r:int(r['frame_id']))
        full_replay=read_csv(RESULTS/(group+'_all.csv'))
        for place in (['original','bright'] if group=='group_c' else ['original']):
            cfg=Config(size=C.sizeof(Config))
            if group=='group_c':
                w=read(POLICY)
                cfg.material_mode=1+(place=='bright')
                cfg.request,cfg.band=Box(*w['reference_box']),Box(*w['fixed_band'])
                cfg.floor,cfg.virtual=w['fixed_floor'],pair(w['reference_virtual_points'])
            h=C.c_void_p()
            pred=[]
            try:
                for row in inputs:
                    i=int(row['frame_id'])
                    meta=read(OLD/'evidence'/group/str(i)/'metadata.json')
                    info=meta['input']
                    assert row['sha256']==info['image_sha']
                    if not h.value:
                        ref=old.current(info['reference'],info['ref_sha'])
                        assert dll.Crack510Create(C.byref(image(ref)),pair(meta['fixed_points']),C.byref(cfg),C.byref(h))==0
                    cur=old.current(info['current'],info['image_sha'])
                    result=Result(size=C.sizeof(Result))
                    assert dll.Crack510Process(h,C.byref(image(cur)),pair(meta['current_points']),C.byref(result))==0
                    pts=(Point*result.count)()
                    assert dll.Crack510CopyPath(h,pts,result.count)==result.count
                    path=[[v.x,v.y] for v in pts]
                    tip=path[-1] if path else None
                    replay=next(r for r in full_replay if int(r['frame'])==i and r['place']==place and r['mode']=='full')
                    assert tip==(json.loads(replay['actual']) if replay['actual'] else None)
                    pred.append(dict(status=['NO_NOTCH_BODY','no_tip','VALID'][result.status],points=path,tip=tip))
            finally:
                dll.Crack510Destroy(h)
            for row,m in zip(inputs,pred):
                shapes=read(PACKAGE/row['selected_json'])['shapes']
                gt=next((s['points'][0] for s in shapes if s['label']=='crack_tip'),None)
                paths=[np.asarray(s['points']) for s in shapes if s['label']=='crack_path']
                all_scores.append(dict(group=group,place=place,frame=row['frame_id'],**evaluate(m,paths,gt)))
    with (RESULTS/'native_full_label_scores.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,all_scores[0]);w.writeheader();w.writerows(all_scores)
    for g,p in dict.fromkeys((a['group'],a['place']) for a in all_scores):
        print(g,p,sum(bool(a['joint']) for a in all_scores if a['group']==g and a['place']==p))

if __name__=='__main__':main()
