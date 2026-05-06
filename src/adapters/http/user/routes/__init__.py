"""Import each route module so decorators register on the shared router."""

from src.adapters.http.user.routes import create, delete, get, list, update

__all__ = ["create", "delete", "get", "list", "update"]
