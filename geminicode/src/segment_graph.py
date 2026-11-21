"""Module M4: Segment connectivity graph, inferred gaps, candidate paths with distinct termination."""
from dataclasses import dataclass, field
import math
from typing import Optional
from .raw_multiscale_valley import ObservedSegment
from .segment_features import SegmentFeatures
from .geometry_notch import NotchGeometry

@dataclass
class GraphEdge:
    from_seg_id: int
    to_seg_id: int
    gap_distance: float
    edge_type: str  # 'OBSERVED_CONTINUATION' or 'INFERRED_GAP'
    angle_diff_deg: float
    penalty: float

@dataclass
class CandidatePath:
    path_id: int
    segment_ids: list[int]
    edges: list[GraphEdge]
    total_score: float
    inferred_gap_count: int
    total_gap_length: float
    terminal_observed_endpoint: tuple[float, float]
    terminal_segment_id: int
    evidence_state: str = "CANDIDATE"  # 'CANDIDATE', 'CONFIRMED', 'UNCERTAIN', 'REJECTED'
    rejection_reason: Optional[str] = None

def build_segment_graph(
    segments: list[ObservedSegment],
    features: list[SegmentFeatures],
    cfg: dict,
) -> tuple[dict[int, list[GraphEdge]], dict[int, list[GraphEdge]]]:
    """Build directed acyclic forward connectivity graph between segments."""
    c_cfg = cfg.get('connectivity', {})
    max_direct_gap = float(c_cfg.get('max_direct_gap_px', 4.0))
    max_inferred_gap = float(c_cfg.get('max_inferred_gap_px', 16.0))
    angle_diff_max = float(c_cfg.get('angle_diff_max_deg', 45.0))
    gap_penalty_factor = float(c_cfg.get('gap_penalty_factor', 1.5))
    
    seg_map = {s.segment_id: s for s in segments}
    forward_edges: dict[int, list[GraphEdge]] = {s.segment_id: [] for s in segments}
    backward_edges: dict[int, list[GraphEdge]] = {s.segment_id: [] for s in segments}
    
    n = len(segments)
    for i in range(n):
        s_from = segments[i]
        end_pt = s_from.end_pt
        
        for j in range(i + 1, n):
            s_to = segments[j]
            start_pt = s_to.start_pt
            
            # Forward progression check in +x direction
            dx = start_pt[0] - end_pt[0]
            if dx < -2.0:
                continue
            if dx > max_inferred_gap * 1.5:
                # Segments are sorted by x, but y might differ; we can break if dx is too large
                if dx > max_inferred_gap * 2.5:
                    break
            
            dy = start_pt[1] - end_pt[1]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > max_inferred_gap:
                continue
            
            # Angle check
            vec_ang = math.atan2(dy, max(0.1, dx))
            angle_diff = abs(math.degrees(vec_ang - s_from.mean_angle_rad))
            if angle_diff > 180.0:
                angle_diff = 360.0 - angle_diff
            if angle_diff > angle_diff_max:
                continue
            
            edge_type = 'OBSERVED_CONTINUATION' if dist <= max_direct_gap else 'INFERRED_GAP'
            penalty = 0.0 if edge_type == 'OBSERVED_CONTINUATION' else dist * gap_penalty_factor
            
            edge = GraphEdge(
                from_seg_id=s_from.segment_id,
                to_seg_id=s_to.segment_id,
                gap_distance=dist,
                edge_type=edge_type,
                angle_diff_deg=angle_diff,
                penalty=penalty,
            )
            forward_edges[s_from.segment_id].append(edge)
            backward_edges[s_to.segment_id].append(edge)
            
    return forward_edges, backward_edges

