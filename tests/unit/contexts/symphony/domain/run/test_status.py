"""Unit tests for RunStatus string enum."""

import pytest

from src.contexts.symphony.domain.run.status import RunStatus


def test_all_eleven_values_exist():
    expected = {
        "received",
        "gen_spec",
        "spec_pending",
        "gen_plan",
        "plan_pending",
        "execute",
        "gates",
        "pr_open",
        "done",
        "failed",
        "retry_pending",
    }
    actual = {s.value for s in RunStatus}
    assert actual == expected


def test_string_coercion_from_value():
    assert RunStatus("received") == RunStatus.RECEIVED
    assert RunStatus("done") == RunStatus.DONE
    assert RunStatus("failed") == RunStatus.FAILED


def test_str_returns_value():
    assert str(RunStatus.RECEIVED) == "received"
    assert str(RunStatus.DONE) == "done"
    assert str(RunStatus.FAILED) == "failed"


def test_value_access():
    assert RunStatus.GEN_SPEC.value == "gen_spec"
    assert RunStatus.SPEC_PENDING.value == "spec_pending"
    assert RunStatus.GEN_PLAN.value == "gen_plan"
    assert RunStatus.PLAN_PENDING.value == "plan_pending"
    assert RunStatus.EXECUTE.value == "execute"
    assert RunStatus.GATES.value == "gates"
    assert RunStatus.PR_OPEN.value == "pr_open"
    assert RunStatus.RETRY_PENDING.value == "retry_pending"


def test_invalid_value_raises():
    with pytest.raises(ValueError):
        RunStatus("nonexistent")


def test_enum_equality():
    assert RunStatus.RECEIVED == RunStatus.RECEIVED
    assert RunStatus.RECEIVED != RunStatus.DONE
