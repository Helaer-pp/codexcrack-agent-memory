"""V6.0 research runner. S3 failed the mandatory negative-control gate."""
from research.crack_tip_runner_adapter import CrackTipRelease
from . import batch, domain, difference_views

CANDIDATE = CrackTipRelease("V6.0", "S2", batch, domain, difference_views)
