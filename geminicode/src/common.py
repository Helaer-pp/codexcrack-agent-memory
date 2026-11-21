"""Core utilities, serialization, hashing, and project invariants."""
import csv
import gzip
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import cv2
import numpy as np

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

GROUPS = {'group_a': 551, 'three_point_bend': 520, 'group_c': 562}
ROLES = {'group_a': 'DEV', 'three_point_bend': 'DEV', 'group_c': 'LOCKED'}
VISIBLE = {'group_a': 19, 'three_point_bend': 15, 'group_c': 20}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def sha256_file(p: str | Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def clean_data(v):
    if isinstance(v, (np.ndarray,)):
        return clean_data(v.tolist())
    if isinstance(v, (np.generic,)):
        return clean_data(v.item())
    if isinstance(v, float) and not np.isfinite(v):
        return None
    if isinstance(v, dict):
        return {str(k): clean_data(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [clean_data(x) for x in v]
    return v

def save_json(path: str | Path, data: any, indent: int = 2, overwrite: bool = False):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    b = json.dumps(clean_data(data), ensure_ascii=False, indent=indent, allow_nan=False).encode('utf-8')
    if p.exists() and not overwrite:
        assert p.read_bytes() == b, f"Refusing silent overwrite with different content: {p}"
    else:
        p.write_bytes(b)

def load_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def save_json_gz(path: str | Path, data: any, overwrite: bool = False):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    b = gzip.compress(
        json.dumps(clean_data(data), ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8'),
        mtime=0
    )
    if p.exists() and not overwrite:
        assert p.read_bytes() == b, f"Refusing silent overwrite with different content: {p}"
    else:
        p.write_bytes(b)

def load_json_gz(path: str | Path):
    return json.loads(gzip.decompress(Path(path).read_bytes()).decode('utf-8'))

def save_csv(path: str | Path, rows_data: list[dict], overwrite: bool = False):
    import io
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows_data = list(rows_data)
    if not rows_data:
        p.write_text('', encoding='utf-8')
        return
    keys = list(dict.fromkeys(k for r in rows_data for k in r))
    s = io.StringIO(newline='')
    w = csv.DictWriter(s, fieldnames=keys)
    w.writeheader()
    w.writerows(clean_data(rows_data))
    text = s.getvalue()
    if p.exists() and not overwrite:
        assert p.read_text(encoding='utf-8') == text, f"Refusing silent overwrite: {p}"
    else:
        p.write_text(text, encoding='utf-8')

def load_csv(path: str | Path) -> list[dict]:
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def read_uint8_bmp(path: str | Path) -> np.ndarray:
    raw = Path(path).read_bytes()
    img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Failed to decode BMP image: {path}")
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if img.dtype != np.uint8:
        raise ValueError(f"Expected uint8 image, got {img.dtype} from {path}")
    return img

def parse_anchors_file(path: str | Path) -> dict[int, tuple[list[float], list[float]]]:
    import re
    result = {}
    content = Path(path).read_bytes().decode('gb18030', errors='replace')
    for line in content.splitlines():
        nums = re.findall(r'[-+]?\d+(?:\.\d+)?', line)
        if len(nums) == 5 and line.lower().lstrip().startswith('num'):
            k = int(nums[0])
            v = list(map(float, nums[1:]))
            assert k not in result, f"Duplicate tracking frame index {k} in {path}"
            # [P1_x, P1_y], [P2_x, P2_y]
            result[k] = ([v[0], v[1]], [v[2], v[3]])
    return result

def get_source_file_hashes() -> dict[str, str]:
    files = {}
    for p in sorted(PACKAGE_ROOT.rglob('*')):
        if p.is_file() and p.suffix in ['.py', '.yaml', '.json', '.md']:
            rel = str(p.relative_to(PROJECT_ROOT)).replace('\\', '/')
            files[rel] = sha256_file(p)
    return files
