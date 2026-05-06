"""Integration tests for SQLAlchemyPlanRepository against SQLite in-memory."""

from uuid import uuid4

import pytest

from src.contexts.symphony.adapters.persistence.plan.repository import SQLAlchemyPlanRepository
from src.contexts.symphony.adapters.persistence.run.repository import SQLAlchemyRunRepository
from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.domain.run.entity import Run


async def _save_run(session) -> Run:
    repo = SQLAlchemyRunRepository(session)
    run = Run.create(issue_id="ISSUE-PLAN")
    return await repo.save(run)


def _make_plan(run_id, version: int = 1, content: str = "plan content") -> Plan:
    return Plan.create(run_id=run_id, version=version, content=content)


async def test_save_and_find_by_id(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemyPlanRepository(async_session)
    plan = _make_plan(run.id)

    saved = await repo.save(plan)
    found = await repo.find_by_id(saved.id)

    assert found is not None
    assert found.id == saved.id
    assert found.run_id == run.id
    assert found.version == 1


async def test_find_by_id_returns_none_when_missing(async_session):
    repo = SQLAlchemyPlanRepository(async_session)

    result = await repo.find_by_id(uuid4())

    assert result is None


async def test_find_latest_for_run(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemyPlanRepository(async_session)
    await repo.save(_make_plan(run.id, version=1))
    await repo.save(_make_plan(run.id, version=2))
    await repo.save(_make_plan(run.id, version=3))

    latest = await repo.find_latest_for_run(run.id)

    assert latest is not None
    assert latest.version == 3


async def test_find_latest_for_run_returns_none_when_empty(async_session):
    repo = SQLAlchemyPlanRepository(async_session)

    result = await repo.find_latest_for_run(uuid4())

    assert result is None


async def test_list_by_run(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemyPlanRepository(async_session)
    await repo.save(_make_plan(run.id, version=1))
    await repo.save(_make_plan(run.id, version=2))

    plans = await repo.list_by_run(run.id)

    assert len(plans) == 2
    assert [p.version for p in plans] == [1, 2]


async def test_list_by_run_excludes_other_runs(async_session):
    run_a = await _save_run(async_session)
    run_b = await _save_run(async_session)
    repo = SQLAlchemyPlanRepository(async_session)
    await repo.save(_make_plan(run_a.id, version=1))
    await repo.save(_make_plan(run_b.id, version=1))

    plans = await repo.list_by_run(run_a.id)

    assert len(plans) == 1
    assert plans[0].run_id == run_a.id


async def test_update_persists_approval(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemyPlanRepository(async_session)
    plan = _make_plan(run.id)
    saved = await repo.save(plan)

    saved.approve(by="reviewer@example.com")
    updated = await repo.update(saved)

    assert updated.approved_by == "reviewer@example.com"
    assert updated.approved_at is not None
    assert updated.rejection_reason is None


async def test_update_persists_rejection(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemyPlanRepository(async_session)
    plan = _make_plan(run.id)
    saved = await repo.save(plan)

    saved.reject(reason="Needs more detail.")
    updated = await repo.update(saved)

    assert updated.rejection_reason == "Needs more detail."
    assert updated.approved_at is None


async def test_update_rejects_second_verdict(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemyPlanRepository(async_session)
    plan = _make_plan(run.id)
    saved = await repo.save(plan)

    # Apply first verdict
    saved.approve(by="first@example.com")
    approved = await repo.update(saved)

    # The entity enforces write-once: reject() raises immediately on an already-decided plan
    with pytest.raises(ValueError, match="already has a verdict"):
        approved.reject(reason="Oops")


async def test_update_raises_when_plan_not_found(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemyPlanRepository(async_session)
    # Build a valid plan entity but never persist it — update must raise
    detached = Plan.create(run_id=run.id, version=99, content="never saved")

    with pytest.raises(ValueError, match="Verdict already applied"):
        await repo.update(detached)
