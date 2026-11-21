"""A-prime-2 independent research utilities; all artifacts stay in output/."""
from pathlib import Path
import sys, os, json, csv, time, hashlib, struct, collections, re
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'research/aprime/experiments'))
from common_ap import (api, np, cv2, sha, scalar, write, save, rows, csvout,
                       jl, read, native, guard, utc, anchors, rigid, apply, sample)
RUN_ID = os.environ.get('CRACK_AP2_RUN','aprime2_20261105_r01')
if not re.fullmatch(r'[A-Za-z0-9_-]+',RUN_ID):raise ValueError('Unsafe run ID')
RUN = ROOT / 'output/runs' / RUN_ID
SOURCE = ROOT / 'research/aprime2'
SECTIONS = ['01_protocol_and_freeze', '02_source', '03_A_candidate_audit',
            '04_reference_validity', '05_DEV', '07_native_timing', '08_media', '09_reports']
for name in SECTIONS:
    (RUN / name).mkdir(parents=True, exist_ok=True)
cv2.setNumThreads(1)

def put(p, a):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(p.suffix, a); assert ok
    buf.tofile(str(p)); return sha(p)

def dump_line(f, obj):
    f.write(json.dumps(obj, ensure_ascii=False, default=scalar, allow_nan=False) + '\n')

def formal(n, p):
    return dict(confirmed_tip=bool(n['tip_confirmed']), tip=n.get('tip_original_px'),
                raw_path=p, width_px=n.get('terminal_audit', {}).get('path_width_median_px', 2))
