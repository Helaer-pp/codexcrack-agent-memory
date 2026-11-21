"""Module M8: Branch endpoint verification, anomaly jump recheck, argmax(image_x) tip selection."""
from dataclasses import dataclass
import math
from typing import Optional
from .multitrack import TrackBranch
from .segment_graph import CandidatePath
from .raw_multiscale_valley import ObservedSegment
from .registration import DualRegistrationResult

@dataclass
class VerifiedBranchTip:
    track_id: str
    tip_coords: tuple[float, float]  # (x, y)
    score: float
    raw_depth: float
    evidence_state: str  # 'VERIFIED', 'UNCERTAIN', 'REJECTED'
    recheck_passed: bool
    jump_distance: float
    flags: list[str]

@dataclass
class TipSelectionResult:
    status: str  # 'VALID', 'NO_VISIBLE_TRACK', 'IDENTITY_UNCERTAIN', 'TRACK_LOST', 'BUDGET_EXHAUSTED'
    tip_x: Optional[float]
    tip_y: Optional[float]
    selected_track_id: Optional[str]
    selection_rule: str
    preferred_uncertain_tip: Optional[tuple[float, float]]
    candidate_tips: list[dict]
    flags: list[str]
    failure_reason: Optional[str]

def select_rightmost_tip(
    active_associations: list[tuple[TrackBranch, CandidatePath]],
    segments_map: dict[int, ObservedSegment],
    dual_reg: DualRegistrationResult,
    cfg: dict,
) -> TipSelectionResult:
    """Select the rightmost verified crack tip: argmax(image_x) among all verified reliable branches."""
    t_cfg = cfg.get('tip_selection', {})
    anomaly_thresh = float(t_cfg.get('anomaly_jump_threshold_px', 45.0))
    min_score = float(cfg.get('scoring', {}).get('min_branch_score', 2.0))
    
    verified_tips: list[VerifiedBranchTip] = []
    uncertain_tips: list[VerifiedBranchTip] = []
    flags: list[str] = []
    
    candidate_records: list[dict] = []
    
    for branch, cand in active_associations:
        tip_pt = cand.terminal_observed_endpoint
        term_seg = segments_map.get(cand.terminal_segment_id)
        raw_depth = term_seg.mean_depth if term_seg else 0.0
        
        # Calculate jump distance relative to previous historical tip
        jump_dist = 0.0
        branch_flags = []
        if len(branch.historical_tips) >= 2:
            prev_tip = branch.historical_tips[-2]
            jump_dist = math.hypot(tip_pt[0] - prev_tip[0], tip_pt[1] - prev_tip[1])
        
        # Motion Anomaly Recheck (NO hard rejection!)
        recheck_passed = True
        if jump_dist > anomaly_thresh:
            branch_flags.append('MOTION_ANOMALY_RECHECK')
            flags.append(f'BRANCH_{branch.track_id}_MOTION_ANOMALY_JUMP_{jump_dist:.1f}px')
            
            # Independent evidence audit:
            # Requires either strong raw valley depth or strong positive difference support
            has_strong_raw = (raw_depth >= 2.5) and (cand.total_score >= min_score * 1.2)
            has_strong_diff = (
                (dual_reg.fixed.confidence > 0.3 and cand.total_score >= min_score) or
                (dual_reg.prev.confidence > 0.3 and cand.total_score >= min_score)
            )
            if not (has_strong_raw or has_strong_diff):
                recheck_passed = False
                branch_flags.append('ANOMALY_RECHECK_EVIDENCE_WEAK')
        
        # Verify crack observation and identity:
        # Rather than hard capping gap count to <= 4, check gap ratio (gap length vs total path length)
        path_observed_len = sum(segments_map[sid].length for sid in cand.segment_ids if sid in segments_map)
        path_total_len = path_observed_len + cand.total_gap_length
        gap_ratio = cand.total_gap_length / max(1.0, path_total_len)
        gap_ok = (gap_ratio <= 0.35) or (cand.inferred_gap_count <= 5) or (cand.total_score >= 80.0 and gap_ratio <= 0.45)
        is_verified = (cand.total_score >= min_score) and recheck_passed and gap_ok
        
        cand_dict = {
            'track_id': branch.track_id,
            'x': float(tip_pt[0]),
            'y': float(tip_pt[1]),
            'score': float(cand.total_score),
            'raw_depth': float(raw_depth),
            'jump_dist': float(jump_dist),
            'evidence_state': 'VERIFIED' if is_verified else 'UNCERTAIN',
            'flags': branch_flags,
        }
        candidate_records.append(cand_dict)
        
        branch_tip_obj = VerifiedBranchTip(
            track_id=branch.track_id,
            tip_coords=tip_pt,
            score=cand.total_score,
            raw_depth=raw_depth,
            evidence_state='VERIFIED' if is_verified else 'UNCERTAIN',
            recheck_passed=recheck_passed,
            jump_distance=jump_dist,
            flags=branch_flags,
        )
        
        if is_verified:
            verified_tips.append(branch_tip_obj)
        else:
            uncertain_tips.append(branch_tip_obj)
            
    # Decision: Select argmax(image_x) among verified tips
    if verified_tips:
        # Sort by image_x descending
        # Tie-breaker: higher composite score
        verified_tips.sort(key=lambda t: (t.tip_coords[0], t.score), reverse=True)
        winner = verified_tips[0]
        
        return TipSelectionResult(
            status='VALID',
            tip_x=float(winner.tip_coords[0]),
            tip_y=float(winner.tip_coords[1]),
            selected_track_id=winner.track_id,
            selection_rule='MAX_VALID_IMAGE_X',
            preferred_uncertain_tip=None,
            candidate_tips=candidate_records,
            flags=flags,
            failure_reason=None,
        )
    
    # If no verified tips, check uncertain tips
    preferred_uncertain = None
    if uncertain_tips:
        uncertain_tips.sort(key=lambda t: (t.tip_coords[0], t.score), reverse=True)
        preferred_uncertain = (float(uncertain_tips[0].tip_coords[0]), float(uncertain_tips[0].tip_coords[1]))
        return TipSelectionResult(
            status='IDENTITY_UNCERTAIN',
            tip_x=None,
            tip_y=None,
            selected_track_id=None,
            selection_rule='MAX_VALID_IMAGE_X',
            preferred_uncertain_tip=preferred_uncertain,
            candidate_tips=candidate_records,
            flags=flags,
            failure_reason='INSUFFICIENT_EVIDENCE_FOR_VERIFIED_TIP',
        )
        
    return TipSelectionResult(
        status='NO_VISIBLE_TRACK',
        tip_x=None,
        tip_y=None,
        selected_track_id=None,
        selection_rule='MAX_VALID_IMAGE_X',
        preferred_uncertain_tip=None,
        candidate_tips=candidate_records,
        flags=flags,
        failure_reason='NO_CRACK_CANDIDATES_FOUND_IN_ROI',
    )
