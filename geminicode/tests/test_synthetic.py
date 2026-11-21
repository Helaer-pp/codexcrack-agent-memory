"""Synthetic invariant tests verifying core algorithm requirements."""
import numpy as np
import yaml

from geminicode.src.raw_multiscale_valley import extract_raw_valley_segments
from geminicode.src.geometry_notch import compute_notch_geometry
from geminicode.src.segment_graph import generate_candidate_paths
from geminicode.src.segment_features import compute_segment_features
from geminicode.src.registration import perform_dual_registration
from geminicode.src.engine import CrackTipEngine
from geminicode.src.common import PACKAGE_ROOT

def load_default_cfg():
    cfg_path = PACKAGE_ROOT / 'configs/unified_global.yaml'
    return yaml.safe_load(cfg_path.read_text(encoding='utf-8'))

def test_1px_thin_line_preservation():
    """Verify that a 1px thin dark line is detected and not smoothed out."""
    cfg = load_default_cfg()
    h, w = 200, 300
    # Background 180, line intensity 160 (depth 20)
    img = np.full((h, w), 180, dtype=np.uint8)
    # Draw horizontal 1px dark line from x=50 to x=150 at y=100
    img[100, 50:151] = 160
    
    roi = (40, 80, 160, 120)
    segments = extract_raw_valley_segments(img, roi, cfg)
    assert len(segments) >= 1, "Failed to detect 1px thin dark line"
    
    # Check that segment endpoints cover approximately 50 to 150
    rightmost_x = max(s.end_pt[0] for s in segments)
    assert abs(rightmost_x - 150) <= 2.0, f"Expected endpoint around 150, got {rightmost_x}"

def test_bifurcation_rightmost_argmax_x_selection():
    """Verify that among multiple branches, the one with largest x is chosen (argmax x)."""
    cfg = load_default_cfg()
    h, w = 300, 400
    img = np.full((h, w), 180, dtype=np.uint8)
    
    # Common stem: y=150, x from 50 to 100
    img[150, 50:101] = 155
    # Branch 1 (shorter in x, ends at x=140): y from 150 to 130
    for i, x in enumerate(range(100, 141)):
        y = int(150 - i * 0.5)
        img[y, x] = 155
    # Branch 2 (longer in x, ends at x=190): y from 150 to 170
    for i, x in enumerate(range(100, 191)):
        y = int(150 + i * 0.2)
        img[y, x] = 155
        
    p1 = [40.0, 100.0]
    p2 = [40.0, 200.0]
    
    engine = CrackTipEngine(cfg)
    engine.initialize(img, p1, p2)
    output = engine.process_frame(img, p1, p2, prev_img=None, prev_p1=None, prev_p2=None)
    
    assert output.status == 'VALID', f"Expected VALID status, got {output.status}"
    assert output.tip_x is not None, "Tip x is None"
    # Should choose branch 2 (near x=190), NOT branch 1 (x=140)
    assert abs(output.tip_x - 190.0) <= 4.0, f"Expected rightmost tip at ~190, got {output.tip_x}"

def test_inferred_gap_bridging():
    """Verify that a small gap (8px) is bridged, but gap pixels are not reported as tip."""
    cfg = load_default_cfg()
    h, w = 200, 300
    img = np.full((h, w), 180, dtype=np.uint8)
    
    # Segment 1: x=50 to 90
    img[100, 50:91] = 155
    # Gap: x=91 to 99 (9px gap)
    # Segment 2: x=100 to 140
    img[100, 100:141] = 155
    
    roi = (40, 80, 160, 120)
    segments = extract_raw_valley_segments(img, roi, cfg)
    assert len(segments) >= 2, f"Expected at least 2 distinct segments, got {len(segments)}"
    
    geom = compute_notch_geometry([40.0, 50.0], [40.0, 150.0], [40.0, 50.0], [40.0, 150.0], img, w, h, cfg)
    dual_reg = perform_dual_registration(img, [40.0, 50.0], [40.0, 150.0], img, [40.0, 50.0], [40.0, 150.0], None, None, None, roi, cfg)
    features = compute_segment_features(segments, dual_reg, geom, cfg)
    paths = generate_candidate_paths(segments, features, geom, cfg)
    
    assert len(paths) >= 1, "Failed to connect bridged path"
    best_path = paths[0]
    assert best_path.inferred_gap_count >= 1, "Expected path to have at least 1 inferred gap"
    # Tip must be on the second segment (near x=140), not inside the gap
    assert abs(best_path.terminal_observed_endpoint[0] - 140.0) <= 2.0

def test_dual_reference_independent_degradation():
    """Verify that if one reference channel fails or is absent, the other operates independently."""
    cfg = load_default_cfg()
    h, w = 200, 300
    img1 = np.full((h, w), 180, dtype=np.uint8)
    # Add texture
    np.random.seed(42)
    noise = np.random.randint(-15, 15, (h, w), dtype=np.int16)
    img_tex = np.clip(img1.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    p1 = [50.0, 50.0]
    p2 = [50.0, 150.0]
    roi = (40, 40, 180, 160)
    
    # prev_ref is None (first frame case)
    dual_reg = perform_dual_registration(img_tex, p1, p2, img_tex, p1, p2, None, None, None, roi, cfg)
    assert dual_reg.fixed.status in ['AVAILABLE', 'DEGRADED'], f"Fixed ref should be available, got {dual_reg.fixed.status}"
    assert dual_reg.prev.status == 'UNAVAILABLE', f"Prev ref should be UNAVAILABLE, got {dual_reg.prev.status}"
    assert dual_reg.diff_prev is None, "diff_prev should be None when prev is unavailable"

def test_motion_anomaly_recheck_large_jump():
    """Verify that large tip jumps trigger recheck and are accepted if RAW evidence is strong (no hard cutoff)."""
    cfg = load_default_cfg()
    h, w = 300, 500
    img = np.full((h, w), 180, dtype=np.uint8)
    
    p1 = [40.0, 100.0]
    p2 = [40.0, 200.0]
    
    # Frame 1: crack extends to x=100
    img1 = img.copy()
    img1[150, 50:101] = 150
    
    engine = CrackTipEngine(cfg)
    engine.initialize(img1, p1, p2)
    out1 = engine.process_frame(img1, p1, p2, prev_img=None, prev_p1=None, prev_p2=None)
    assert out1.status == 'VALID'
    assert abs(out1.tip_x - 100.0) <= 3.0
    
    # Frame 2: sudden jump by 80px to x=180 (well above anomaly threshold of 45px)
    img2 = img.copy()
    img2[150, 50:181] = 145  # Strong raw dark line
    out2 = engine.process_frame(img2, p1, p2, prev_img=img1, prev_p1=p1, prev_p2=p2)
    
    # Should NOT be MOTION_REJECTED! It should pass recheck and be accepted as VALID!
    assert out2.status == 'VALID', f"Expected VALID status, got {out2.status}"
    assert abs(out2.tip_x - 180.0) <= 3.0, f"Expected tip at 180, got {out2.tip_x}"
    # Must have triggered MOTION_ANOMALY_RECHECK in flags
    recheck_flags = [f for f in out2.flags if 'MOTION_ANOMALY' in f]
    assert len(recheck_flags) >= 1, f"Expected anomaly recheck flag, got {out2.flags}"
