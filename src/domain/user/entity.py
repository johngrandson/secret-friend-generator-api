"""User entity — domain model with identity and behaviour."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.domain._shared.aggregate_root import AggregateRoot
from src.domain.user.email import Email
from src.domain.user.events import UserCreated, UserDeactivated, UserUpdated


@dataclass
class User(AggregateRoot):
    """Aggregate root representing an application user."""

    email: Email
    name: str
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def deactivate(self) -> None:
        """Mark the user as inactive and collect a UserDeactivated event."""
        if self.is_active:
            self.is_active = False
            self.collect_event(UserDeactivated(user_id=self.id))

    def activate(self) -> None:
        """Re-activate a previously deactivated user."""
        self.is_active = True

    def can_login(self) -> bool:
        """Return True when the user is allowed to authenticate."""
        return self.is_active

    def update_name(self, new_name: str) -> None:
        """Replace the user's display name and collect a UserUpdated event."""
        if not new_name.strip():
            raise ValueError("Name must not be blank.")
        if self.name != new_name:
            self.name = new_name
            self.collect_event(UserUpdated(user_id=self.id))

    @classmethod
    def create(cls, email: Email, name: str) -> "User":
        """Factory method — enforces invariants at construction time."""
        if not name.strip():
            raise ValueError("Name must not be blank.")
        user = cls(email=email, name=name)
        user.collect_event(
            UserCreated(user_id=user.id, email=str(email), name=name)
        )
        return user
