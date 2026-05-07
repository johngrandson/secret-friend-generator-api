"""Paused-reason string constants for OrchestrateRunResponse.paused_reason.

Single source of truth imported by HTTP routes, tests, and the use case.
"""

from typing import Final

REASON_AWAITING_SPEC_APPROVAL: Final[str] = "awaiting_spec_approval"
REASON_AWAITING_PLAN_APPROVAL: Final[str] = "awaiting_plan_approval"
REASON_AWAITING_RETRY: Final[str] = "awaiting_retry"
REASON_NO_SPEC_FOUND: Final[str] = "no_spec_found"
REASON_NO_PLAN_FOUND: Final[str] = "no_plan_found"
