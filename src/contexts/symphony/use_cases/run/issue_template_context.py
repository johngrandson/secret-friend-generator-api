"""Shared dictionary builder for issue-driven prompt templates.

The Spec, Plan, and Run prompts each substituted issue fields into a
``string.Template`` using the same shape of context dict. Centralising
the dict shape here means new prompt fields land in one place.
"""

from collections.abc import Mapping
from typing import Any

from src.contexts.symphony.domain.backlog.issue import Issue


def build_issue_template_context(
    issue: Issue,
    *,
    extra: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return the canonical issue-template context dict.

    ``extra`` keys are merged on top — pass ``approved_spec_content`` for
    the plan prompt, or ``spec_content`` / ``plan_content`` / ``attempt``
    for the run prompt.
    """
    context: dict[str, Any] = {
        "issue_identifier": issue.identifier,
        "issue_title": issue.title,
        "issue_state": issue.state,
        "issue_priority": issue.priority.name,
        "issue_labels": ", ".join(issue.labels) or "(none)",
        "issue_url": issue.url or "(no URL)",
        "issue_description": issue.description or "(no description provided)",
    }
    if extra:
        context.update(extra)
    return context
