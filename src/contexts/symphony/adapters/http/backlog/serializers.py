"""Serialization helpers — Issue → JSON-serialisable dict."""

from src.contexts.symphony.domain.backlog.issue import Issue


def to_issue_output(issue: Issue) -> dict:
    """Serialize an Issue VO to a plain dict for JSON responses."""
    return {
        "identifier": issue.identifier,
        "title": issue.title,
        "description": issue.description,
        "priority": issue.priority.name,
        "state": issue.state,
        "branch_name": issue.branch_name,
        "labels": list(issue.labels),
        "url": issue.url,
        "created_at": issue.created_at.isoformat(),
        "updated_at": (
            issue.updated_at.isoformat() if issue.updated_at else None
        ),
        "blocked_by": list(issue.blocked_by),
    }
