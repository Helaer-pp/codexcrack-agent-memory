"""Area-triggered native-pixel corridor and local transverse vertex refinement."""
from dataclasses import replace
import numpy as np

def narrow(p,stage):
    if stage=='S1' or p.local.size<=250000:return p
    center=round(float(np.median(np.asarray(p.starts)[:,1])))
    half=max(8,round(.085*p.scale))
    low=max(0,min(center-half,min(y for x,y in p.starts)))
    high=min(len(p.local),max(center+half+1,max(y for x,y in p.starts)+1))
    ys,xs=p.sl
    return replace(p,local=p.local[low:high],sl=(slice(ys.start+low,ys.start+high),xs),
                   starts=[(x,y-low) for x,y in p.starts],origin=(p.origin[0],p.origin[1]+low))

def refine(model,p,fixed):
    if model['tip'] is None:return
    x,y=model['tip']
    reg=model['diagnostics']['dual'].get('registration') or {}
    dx,dy=reg.get('shift') or (0,0)
    # Refine transverse position within the terminal column. Keep longitudinal DP support.
    if not (1<=y<len(p.raw)-1 and 1<=y+dy<len(fixed)-1 and 0<=x+dx<fixed.shape[1]):return
    gray=p.raw[y-1:y+2,x].astype(float)
    ref=fixed[y+dy-1:y+dy+2,x+dx].astype(float)
    v=-gray
    if np.isfinite(ref).all():v+=.25*(ref-gray)
    curvature=2*v[1]-v[0]-v[2]
    if min(v[1]-v[0],v[1]-v[2])<=0 or curvature<p.noise:return
    tip=[x,y+float(np.clip(.5*(v[2]-v[0])/curvature,-.5,.5))]
    model['tip']=model['points'][-1]=tip
    d=model['diagnostics'];d['dual']['peak']=tip
    d['dual']['coarse_tip']=[x,y]
    d['candidates'][d['selected']]['tip']=tip
    for branch in d['dual']['branches']:
        if d['dual']['pick']=='BRANCH_'+str(branch['id']):branch['tip']=tip
