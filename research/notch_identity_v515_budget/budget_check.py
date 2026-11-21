"""Exercise the adaptive prefix both before and beyond its first right boundary."""
import numpy as np
import cv2
from . import probes,terminal,batch as b
from .run import frozen

def main():
    frozen()
    cv2.setNumThreads(1)
    raw,fixed,hint,scale,gt=probes.images(('weak_material_bridge',0,1.,1.,1,17))
    raw=np.pad(raw,((0,0),(0,4200)),mode='edge')
    fixed=np.pad(fixed,((0,0),(0,4200)),mode='edge')
    output=[]
    for long in (False,True):
        cur=raw.copy()
        if long:
            y=np.arange(len(cur))[:,None]
            region=fixed[:,180:3600].astype(float)
            cur[:,180:3600]=np.clip(region-60*np.exp(-.5*((y-87)/1.05)**2),0,255).astype('uint8')
        for stage in ('S1','S2'):
            prep=terminal.prepare(cur,hint,scale,stage,reference=fixed)
            pred=terminal.predict(prep,None,fixed.astype('float32'))
            d=pred['diagnostics']['dual']
            output.append(dict(long=long,stage=stage,tip=pred['tip'],visits=d['field_visits'],right_active=d['right_active']))
    b.save(b.OUT/'budget_synthetic.json',output)
    short,short_fast,extended,extended_fast=output
    assert short_fast['visits'][0]<=180000 and len(short_fast['visits'])==1
    assert len(extended_fast['visits'])>1 and extended_fast['tip'][0]>3500
    assert abs(extended['tip'][0]-extended_fast['tip'][0])<=1
    print(output,flush=True)
if __name__=='__main__':main()
