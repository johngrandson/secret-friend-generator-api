import math
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Cosine similarity in [-1, 1], or 0.0 if either vector is zero-length.
    """
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryVectorStore:
    """Simple in-memory vector store backed by cosine similarity search.

    Args:
        embeddings: LangChain Embeddings implementation used to embed text.
    """

    def __init__(self, embeddings: Embeddings) -> None:
        self._chunks: list[dict[str, Any]] = []
        self._embeddings = embeddings

    async def add_documents(self, docs: list[Document]) -> None:
        """Embed and store a list of documents.

        Args:
            docs: Documents whose page_content will be embedded and stored.
        """
        texts = [d.page_content for d in docs]
        vectors = await self._embeddings.embed_documents(texts)
        for i, doc in enumerate(docs):
            self._chunks.append(
                {
                    "content": texts[i],
                    "embedding": vectors[i],
                    "metadata": doc.metadata,
                }
            )

    async def search(self, query: str, k: int = 4) -> list[str]:
        """Return the top-k most similar document contents for a query.

        Args:
            query: Query string to embed and compare against stored chunks.
            k: Maximum number of results to return.

        Returns:
            List of content strings ordered by descending similarity.
        """
        if not self._chunks:
            return []
        query_vec = await self._embeddings.embed_query(query)
        scored = [
            (c["content"], _cosine_similarity(query_vec, c["embedding"]))
            for c in self._chunks
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [content for content, _ in scored[:k]]

    @property
    def size(self) -> int:
        """Number of stored chunks."""
        return len(self._chunks)
