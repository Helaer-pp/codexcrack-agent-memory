"""Module M1: P1/P2 geometric initialization, notch root candidate, working & safe ROI."""
from dataclasses import dataclass
import cv2
import numpy as np

@dataclass
class NotchGeometry:
    center: tuple[float, float]
    gauge_d: float
    normal_u: tuple[float, float]
    opening_proxy: float
    notch_root: tuple[float, float]
    root_confidence: float
    origin_zone: tuple[float, float, float, float]  # (xmin, ymin, xmax, ymax)
    working_roi: tuple[int, int, int, int]          # (xmin, ymin, xmax, ymax)
    safe_roi: tuple[int, int, int, int]             # (xmin, ymin, xmax, ymax)

def compute_notch_geometry(
    current_p1: list[float],
    current_p2: list[float],
    ref_p1: list[float],
    ref_p2: list[float],
    ref_img: np.ndarray,
    img_w: int,
    img_h: int,
    cfg: dict,
) -> NotchGeometry:
    """Compute geometric frame, notch root candidate, and initial bounding ROIs."""
    p1 = np.array(current_p1, dtype=float)
    p2 = np.array(current_p2, dtype=float)
    center = (p1 + p2) / 2.0
    c_x, c_y = float(center[0]), float(center[1])
    
    gauge_d = float(np.linalg.norm(p2 - p1))
    assert gauge_d > 10.0, f"Degenerate anchor gauge distance: {gauge_d}"
    
    # Unit normal pointing towards +x (rightwards)
    # v = p2 - p1. Normal perpendicular to v is (v_y, -v_x) or (-v_y, v_x).
    # We guarantee normal_u[0] > 0
    v = p2 - p1
    n = np.array([v[1], -v[0]], dtype=float)
    if n[0] < 0:
        n = -n
    norm_n = np.linalg.norm(n)
    if norm_n > 1e-6:
        n = n / norm_n
    else:
        n = np.array([1.0, 0.0], dtype=float)
    
    # Opening proxy
    ref_d = float(np.linalg.norm(np.array(ref_p2) - np.array(ref_p1)))
    opening_proxy = gauge_d - ref_d
    
    # Locate notch root in reference image
    # Search in window around center towards the normal direction
    geo_cfg = cfg.get('geometry', {})
    win_w = int(geo_cfg.get('notch_detect_window_w', 120))
    
    # Bounded corridor in width direction (Y) strictly within P1P2:
    # Upper edge shifted down by 1/6 * gauge_d from P1
    # Lower edge shifted up by 1/6 * gauge_d from P2
    p_top = float(min(p1[1], p2[1]))
    p_bot = float(max(p1[1], p2[1]))
    inset_ratio_y = float(geo_cfg.get('p1p2_inset_ratio_y', 1.0 / 6.0))
    inset_y = inset_ratio_y * gauge_d
    
    w_ymin = max(0, int(round(p_top + inset_y)))
    w_ymax = min(img_h, int(round(p_bot - inset_y)))
    if w_ymax <= w_ymin:
        w_ymin = max(0, int(round(c_y - 0.25 * gauge_d)))
        w_ymax = min(img_h, int(round(c_y + 0.25 * gauge_d)))
    
    x0 = max(0, int(c_x - 30))
    x1 = min(img_w, int(c_x + win_w))
    y0 = w_ymin
    y1 = w_ymax
    
    root_x, root_y = c_x, c_y
    root_conf = 0.5
    
    if x1 > x0 + 10 and y1 > y0 + 10:
        sub = ref_img[y0:y1, x0:x1]
        # Otsu or adaptive threshold to detect dark notch region
        blur = cv2.GaussianBlur(sub, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        best_pt = None
        max_notch_x = -1.0
        
        for cnt in contours:
            if cv2.contourArea(cnt) < 50:
                continue
            # Look for contour points closest to centerline y = c_y
            for pt in cnt:
                px, py = float(pt[0][0] + x0), float(pt[0][1] + y0)
                if abs(py - c_y) < gauge_d * 0.4:
                    if px > max_notch_x:
                        max_notch_x = px
                        best_pt = (px, py)
        
        if best_pt is not None and max_notch_x > c_x:
            root_x, root_y = best_pt
            root_conf = 0.85
        else:
            # Fallback to geometry heuristic
            root_x = c_x + 0.15 * gauge_d
            root_y = c_y
            root_conf = 0.40
    
    # Define origin zone (for crack origination candidate search near notch root)
    corridor_y = min(40.0, 0.25 * gauge_d)
    oz_xmin = max(0.0, c_x - 20.0)
    oz_xmax = min(float(img_w), root_x + 0.4 * gauge_d)
    oz_ymin = max(float(w_ymin), root_y - corridor_y)
    oz_ymax = min(float(w_ymax), root_y + corridor_y)
    origin_zone = (oz_xmin, oz_ymin, oz_xmax, oz_ymax)
    
    # Working ROI
    init_w = geo_cfg.get('initial_roi_width_px', 520)
    margin_x_left = geo_cfg.get('roi_margin_x_left', 40)
    
    w_xmin = max(0, int(root_x - margin_x_left))
    w_xmax = min(img_w, int(w_xmin + init_w))
    working_roi = (w_xmin, w_ymin, w_xmax, w_ymax)
    
    # Safe ROI strictly bounded in width direction within P1P2 [w_ymin, w_ymax]
    safe_max_w_ratio = geo_cfg.get('safe_roi_max_width_ratio', 0.85)
    s_xmin = max(0, int(c_x - margin_x_left * 1.5))
    s_xmax = min(img_w, int(img_w * safe_max_w_ratio))
    s_ymin = w_ymin
    s_ymax = w_ymax
    safe_roi = (s_xmin, s_ymin, s_xmax, s_ymax)
    
    return NotchGeometry(
        center=(c_x, c_y),
        gauge_d=gauge_d,
        normal_u=(float(n[0]), float(n[1])),
        opening_proxy=opening_proxy,
        notch_root=(root_x, root_y),
        root_confidence=root_conf,
        origin_zone=origin_zone,
        working_roi=working_roi,
        safe_roi=safe_roi,
    )
