"""The task-specified V5.16 research delivery when S4 fails its admission gate."""
from research.crack_tip_runner_adapter import CrackTipRelease
from . import batch, domain, difference_views

CANDIDATE = CrackTipRelease("V5.16", "S3", batch, domain, difference_views)
