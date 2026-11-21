"""Transport the fixed specimen envelope using tracked motion; test illumination at each anchor."""
import cv2
import numpy as np
from research.notch_identity_v58_bright.region import band, paired_points


def geometry(raw,origin,fixed,meta,settings,delta=None):
    old=np.asarray(meta['current_points'],float)
    previous=np.asarray(meta['fixed_points'],float)
    motion=old-previous
    source=np.array(settings['reference_box'],int)
    dx=round(float(motion[:,0].mean()))
    moved=source+[dx,round(motion[0,1]),dx,round(motion[1,1])]
    # The screenshot defines the two exterior shadow edges. A growing internal
    # dark line must never redefine those edges or cut the search into halves.
    l0,t0,r0,b0=settings['fixed_band']
    current=[l0+dx,t0+round(motion[0,1]),r0+dx,b0+round(motion[1,1])]
    ox,oy=origin
    h,w=raw.shape
    current=[max(ox,current[0]),max(oy,current[1]),min(ox+w,current[2]),min(oy+h,current[3])]
    # Use the same intensity estimator as the comparator for the two point
    # patches. The current frame's bright row runs do not define its envelope.
    _,cut=band(raw,origin,moved)
    ref_box=settings['fixed_band'];floor=settings['fixed_floor']
    l,t=np.maximum(current[:2],ref_box[:2])
    r,b=np.minimum(current[2:],ref_box[2:])
    if r-l<50 or b-t<32:return None
    box=list(map(int,(l,t,r,b)))
    nominal=np.asarray(settings['reference_virtual_points'],float)
    requested=nominal if delta is None else nominal+delta
    rf,cp=paired_points(fixed,raw,origin,box,[floor,cut],requested,motion)
    if rf is None:return None
    return dict(box=box,ref_band=ref_box,cur_band=current,floors=[floor,cut],
                original_ref=previous.tolist(),original_cur=old.tolist(),requested_ref=requested.tolist(),
                ref_points=rf.tolist(),cur_points=cp.tolist())
