"""RAG app — retrieval-augmented agent backed by an in-memory vector store."""

from langgraph.graph.state import CompiledStateGraph

from src.domain.agents.config.embeddings_factory import create_embeddings
from src.domain.agents.config.llm_factory import create_llm
from src.domain.agents.core.factory import make_agent
from src.domain.agents.tools.rag_sample_docs import SAMPLE_DOCS
from src.domain.agents.tools.rag import (
    build_vector_store,
    create_retrieval_tool,
)
from src.domain.agents.tools.rag_vector_store import InMemoryVectorStore

# Module-level cache so the store is only built once per process.
_vector_store: InMemoryVectorStore | None = None


async def init_rag_store(custom_docs: list[str] | None = None) -> InMemoryVectorStore:
    """Build and cache an InMemoryVectorStore from sample or custom documents.

    The result is cached globally so repeated calls are free.

    Args:
        custom_docs: Optional list of raw text strings to ingest instead of
            the default SAMPLE_DOCS.

    Returns:
        A populated InMemoryVectorStore instance.
    """
    global _vector_store
    if _vector_store is None:
        embeddings = create_embeddings()
        docs = custom_docs if custom_docs is not None else SAMPLE_DOCS
        _vector_store = await build_vector_store(embeddings=embeddings, documents=docs)
    return _vector_store


def create_rag_app(vector_store: InMemoryVectorStore) -> CompiledStateGraph:
    """Build a RAG agent that searches a pre-built vector store.

    Args:
        vector_store: Populated InMemoryVectorStore to query.

    Returns:
        Compiled agent graph with an ``invoke`` method.
    """
    llm = create_llm()
    retrieval_tool = create_retrieval_tool(vector_store)

    return make_agent(
        name="rag_agent",
        llm=llm,
        tools=[retrieval_tool],
        system=(
            "You are a knowledgeable assistant. "
            "Use the search_knowledge_base tool to find relevant information "
            "before answering questions."
        ),
    )
