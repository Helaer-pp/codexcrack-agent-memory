"""Module M3: Dual independent references (fixed & prev) registration, quality masks & signed difference."""
from dataclasses import dataclass
from typing import Optional
import cv2
import numpy as np

@dataclass
class RegistrationChannel:
    name: str  # 'fixed' or 'prev'
    status: str  # 'AVAILABLE', 'UNAVAILABLE', 'DEGRADED'
    warp_img: Optional[np.ndarray]
    valid_mask: Optional[np.ndarray]
    confidence: float
    tx: float
    ty: float
    mean_ncc: float
    invalid_reason: Optional[str] = None

@dataclass
class DualRegistrationResult:
    fixed: RegistrationChannel
    prev: RegistrationChannel
    diff_fixed: Optional[np.ndarray]
    diff_prev: Optional[np.ndarray]

def register_single_reference(
    current_img: np.ndarray,
    current_p1: list[float],
    current_p2: list[float],
    ref_img: Optional[np.ndarray],
    ref_p1: Optional[list[float]],
    ref_p2: Optional[list[float]],
    notch_roi: tuple[int, int, int, int],
    channel_name: str,
    cfg: dict,
) -> RegistrationChannel:
    """Register a single reference image to current frame with quality auditing."""
    if ref_img is None or ref_p1 is None or ref_p2 is None:
        return RegistrationChannel(
            name=channel_name,
            status='UNAVAILABLE',
            warp_img=None,
            valid_mask=None,
            confidence=0.0,
            tx=0.0,
            ty=0.0,
            mean_ncc=0.0,
            invalid_reason='REFERENCE_IMAGE_OR_P1P2_NONE',
        )
    
    r_cfg = cfg.get('registration', {})
    patch_size = int(r_cfg.get('patch_size', 64))
    patch_step = int(r_cfg.get('patch_grid_step', 32))
    ncc_thresh = float(r_cfg.get('ncc_threshold', 0.60))
    min_patches = int(r_cfg.get('min_trusted_patches', 4))
    max_trans = float(r_cfg.get('max_translation_px', 60.0))
    
    h, w = current_img.shape[:2]
    
    # 1. Coarse anchor-based similarity transform
    src_pts = np.float32([ref_p1, ref_p2])
    dst_pts = np.float32([current_p1, current_p2])
    
    # Estimate similarity / affine transform
    M_coarse = cv2.estimateAffinePartial2D(src_pts.reshape(-1, 1, 2), dst_pts.reshape(-1, 1, 2))[0]
    if M_coarse is None:
        return RegistrationChannel(
            name=channel_name,
            status='UNAVAILABLE',
            warp_img=None,
            valid_mask=None,
            confidence=0.0,
            tx=0.0,
            ty=0.0,
            mean_ncc=0.0,
            invalid_reason='COARSE_AFFINE_ESTIMATION_FAILED',
        )
    
    ref_coarse_warp = cv2.warpAffine(ref_img, M_coarse, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    
    # 2. Multi-patch fine NCC matching in stable texture areas
    # Avoid crack notch ROI
    rx0, ry0, rx1, ry1 = notch_roi
    
    # Define search regions outside crack notch ROI (e.g., above and below anchors, or left of notch)
    sample_rects = [
        # Region above P1
        (max(0, int(current_p1[0] - 150)), max(0, int(current_p1[1] - 250)),
         min(w, int(current_p1[0] + 150)), max(0, int(current_p1[1] - 50))),
        # Region below P2
        (max(0, int(current_p2[0] - 150)), min(h, int(current_p2[1] + 50)),
         min(w, int(current_p2[0] + 150)), min(h, int(current_p2[1] + 250))),
        # Region to the left of P1/P2
        (max(0, int(min(current_p1[0], current_p2[0]) - 250)),
         max(0, int(min(current_p1[1], current_p2[1]) - 50)),
         max(0, int(min(current_p1[0], current_p2[0]) - 50)),
         min(h, int(max(current_p1[1], current_p2[1]) + 50))),
    ]
    
    patch_offsets_x = []
    patch_offsets_y = []
    patch_nccs = []
    
    search_half = 12
    for x_min, y_min, x_max, y_max in sample_rects:
        if x_max <= x_min + patch_size or y_max <= y_min + patch_size:
            continue
        for py in range(y_min, y_max - patch_size, patch_step):
            for px in range(x_min, x_max - patch_size, patch_step):
                cur_patch = current_img[py:py + patch_size, px:px + patch_size]
                # Check texture variance
                std_cur = float(np.std(cur_patch))
                if std_cur < 5.0:
                    continue  # Low texture region
                
                # Search window in coarse warped ref
                sy0 = max(0, py - search_half)
                sy1 = min(h, py + patch_size + search_half)
                sx0 = max(0, px - search_half)
                sx1 = min(w, px + patch_size + search_half)
                
                ref_sub = ref_coarse_warp[sy0:sy1, sx0:sx1]
                if ref_sub.shape[0] < patch_size or ref_sub.shape[1] < patch_size:
                    continue
                
                res = cv2.matchTemplate(ref_sub, cur_patch, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                
                if max_val >= ncc_thresh:
                    # Offset relative to center
                    dx = max_loc[0] - (px - sx0)
                    dy = max_loc[1] - (py - sy0)
                    if abs(dx) <= search_half and abs(dy) <= search_half:
                        patch_offsets_x.append(dx)
                        patch_offsets_y.append(dy)
                        patch_nccs.append(max_val)
    
    fine_dx = 0.0
    fine_dy = 0.0
    mean_ncc = 0.0
    
    if len(patch_nccs) >= min_patches:
        fine_dx = float(np.median(patch_offsets_x))
        fine_dy = float(np.median(patch_offsets_y))
        mean_ncc = float(np.mean(patch_nccs))
        status = 'AVAILABLE'
        confidence = float(min(1.0, mean_ncc * (len(patch_nccs) / (min_patches * 2.0))))
        invalid_reason = None
    elif len(patch_nccs) > 0:
        fine_dx = float(np.median(patch_offsets_x))
        fine_dy = float(np.median(patch_offsets_y))
        mean_ncc = float(np.mean(patch_nccs))
        status = 'DEGRADED'
        confidence = float(mean_ncc * 0.5)
        invalid_reason = f'INSUFFICIENT_TRUSTED_PATCHES_{len(patch_nccs)}'
    else:
        # Fall back to coarse alignment only
        status = 'DEGRADED'
        confidence = 0.35
        invalid_reason = 'NO_FINE_PATCH_MATCHES_COARSE_FALLBACK'
    
    # Total translation update
    M_fine = M_coarse.copy()
    M_fine[0, 2] += fine_dx
    M_fine[1, 2] += fine_dy
    
    total_tx = float(M_fine[0, 2])
    total_ty = float(M_fine[1, 2])
    
    warp_img = cv2.warpAffine(ref_img, M_fine, (w, h), borderMode=cv2.BORDER_REFLECT)
    valid_mask = cv2.warpAffine(np.ones_like(ref_img, dtype=np.uint8) * 255, M_fine, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=0) > 0
    
    return RegistrationChannel(
        name=channel_name,
        status=status,
        warp_img=warp_img,
        valid_mask=valid_mask,
        confidence=confidence,
        tx=total_tx,
        ty=total_ty,
        mean_ncc=mean_ncc,
        invalid_reason=invalid_reason,
    )

def perform_dual_registration(
    current_img: np.ndarray,
    current_p1: list[float],
    current_p2: list[float],
    fixed_ref_img: np.ndarray,
    fixed_p1: list[float],
    fixed_p2: list[float],
    prev_ref_img: Optional[np.ndarray],
    prev_p1: Optional[list[float]],
    prev_p2: Optional[list[float]],
    notch_roi: tuple[int, int, int, int],
    cfg: dict,
) -> DualRegistrationResult:
    """Register both fixed reference and previous actual frame independently."""
    ch_fixed = register_single_reference(
        current_img=current_img,
        current_p1=current_p1,
        current_p2=current_p2,
        ref_img=fixed_ref_img,
        ref_p1=fixed_p1,
        ref_p2=fixed_p2,
        notch_roi=notch_roi,
        channel_name='fixed',
        cfg=cfg,
    )
    
    ch_prev = register_single_reference(
        current_img=current_img,
        current_p1=current_p1,
        current_p2=current_p2,
        ref_img=prev_ref_img,
        ref_p1=prev_p1,
        ref_p2=prev_p2,
        notch_roi=notch_roi,
        channel_name='prev',
        cfg=cfg,
    )
    
    # Signed differences: positive = current is darker than aligned reference
    cur_f = current_img.astype(np.float32)
    
    diff_fixed = None
    if ch_fixed.warp_img is not None:
        diff_fixed = ch_fixed.warp_img.astype(np.float32) - cur_f
    
    diff_prev = None
    if ch_prev.warp_img is not None:
        diff_prev = ch_prev.warp_img.astype(np.float32) - cur_f
    
    return DualRegistrationResult(
        fixed=ch_fixed,
        prev=ch_prev,
        diff_fixed=diff_fixed,
        diff_prev=diff_prev,
    )
