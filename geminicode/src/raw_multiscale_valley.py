"""Module M2: RAW-preserving multiscale directional cross-section dark valley & segment extraction."""
from dataclasses import dataclass
import math
import cv2
import numpy as np

@dataclass
class ObservedSegment:
    segment_id: int
    pixel_trace: list[tuple[float, float]]
    start_pt: tuple[float, float]  # Proximal (lower x)
    end_pt: tuple[float, float]    # Distal (higher x)
    length: float
    mean_depth: float
    mean_contrast: float
    mean_angle_rad: float
    is_observed: bool = True
    quality: float = 1.0

def extract_raw_valley_segments(
    image: np.ndarray,
    roi: tuple[int, int, int, int],
    cfg: dict,
) -> list[ObservedSegment]:
    """Extract actual continuous dark line segments inside ROI preserving 1px raw lines."""
    x0, y0, x1, y1 = roi
    h, w = image.shape[:2]
    x0 = max(0, min(w - 1, x0))
    x1 = max(0, min(w, x1))
    y0 = max(0, min(h - 1, y0))
    y1 = max(0, min(h, y1))
    
    if x1 <= x0 + 4 or y1 <= y0 + 4:
        return []
    
    roi_img = image[y0:y1, x0:x1].astype(np.float32)
    rh, rw = roi_img.shape
    
    v_cfg = cfg.get('raw_multiscale_valley', {})
    angles_deg = v_cfg.get('angles_deg', [-60, -45, -30, -15, 0, 15, 30, 45, 60])
    scales = v_cfg.get('scales', [1.0, 1.8, 2.8])
    valley_depth_min = float(v_cfg.get('valley_depth_min', 2.5))
    valley_contrast_min = float(v_cfg.get('valley_contrast_min', 0.03))
    min_seg_len = int(v_cfg.get('min_segment_length_px', 3))
    half_len = int(v_cfg.get('profile_half_len', 7))
    
    # Precompute directional normal vectors
    # Tangent angle theta: crack propagation towards +x. Normal is perpendicular.
    normals = []
    for deg in angles_deg:
        rad = math.radians(deg)
        # Tangent vector: (cos(rad), sin(rad))
        # Normal vector: (-sin(rad), cos(rad))
        nx = -math.sin(rad)
        ny = math.cos(rad)
        normals.append((rad, nx, ny))
    
    best_valley = np.zeros((rh, rw), dtype=np.float32)
    best_angle = np.zeros((rh, rw), dtype=np.float32)
    best_contrast = np.zeros((rh, rw), dtype=np.float32)
    
    # Evaluate cross-section valley depth along each normal
    for rad, nx, ny in normals:
        for scale in scales:
            s_nx = nx * scale
            s_ny = ny * scale
            
            # Sample flanking points
            # Center is at (x, y)
            # Left flank at -s_n, right flank at +s_n
            # Use cv2.warpAffine or map_coordinates for vectorization
            M_l = np.float32([[1, 0, -s_nx], [0, 1, -s_ny]])
            M_r = np.float32([[1, 0, s_nx], [0, 1, s_ny]])
            
            left_val = cv2.warpAffine(roi_img, M_l, (rw, rh), borderMode=cv2.BORDER_REFLECT)
            right_val = cv2.warpAffine(roi_img, M_r, (rw, rh), borderMode=cv2.BORDER_REFLECT)
            
            # Secondary wider flank to confirm valley
            M_l2 = np.float32([[1, 0, -s_nx * 2.0], [0, 1, -s_ny * 2.0]])
            M_r2 = np.float32([[1, 0, s_nx * 2.0], [0, 1, s_ny * 2.0]])
            left_val2 = cv2.warpAffine(roi_img, M_l2, (rw, rh), borderMode=cv2.BORDER_REFLECT)
            right_val2 = cv2.warpAffine(roi_img, M_r2, (rw, rh), borderMode=cv2.BORDER_REFLECT)
            
            flank_left = np.maximum(left_val, left_val2)
            flank_right = np.maximum(right_val, right_val2)
            flank_bg = (flank_left + flank_right) / 2.0
            
            # Valley depth: both flanks should be higher than center
            depth = np.minimum(flank_left - roi_img, flank_right - roi_img)
            contrast = depth / np.maximum(1.0, flank_bg)
            
            # Prefer strictly higher depth; on tie (within 0.1), prefer angle closer to horizontal (smaller abs(rad))
            better = (depth > best_valley + 0.1) | (
                (np.abs(depth - best_valley) <= 0.1) & (abs(rad) < np.abs(best_angle))
            )
            mask = better & (depth >= valley_depth_min) & (contrast >= valley_contrast_min)
            best_valley[mask] = depth[mask]
            best_angle[mask] = rad
            best_contrast[mask] = contrast[mask]
    
    # Non-maximum suppression perpendicular to line (along normal)
    candidate_mask = np.zeros((rh, rw), dtype=bool)
    pad = 2
    for y in range(pad, rh - pad):
        for x in range(pad, rw - pad):
            v = best_valley[y, x]
            if v < valley_depth_min:
                continue
            ang = best_angle[y, x]
            # Normal direction
            nx = -math.sin(ang)
            ny = math.cos(ang)
            
            # Check neighbors along normal
            x_prev, y_prev = int(round(x - nx)), int(round(y - ny))
            x_next, y_next = int(round(x + nx)), int(round(y + ny))
            
            if 0 <= y_prev < rh and 0 <= x_prev < rw and best_valley[y_prev, x_prev] > v:
                continue
            if 0 <= y_next < rh and 0 <= x_next < rw and best_valley[y_next, x_next] > v:
                continue
            
            candidate_mask[y, x] = True
    
    # Connected component labeling & segment construction
    # Connect 8-neighbors
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        candidate_mask.astype(np.uint8), connectivity=8
    )
    
    segments: list[ObservedSegment] = []
    seg_id = 0
    
    for lbl in range(1, num_labels):
        area = stats[lbl, cv2.CC_STAT_AREA]
        if area < min_seg_len:
            continue
        
        ys, xs = np.where(labels == lbl)
        if len(xs) < min_seg_len:
            continue
        
        # Sort points by x (along crack propagation direction)
        pts = list(zip(xs, ys))
        pts.sort(key=lambda p: (p[0], p[1]))
        
        # Global image coordinates
        global_trace = [(float(px + x0), float(py + y0)) for px, py in pts]
        
        # Compute sub-pixel refinement if enabled
        start_pt = global_trace[0]
        end_pt = global_trace[-1]
        
        # Segment length
        length = float(np.linalg.norm(np.array(end_pt) - np.array(start_pt)))
        if length < 1.5 and len(pts) < min_seg_len:
            continue
        
        # Mean depth and contrast
        depths = [float(best_valley[py, px]) for px, py in pts]
        contrasts = [float(best_contrast[py, px]) for px, py in pts]
        angles = [float(best_angle[py, px]) for px, py in pts]
        
        mean_depth = float(np.mean(depths))
        mean_contrast = float(np.mean(contrasts))
        mean_angle = float(math.atan2(end_pt[1] - start_pt[1], max(0.1, end_pt[0] - start_pt[0]))) if length >= 2.0 else float(np.mean(angles))
        
        # Quality score based on continuity, depth and length
        quality = float(mean_depth * math.sqrt(len(pts)) * (1.0 + mean_contrast))
        
        segments.append(ObservedSegment(
            segment_id=seg_id,
            pixel_trace=global_trace,
            start_pt=start_pt,
            end_pt=end_pt,
            length=length,
            mean_depth=mean_depth,
            mean_contrast=mean_contrast,
            mean_angle_rad=mean_angle,
            is_observed=True,
            quality=quality,
        ))
        seg_id += 1
    
    # Sort segments by starting x
    segments.sort(key=lambda s: (s.start_pt[0], s.start_pt[1]))
    return segments
