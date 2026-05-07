"""Unit tests for the run prompt renderer."""

from datetime import datetime, timezone

import pytest

from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority
from src.contexts.symphony.use_cases.run.prompt_renderer import render_run_prompt


def _issue() -> Issue:
    return Issue(
        identifier="ENG-3",
        title="Add thing",
        description="lengthy description",
        priority=IssuePriority.HIGH,
        state="In Progress",
        branch_name=None,
        labels=("agent", "auto"),
        created_at=datetime.now(timezone.utc),
        url="https://example/ENG-3",
    )


def test_render_substitutes_all_known_fields() -> None:
    template = (
        "${issue_identifier} | ${issue_title} | ${issue_priority} | "
        "${issue_labels} | ${spec_content} | ${plan_content} | ${attempt}"
    )
    rendered = render_run_prompt(
        template=template,
        issue=_issue(),
        spec_content="SPEC",
        plan_content="PLAN",
        attempt=2,
    )
    assert "ENG-3" in rendered
    assert "Add thing" in rendered
    assert "HIGH" in rendered
    assert "agent, auto" in rendered
    assert "SPEC" in rendered
    assert "PLAN" in rendered
    assert "| 2" in rendered


def test_render_leaves_unknown_placeholders_literal() -> None:
    template = "Known ${issue_identifier} unknown ${not_a_field}"
    rendered = render_run_prompt(
        template=template,
        issue=_issue(),
        spec_content="",
        plan_content="",
        attempt=1,
    )
    assert "ENG-3" in rendered
    assert "${not_a_field}" in rendered  # safe_substitute leaves it literal


def test_render_rejects_zero_attempt() -> None:
    with pytest.raises(ValueError, match="attempt"):
        render_run_prompt(
            template="x",
            issue=_issue(),
            spec_content="",
            plan_content="",
            attempt=0,
        )
