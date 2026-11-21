"""Module M5: Multidimensional segment-level evidence scoring."""
from dataclasses import dataclass
import math
import numpy as np
from .raw_multiscale_valley import ObservedSegment
from .registration import DualRegistrationResult
from .geometry_notch import NotchGeometry

@dataclass
class SegmentFeatures:
    segment_id: int
    raw_depth: float
    raw_contrast: float
    length: float
    fixed_diff_mean: float
    fixed_diff_pos_ratio: float
    fixed_diff_contrast: float
    fixed_conf: float
    prev_diff_mean: float
    prev_diff_pos_ratio: float
    prev_diff_contrast: float
    prev_conf: float
    notch_dist: float
    angle_alignment: float  # cos(angle), crack propagates along +x
    opening_proxy: float
    composite_score: float

def compute_segment_features(
    segments: list[ObservedSegment],
    dual_reg: DualRegistrationResult,
    geometry: NotchGeometry,
    cfg: dict,
) -> list[SegmentFeatures]:
    """Extract multi-dimensional evidence features for each extracted segment."""
    sc_cfg = cfg.get('scoring', {})
    w_raw = float(sc_cfg.get('raw_valley_weight', 1.0))
    w_cnt = float(sc_cfg.get('contrast_weight', 0.8))
    w_fxd = float(sc_cfg.get('fixed_diff_weight', 1.2))
    w_prv = float(sc_cfg.get('prev_diff_weight', 0.8))
    w_prox = float(sc_cfg.get('origin_proximity_weight', 0.6))
    
    root_x, root_y = geometry.notch_root
    gauge_d = geometry.gauge_d
    opening_proxy = geometry.opening_proxy
    
    features_list: list[SegmentFeatures] = []
    
    h = dual_reg.diff_fixed.shape[0] if dual_reg.diff_fixed is not None else 1000
    w = dual_reg.diff_fixed.shape[1] if dual_reg.diff_fixed is not None else 1000
    
    for seg in segments:
        pts = seg.pixel_trace
        if not pts:
            continue
        
        # 1. Fixed reference diff sampling
        fixed_diff_mean = 0.0
        fixed_pos_ratio = 0.0
        fixed_contrast = 0.0
        fixed_conf = dual_reg.fixed.confidence
        
        if dual_reg.diff_fixed is not None and dual_reg.fixed.status in ['AVAILABLE', 'DEGRADED']:
            vals = []
            bg_vals = []
            for px, py in pts:
                ix, iy = int(round(px)), int(round(py))
                if 0 <= iy < h and 0 <= ix < w:
                    vals.append(float(dual_reg.diff_fixed[iy, ix]))
                    # Sample flanking background (+/- 5px vertical)
                    if 0 <= iy - 5 < h:
                        bg_vals.append(float(dual_reg.diff_fixed[iy - 5, ix]))
                    if 0 <= iy + 5 < h:
                        bg_vals.append(float(dual_reg.diff_fixed[iy + 5, ix]))
            if vals:
                fixed_diff_mean = float(np.mean(vals))
                fixed_pos_ratio = float(np.mean(np.array(vals) > 0.0))
                bg_mean = float(np.mean(bg_vals)) if bg_vals else 0.0
                fixed_contrast = fixed_diff_mean - bg_mean
        
        # 2. Previous frame diff sampling
        prev_diff_mean = 0.0
        prev_pos_ratio = 0.0
        prev_contrast = 0.0
        prev_conf = dual_reg.prev.confidence
        
        if dual_reg.diff_prev is not None and dual_reg.prev.status in ['AVAILABLE', 'DEGRADED']:
            vals = []
            bg_vals = []
            for px, py in pts:
                ix, iy = int(round(px)), int(round(py))
                if 0 <= iy < h and 0 <= ix < w:
                    vals.append(float(dual_reg.diff_prev[iy, ix]))
                    if 0 <= iy - 5 < h:
                        bg_vals.append(float(dual_reg.diff_prev[iy - 5, ix]))
                    if 0 <= iy + 5 < h:
                        bg_vals.append(float(dual_reg.diff_prev[iy + 5, ix]))
            if vals:
                prev_diff_mean = float(np.mean(vals))
                prev_pos_ratio = float(np.mean(np.array(vals) > 0.0))
                bg_mean = float(np.mean(bg_vals)) if bg_vals else 0.0
                prev_contrast = prev_diff_mean - bg_mean
        
        # 3. Notch origin proximity
        # Distance from segment proximal start point to notch root
        sx, sy = seg.start_pt
        dx = sx - root_x
        dy = sy - root_y
        notch_dist = math.sqrt(dx * dx + dy * dy)
        # Normalized proximity score: 1.0 when near root, decays gently with distance
        prox_score = math.exp(-max(0.0, notch_dist) / (gauge_d * 2.0))
        
        # 4. Angle alignment (direction towards +x)
        angle_alignment = max(0.0, math.cos(seg.mean_angle_rad))
        
        # 5. Composite score calculation
        # Raw valley evidence (always available)
        raw_score = seg.mean_depth * math.sqrt(seg.length)
        contrast_score = seg.mean_contrast * 10.0
        
        # Difference contribution (weighted by channel confidence, never fatal if unavailable)
        diff_contrib = 0.0
        if fixed_conf > 0.1:
            diff_contrib += fixed_conf * (fixed_contrast * 0.5 + fixed_pos_ratio * 2.0)
        if prev_conf > 0.1:
            diff_contrib += prev_conf * (prev_contrast * 0.4 + prev_pos_ratio * 1.5)
        
        # Opening proxy reinforcement (weak auxiliary)
        opening_bonus = 0.0
        if opening_proxy > 0.5 and (fixed_diff_mean > 0.0 or prev_diff_mean > 0.0):
            opening_bonus = min(1.0, opening_proxy * 0.2)
        
        composite = (
            w_raw * raw_score +
            w_cnt * contrast_score +
            w_fxd * diff_contrib +
            w_prox * prox_score * 3.0 +
            opening_bonus
        ) * (0.5 + 0.5 * angle_alignment)
        
        features_list.append(SegmentFeatures(
            segment_id=seg.segment_id,
            raw_depth=seg.mean_depth,
            raw_contrast=seg.mean_contrast,
            length=seg.length,
            fixed_diff_mean=fixed_diff_mean,
            fixed_diff_pos_ratio=fixed_pos_ratio,
            fixed_diff_contrast=fixed_contrast,
            fixed_conf=fixed_conf,
            prev_diff_mean=prev_diff_mean,
            prev_diff_pos_ratio=prev_pos_ratio,
            prev_diff_contrast=prev_contrast,
            prev_conf=prev_conf,
            notch_dist=notch_dist,
            angle_alignment=angle_alignment,
            opening_proxy=opening_proxy,
            composite_score=float(composite),
        ))
    
    return features_list
