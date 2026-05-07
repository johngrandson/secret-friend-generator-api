"""Pydantic request schemas for the Organization HTTP boundary."""

from uuid import UUID

from pydantic import BaseModel

from src.contexts.tenancy.domain.role.value_objects import Role


class CreateOrganizationInput(BaseModel):
    name: str
    slug: str
    owner_user_id: UUID


class AddMemberInput(BaseModel):
    user_id: UUID
    role: Role


class ChangeMemberRoleInput(BaseModel):
    role: Role
