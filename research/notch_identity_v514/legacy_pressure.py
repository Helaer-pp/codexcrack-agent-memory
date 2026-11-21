"""Measure the previous Python detector on identical sensor frames and corrected points."""
import ast
from time import perf_counter
import numpy as np
import cv2
from research.notch_identity_v513 import batch as v513
from research.unified_crack_tip_60q.features import scene_geometry,register_reference,CONFIG
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b


def main():
    results=[];cv2.setNumThreads(1)
    for group,i in [('group_a',398),('three_point_bend',248),('group_c',335)]:
        assert b.read(b.ROOT/'config/dataset_usage_policy.json')['groups'][group] in ('DEVELOPMENT','VALIDATION_ONLY')
        pressure=b.read_csv(b.OUT/(group+'_stress.csv'))
        cases=[r for r in pressure if r['stage']=='S1' and r['repeat']=='0' and r['direction']=='left' and r['frame']==str(i)]
        assert len(cases)==4
        meta=b.read(b.OLD/'evidence'/group/str(i)/'metadata.json')
        info=meta['input']
        current=b.old.current(info['current'],info['image_sha']);fixed=b.old.read_fixed(info['reference'],info['ref_sha'])
        l,t,r,bt=meta['evidence']['scene']['bounds']
        mask=b.geometry(current[t:bt,l:r],[l,t],fixed,meta,b.read(b.POLICY)) if group=='group_c' else None
        for rep in range(4):
            for rec in cases[rep:]+cases[:rep]:
                cp,rp=np.array(ast.literal_eval(rec['actual_current'])),np.array(ast.literal_eval(rec['actual']))
                start=perf_counter()
                scene=scene_geometry(current,cp,fixed,rp,None,CONFIG)
                if mask:scene['bounds']=mask['box']
                x,y,right,bottom=scene['bounds']
                ref,_=register_reference(fixed,current,rp,cp,scene,CONFIG)
                before=perf_counter()
                m,dt=v513.run_mode(current[y:bottom,x:right],fixed[y:bottom,x:right],cp,rp,np.array([x,y]),'S3','full',aligned=ref['aligned'])
                results.append(dict(group=group,frame=i,repeat=rep,delta=rec['delta'],actual_dx=rec['actual_dx'],
                    pixels=ref['aligned'].size,total_ms=(perf_counter()-start)*1000,upstream_ms=(before-start)*1000,
                    detector_ms=1000*dt,tip=m['tip']))
    write_csv(b.OUT/'v513_left.csv',results)
