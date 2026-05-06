"""Pydantic request/response schemas for the User HTTP boundary."""

from typing import Optional

from pydantic import BaseModel, EmailStr


class CreateUserInput(BaseModel):
    email: EmailStr
    name: str


class UpdateUserInput(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
