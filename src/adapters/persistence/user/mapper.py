"""Mapping functions between User domain entity and UserModel ORM row."""

from src.domain.user.entity import User
from src.domain.user.email import Email
from src.adapters.persistence.user.model import UserModel


def to_entity(model: UserModel) -> User:
    """Convert a UserModel ORM row to a User domain entity."""
    return User(
        id=model.id,
        email=Email(model.email),
        name=model.name,
        is_active=model.is_active,
        created_at=model.created_at,
    )


def to_model(user: User) -> UserModel:
    """Convert a User domain entity to a UserModel ORM row."""
    return UserModel(
        id=user.id,
        email=str(user.email),
        name=user.name,
        is_active=user.is_active,
        created_at=user.created_at,
    )
