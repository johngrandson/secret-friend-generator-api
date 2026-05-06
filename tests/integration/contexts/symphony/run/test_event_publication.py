"""Integration tests for event publication via real SQLAlchemySymphonyUnitOfWork.

These exercise the production path that AsyncMock-based unit tests cannot:
the adapter returns a fresh Run from `to_entity(model)`, so events MUST be
collected from the input entity (not the repo return value) — see
`docs/event-publication-pattern.md`.

If the use-case regresses to `saved.pull_events()`, these tests fail.
"""

from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.contexts.symphony.domain.run.events import RunStarted
from src.contexts.symphony.use_cases.run.create import CreateRunRequest, CreateRunUseCase


async def test_create_run_publishes_run_started_event(async_session, fake_publisher):
    uow = SQLAlchemySymphonyUnitOfWork(async_session)
    use_case = CreateRunUseCase(uow=uow, event_publisher=fake_publisher)

    resp = await use_case.execute(CreateRunRequest(issue_id="ISSUE-99"))

    assert resp.success is True
    started = [e for e in fake_publisher.published if isinstance(e, RunStarted)]
    assert len(started) == 1
    assert started[0].issue_id == "ISSUE-99"
