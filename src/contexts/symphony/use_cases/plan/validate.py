"""Plan content validator — pure function, no I/O.

Verifies the generated ``.symphony/plan.md`` exposes a top-level
``## Phases`` header and at least ``MIN_CHECKBOXES`` unchecked checkbox
items. Same shape contract as the origem ``plan_generator``.
"""

REQUIRED_HEADER = "## Phases"
CHECKBOX_MARKER = "- [ ]"
MIN_CHECKBOXES = 3


class PlanStructureError(Exception):
    """Generated plan content is missing required header or checkboxes."""


def validate_plan_content(content: str) -> None:
    """Raise ``PlanStructureError`` if the plan structure is invalid."""
    if REQUIRED_HEADER not in content:
        raise PlanStructureError(
            f"plan missing required header {REQUIRED_HEADER!r}"
        )
    checkbox_count = content.count(CHECKBOX_MARKER)
    if checkbox_count < MIN_CHECKBOXES:
        raise PlanStructureError(
            f"plan needs ≥{MIN_CHECKBOXES} checkbox items "
            f"({CHECKBOX_MARKER!r}); found {checkbox_count}"
        )
