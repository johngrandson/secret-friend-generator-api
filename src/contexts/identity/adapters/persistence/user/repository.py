"""SQLAlchemy async implementation of IUserRepository.

Implements IUserRepository structurally (no explicit inheritance).
Protocol structural typing: matching method signatures satisfy the contract.

Note: no session.commit() here — the Unit of Work owns the transaction boundary.
session.flush() stages changes so the UoW commit sees them.
"""

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.identity.domain.user.email import Email
from src.contexts.identity.domain.user.entity import User
from src.contexts.identity.adapters.persistence.user.mapper import to_entity, to_model
from src.contexts.identity.adapters.persistence.user.model import UserModel


class SQLAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        row = result.scalar_one_or_none()
        return to_entity(row) if row else None

    async def find_by_email(self, email: Email) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == str(email))
        )
        row = result.scalar_one_or_none()
        return to_entity(row) if row else None

    async def list(self, limit: int = 20, offset: int = 0) -> list[User]:
        result = await self._session.execute(
            select(UserModel).order_by(UserModel.created_at).limit(limit).offset(offset)
        )
        return [to_entity(row) for row in result.scalars().all()]

    async def save(self, user: User) -> User:
        model = to_model(user)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return to_entity(model)

    async def update(self, user: User) -> User:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"User {user.id} not found for update.")
        model.name = user.name
        model.is_active = user.is_active
        await self._session.flush()
        await self._session.refresh(model)
        return to_entity(model)

    async def delete(self, user_id: UUID) -> bool:
        count_result = await self._session.execute(
            select(func.count()).where(UserModel.id == user_id)
        )
        exists = bool(count_result.scalar_one() > 0)
        if exists:
            await self._session.execute(
                delete(UserModel).where(UserModel.id == user_id)
            )
            await self._session.flush()
        return exists
