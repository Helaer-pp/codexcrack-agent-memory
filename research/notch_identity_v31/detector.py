"""Origin segmentation and photometric normalization in the current exposure."""
import numpy as np
from research.notch_identity_v3 import detector as legacy
from research.notch_identity_v3.detector import px


def exposure(raw,hint,scale):
    x,y=np.rint(hint).astype(int)
    r=px(scale,.23)
    patch=raw[max(0,y-r):min(len(raw),y+r+1),max(0,x-2*r):min(raw.shape[1],x+r+1)]
    if not patch.size:
        return 0.,1.
    low,mid=np.percentile(patch,[3,70])
    return float(low),max(float(mid-low),np.finfo(np.float32).eps)


def locate_root(raw,hint,scale,adaptive):
    low,contrast=exposure(raw,hint,scale)
    if adaptive:
        # The old component extractor receives only a binary geometry mask.
        geom=np.where(raw<low+.28*contrast,0,255).astype(np.uint8)
    else:
        geom=raw
    return legacy.locate_root(geom,hint,scale),low,contrast

