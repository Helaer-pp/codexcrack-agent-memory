"""Module M7: Dynamic segmented ROI expansion, forward scout, and computational budget."""
from dataclasses import dataclass
from typing import Optional
from .segment_graph import CandidatePath
from .geometry_notch import NotchGeometry

@dataclass
class DynamicRoiState:
    current_roi: tuple[int, int, int, int]
    expansions_count: int
    lateral_expansions_count: int
    scout_triggered: bool
    budget_exhausted: bool

def check_and_expand_roi(
    current_roi: tuple[int, int, int, int],
    candidates: list[CandidatePath],
    geometry: NotchGeometry,
    expansions_so_far: int,
    lateral_expansions_so_far: int,
    cfg: dict,
) -> tuple[tuple[int, int, int, int], bool, bool]:
    """Check if candidate endpoints approach ROI boundary and expand if budget permits.
    
    Returns:
        (new_roi, expanded_flag, budget_exhausted_flag)
    """
    x0, y0, x1, y1 = current_roi
    s_x0, s_y0, s_x1, s_y1 = geometry.safe_roi
    
    d_cfg = cfg.get('dynamic_roi', {})
    scout_margin = float(d_cfg.get('forward_scout_margin_px', 45.0))
    step_x = int(d_cfg.get('expansion_step_px', 120))
    max_exp = int(d_cfg.get('max_expansions_per_frame', 12))
    max_total_w = int(d_cfg.get('max_total_roi_width_px', 2400))
    step_y = int(d_cfg.get('lateral_expansion_step_px', 30))
    max_lat_exp = int(d_cfg.get('max_lateral_expansions', 4))
    
    if expansions_so_far >= max_exp or (x1 - x0) >= max_total_w:
        return current_roi, False, True
    
    # Check if any candidate tip is close to the right boundary
    needs_expand_x = False
    needs_expand_y_up = False
    needs_expand_y_down = False
    
    for cand in candidates:
        tip_x, tip_y = cand.terminal_observed_endpoint
        if tip_x >= (x1 - scout_margin):
            needs_expand_x = True
        if tip_y <= (y0 + 15):
            needs_expand_y_up = True
        if tip_y >= (y1 - 15):
            needs_expand_y_down = True
            
    if not (needs_expand_x or needs_expand_y_up or needs_expand_y_down):
        return current_roi, False, False
    
    new_x0 = x0
    new_x1 = x1
    new_y0 = y0
    new_y1 = y1
    
    if needs_expand_x:
        new_x1 = min(s_x1, x1 + step_x)
        
    if needs_expand_y_up and lateral_expansions_so_far < max_lat_exp:
        new_y0 = max(s_y0, y0 - step_y)
        
    if needs_expand_y_down and lateral_expansions_so_far < max_lat_exp:
        new_y1 = min(s_y1, y1 + step_y)
        
    expanded = (new_x1 > x1) or (new_y0 < y0) or (new_y1 > y1)
    new_roi = (new_x0, new_y0, new_x1, new_y1)
    
    return new_roi, expanded, False
