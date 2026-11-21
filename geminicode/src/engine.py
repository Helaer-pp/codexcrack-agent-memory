"""Module M9: Unified Crack Tip Detection Engine & State Machine."""
from dataclasses import dataclass
import time
from typing import Optional
import numpy as np

from .common import utc_now, clean_data
from .geometry_notch import compute_notch_geometry, NotchGeometry
from .raw_multiscale_valley import extract_raw_valley_segments, ObservedSegment
from .registration import perform_dual_registration, DualRegistrationResult
from .segment_features import compute_segment_features, SegmentFeatures
from .segment_graph import generate_candidate_paths, CandidatePath
from .multitrack import MultiTrackState, update_multitrack_state
from .dynamic_roi import check_and_expand_roi
from .tip_selection import select_rightmost_tip, TipSelectionResult

@dataclass
class FrameOutput:
    schema_version: str
    frame_key: str
    status: str
    tip_x: Optional[float]
    tip_y: Optional[float]
    selected_track_id: Optional[str]
    selection_rule: str
    preferred_uncertain_tip: Optional[tuple[float, float]]
    candidate_tips: list[dict]
    channels: dict
    flags: list[str]
    failure_reason: Optional[str]
    failure_stage: Optional[str]
    budget: dict
    diagnostics: dict
    provenance: dict

    def to_dict(self) -> dict:
        return clean_data({
            'schema_version': self.schema_version,
            'frame_key': self.frame_key,
            'status': self.status,
            'tip_x': self.tip_x,
            'tip_y': self.tip_y,
            'selected_track_id': self.selected_track_id,
            'selection_rule': self.selection_rule,
            'preferred_uncertain_tip': self.preferred_uncertain_tip,
            'candidate_tips': self.candidate_tips,
            'channels': self.channels,
            'flags': self.flags,
            'failure_reason': self.failure_reason,
            'failure_stage': self.failure_stage,
            'budget': self.budget,
            'diagnostics': self.diagnostics,
            'provenance': self.provenance,
        })

