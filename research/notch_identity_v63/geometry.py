"""X-independent row profile and two-pass measurement of internal reference notches."""
import numpy as np
from research.notch_identity_v62.geometry import (
    PhysicalScene, component_tip, locate_current_notch, measure, quiet_mouth,
)


def material(raw, fixed, current_hint, reference_hint, scale):
    height, width = fixed.shape
    # Anchor the sample grid at the right image boundary, away from the left notch.
    # A synchronized left shift expands this crop at its left edge.
    profile = np.median(fixed[:, width-1::-7], axis=1)
    sample = fixed[::3, width-1::-7]
    low, high = np.percentile(sample, (3, 85))
    if high <= low:
        low = float(sample.min())
    illuminated = profile > low + .43*(high-low)
    edges = np.flatnonzero(np.diff(np.r_[False, illuminated, False]))
    strips = [(a,b) for a,b in zip(edges[::2],edges[1::2]) if b-a>=16]
    if not strips:
        return None
    y = reference_hint[1]
    a,b = min(strips,key=lambda pair:max(pair[0]-y,y-pair[1]+1,0))
    dy = round(current_hint[1]-y)
    top,bottom = max(0,a,a+dy),min(height,b,b+dy)
    return (int(top),int(bottom)) if bottom-top>=12 else None


def locate_reference_notch(ref_band, ref_hint, scale, edge_apex):
    edge = edge_apex(ref_band,ref_hint,scale)
    if edge is not None:
        return edge,'edge'
    coarse = component_tip(ref_band,ref_hint,0,ref_band.shape[1])
    if coarse is None:
        return None,'missing'
    x,y = coarse
    # The connected body behind the provisional right edge supplies the dark
    # reference level. The margins on its right and above/below supply primer.
    top = max(0,y-round(.45*scale))
    bottom = min(len(ref_band),y+round(.45*scale)+1)
    left = max(0,x-round(1.25*scale))
    right = min(ref_band.shape[1],x+round(.20*scale)+1)
    tip = component_tip(ref_band[top:bottom],(x,y-top),left,right)
    if tip is None or abs(tip[0]-x)>.2*scale or abs(tip[1]+top-y)>.2*scale:
        return None,'missing'
    return [tip[0],tip[1]+top],'global_refined'
