"""Offline per-column audit of the registered gray-level difference on the selected trace."""
import cv2
import numpy as np
from . import terminal as t
from . import batch as b
from research.v3_labelme_comparison.compare import write_csv

def audit(p,reg,fixed,track,origin,ridge,old,new,net):
    gray=p.local[:,p.front:].astype(np.float32)
    x,y=track.T
    dx,dy=reg['shift']
    ref=cv2.warpAffine(fixed[p.sl],np.float32([[1,0,p.front+dx],[0,1,dy]]),(gray.shape[1],len(gray)),
        flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
    s=p.scale;threshold=max(3*p.noise,.035*p.span);radius=max(1,t.px(s,.0065))
    def prominence(im):
        pad=np.pad(im,((radius,radius),(0,0)),mode='edge')
        return np.maximum(0,im-np.maximum(pad[:-2*radius],pad[2*radius:]))
    diff=np.where(np.isfinite(ref),ref-gray,0.)
    depth=prominence(diff)
    strength=depth[y,x]/threshold
    contrast=depth[y,x]/np.maximum(diff[y,x],threshold)
    ref_dark=prominence(-np.where(np.isfinite(ref),ref,gray))
    q=cv2.blur(ref_dark,(2*t.px(s,.009)+1,1))
    q=cv2.dilate(q,np.ones((2*radius+1,1),np.uint8))
    q=cv2.dilate(q,np.ones((2*t.px(s,.038)+1,2*t.px(s,.009)+1),np.uint8))
    risk=q[y,x]/np.maximum(threshold,depth[y,x])
    rows=[]
    for j,(cx,cy) in enumerate(track):
        rows.append(dict(x=int(cx+origin[0]),y=int(cy+origin[1]),delta=float(diff[cy,cx]),T=threshold,
            A=float(strength[j]),Cd=float(contrast[j]),Q=float(risk[j]),fine=bool(ridge[cx,cy]),
            old=float(old[cx,cy]),new=float(new[cx,cy]),net_after_turn_cost=float(net[j]),combined_support=bool(ridge[cx,cy] or net[j]>.05),uplift=float(new[cx,cy]-old[cx,cy])))
    write_csv(b.OUT/'frame215_bridge_columns.csv',rows)
    gates=[diff[y,x]>1.15*threshold,strength>1,contrast>.27,risk<.55]
    return [len(rows),*[int(a.sum()) for a in gates],int(np.logical_and.reduce(gates).sum()),int(ridge[x,y].sum()),int(np.sum(new[x,y]>old[x,y]+1e-5))]
