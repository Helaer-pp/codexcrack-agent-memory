"""Independent UCTIP-60Q implementation; historical algorithms are read-only."""
import os
from pathlib import Path
_root=Path(__file__).resolve().parents[2]
os.environ.setdefault('NUMBA_CACHE_DIR',str(_root/'output/cache/unified60q_numba'))
os.environ.setdefault('MPLCONFIGDIR',str(_root/'output/cache/matplotlib'))
