from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from src.shared.app_config import settings


def create_llm(
    model: str | None = None,
    temperature: float | None = None,
) -> ChatOpenAI:
    """Create a ChatOpenAI instance using env defaults or explicit overrides.

    Args:
        model: Model name to use. Defaults to LLM_MODEL env var.
        temperature: Sampling temperature. Defaults to 0.7.

    Returns:
        Configured ChatOpenAI instance.
    """
    
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")
    
    return ChatOpenAI(
        model=model or settings.LLM_MODEL,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        api_key=SecretStr(settings.OPENAI_API_KEY),
    )
