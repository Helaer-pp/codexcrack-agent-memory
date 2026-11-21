"""Offline transverse gray profiles for the named overreach frames on sealed paths."""
import ast
import json
import numpy as np
from research.v3_labelme_comparison.compare import write_csv
from . import batch as b

def measure(models,scores):
    result=[]
    for group,place,frame in sorted(scores):
        targets={'group_a':(398,),'three_point_bend':(335,413,435,503),'group_c':(510,)}
        if frame not in targets[group]:continue
        key=group,place,frame
        m=models[key,'S3']
        path=np.rint(m['points']).astype(int)
        if not len(path):continue
        gt=ast.literal_eval(scores[key]['gt'])
        meta=b.read(b.OLD/'evidence'/group/str(frame)/'metadata.json')['input']
        gray=b.old.current(meta['current'],meta['image_sha'])
        x,y=path.T
        def sample(offset):return gray[np.clip(y+offset,0,len(gray)-1),x].astype(float)
        center=np.minimum(sample(0),.5*(sample(-1)+sample(1)))
        def shoulders(radii):return np.minimum(np.mean([sample(-r) for r in radii],0),np.mean([sample(r) for r in radii],0))-center
        narrow,broad=shoulders((1,2)),shoulders((4,5,6))
        for lab,mask in [('proximal_12',(x>=gt[0]-12)&(x<=gt[0])),('beyond_gt',x>gt[0])]:
            result.append(dict(group=group,placement=place,frame=frame,region=lab,columns=int(mask.sum()),
                               narrow_median=float(np.median(narrow[mask])) if mask.any() else None,
                               broad_median=float(np.median(broad[mask])) if mask.any() else None))
    write_csv(b.OUT/'tail_profiles.csv',result)
    return result
