"""Contractual invariant and security tests."""
from pathlib import Path
import numpy as np
import yaml

from geminicode.src.engine import CrackTipEngine
from geminicode.src.geometry_notch import compute_notch_geometry
from geminicode.src.common import PACKAGE_ROOT

def load_default_cfg():
    cfg_path = PACKAGE_ROOT / 'configs/unified_global.yaml'
    return yaml.safe_load(cfg_path.read_text(encoding='utf-8'))

def test_anchor_swap_symmetry():
    """Verify that swapping P1 and P2 preserves rightward search direction (+x)."""
    cfg = load_default_cfg()
    h, w = 300, 400
    img = np.full((h, w), 180, dtype=np.uint8)
    
    p1 = [50.0, 100.0]
    p2 = [50.0, 200.0]
    
    geom_normal = compute_notch_geometry(p1, p2, p1, p2, img, w, h, cfg)
    geom_swapped = compute_notch_geometry(p2, p1, p2, p1, img, w, h, cfg)
    
    # In both cases normal_u[0] must be positive (+x direction)
    assert geom_normal.normal_u[0] > 0.0, f"Normal x should be positive, got {geom_normal.normal_u}"
    assert geom_swapped.normal_u[0] > 0.0, f"Swapped normal x should still be positive, got {geom_swapped.normal_u}"
    # Working ROI should still be in positive x
    assert geom_swapped.working_roi[0] >= 0
    assert geom_swapped.working_roi[2] > geom_swapped.working_roi[0]

def test_no_gt_leakage():
    """Verify that algorithm modules do not import or reference GT/label sources."""
    src_dir = PACKAGE_ROOT / 'src'
    forbidden_tokens = ['selected_frames.csv', 'human_annotations', 'labelme', 'crack_tip', 'crack_path']
    for p in src_dir.glob('*.py'):
        content = p.read_text(encoding='utf-8')
        for tok in forbidden_tokens:
            assert tok not in content, f"Forbidden GT token '{tok}' found in inference module {p.name}"

def test_deterministic_repeatability():
    """Verify that identical inputs produce bitwise identical engine outputs."""
    cfg = load_default_cfg()
    h, w = 200, 300
    img = np.full((h, w), 180, dtype=np.uint8)
    img[100, 40:120] = 150
    p1 = [30.0, 60.0]
    p2 = [30.0, 140.0]
    
    engine1 = CrackTipEngine(cfg)
    engine1.initialize(img, p1, p2)
    out1 = engine1.process_frame(img, p1, p2, prev_img=None, prev_p1=None, prev_p2=None).to_dict()
    
    engine2 = CrackTipEngine(cfg)
    engine2.initialize(img, p1, p2)
    out2 = engine2.process_frame(img, p1, p2, prev_img=None, prev_p1=None, prev_p2=None).to_dict()
    
    # Compare outputs excluding timestamp
    out1['provenance'].pop('utc')
    out2['provenance'].pop('utc')
    out1['budget'].pop('time_ms')
    out2['budget'].pop('time_ms')
    
    assert out1 == out2, "Engine outputs are not deterministic across identical calls"
