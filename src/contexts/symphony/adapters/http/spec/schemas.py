"""Pydantic request/response schemas for the Spec HTTP boundary."""

from uuid import UUID

from pydantic import BaseModel


class CreateSpecInput(BaseModel):
    run_id: UUID
    version: int
    content: str


class ApproveSpecInput(BaseModel):
    approved_by: str


class RejectSpecInput(BaseModel):
    reason: str
