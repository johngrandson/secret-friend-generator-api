from langchain_openai import ChatOpenAI

from src.shared.app_config import settings


def create_llm(
    model: str | None = None,
    temperature: float | None = None,
) -> ChatOpenAI:
    """Create a ChatOpenAI instance using env defaults or explicit overrides.

    Args:
        model: Model name to use. Defaults to LLM_MODEL env var.
        temperature: Sampling temperature. Defaults to LLM_TEMPERATURE env var.

    Returns:
        Configured ChatOpenAI instance.
    """
    default_temp = settings.LLM_TEMPERATURE
    effective_temp = temperature if temperature is not None else default_temp
    return ChatOpenAI(
        model=model or settings.LLM_MODEL,
        temperature=effective_temp,
        api_key=settings.OPENAI_API_KEY or None,
    )
