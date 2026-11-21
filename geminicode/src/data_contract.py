"""Data contract and temporal sequence generator with zero GT leakage."""
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional
import numpy as np

from .common import (
    PROJECT_ROOT,
    GROUPS,
    ROLES,
    read_uint8_bmp,
    parse_anchors_file,
    load_csv,
)

@dataclass
class FrameInput:
    group: str
    frame_id: str
    tracking_num: int
    current_img: np.ndarray
    current_p1: list[float]
    current_p2: list[float]
    prev_img: Optional[np.ndarray]
    prev_p1: Optional[list[float]]
    prev_p2: Optional[list[float]]
    fixed_ref_img: np.ndarray
    fixed_ref_p1: list[float]
    fixed_ref_p2: list[float]
    width: int
    height: int
    raw_path: str
    ref_path: str

class SequenceLoader:
    """Loads temporal image sequences strictly adhering to historical causality.
    
    Zero GT access: This class does NOT import or read any ground truth labels.
    """
    def __init__(self, inventory_csv_path: str | Path):
        self.inventory_path = Path(inventory_csv_path)
        self.rows = load_csv(self.inventory_path)
        # Group by dataset
        self.groups_data: dict[str, list[dict]] = {}
        for r in self.rows:
            g = r['group']
            self.groups_data.setdefault(g, []).append(r)
        for g, part in self.groups_data.items():
            part.sort(key=lambda x: int(x['tracking_num']))
            expected = GROUPS.get(g)
            if expected is not None:
                assert len(part) == expected, f"Group {g} has {len(part)} frames, expected {expected}"
            tracking_indices = [int(x['tracking_num']) for x in part]
            assert tracking_indices == list(range(len(part))), f"Group {g} tracking numbers not contiguous 0..N-1"

    def iter_group(self, group: str) -> Iterator[FrameInput]:
        """Iterate frames in temporal order for a specific group."""
        assert group in self.groups_data, f"Unknown group: {group}"
        part = self.groups_data[group]
        
        # Load anchor points once per group
        anchor_file = PROJECT_ROOT / part[0]['point_source']
        if not anchor_file.exists():
            # Try absolute path or relative to project root
            anchor_file = Path(part[0]['point_source'])
        anchors_map = parse_anchors_file(anchor_file)
        
        # Load fixed reference image
        ref_path = Path(part[0]['reference'])
        fixed_ref_img = read_uint8_bmp(ref_path)
        ref_h, ref_w = fixed_ref_img.shape[:2]
        
        # Reference anchors: frame 0 tracking anchors as fixed reference anchors
        ref_p1, ref_p2 = anchors_map[0]
        
        prev_img = None
        prev_p1 = None
        prev_p2 = None
        
        for idx, row in enumerate(part):
            t_num = int(row['tracking_num'])
            cur_path = Path(row['current'])
            cur_img = read_uint8_bmp(cur_path)
            h, w = cur_img.shape[:2]
            
            cur_p1, cur_p2 = anchors_map[t_num]
            
            frame_input = FrameInput(
                group=group,
                frame_id=row['frame_id'],
                tracking_num=t_num,
                current_img=cur_img,
                current_p1=cur_p1,
                current_p2=cur_p2,
                prev_img=prev_img,
                prev_p1=prev_p1,
                prev_p2=prev_p2,
                fixed_ref_img=fixed_ref_img,
                fixed_ref_p1=ref_p1,
                fixed_ref_p2=ref_p2,
                width=w,
                height=h,
                raw_path=str(cur_path),
                ref_path=str(ref_path),
            )
            yield frame_input
            
            # Advance previous frame to current frame
            prev_img = cur_img
            prev_p1 = cur_p1
            prev_p2 = cur_p2
