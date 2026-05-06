"""Integration tests for event publication via real SQLAlchemySymphonyUnitOfWork.

These exercise the production path that AsyncMock-based unit tests cannot:
the adapter returns a fresh Plan from `to_entity(model)`, so events MUST be
collected from the input entity (not the repo return value) — see
`docs/event-publication-pattern.md`.

If the use-case regresses to `saved.pull_events()`, these tests fail.
"""

from src.contexts.symphony.adapters.persistence.unit_of_work import (
    SQLAlchemySymphonyUnitOfWork,
)
from src.contexts.symphony.domain.plan.events import PlanApproved, PlanCreated, PlanRejected
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.use_cases.plan.approve import ApprovePlanRequest, ApprovePlanUseCase
from src.contexts.symphony.use_cases.plan.create import CreatePlanRequest, CreatePlanUseCase
from src.contexts.symphony.use_cases.plan.reject import RejectPlanRequest, RejectPlanUseCase


async def _save_run(session) -> Run:
    """Helper: persist a Run directly via flush+commit so the FK exists for plans."""
    from src.contexts.symphony.adapters.persistence.run.mapper import to_model
    run = Run.create(issue_id="ISSUE-EVT-PLAN")
    model = to_model(run)
    session.add(model)
    await session.flush()
    await session.commit()
    return run


async def test_create_plan_publishes_plan_created_event(async_session, fake_publisher):
    run = await _save_run(async_session)
    uow = SQLAlchemySymphonyUnitOfWork(async_session)
    use_case = CreatePlanUseCase(uow=uow, event_publisher=fake_publisher)

    resp = await use_case.execute(
        CreatePlanRequest(run_id=run.id, version=1, content="plan body")
    )

    assert resp.success is True
    created = [e for e in fake_publisher.published if isinstance(e, PlanCreated)]
    assert len(created) == 1
    assert created[0].run_id == run.id
    assert created[0].version == 1


async def test_approve_plan_publishes_plan_approved_event(async_session, fake_publisher):
    run = await _save_run(async_session)
    uow = SQLAlchemySymphonyUnitOfWork(async_session)
    create_uc = CreatePlanUseCase(uow=uow, event_publisher=fake_publisher)
    approve_uc = ApprovePlanUseCase(uow=uow, event_publisher=fake_publisher)

    create_resp = await create_uc.execute(
        CreatePlanRequest(run_id=run.id, version=1, content="plan body")
    )
    fake_publisher.published.clear()  # discard the create event

    approve_resp = await approve_uc.execute(
        ApprovePlanRequest(
            plan_id=create_resp.plan.id, approved_by="reviewer@example.com"
        )
    )

    assert approve_resp.success is True
    approved = [e for e in fake_publisher.published if isinstance(e, PlanApproved)]
    assert len(approved) == 1
    assert approved[0].plan_id == create_resp.plan.id
    assert approved[0].approved_by == "reviewer@example.com"


async def test_reject_plan_publishes_plan_rejected_event(async_session, fake_publisher):
    run = await _save_run(async_session)
    uow = SQLAlchemySymphonyUnitOfWork(async_session)
    create_uc = CreatePlanUseCase(uow=uow, event_publisher=fake_publisher)
    reject_uc = RejectPlanUseCase(uow=uow, event_publisher=fake_publisher)

    create_resp = await create_uc.execute(
        CreatePlanRequest(run_id=run.id, version=1, content="plan body")
    )
    fake_publisher.published.clear()  # discard the create event

    reject_resp = await reject_uc.execute(
        RejectPlanRequest(
            plan_id=create_resp.plan.id, reason="Insufficient detail."
        )
    )

    assert reject_resp.success is True
    rejected = [e for e in fake_publisher.published if isinstance(e, PlanRejected)]
    assert len(rejected) == 1
    assert rejected[0].plan_id == create_resp.plan.id
    assert rejected[0].reason == "Insufficient detail."
