from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from src.shared.app_config import settings

DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"


def create_embeddings(model: str | None = None) -> OpenAIEmbeddings:
    """Create an OpenAIEmbeddings instance using env defaults or an explicit model.

    Args:
        model: Embedding model name. Defaults to DEFAULT_EMBEDDING_MODEL.

    Returns:
        Configured OpenAIEmbeddings instance.
    """
    return OpenAIEmbeddings(
        model=model or DEFAULT_EMBEDDING_MODEL,
        api_key=SecretStr(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None,
    )
