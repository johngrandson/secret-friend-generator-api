"""Unit tests for the pure pr_body_builder helpers."""

from datetime import datetime, timezone
from uuid import uuid4

from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority
from src.contexts.symphony.domain.gate_result.value_object import GateResult
from src.contexts.symphony.domain.gate_result.value_object import OUTPUT_MAX_LEN
from src.contexts.symphony.use_cases.run.pr_body_builder import (
    build_pr_body,
    sum_token_usage,
)
from src.shared.agentic.agent_runner import TokenUsage
from src.shared.agentic.gate import GateName, GateStatus


def _issue() -> Issue:
    return Issue(
        identifier="ENG-42",
        title="Add gate result table",
        description="Make PR bodies machine-readable.",
        priority=IssuePriority.MEDIUM,
        state="In Progress",
        branch_name=None,
        labels=("agent",),
        created_at=datetime.now(timezone.utc),
        url="https://example/ENG-42",
    )


def _passed_gate(name: str = "ci") -> GateResult:
    return GateResult(
        run_id=uuid4(),
        gate_name=GateName(name),
        status=GateStatus.PASSED,
        output="all good",
        duration_ms=1234,
    )


def _failed_gate(output: str = "FAIL!") -> GateResult:
    return GateResult(
        run_id=uuid4(),
        gate_name=GateName("ci"),
        status=GateStatus.FAILED,
        output=output,
        duration_ms=4321,
    )


def test_build_pr_body_includes_canonical_sections() -> None:
    body = build_pr_body(
        issue=_issue(),
        spec_content="# spec body",
        plan_content="# plan body",
        gate_results=[_passed_gate()],
        total_usage=TokenUsage(input_tokens=100, output_tokens=20, total_tokens=120),
        model="claude-sonnet-4-6",
    )
    for section in (
        "## Issue",
        "ENG-42",
        "Add gate result table",
        "## Approved Spec",
        "# spec body",
        "## Approved Plan",
        "# plan body",
        "## Gate Results",
        "| ci | passed | 1234 |",
        "## Token Usage",
        "Input: 100",
        "Output: 20",
        "Total: 120",
        "Model: claude-sonnet-4-6",
    ):
        assert section in body, f"missing: {section}"


def test_build_pr_body_appends_failing_gate_output() -> None:
    body = build_pr_body(
        issue=_issue(),
        spec_content="s",
        plan_content="p",
        gate_results=[_failed_gate(output="boom\nstack trace")],
        total_usage=TokenUsage(),
        model="m",
    )
    assert "## Failed Gate Output" in body
    assert "boom" in body
    assert "stack trace" in body


def test_build_pr_body_omits_failing_section_when_no_failures() -> None:
    body = build_pr_body(
        issue=_issue(),
        spec_content="s",
        plan_content="p",
        gate_results=[_passed_gate()],
        total_usage=TokenUsage(),
        model="m",
    )
    assert "## Failed Gate Output" not in body


def test_build_pr_body_caps_failing_output_via_domain_truncation() -> None:
    """GateResult VO truncates output to OUTPUT_MAX_LEN; builder echoes verbatim."""
    huge = "x" * (OUTPUT_MAX_LEN * 2)
    gate = _failed_gate(output=huge)
    assert len(gate.output) == OUTPUT_MAX_LEN  # VO clipped already
    body = build_pr_body(
        issue=_issue(),
        spec_content="s",
        plan_content="p",
        gate_results=[gate],
        total_usage=TokenUsage(),
        model="m",
    )
    failing_section = body.split("## Failed Gate Output")[1]
    # Failing block bounded by OUTPUT_MAX_LEN + a small markdown wrapper budget
    assert len(failing_section) < OUTPUT_MAX_LEN + 200


def test_build_pr_body_handles_no_gate_results() -> None:
    body = build_pr_body(
        issue=_issue(),
        spec_content="s",
        plan_content="p",
        gate_results=[],
        total_usage=TokenUsage(),
        model="m",
    )
    assert "## Gate Results" in body
    assert "| — | — | — |" in body


def test_sum_token_usage_aggregates_three_sessions() -> None:
    a = TokenUsage(input_tokens=10, output_tokens=2, total_tokens=12)
    b = TokenUsage(input_tokens=5, output_tokens=3, total_tokens=8)
    c = TokenUsage()  # zeros
    total = sum_token_usage([a, b, c])
    assert total.input_tokens == 15
    assert total.output_tokens == 5
    assert total.total_tokens == 20


def test_sum_token_usage_empty_returns_zero() -> None:
    total = sum_token_usage([])
    assert total.input_tokens == 0
    assert total.output_tokens == 0
    assert total.total_tokens == 0
