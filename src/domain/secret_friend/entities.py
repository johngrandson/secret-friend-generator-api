"""SecretFriend aggregate — pure domain entity with invariant enforcement."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SecretFriend:
    gift_giver_id: int
    gift_receiver_id: int
    id: int | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if self.gift_giver_id == self.gift_receiver_id:
            raise ValueError(
                "Gift giver and gift receiver cannot be the same person."
            )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SecretFriend):
            return False
        return self.id is not None and self.id == other.id

    def __hash__(self) -> int:
        return hash(("SecretFriend", self.id))
