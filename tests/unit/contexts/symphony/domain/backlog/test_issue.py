"""Unit tests for the Issue value object and IssuePriority enum."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from src.contexts.symphony.domain.backlog.issue import Issue, IssuePriority

_TS = datetime(2024, 1, 15, tzinfo=timezone.utc)


def _issue(
    identifier: str = "ENG-123",
    title: str = "Fix login bug",
    description: str = "Users cannot log in with SSO.",
    priority: IssuePriority = IssuePriority.HIGH,
    state: str = "todo",
    branch_name: str | None = "fix/login-bug",
    labels: tuple[str, ...] = ("bug", "auth"),
    created_at: datetime = _TS,
) -> Issue:
    return Issue(
        identifier=identifier,
        title=title,
        description=description,
        priority=priority,
        state=state,
        branch_name=branch_name,
        labels=labels,
        created_at=created_at,
    )


def test_valid_issue_constructs():
    issue = _issue()
    assert issue.identifier == "ENG-123"
    assert issue.title == "Fix login bug"
    assert issue.priority == IssuePriority.HIGH
    assert issue.state == "todo"
    assert issue.branch_name == "fix/login-bug"
    assert issue.labels == ("bug", "auth")


def test_valid_issue_with_no_branch():
    issue = _issue(branch_name=None)
    assert issue.branch_name is None


def test_valid_issue_with_empty_labels():
    issue = _issue(labels=())
    assert issue.labels == ()


def test_blank_identifier_raises():
    with pytest.raises(ValueError, match="identifier"):
        _issue(identifier="   ")


def test_empty_identifier_raises():
    with pytest.raises(ValueError):
        _issue(identifier="")


def test_blank_title_raises():
    with pytest.raises(ValueError, match="title"):
        _issue(title="   ")


def test_empty_title_raises():
    with pytest.raises(ValueError):
        _issue(title="")


def test_issue_priority_int_values():
    assert IssuePriority.NO_PRIORITY == 0
    assert IssuePriority.URGENT == 1
    assert IssuePriority.HIGH == 2
    assert IssuePriority.MEDIUM == 3
    assert IssuePriority.LOW == 4


def test_issue_priority_coercion_from_int():
    assert IssuePriority(2) == IssuePriority.HIGH
    assert IssuePriority(0) == IssuePriority.NO_PRIORITY


def test_issue_is_frozen():
    issue = _issue()
    with pytest.raises(FrozenInstanceError):
        issue.title = "changed"  # type: ignore[misc]


def test_equal_issues_are_equal():
    a = _issue(identifier="ENG-1", title="T")
    b = _issue(identifier="ENG-1", title="T")
    assert a == b


def test_different_identifier_not_equal():
    a = _issue(identifier="ENG-1")
    b = _issue(identifier="ENG-2")
    assert a != b
