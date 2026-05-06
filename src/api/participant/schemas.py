"""Participant API DTOs — Pydantic only at the edge."""

from datetime import datetime

from pydantic import BaseModel, model_validator

from src.domain.participant.value_objects import ParticipantStatus


class ParticipantBase(BaseModel):
    """Minimal projection used by GroupRead to avoid circular imports."""

    model_config = {"from_attributes": True}
    id: int
    name: str


class ParticipantCreate(BaseModel):
    name: str
    group_id: int


class ParticipantRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    group_id: int
    gift_hint: str | None = None
    status: ParticipantStatus = ParticipantStatus.PENDING
    created_at: datetime
    updated_at: datetime | None = None


class ParticipantList(BaseModel):
    participants: list[ParticipantRead]


class ParticipantUpdate(BaseModel):
    name: str | None = None
    gift_hint: str | None = None
    status: ParticipantStatus | None = None

    @model_validator(mode="before")
    @classmethod
    def at_least_one_field(cls, data: object) -> object:
        if isinstance(data, dict) and all(v is None for v in data.values()):
            raise ValueError("At least one field must be provided")
        return data
