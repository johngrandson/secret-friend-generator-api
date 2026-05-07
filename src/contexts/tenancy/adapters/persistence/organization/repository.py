"""SQLAlchemy async implementation of IOrganizationRepository.

Implements IOrganizationRepository structurally. The aggregate root owns
its membership rows: save / update rewrite the full member set inside the
same transaction. The Unit of Work owns commit; this repository only flushes.
"""

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.tenancy.adapters.persistence.organization.mapper import (
    to_entity,
    to_member_models,
    to_org_model,
)
from src.contexts.tenancy.adapters.persistence.organization.model import (
    OrganizationMemberModel,
    OrganizationModel,
)
from src.contexts.tenancy.domain.organization.entity import Organization
from src.contexts.tenancy.domain.organization.value_objects import Slug


class SQLAlchemyOrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, organization_id: UUID) -> Organization | None:
        org_row = (
            await self._session.execute(
                select(OrganizationModel).where(OrganizationModel.id == organization_id)
            )
        ).scalar_one_or_none()
        if org_row is None:
            return None
        member_rows = (
            await self._session.execute(
                select(OrganizationMemberModel).where(
                    OrganizationMemberModel.organization_id == organization_id
                )
            )
        ).scalars().all()
        return to_entity(org_row, member_rows)

    async def find_by_slug(self, slug: Slug) -> Organization | None:
        org_row = (
            await self._session.execute(
                select(OrganizationModel).where(OrganizationModel.slug == str(slug))
            )
        ).scalar_one_or_none()
        if org_row is None:
            return None
        return await self.find_by_id(org_row.id)

    async def list_for_user(self, user_id: UUID) -> list[Organization]:
        org_ids = (
            await self._session.execute(
                select(OrganizationMemberModel.organization_id).where(
                    OrganizationMemberModel.user_id == user_id
                )
            )
        ).scalars().all()
        if not org_ids:
            return []
        org_rows = (
            await self._session.execute(
                select(OrganizationModel)
                .where(OrganizationModel.id.in_(org_ids))
                .order_by(OrganizationModel.created_at)
            )
        ).scalars().all()
        all_member_rows = (
            await self._session.execute(
                select(OrganizationMemberModel).where(
                    OrganizationMemberModel.organization_id.in_(org_ids)
                )
            )
        ).scalars().all()
        members_by_org: dict[UUID, list[OrganizationMemberModel]] = {}
        for row in all_member_rows:
            members_by_org.setdefault(row.organization_id, []).append(row)
        return [to_entity(org, members_by_org.get(org.id, [])) for org in org_rows]

    async def save(self, organization: Organization) -> Organization:
        org_model = to_org_model(organization)
        self._session.add(org_model)
        for member_model in to_member_models(organization):
            self._session.add(member_model)
        await self._session.flush()
        await self._session.refresh(org_model)
        return await self._reload(organization.id) or organization

    async def update(self, organization: Organization) -> Organization:
        org_row = (
            await self._session.execute(
                select(OrganizationModel).where(OrganizationModel.id == organization.id)
            )
        ).scalar_one_or_none()
        if org_row is None:
            raise ValueError(f"Organization {organization.id} not found for update.")
        org_row.name = organization.name
        org_row.slug = str(organization.slug)
        await self._session.execute(
            delete(OrganizationMemberModel).where(
                OrganizationMemberModel.organization_id == organization.id
            )
        )
        for member_model in to_member_models(organization):
            self._session.add(member_model)
        await self._session.flush()
        return await self._reload(organization.id) or organization

    async def delete(self, organization_id: UUID) -> bool:
        exists = bool(
            (
                await self._session.execute(
                    select(func.count()).where(
                        OrganizationModel.id == organization_id
                    )
                )
            ).scalar_one()
            > 0
        )
        if exists:
            await self._session.execute(
                delete(OrganizationModel).where(OrganizationModel.id == organization_id)
            )
            await self._session.flush()
        return exists

    async def _reload(self, organization_id: UUID) -> Organization | None:
        return await self.find_by_id(organization_id)
