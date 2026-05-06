"""Pydantic request/response schemas for the Plan HTTP boundary."""

from uuid import UUID

from pydantic import BaseModel


class CreatePlanInput(BaseModel):
    run_id: UUID
    version: int
    content: str


class ApprovePlanInput(BaseModel):
    approved_by: str


class RejectPlanInput(BaseModel):
    reason: str
