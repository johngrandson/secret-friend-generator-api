from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document

from src.domain.agents.tools.rag_vector_store import (
    InMemoryVectorStore,
    _cosine_similarity,
)


# ---------------------------------------------------------------------------
# _cosine_similarity unit tests
# ---------------------------------------------------------------------------


def test_cosine_similarity_identical_vectors() -> None:
    v = [1.0, 0.0, 0.0]
    assert _cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors() -> None:
    assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_opposite_vectors() -> None:
    assert _cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_cosine_similarity_zero_vector_returns_zero() -> None:
    assert _cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_embeddings(vectors: list[list[float]]) -> MagicMock:
    """Return a mock Embeddings whose embed_documents returns `vectors`
    and embed_query returns the first vector."""
    embeddings = MagicMock()
    embeddings.embed_documents = MagicMock(return_value=vectors)
    embeddings.embed_query = MagicMock(return_value=vectors[0])
    return embeddings


# ---------------------------------------------------------------------------
# InMemoryVectorStore tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_documents_increments_size() -> None:
    vecs = [[1.0, 0.0], [0.0, 1.0]]
    embeddings = _make_embeddings(vecs)
    store = InMemoryVectorStore(embeddings)
    docs = [Document(page_content="doc a"), Document(page_content="doc b")]
    await store.add_documents(docs)
    assert store.size == 2


@pytest.mark.asyncio
async def test_search_returns_most_similar_first() -> None:
    # doc a: [1,0], doc b: [0,1] — query [1,0] → doc a should rank first
    vecs = [[1.0, 0.0], [0.0, 1.0]]
    embeddings = _make_embeddings(vecs)
    # query vector = [1, 0]
    embeddings.embed_query = MagicMock(return_value=[1.0, 0.0])
    store = InMemoryVectorStore(embeddings)
    docs = [Document(page_content="doc a"), Document(page_content="doc b")]
    await store.add_documents(docs)
    results = await store.search("anything", k=2)
    assert results[0] == "doc a"


@pytest.mark.asyncio
async def test_search_respects_k_limit() -> None:
    vecs = [[1.0, 0.0], [0.9, 0.1], [0.8, 0.2], [0.1, 0.9]]
    embeddings = _make_embeddings(vecs)
    embeddings.embed_query = MagicMock(return_value=[1.0, 0.0])
    store = InMemoryVectorStore(embeddings)
    docs = [Document(page_content=f"doc {i}") for i in range(4)]
    await store.add_documents(docs)
    results = await store.search("q", k=2)
    assert len(results) == 2


@pytest.mark.asyncio
async def test_search_empty_store_returns_empty_list() -> None:
    embeddings = MagicMock()
    store = InMemoryVectorStore(embeddings)
    results = await store.search("query")
    assert results == []


@pytest.mark.asyncio
async def test_add_documents_stores_metadata() -> None:
    vecs = [[1.0, 0.0]]
    embeddings = _make_embeddings(vecs)
    store = InMemoryVectorStore(embeddings)
    doc = Document(page_content="hello", metadata={"source": "test"})
    await store.add_documents([doc])
    assert store._chunks[0]["metadata"] == {"source": "test"}
