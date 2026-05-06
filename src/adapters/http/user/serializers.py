"""Serialization helpers — UserDTO → JSON-serialisable dict."""

from src.use_cases.user.dto import UserDTO


def to_user_output(dto: UserDTO) -> dict:
    """Serialize a UserDTO to a plain dict for JSON responses."""
    return {
        "id": str(dto.id),
        "email": dto.email,
        "name": dto.name,
        "is_active": dto.is_active,
    }
