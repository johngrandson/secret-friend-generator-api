from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore


def test_get_checkpointer_returns_memory_saver() -> None:
    from src.domain.agents.config.agents_checkpointer import get_checkpointer

    result = get_checkpointer()
    assert isinstance(result, MemorySaver)


def test_get_checkpointer_returns_new_instance_each_call() -> None:
    from src.domain.agents.config.agents_checkpointer import get_checkpointer

    a = get_checkpointer()
    b = get_checkpointer()
    assert a is not b


def test_get_store_returns_in_memory_store() -> None:
    from src.domain.agents.config.agents_checkpointer import get_store

    result = get_store()
    assert isinstance(result, InMemoryStore)


def test_get_store_returns_new_instance_each_call() -> None:
    from src.domain.agents.config.agents_checkpointer import get_store

    a = get_store()
    b = get_store()
    assert a is not b
