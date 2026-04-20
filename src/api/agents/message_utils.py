"""Shared helpers for message serialisation used across agent routes."""

from typing import Any


def last_message_content(messages: list[Any]) -> str | None:
    """Extract string content from the last message in the list.

    Handles both dict-style messages and LangChain message objects.
    """
    if not messages:
        return None
    last = messages[-1]
    if isinstance(last, dict):
        return last.get("content")
    return getattr(last, "content", None)


def serialise_message(m: Any) -> dict[str, Any]:
    """Serialise a LangChain message object or plain dict to a dict.

    Uses ``model_dump`` when available (Pydantic v2), falls back to
    ``dict()``, and finally wraps the string representation.
    """
    if isinstance(m, dict):
        return m
    dumper = getattr(m, "model_dump", None) or getattr(m, "dict", None)
    if dumper is not None:
        return dumper()
    return {"content": str(m)}
