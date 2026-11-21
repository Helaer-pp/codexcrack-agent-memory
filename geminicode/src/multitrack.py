"""Module M6: Multi-branch track state, hysteresis, and historical extent separation."""
from dataclasses import dataclass, field
import math
from typing import Optional
from .segment_graph import CandidatePath

@dataclass
class TrackBranch:
    track_id: str
    state: str  # 'ACTIVE', 'LOST', 'REACQUIRING'
    consecutive_lost: int
    current_observed_tip: Optional[tuple[float, float]]
    current_path_id: Optional[int]
    current_score: float
    historical_max_x: float
    historical_tips: list[tuple[float, float]] = field(default_factory=list)
    evidence_confirmed: bool = False

@dataclass
class MultiTrackState:
    branches: list[TrackBranch] = field(default_factory=list)
    next_track_idx: int = 1
    last_confirmed_frame: int = -1

def update_multitrack_state(
    state: MultiTrackState,
    candidate_paths: list[CandidatePath],
    frame_idx: int,
    cfg: dict,
) -> tuple[MultiTrackState, list[tuple[TrackBranch, CandidatePath]]]:
    """Update multi-track lifecycle with hysteresis and historical separation."""
    m_cfg = cfg.get('multitrack', {})
    max_lost = int(m_cfg.get('max_lost_frames', 5))
    hysteresis_bonus = float(m_cfg.get('history_hysteresis_bonus', 0.4))
    split_dist_min = float(m_cfg.get('branch_split_dist_min_px', 6.0))
    min_confirm_obs = int(m_cfg.get('branch_confirmation_observations', 2))
    
    # 1. Apply hysteresis bonus to candidate paths matching existing active/lost tracks
    matched_candidates: set[int] = set()
    active_associations: list[tuple[TrackBranch, CandidatePath]] = []
    
    for branch in state.branches:
        if branch.state == 'LOST' and branch.consecutive_lost > max_lost:
            continue  # Track timed out
        
        last_tip = branch.historical_tips[-1] if branch.historical_tips else None
        best_cand = None
        best_cand_score = -1e9
        
        for cand in candidate_paths:
            if cand.path_id in matched_candidates:
                continue
            tip = cand.terminal_observed_endpoint
            
            # Proximity to last observed tip of this track
            bonus = 0.0
            if last_tip is not None:
                dist = math.hypot(tip[0] - last_tip[0], tip[1] - last_tip[1])
                # Smooth hysteresis bonus (decays gently with distance, no hard cutoff)
                bonus = hysteresis_bonus * math.exp(-dist / 80.0)
            
            adjusted_score = cand.total_score + bonus
            if adjusted_score > best_cand_score:
                best_cand_score = adjusted_score
                best_cand = cand
                
        if best_cand is not None and best_cand_score > 2.0:
            matched_candidates.add(best_cand.path_id)
            # Update branch state
            old_state = branch.state
            new_state = 'ACTIVE' if old_state != 'LOST' else 'REACQUIRING'
            branch.state = new_state
            branch.consecutive_lost = 0
            branch.current_observed_tip = best_cand.terminal_observed_endpoint
            branch.current_path_id = best_cand.path_id
            branch.current_score = best_cand.total_score
            branch.historical_tips.append(best_cand.terminal_observed_endpoint)
            branch.historical_max_x = max(branch.historical_max_x, best_cand.terminal_observed_endpoint[0])
            if len(branch.historical_tips) >= min_confirm_obs:
                branch.evidence_confirmed = True
            active_associations.append((branch, best_cand))
        else:
            # Track not observed in current frame
            branch.state = 'LOST'
            branch.consecutive_lost += 1
            branch.current_observed_tip = None  # Crucial: NEVER copy historical tip as current tip!
            branch.current_path_id = None
            branch.current_score = 0.0
    
    # 2. Check remaining unmatched candidates to initialize new branches / tracks
    for cand in candidate_paths:
        if cand.path_id in matched_candidates:
            continue
        if cand.total_score < 3.0:
            continue  # Insufficient evidence for new track
        
        cand_tip = cand.terminal_observed_endpoint
        # Verify it is sufficiently separated from existing active branches
        is_distinct = True
        for b in state.branches:
            if b.current_observed_tip is not None:
                d = math.hypot(cand_tip[0] - b.current_observed_tip[0], cand_tip[1] - b.current_observed_tip[1])
                if d < split_dist_min:
                    is_distinct = False
                    break
        
        if is_distinct:
            track_id = f"trk-{state.next_track_idx:02d}"
            state.next_track_idx += 1
            new_branch = TrackBranch(
                track_id=track_id,
                state='ACTIVE',
                consecutive_lost=0,
                current_observed_tip=cand_tip,
                current_path_id=cand.path_id,
                current_score=cand.total_score,
                historical_max_x=cand_tip[0],
                historical_tips=[cand_tip],
                evidence_confirmed=(min_confirm_obs <= 1),
            )
            state.branches.append(new_branch)
            matched_candidates.add(cand.path_id)
            active_associations.append((new_branch, cand))
            
    # Prune timed-out lost tracks
    state.branches = [b for b in state.branches if not (b.state == 'LOST' and b.consecutive_lost > max_lost)]
    
    return state, active_associations
