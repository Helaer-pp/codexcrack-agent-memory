"""V6.3 center-notch and registration-gate candidate."""
from research.crack_tip_runner_adapter import CrackTipRelease
from . import batch, domain, difference_views

CANDIDATE = CrackTipRelease("V6.3", "S2", batch, domain, difference_views)
