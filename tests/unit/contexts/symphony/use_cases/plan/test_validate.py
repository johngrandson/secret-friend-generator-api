"""Unit tests for the plan content validator."""

import pytest

from src.contexts.symphony.use_cases.plan.validate import (
    PlanStructureError,
    validate_plan_content,
)

VALID_PLAN = """
## Phases

### Phase 1: setup
**Goal:** scaffold

- [ ] add foo.py
- [ ] add bar.py
- [ ] wire deps
"""


def test_validate_plan_content_accepts_minimal_valid_plan() -> None:
    validate_plan_content(VALID_PLAN)


def test_validate_plan_content_rejects_missing_phases_header() -> None:
    bad = VALID_PLAN.replace("## Phases", "## OtherHeader")
    with pytest.raises(PlanStructureError, match="Phases"):
        validate_plan_content(bad)


def test_validate_plan_content_rejects_too_few_checkboxes() -> None:
    bad = """
## Phases

### Phase 1
- [ ] only one
- [ ] two
"""
    with pytest.raises(PlanStructureError, match="≥3"):
        validate_plan_content(bad)


def test_validate_plan_content_rejects_no_checkboxes() -> None:
    bad = "## Phases\nno checkboxes here"
    with pytest.raises(PlanStructureError):
        validate_plan_content(bad)
