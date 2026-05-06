"""SQLAlchemy async implementation of ISpecRepository.

Implements ISpecRepository structurally (no explicit inheritance).
Protocol structural typing: matching method signatures satisfy the contract.

Note: no session.commit() here — the Unit of Work owns the transaction boundary.
session.flush() stages changes so the UoW commit sees them.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.symphony.domain.spec.entity import Spec
from src.contexts.symphony.adapters.persistence.spec.mapper import to_entity, to_model
from src.contexts.symphony.adapters.persistence.spec.model import SpecModel


class SQLAlchemySpecRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, spec_id: UUID) -> Spec | None:
        result = await self._session.execute(
            select(SpecModel).where(SpecModel.id == spec_id)
        )
        row = result.scalar_one_or_none()
        return to_entity(row) if row else None

    async def find_latest_for_run(self, run_id: UUID) -> Spec | None:
        result = await self._session.execute(
            select(SpecModel)
            .where(SpecModel.run_id == run_id)
            .order_by(SpecModel.version.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return to_entity(row) if row else None

    async def list_by_run(self, run_id: UUID) -> list[Spec]:
        result = await self._session.execute(
            select(SpecModel)
            .where(SpecModel.run_id == run_id)
            .order_by(SpecModel.version)
        )
        return [to_entity(row) for row in result.scalars().all()]

    async def save(self, spec: Spec) -> Spec:
        model = to_model(spec)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return to_entity(model)

    async def update(self, spec: Spec) -> Spec:
        result = await self._session.execute(
            select(SpecModel).where(
                SpecModel.id == spec.id,
                SpecModel.approved_at.is_(None),
                SpecModel.rejection_reason.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Verdict already applied for spec {spec.id}")
        model.approved_at = spec.approved_at
        model.approved_by = spec.approved_by
        model.rejection_reason = spec.rejection_reason
        await self._session.flush()
        await self._session.refresh(model)
        return to_entity(model)
