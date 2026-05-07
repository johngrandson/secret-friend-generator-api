"""Pure helper to render the workflow execution prompt template.

The template comes from ``workflow.prompt_template`` (operator-supplied
WORKFLOW.md body). We treat it as a ``string.Template`` so unknown
``${var}`` references stay literal (``safe_substitute``) instead of
crashing the run on a typo.

Variables exposed:
    issue_identifier, issue_title, issue_description, issue_state,
    issue_priority, issue_labels, issue_url,
    spec_content, plan_content, attempt
"""

from string import Template
from typing import Any

from src.contexts.symphony.domain.backlog.issue import Issue


def render_run_prompt(
    *,
    template: str,
    issue: Issue,
    spec_content: str,
    plan_content: str,
    attempt: int,
) -> str:
    """Substitute issue + spec/plan content + attempt into ``template``."""
    if attempt < 1:
        raise ValueError("attempt must be >= 1")
    context: dict[str, Any] = {
        "issue_identifier": issue.identifier,
        "issue_title": issue.title,
        "issue_description": issue.description or "(no description provided)",
        "issue_state": issue.state,
        "issue_priority": issue.priority.name,
        "issue_labels": ", ".join(issue.labels) or "(none)",
        "issue_url": issue.url or "(no URL)",
        "spec_content": spec_content.strip(),
        "plan_content": plan_content.strip(),
        "attempt": str(attempt),
    }
    return Template(template).safe_substitute(context)
