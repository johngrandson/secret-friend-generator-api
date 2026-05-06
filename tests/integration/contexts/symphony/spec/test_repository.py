"""Integration tests for SQLAlchemySpecRepository against SQLite in-memory."""

from uuid import uuid4

import pytest

from src.contexts.symphony.adapters.persistence.run.repository import SQLAlchemyRunRepository
from src.contexts.symphony.adapters.persistence.spec.repository import SQLAlchemySpecRepository
from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.spec.entity import Spec


async def _save_run(session) -> Run:
    repo = SQLAlchemyRunRepository(session)
    run = Run.create(issue_id="ISSUE-SPEC")
    return await repo.save(run)


def _make_spec(run_id, version: int = 1, content: str = "spec content") -> Spec:
    return Spec.create(run_id=run_id, version=version, content=content)


async def test_save_and_find_by_id(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemySpecRepository(async_session)
    spec = _make_spec(run.id)

    saved = await repo.save(spec)
    found = await repo.find_by_id(saved.id)

    assert found is not None
    assert found.id == saved.id
    assert found.run_id == run.id
    assert found.version == 1


async def test_find_by_id_returns_none_when_missing(async_session):
    repo = SQLAlchemySpecRepository(async_session)

    result = await repo.find_by_id(uuid4())

    assert result is None


async def test_find_latest_for_run(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemySpecRepository(async_session)
    await repo.save(_make_spec(run.id, version=1))
    await repo.save(_make_spec(run.id, version=2))
    await repo.save(_make_spec(run.id, version=3))

    latest = await repo.find_latest_for_run(run.id)

    assert latest is not None
    assert latest.version == 3


async def test_find_latest_for_run_returns_none_when_empty(async_session):
    repo = SQLAlchemySpecRepository(async_session)

    result = await repo.find_latest_for_run(uuid4())

    assert result is None


async def test_list_by_run(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemySpecRepository(async_session)
    await repo.save(_make_spec(run.id, version=1))
    await repo.save(_make_spec(run.id, version=2))

    specs = await repo.list_by_run(run.id)

    assert len(specs) == 2
    assert [s.version for s in specs] == [1, 2]


async def test_list_by_run_excludes_other_runs(async_session):
    run_a = await _save_run(async_session)
    run_b = await _save_run(async_session)
    repo = SQLAlchemySpecRepository(async_session)
    await repo.save(_make_spec(run_a.id, version=1))
    await repo.save(_make_spec(run_b.id, version=1))

    specs = await repo.list_by_run(run_a.id)

    assert len(specs) == 1
    assert specs[0].run_id == run_a.id


async def test_update_persists_approval(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemySpecRepository(async_session)
    spec = _make_spec(run.id)
    saved = await repo.save(spec)

    saved.approve(by="reviewer@example.com")
    updated = await repo.update(saved)

    assert updated.approved_by == "reviewer@example.com"
    assert updated.approved_at is not None
    assert updated.rejection_reason is None


async def test_update_persists_rejection(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemySpecRepository(async_session)
    spec = _make_spec(run.id)
    saved = await repo.save(spec)

    saved.reject(reason="Needs more detail.")
    updated = await repo.update(saved)

    assert updated.rejection_reason == "Needs more detail."
    assert updated.approved_at is None


async def test_update_rejects_second_verdict(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemySpecRepository(async_session)
    spec = _make_spec(run.id)
    saved = await repo.save(spec)

    # Apply first verdict
    saved.approve(by="first@example.com")
    approved = await repo.update(saved)

    # The entity enforces write-once: reject() raises immediately on an already-decided spec
    with pytest.raises(ValueError, match="already has a verdict"):
        approved.reject(reason="Oops")


async def test_update_raises_when_spec_not_found(async_session):
    run = await _save_run(async_session)
    repo = SQLAlchemySpecRepository(async_session)
    # Build a valid spec entity but never persist it — update must raise
    detached = Spec.create(run_id=run.id, version=99, content="never saved")

    with pytest.raises(ValueError, match="Verdict already applied"):
        await repo.update(detached)
