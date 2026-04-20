from unittest.mock import patch

from langchain_openai import ChatOpenAI

import src.domain.agents.config.llm_factory as mod


def test_create_llm_returns_chat_openai() -> None:
    with (
        patch.object(mod.settings, "OPENAI_API_KEY", "sk-test"),
        patch.object(mod.settings, "LLM_MODEL", "gpt-4o-mini"),
        patch.object(mod.settings, "LLM_TEMPERATURE", 0.0),
    ):
        llm = mod.create_llm()
        assert isinstance(llm, ChatOpenAI)


def test_create_llm_uses_defaults() -> None:
    with (
        patch.object(mod.settings, "OPENAI_API_KEY", "sk-test"),
        patch.object(mod.settings, "LLM_MODEL", "gpt-4o-mini"),
        patch.object(mod.settings, "LLM_TEMPERATURE", 0.0),
    ):
        llm = mod.create_llm()
        assert llm.model_name == "gpt-4o-mini"
        assert llm.temperature == 0.0


def test_create_llm_respects_model_override() -> None:
    with (
        patch.object(mod.settings, "OPENAI_API_KEY", "sk-test"),
        patch.object(mod.settings, "LLM_MODEL", "gpt-4o-mini"),
        patch.object(mod.settings, "LLM_TEMPERATURE", 0.0),
    ):
        llm = mod.create_llm(model="gpt-4o")
        assert llm.model_name == "gpt-4o"


def test_create_llm_respects_temperature_override() -> None:
    with (
        patch.object(mod.settings, "OPENAI_API_KEY", "sk-test"),
        patch.object(mod.settings, "LLM_MODEL", "gpt-4o-mini"),
        patch.object(mod.settings, "LLM_TEMPERATURE", 0.0),
    ):
        llm = mod.create_llm(temperature=0.9)
        assert llm.temperature == 0.9
