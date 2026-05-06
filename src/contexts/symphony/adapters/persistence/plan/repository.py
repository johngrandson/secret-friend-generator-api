"""SQLAlchemy async implementation of IPlanRepository.

Implements IPlanRepository structurally (no explicit inheritance).
Protocol structural typing: matching method signatures satisfy the contract.

Note: no session.commit() here — the Unit of Work owns the transaction boundary.
session.flush() stages changes so the UoW commit sees them.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.symphony.domain.plan.entity import Plan
from src.contexts.symphony.adapters.persistence.plan.mapper import to_entity, to_model
from src.contexts.symphony.adapters.persistence.plan.model import PlanModel


class SQLAlchemyPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, plan_id: UUID) -> Plan | None:
        result = await self._session.execute(
            select(PlanModel).where(PlanModel.id == plan_id)
        )
        row = result.scalar_one_or_none()
        return to_entity(row) if row else None

    async def find_latest_for_run(self, run_id: UUID) -> Plan | None:
        result = await self._session.execute(
            select(PlanModel)
            .where(PlanModel.run_id == run_id)
            .order_by(PlanModel.version.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return to_entity(row) if row else None

    async def list_by_run(self, run_id: UUID) -> list[Plan]:
        result = await self._session.execute(
            select(PlanModel)
            .where(PlanModel.run_id == run_id)
            .order_by(PlanModel.version)
        )
        return [to_entity(row) for row in result.scalars().all()]

    async def save(self, plan: Plan) -> Plan:
        model = to_model(plan)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return to_entity(model)

    async def update(self, plan: Plan) -> Plan:
        result = await self._session.execute(
            select(PlanModel).where(
                PlanModel.id == plan.id,
                PlanModel.approved_at.is_(None),
                PlanModel.rejection_reason.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Verdict already applied for plan {plan.id}")
        model.approved_at = plan.approved_at
        model.approved_by = plan.approved_by
        model.rejection_reason = plan.rejection_reason
        await self._session.flush()
        await self._session.refresh(model)
        return to_entity(model)
