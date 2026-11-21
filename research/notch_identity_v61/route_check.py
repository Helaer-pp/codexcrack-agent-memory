"""Offline factorial check of scale and quiet-floor on identical native vertices."""
import json
import numpy as np
from . import batch as b, geometry, inputs
from research.notch_identity_v59 import geometry as locator
from research.notch_identity_v60 import geometry as old_geom
from research.v3_labelme_comparison.compare import write_csv


def main():
    rows=[]
    for g,frame in [('group_c',7),('three_point_bend',1),('group_h',78)]:
        path=b.OUT/(g+'.jsonl')
        assert b.sha(path)==b.read(b.OUT/(g+'_seal.json'))['predictions']
        with path.open(encoding='utf8') as stream:
            rec=next(json.loads(s) for i,s in enumerate(stream,1) if i==frame)
        inp=inputs.metadata(g,frame)['input']
        x,y,r,bot=rec['box'];off=np.array([x,y])
        ref=b.old.read_fixed(inp['reference'],inp['ref_sha'])[y:bot,x:r]
        cur=b.old.current(inp['current'],inp['image_sha'])[y:bot,x:r]
        for pl,mm in rec['mappings'].items():
            cp,rp=[np.mean(mm['S2'][k],axis=0)-off for k in ('cur','ref')]
            t,z=locator.material(cur,ref,cp,rp,b.SCALE)
            a,f=cur[t:z],ref[t:z]
            tip=geometry.apex_with_center_fallback(f,rp-[0,t],b.SCALE,locator.apex)
            now=geometry.apex_with_center_fallback(a,np.array(tip)+cp-rp,b.SCALE,locator.apex)
            for geom in (old_geom,geometry):
                _,scale=geom.measure(f,tip)
                for floor in (old_geom,geometry):
                    quiet,delta,cut=floor.quiet_mouth(a,f,now,tip,scale)
                    rows.append(dict(group=g,placement=pl,frame=frame,scale=scale,
                              floor_version='6.1' if floor==geometry else '6.0',residual=delta,floor=cut,quiet=quiet))
    write_csv(b.OUT/'scale_floor.csv',rows)

if __name__=='__main__':main()
