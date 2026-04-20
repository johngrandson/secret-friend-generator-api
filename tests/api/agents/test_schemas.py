"""Tests for agents API schemas."""

import pytest
from pydantic import ValidationError

from src.api.agents.schemas import (
    HealthResponse,
    InvokeBody,
    InvokeResponse,
    MessageInput,
    ResumeBody,
    StreamEvent,
    ThreadStateResponse,
)


# --- MessageInput ---


def test_message_input_stores_role_and_content():
    msg = MessageInput(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"


def test_message_input_requires_role():
    with pytest.raises(ValidationError):
        MessageInput(content="hello")


def test_message_input_requires_content():
    with pytest.raises(ValidationError):
        MessageInput(role="user")


# --- InvokeBody ---


def test_invoke_body_defaults():
    body = InvokeBody()
    assert body.messages == []
    assert body.thread_id == "default"


def test_invoke_body_accepts_messages():
    body = InvokeBody(messages=[{"role": "user", "content": "hi"}], thread_id="t1")
    assert len(body.messages) == 1
    assert body.thread_id == "t1"


# --- ResumeBody ---


def test_resume_body_default_thread_id():
    body = ResumeBody(decision="approve")
    assert body.thread_id == "default"
    assert body.decision == "approve"


def test_resume_body_requires_decision():
    with pytest.raises(ValidationError):
        ResumeBody()


# --- InvokeResponse ---


def test_invoke_response_optional_fields_default_none():
    resp = InvokeResponse(messages=[])
    assert resp.structured_response is None
    assert resp.last_message is None


def test_invoke_response_accepts_all_fields():
    resp = InvokeResponse(
        messages=[{"role": "ai", "content": "done"}],
        structured_response={"key": "val"},
        last_message="done",
    )
    assert resp.last_message == "done"
    assert resp.structured_response == {"key": "val"}


# --- StreamEvent ---


def test_stream_event_token_type():
    event = StreamEvent(type="token", content="hello", node="agent")
    assert event.type == "token"
    assert event.content == "hello"
    assert event.node == "agent"


def test_stream_event_done_type_no_content():
    event = StreamEvent(type="done")
    assert event.content is None
    assert event.node is None


def test_stream_event_invalid_type_raises():
    with pytest.raises(ValidationError):
        StreamEvent(type="unknown")


# --- ThreadStateResponse ---


def test_thread_state_response_allows_none_values():
    resp = ThreadStateResponse(values=None, next=[], tasks=[])
    assert resp.values is None


def test_thread_state_response_stores_data():
    resp = ThreadStateResponse(values={"k": "v"}, next=["node_a"], tasks=[{"id": "1"}])
    assert resp.values == {"k": "v"}
    assert resp.next == ["node_a"]
    assert resp.tasks == [{"id": "1"}]


# --- HealthResponse ---


def test_health_response_stores_fields():
    resp = HealthResponse(status="ok", apps=["supervisor", "swarm"], mcp_tools_loaded=3)
    assert resp.status == "ok"
    assert resp.apps == ["supervisor", "swarm"]
    assert resp.mcp_tools_loaded == 3


def test_health_response_requires_all_fields():
    with pytest.raises(ValidationError):
        HealthResponse(status="ok")