def generate_candidate_paths(
    segments: list[ObservedSegment],
    features: list[SegmentFeatures],
    geometry: NotchGeometry,
    cfg: dict,
) -> list[CandidatePath]:
    """Generate and rank candidate paths while strictly preserving distinct termination endpoints."""
    if not segments:
        return []
    
    forward_edges, _ = build_segment_graph(segments, features, cfg)
    feat_map = {f.segment_id: f for f in features}
    seg_map = {s.segment_id: s for s in segments}
    
    b_cfg = cfg.get('budget', {})
    beam_width = int(b_cfg.get('max_candidate_paths', 64))
    distinct_margin = float(cfg.get('connectivity', {}).get('preserve_distinct_terminal_margin_px', 5.0))
    min_score = float(cfg.get('scoring', {}).get('min_branch_score', 2.0))
    
    # Identify seed segments (proximal segments near origin zone or with low notch distance)
    root_x, root_y = geometry.notch_root
    oz_xmin, oz_ymin, oz_xmax, oz_ymax = geometry.origin_zone
    
    corridor_y = min(40.0, geometry.gauge_d * 0.25)
    seed_segs = []
    for s in segments:
        sx, sy = s.start_pt
        # In origin zone or close to root corridor
        in_origin = (oz_xmin <= sx <= oz_xmax + 40.0) and (abs(sy - root_y) <= corridor_y)
        if in_origin:
            seed_segs.append(s)
            
    if not seed_segs:
        # Fall back to leftmost segments
        seed_segs = sorted(segments, key=lambda s: s.start_pt[0])[:5]
    
    # Beam search exploration
    # Queue of active partial paths: (score, [seg_ids], [edges])
    active_paths: list[tuple[float, list[int], list[GraphEdge]]] = []
    for s in seed_segs:
        f = feat_map.get(s.segment_id)
        sc = f.composite_score if f else 1.0
        active_paths.append((sc, [s.segment_id], []))
    
    completed_paths: list[tuple[float, list[int], list[GraphEdge]]] = []
    
    # Max exploration depth
    for _ in range(30):
        if not active_paths:
            break
        
        next_active = []
        for score, seg_ids, edges in active_paths:
            cur_id = seg_ids[-1]
            out_edges = forward_edges.get(cur_id, [])
            
            if not out_edges:
                # Path terminated
                completed_paths.append((score, seg_ids, edges))
                continue
            
            # Branch or extend
            extended = False
            for edge in out_edges:
                next_id = edge.to_seg_id
                if next_id in seg_ids:
                    continue  # Loop prevention
                f = feat_map.get(next_id)
                seg_sc = f.composite_score if f else 1.0
                new_score = score + seg_sc - edge.penalty
                
                next_active.append((new_score, seg_ids + [next_id], edges + [edge]))
                extended = True
                
            if not extended:
                completed_paths.append((score, seg_ids, edges))
                
        # Beam pruning: keep top-scoring active paths
        next_active.sort(key=lambda p: p[0], reverse=True)
        active_paths = next_active[:beam_width * 2]
    
    # Include remaining active paths in completed
    completed_paths.extend(active_paths)
    
    # Deduplication preserving distinct endpoints
    # Sort completed paths by score descending
    completed_paths.sort(key=lambda p: p[0], reverse=True)
    
    distinct_candidates: list[CandidatePath] = []
    seen_endpoints: list[tuple[float, float]] = []
    path_counter = 0
    
    for score, seg_ids, edges in completed_paths:
        if score < min_score:
            continue
        
        term_seg = seg_map[seg_ids[-1]]
        term_endpoint = term_seg.end_pt  # Last reliable observed segment endpoint
        
        # Check if another candidate has virtually identical endpoint
        is_duplicate = False
        for ep in seen_endpoints:
            if math.hypot(term_endpoint[0] - ep[0], term_endpoint[1] - ep[1]) < distinct_margin:
                is_duplicate = True
                break
        
        if is_duplicate:
            continue
        
        seen_endpoints.append(term_endpoint)
        inferred_count = sum(1 for e in edges if e.edge_type == 'INFERRED_GAP')
        total_gap = sum(e.gap_distance for e in edges if e.edge_type == 'INFERRED_GAP')
        
        distinct_candidates.append(CandidatePath(
            path_id=path_counter,
            segment_ids=seg_ids,
            edges=edges,
            total_score=score,
            inferred_gap_count=inferred_count,
            total_gap_length=total_gap,
            terminal_observed_endpoint=term_endpoint,
            terminal_segment_id=term_seg.segment_id,
            evidence_state="CANDIDATE",
        ))
        path_counter += 1
        if len(distinct_candidates) >= beam_width:
            break
            
    return distinct_candidates
