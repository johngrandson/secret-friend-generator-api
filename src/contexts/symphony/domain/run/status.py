"""RunStatus — string enum representing pipeline execution states."""

from enum import StrEnum


class RunStatus(StrEnum):
    """All valid states in the Run state machine."""

    RECEIVED = "received"
    GEN_SPEC = "gen_spec"
    SPEC_PENDING = "spec_pending"
    GEN_PLAN = "gen_plan"
    PLAN_PENDING = "plan_pending"
    EXECUTE = "execute"
    GATES = "gates"
    PR_OPEN = "pr_open"
    DONE = "done"
    FAILED = "failed"
    RETRY_PENDING = "retry_pending"
