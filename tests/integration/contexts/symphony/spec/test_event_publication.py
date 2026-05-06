"""Integration tests for event publication via real SQLAlchemySymphonyUnitOfWork.

These exercise the production path that AsyncMock-based unit tests cannot:
the adapter returns a fresh Spec from `to_entity(model)`, so events MUST be
collected from the input entity (not the repo return value) — see
`docs/event-publication-pattern.md`.

If the use-case regresses to `saved.pull_events()`, these tests fail.
"""

from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.spec.events import SpecApproved, SpecCreated, SpecRejected
from src.contexts.symphony.use_cases.spec.approve import ApproveSpecRequest, ApproveSpecUseCase
from src.contexts.symphony.use_cases.spec.create import CreateSpecRequest, CreateSpecUseCase
from src.contexts.symphony.use_cases.spec.reject import RejectSpecRequest, RejectSpecUseCase


async def _save_run(session) -> Run:
    """Helper: persist a Run directly via flush+commit so the FK exists for specs."""
    from src.contexts.symphony.adapters.persistence.run.mapper import to_model
    run = Run.create(issue_id="ISSUE-EVT-SPEC")
    model = to_model(run)
    session.add(model)
    await session.flush()
    await session.commit()
    return run


async def test_create_spec_publishes_spec_created_event(async_session, fake_publisher):
    run = await _save_run(async_session)
    uow = SQLAlchemySymphonyUnitOfWork(async_session)
    use_case = CreateSpecUseCase(uow=uow, event_publisher=fake_publisher)

    resp = await use_case.execute(
        CreateSpecRequest(run_id=run.id, version=1, content="spec body")
    )

    assert resp.success is True
    created = [e for e in fake_publisher.published if isinstance(e, SpecCreated)]
    assert len(created) == 1
    assert created[0].run_id == run.id
    assert created[0].version == 1


async def test_approve_spec_publishes_spec_approved_event(async_session, fake_publisher):
    run = await _save_run(async_session)
    uow = SQLAlchemySymphonyUnitOfWork(async_session)
    create_uc = CreateSpecUseCase(uow=uow, event_publisher=fake_publisher)
    approve_uc = ApproveSpecUseCase(uow=uow, event_publisher=fake_publisher)

    create_resp = await create_uc.execute(
        CreateSpecRequest(run_id=run.id, version=1, content="spec body")
    )
    fake_publisher.published.clear()  # discard the create event

    approve_resp = await approve_uc.execute(
        ApproveSpecRequest(
            spec_id=create_resp.spec.id, approved_by="reviewer@example.com"
        )
    )

    assert approve_resp.success is True
    approved = [e for e in fake_publisher.published if isinstance(e, SpecApproved)]
    assert len(approved) == 1
    assert approved[0].spec_id == create_resp.spec.id
    assert approved[0].approved_by == "reviewer@example.com"


async def test_reject_spec_publishes_spec_rejected_event(async_session, fake_publisher):
    run = await _save_run(async_session)
    uow = SQLAlchemySymphonyUnitOfWork(async_session)
    create_uc = CreateSpecUseCase(uow=uow, event_publisher=fake_publisher)
    reject_uc = RejectSpecUseCase(uow=uow, event_publisher=fake_publisher)

    create_resp = await create_uc.execute(
        CreateSpecRequest(run_id=run.id, version=1, content="spec body")
    )
    fake_publisher.published.clear()  # discard the create event

    reject_resp = await reject_uc.execute(
        RejectSpecRequest(
            spec_id=create_resp.spec.id, reason="Insufficient detail."
        )
    )

    assert reject_resp.success is True
    rejected = [e for e in fake_publisher.published if isinstance(e, SpecRejected)]
    assert len(rejected) == 1
    assert rejected[0].spec_id == create_resp.spec.id
    assert rejected[0].reason == "Insufficient detail."
