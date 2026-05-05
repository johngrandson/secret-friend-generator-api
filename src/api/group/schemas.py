"""Group API DTOs — Pydantic only at the edge."""

from pydantic import BaseModel, Field, model_validator

from src.api.participant.schemas import ParticipantBase
from src.domain.group.value_objects import CategoryEnum


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=4)
    description: str
    category: CategoryEnum = CategoryEnum.santa


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: CategoryEnum | None = None

    @model_validator(mode="before")
    @classmethod
    def at_least_one_field(cls, data: object) -> object:
        if isinstance(data, dict) and not any(data.values()):
            raise ValueError("At least one field must be provided")
        return data


class GroupRead(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    name: str
    description: str
    category: CategoryEnum
    link_url: str | None = None
    participants: list[ParticipantBase] = []


class GroupList(BaseModel):
    groups: list[GroupRead] = Field(default_factory=list)
