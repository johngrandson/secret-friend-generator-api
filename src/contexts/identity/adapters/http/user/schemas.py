"""Pydantic request/response schemas for the User HTTP boundary."""

from pydantic import BaseModel, EmailStr


class CreateUserInput(BaseModel):
    email: EmailStr
    name: str


class UpdateUserInput(BaseModel):
    name: str | None = None
    is_active: bool | None = None
