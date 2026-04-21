"""Pydantic schemas for the agents API layer."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class MessageInput(BaseModel):
    role: str
    content: str


class InvokeBody(BaseModel):
    messages: list[MessageInput] = Field(default_factory=list)
    thread_id: str = "default"


class ResumeBody(BaseModel):
    thread_id: str = "default"
    decision: str


class InvokeResponse(BaseModel):
    messages: list[dict[str, Any]]
    structured_response: dict[str, Any] | None = None
    last_message: str | None = None


class StreamEvent(BaseModel):
    type: Literal["token", "message", "done", "error"]
    content: str | dict[str, Any] | None = None
    node: str | None = None


class ThreadStateResponse(BaseModel):
    values: dict[str, Any] | None
    next: list[str]
    tasks: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    apps: list[str]
    mcp_tools_loaded: int