class CrackTipEngine:
    """Unified detector engine processing video frames sequentially with state history."""
    def __init__(self, cfg: dict, code_hash: str = "N/A", config_hash: str = "N/A"):
        self.cfg = cfg
        self.code_hash = code_hash
        self.config_hash = config_hash
        self.track_state = MultiTrackState()
        self.fixed_ref_img: Optional[np.ndarray] = None
        self.fixed_p1: Optional[list[float]] = None
        self.fixed_p2: Optional[list[float]] = None
        self.frame_counter = 0

    def initialize(
        self,
        fixed_ref_img: np.ndarray,
        fixed_ref_p1: list[float],
        fixed_ref_p2: list[float],
    ):
        """Initialize detector with fixed reference frame and anchors."""
        self.fixed_ref_img = fixed_ref_img
        self.fixed_p1 = fixed_ref_p1
        self.fixed_p2 = fixed_ref_p2
        self.track_state = MultiTrackState()
        self.frame_counter = 0

    def process_frame(
        self,
        current_img: np.ndarray,
        current_p1: list[float],
        current_p2: list[float],
        prev_img: Optional[np.ndarray],
        prev_p1: Optional[list[float]],
        prev_p2: Optional[list[float]],
        frame_meta: Optional[dict] = None,
    ) -> FrameOutput:
        """Process one frame in strict temporal sequence."""
        t_start = time.perf_counter()
        meta = frame_meta or {}
        frame_key = meta.get('frame_key', f"frame_{self.frame_counter}")
        h, w = current_img.shape[:2]
        flags: list[str] = []
        failure_stage: Optional[str] = None
        
        # 1. Geometry initialization (Module M1)
        try:
            geometry = compute_notch_geometry(
                current_p1=current_p1,
                current_p2=current_p2,
                ref_p1=self.fixed_p1,
                ref_p2=self.fixed_p2,
                ref_img=self.fixed_ref_img,
                img_w=w,
                img_h=h,
                cfg=self.cfg,
            )
        except Exception as e:
            failure_stage = "GEOMETRY"
            return FrameOutput(
                schema_version="UCTIP-1.0",
                frame_key=frame_key,
                status="PROCESSING_ERROR",
                tip_x=None,
                tip_y=None,
                selected_track_id=None,
                selection_rule="MAX_VALID_IMAGE_X",
                preferred_uncertain_tip=None,
                candidate_tips=[],
                channels={'fixed': 'UNAVAILABLE', 'prev': 'UNAVAILABLE', 'p1p2': 'DEGRADED'},
                flags=[f"GEOMETRY_ERROR_{type(e).__name__}"],
                failure_reason=str(e),
                failure_stage=failure_stage,
                budget={'exhausted': False},
                diagnostics={},
                provenance={'code_hash': self.code_hash, 'config_hash': self.config_hash},
            )

        # 2. Dual registration (Module M3)
        dual_reg = perform_dual_registration(
            current_img=current_img,
            current_p1=current_p1,
            current_p2=current_p2,
            fixed_ref_img=self.fixed_ref_img,
            fixed_p1=self.fixed_p1,
            fixed_p2=self.fixed_p2,
            prev_ref_img=prev_img,
            prev_p1=prev_p1,
            prev_p2=prev_p2,
            notch_roi=geometry.working_roi,
            cfg=self.cfg,
        )
        
        if prev_img is None:
            flags.append("PREV_REF_MISSING_FIRST_FRAME")
        if dual_reg.fixed.status != 'AVAILABLE':
            flags.append(f"FIXED_REF_{dual_reg.fixed.status}")
        if dual_reg.prev.status != 'AVAILABLE' and prev_img is not None:
            flags.append(f"PREV_REF_{dual_reg.prev.status}")

        # 3. Dynamic segmented ROI expansion loop (Modules M2, M4, M5, M7)
        current_roi = geometry.working_roi
        expansions = 0
        lat_expansions = 0
        budget_exhausted = False
        
        all_segments: list[ObservedSegment] = []
        all_features: list[SegmentFeatures] = []
        candidates: list[CandidatePath] = []
        
        while True:
            # Extract raw valley segments inside current ROI
            all_segments = extract_raw_valley_segments(current_img, current_roi, self.cfg)
            if not all_segments:
                if failure_stage is None:
                    failure_stage = "GRAY_SEGMENT"
                break
                
            # Score segment features
            all_features = compute_segment_features(all_segments, dual_reg, geometry, self.cfg)
            
            # Generate candidate paths
            candidates = generate_candidate_paths(all_segments, all_features, geometry, self.cfg)
            if not candidates:
                if failure_stage is None:
                    failure_stage = "CONNECTIVITY"
                break
                
            # Check dynamic ROI expansion
            new_roi, expanded, budget_exhausted = check_and_expand_roi(
                current_roi=current_roi,
                candidates=candidates,
                geometry=geometry,
                expansions_so_far=expansions,
                lateral_expansions_so_far=lat_expansions,
                cfg=self.cfg,
            )
            
            if expanded and not budget_exhausted:
                if new_roi[2] > current_roi[2]:
                    expansions += 1
                if new_roi[0] < current_roi[0] or new_roi[3] > current_roi[3]:
                    lat_expansions += 1
                current_roi = new_roi
            else:
                break
                
        if budget_exhausted:
            flags.append("BUDGET_EXHAUSTED")

        # 4. Multitrack state update (Module M6)
        self.track_state, active_assoc = update_multitrack_state(
            state=self.track_state,
            candidate_paths=candidates,
            frame_idx=self.frame_counter,
            cfg=self.cfg,
        )
        
        # 5. Tip selection (Module M8)
        seg_map = {s.segment_id: s for s in all_segments}
        tip_result = select_rightmost_tip(active_assoc, seg_map, dual_reg, self.cfg)
        flags.extend(tip_result.flags)
        
        if tip_result.status != 'VALID' and failure_stage is None:
            failure_stage = "TIP_VERIFICATION" if candidates else "NO_CANDIDATE"

        t_elapsed = (time.perf_counter() - t_start) * 1000.0
        self.frame_counter += 1

        channels_info = {
            'fixed': dual_reg.fixed.status,
            'prev': dual_reg.prev.status,
            'p1p2': 'OBSERVED',
        }
        budget_info = {
            'exhausted': budget_exhausted,
            'expansions': expansions,
            'lateral_expansions': lat_expansions,
            'pixels_scanned': int((current_roi[2] - current_roi[0]) * (current_roi[3] - current_roi[1])),
            'time_ms': round(t_elapsed, 2),
        }
        diag_info = {
            'roi': list(current_roi),
            'notch_root': list(geometry.notch_root),
            'opening_proxy': round(geometry.opening_proxy, 4),
            'num_segments': len(all_segments),
            'num_candidates': len(candidates),
            'active_tracks': len(self.track_state.branches),
            'fixed_conf': round(dual_reg.fixed.confidence, 4),
            'prev_conf': round(dual_reg.prev.confidence, 4),
        }
        provenance_info = {
            'code_hash': self.code_hash,
            'config_hash': self.config_hash,
            'utc': utc_now(),
        }

        return FrameOutput(
            schema_version="UCTIP-1.0",
            frame_key=frame_key,
            status=tip_result.status,
            tip_x=tip_result.tip_x,
            tip_y=tip_result.tip_y,
            selected_track_id=tip_result.selected_track_id,
            selection_rule=tip_result.selection_rule,
            preferred_uncertain_tip=tip_result.preferred_uncertain_tip,
            candidate_tips=tip_result.candidate_tips,
            channels=channels_info,
            flags=flags,
            failure_reason=tip_result.failure_reason,
            failure_stage=failure_stage if tip_result.status != 'VALID' else None,
            budget=budget_info,
            diagnostics=diag_info,
            provenance=provenance_info,
        )
