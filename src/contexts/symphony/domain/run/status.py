"""RunStatus — string enum representing pipeline execution states."""

from enum import StrEnum


class RunStatus(StrEnum):
    """All valid states in the Run state machine."""

    RECEIVED = "received"
    GEN_SPEC = "gen_spec"
    SPEC_PENDING = "spec_pending"
    SPEC_APPROVED = "spec_approved"
    GEN_PLAN = "gen_plan"
    PLAN_PENDING = "plan_pending"
    PLAN_APPROVED = "plan_approved"
    EXECUTE = "execute"
    EXECUTED = "executed"
    GATES = "gates"
    GATES_PASSED = "gates_passed"
    GATES_FAILED = "gates_failed"
    PR_OPEN = "pr_open"
    DONE = "done"
    FAILED = "failed"
    RETRY_PENDING = "retry_pending"
