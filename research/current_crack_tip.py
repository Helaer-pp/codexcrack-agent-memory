"""Stable research release and optional latest validation candidate."""
from research.crack_tip_runner_adapter import CrackTipRelease
from research.notch_identity_v515_budget import batch, domain, difference_views

CURRENT = CrackTipRelease("V5.15", "S2", batch, domain, difference_views)
VERSION, STAGE, DEFAULT_SCALE = CURRENT.version, CURRENT.stage, CURRENT.default_scale
analyze, render = CURRENT.analyze, CURRENT.render

def choose(candidate=False):
    if candidate:
        from research.notch_identity_v63.public import CANDIDATE
        return CANDIDATE
    return CURRENT
