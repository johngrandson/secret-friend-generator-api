from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.tools import BaseTool, tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.domain.agents.tools.agents_rag_vector_store import InMemoryVectorStore


async def build_vector_store(
    embeddings: Embeddings,
    documents: list[str],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> InMemoryVectorStore:
    """Chunk raw text documents, embed them, and return a populated vector store.

    Args:
        embeddings: Embeddings implementation used to embed chunks.
        documents: List of raw text strings to ingest.
        chunk_size: Maximum character length per chunk.
        chunk_overlap: Character overlap between consecutive chunks.

    Returns:
        An InMemoryVectorStore loaded with all document chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    docs: list[Document] = []
    for text in documents:
        docs.extend(splitter.create_documents([text]))
    store = InMemoryVectorStore(embeddings)
    await store.add_documents(docs)
    return store


def create_retrieval_tool(vector_store: InMemoryVectorStore) -> BaseTool:
    """Wrap an InMemoryVectorStore in a LangChain async tool.

    Args:
        vector_store: Populated vector store to query.

    Returns:
        An async @tool that searches the knowledge base.
    """

    @tool
    async def search_knowledge_base(query: str, k: int = 4) -> str:
        """Search the knowledge base for relevant information.

        Args:
            query: Natural-language question or keyword query.
            k: Number of top results to return.

        Returns:
            Numbered relevant passages, or a not-found message.
        """
        results = await vector_store.search(query, k)
        if not results:
            return "No relevant documents found."
        return "\n\n".join(f"[{i + 1}] {r}" for i, r in enumerate(results))

    return search_knowledge_base
