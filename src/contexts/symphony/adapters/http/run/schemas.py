"""Pydantic request/response schemas for the Run HTTP boundary."""

from pydantic import BaseModel


class CreateRunInput(BaseModel):
    issue_id: str
