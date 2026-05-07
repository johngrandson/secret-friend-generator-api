"""Pure helper to render a Markdown PR body from run artifacts.

The output is purely a function of its inputs — no I/O, no clocks, no
randomness — so it's trivially testable. The PR body collects the
artifacts a reviewer needs in one place: issue context, approved spec,
approved plan, gate results table, and aggregated token usage.

Per-gate output is already capped at 5000 chars by ``GateResult.__post_init__``
in the domain layer; the builder echoes the value verbatim.
"""

from collections.abc import Iterable

from src.contexts.symphony.domain.backlog.issue import Issue
from src.contexts.symphony.domain.gate_result.value_object import GateResult
from src.shared.agentic.agent_runner import TokenUsage
from src.shared.agentic.gate import GateStatus


def build_pr_body(
    *,
    issue: Issue,
    spec_content: str,
    plan_content: str,
    gate_results: list[GateResult],
    total_usage: TokenUsage,
    model: str,
) -> str:
    """Render the canonical agent-PR body.

    Returns Markdown ready to feed into ``gh pr create --body-file -``.
    """
    rows = "\n".join(
        f"| {r.gate_name} | {r.status.value} | {r.duration_ms} |"
        for r in gate_results
    ) or "| — | — | — |"

    failing_outputs = "\n\n".join(
        f"### {r.gate_name} ({r.status.value})\n```\n{r.output}\n```"
        for r in gate_results
        if r.status == GateStatus.FAILED and r.output
    )

    issue_desc = issue.description or "(no description provided)"
    sections: list[str] = [
        f"## Issue\n**{issue.identifier}**: {issue.title}\n\n{issue_desc}",
        f"## Approved Spec\n```markdown\n{spec_content.strip()}\n```",
        f"## Approved Plan\n```markdown\n{plan_content.strip()}\n```",
        (
            "## Gate Results\n"
            "| Gate | Status | Duration (ms) |\n"
            "|------|--------|---------------|\n"
            f"{rows}"
        ),
    ]
    if failing_outputs:
        sections.append("## Failed Gate Output\n" + failing_outputs)
    sections.append(
        "## Token Usage\n"
        f"- Input: {total_usage.input_tokens}\n"
        f"- Output: {total_usage.output_tokens}\n"
        f"- Total: {total_usage.total_tokens}\n"
        f"- Model: {model}"
    )
    return "\n\n".join(sections) + "\n"


def sum_token_usage(usages: Iterable[TokenUsage]) -> TokenUsage:
    """Aggregate token usage across multiple agent sessions."""
    input_tokens = output_tokens = total_tokens = 0
    for u in usages:
        input_tokens += u.input_tokens
        output_tokens += u.output_tokens
        total_tokens += u.total_tokens
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )


