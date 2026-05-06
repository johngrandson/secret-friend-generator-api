"""Group value objects — pure domain types, no framework deps."""

from dataclasses import dataclass
from enum import Enum


class CategoryEnum(str, Enum):
    santa = "santa"
    chocolate = "chocolate"
    frenemy = "frenemy"
    book = "book"
    wine = "wine"
    easter = "easter"


@dataclass(frozen=True)
class ParticipantSummary:
    """Minimal participant info embedded in Group aggregate (read projection)."""

    id: int
    name: str
