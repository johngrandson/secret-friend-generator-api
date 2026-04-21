from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore


def get_checkpointer() -> MemorySaver:
    """Return a new MemorySaver checkpointer instance.

    Returns:
        Fresh MemorySaver for LangGraph thread persistence.
    """
    return MemorySaver()


def get_store() -> InMemoryStore:
    """Return a new InMemoryStore instance.

    Returns:
        Fresh InMemoryStore for cross-thread memory.
    """
    return InMemoryStore()
