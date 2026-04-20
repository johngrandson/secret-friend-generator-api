"""Tests for the RAG app."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.domain.agents.apps.rag_app as mod
from tests.domain.agents.apps.conftest import ToolCapableFakeLLM


def _make_fake_embeddings(dim: int = 4) -> MagicMock:
    """Return a mock Embeddings that returns fixed-length vectors."""
    embeddings = MagicMock()
    embeddings.embed_documents = AsyncMock(
        side_effect=lambda texts: [[float(i)] * dim for i in range(len(texts))]
    )
    embeddings.embed_query = AsyncMock(return_value=[1.0] * dim)
    return embeddings


@pytest.fixture(autouse=True)
def reset_rag_cache() -> None:
    import src.domain.agents.apps.rag_app as rag_mod

    yield
    rag_mod._vector_store = None


@pytest.mark.asyncio
async def test_init_rag_store_populates_store() -> None:
    fake_embeddings = _make_fake_embeddings()
    with patch.object(mod, "create_embeddings", return_value=fake_embeddings):
        store = await mod.init_rag_store()
    assert store.size > 0


@pytest.mark.asyncio
async def test_init_rag_store_uses_custom_docs() -> None:
    fake_embeddings = _make_fake_embeddings()
    custom = ["doc one", "doc two"]
    with patch.object(mod, "create_embeddings", return_value=fake_embeddings):
        store = await mod.init_rag_store(custom_docs=custom)
    assert store.size > 0


def test_create_rag_app_returns_invokable(fake_llm: ToolCapableFakeLLM) -> None:
    mock_store = MagicMock()
    with patch.object(mod, "create_llm", return_value=fake_llm):
        app = mod.create_rag_app(vector_store=mock_store)
    assert callable(getattr(app, "invoke", None))
