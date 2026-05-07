"""SQLAlchemy async implementation of IRunRepository.

Implements IRunRepository structurally (no explicit inheritance).
Protocol structural typing: matching method signatures satisfy the contract.

Note: no session.commit() here — the Unit of Work owns the transaction boundary.
session.flush() stages changes so the UoW commit sees them.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.symphony.domain.run.entity import Run
from src.contexts.symphony.domain.run.status import RunStatus
from src.contexts.symphony.adapters.persistence.run.mapper import to_entity, to_model
from src.contexts.symphony.adapters.persistence.run.model import RunModel


class SQLAlchemyRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, run_id: UUID) -> Run | None:
        result = await self._session.execute(
            select(RunModel).where(RunModel.id == run_id)
        )
        row = result.scalar_one_or_none()
        return to_entity(row) if row else None

    async def find_due_retries(self, now: datetime) -> list[Run]:
        result = await self._session.execute(
            select(RunModel)
            .where(
                RunModel.status == RunStatus.RETRY_PENDING,
                RunModel.next_attempt_at <= now,
            )
            .order_by(RunModel.next_attempt_at)
        )
        return [to_entity(row) for row in result.scalars().all()]

    async def count_active(self) -> int:
        result = await self._session.execute(
            select(func.count()).where(
                RunModel.status.notin_([RunStatus.DONE, RunStatus.FAILED])
            )
        )
        return int(result.scalar_one())

    async def list_active_identifiers(self) -> list[str]:
        result = await self._session.execute(
            select(RunModel.issue_id).where(
                RunModel.status.notin_([RunStatus.DONE, RunStatus.FAILED])
            )
        )
        return [row for row in result.scalars().all()]

    async def list(self, limit: int = 20, offset: int = 0) -> list[Run]:
        result = await self._session.execute(
            select(RunModel)
            .order_by(RunModel.created_at)
            .limit(limit)
            .offset(offset)
        )
        return [to_entity(row) for row in result.scalars().all()]

    async def save(self, run: Run) -> Run:
        model = to_model(run)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return to_entity(model)

    async def update(self, run: Run) -> Run:
        result = await self._session.execute(
            select(RunModel).where(RunModel.id == run.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Run {run.id} not found for update.")
        model.status = str(run.status)
        model.workspace_path = run.workspace_path
        model.attempt = run.attempt
        model.error = run.error
        model.next_attempt_at = run.next_attempt_at
        await self._session.flush()
        await self._session.refresh(model)
        return to_entity(model)

    async def delete(self, run_id: UUID) -> bool:
        count_result = await self._session.execute(
            select(func.count()).where(RunModel.id == run_id)
        )
        exists = bool(count_result.scalar_one() > 0)
        if exists:
            await self._session.execute(
                delete(RunModel).where(RunModel.id == run_id)
            )
            await self._session.flush()
        return exists
