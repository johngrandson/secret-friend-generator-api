from enum import Enum

from pydantic import BaseModel, Field


class CategoryEnum(str, Enum):
    santa = "santa"
    chocolate = "chocolate"
    frenemy = "frenemy"
    book = "book"
    wine = "wine"
    easter = "easter"


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=4)
    description: str
    category: CategoryEnum = CategoryEnum.santa


class GroupRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str
    category: CategoryEnum
    link_url: str | None = None
    participants: list["ParticipantBase"] = []


class GroupList(BaseModel):
    groups: list[GroupRead] = Field(default_factory=list)


# Deferred import to avoid circular dependency
from src.domain.participant.schemas import ParticipantBase  # noqa: E402

GroupRead.model_rebuild()
