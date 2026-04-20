from unittest.mock import MagicMock

import pytest

from src.domain.agents.tools.rag_sample_docs import SAMPLE_DOCS
from src.domain.agents.tools.rag_tools import (
    build_vector_store,
    create_retrieval_tool,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_embeddings(dim: int = 4) -> MagicMock:
    """Return mock Embeddings that produce deterministic unit vectors."""
    call_count = 0

    def fake_embed_documents(texts: list[str]) -> list[list[float]]:
        nonlocal call_count
        result = []
        for i, _ in enumerate(texts):
            vec = [0.0] * dim
            vec[(call_count + i) % dim] = 1.0
            result.append(vec)
        call_count += len(texts)
        return result

    def fake_embed_query(text: str) -> list[float]:
        vec = [0.0] * dim
        vec[0] = 1.0
        return vec

    embeddings = MagicMock()
    embeddings.embed_documents = fake_embed_documents
    embeddings.embed_query = fake_embed_query
    return embeddings


# ---------------------------------------------------------------------------
# build_vector_store tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_vector_store_has_positive_size() -> None:
    embeddings = _make_embeddings()
    store = await build_vector_store(embeddings, SAMPLE_DOCS)
    assert store.size > 0


@pytest.mark.asyncio
async def test_build_vector_store_with_custom_chunk_size() -> None:
    embeddings = _make_embeddings()
    store_small = await build_vector_store(
        embeddings, SAMPLE_DOCS, chunk_size=100, chunk_overlap=10
    )
    embeddings2 = _make_embeddings()
    store_large = await build_vector_store(
        embeddings2, SAMPLE_DOCS, chunk_size=1000, chunk_overlap=0
    )
    # smaller chunks produce more documents
    assert store_small.size >= store_large.size


@pytest.mark.asyncio
async def test_build_vector_store_single_document() -> None:
    embeddings = _make_embeddings()
    store = await build_vector_store(
        embeddings, ["Short text."], chunk_size=500, chunk_overlap=0
    )
    assert store.size >= 1


# ---------------------------------------------------------------------------
# create_retrieval_tool tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retrieval_tool_returns_string() -> None:
    embeddings = _make_embeddings()
    store = await build_vector_store(embeddings, SAMPLE_DOCS)
    tool = create_retrieval_tool(store)
    result = await tool.ainvoke({"query": "LangGraph", "k": 2})
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_retrieval_tool_formats_numbered_results() -> None:
    embeddings = _make_embeddings()
    store = await build_vector_store(embeddings, SAMPLE_DOCS)
    tool = create_retrieval_tool(store)
    result = await tool.ainvoke({"query": "RAG retrieval", "k": 3})
    assert "[1]" in result
    assert "[2]" in result


@pytest.mark.asyncio
async def test_retrieval_tool_empty_store_returns_not_found() -> None:
    from src.domain.agents.tools.rag_vector_store import InMemoryVectorStore

    embeddings = MagicMock()
    embeddings.embed_documents = MagicMock(return_value=[])
    embeddings.embed_query = MagicMock(return_value=[1.0, 0.0])

    store = InMemoryVectorStore(embeddings)
    tool = create_retrieval_tool(store)
    result = await tool.ainvoke({"query": "anything"})
    assert result == "No relevant documents found."


@pytest.mark.asyncio
async def test_retrieval_tool_respects_k_parameter() -> None:
    embeddings = _make_embeddings(dim=8)
    store = await build_vector_store(
        embeddings, SAMPLE_DOCS, chunk_size=200, chunk_overlap=0
    )
    tool = create_retrieval_tool(store)
    result_k1 = await tool.ainvoke({"query": "supervisor", "k": 1})
    result_k3 = await tool.ainvoke({"query": "supervisor", "k": 3})
    # k=1 must not contain [2], k=3 must
    assert "[2]" not in result_k1
    assert "[2]" in result_k3
