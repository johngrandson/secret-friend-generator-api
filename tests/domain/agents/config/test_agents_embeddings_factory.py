from unittest.mock import patch

from langchain_openai import OpenAIEmbeddings

import src.domain.agents.config.agents_embeddings_factory as mod


def test_create_embeddings_returns_openai_embeddings() -> None:
    with patch.object(mod.settings, "OPENAI_API_KEY", "sk-test"):
        result = mod.create_embeddings()
        assert isinstance(result, OpenAIEmbeddings)


def test_create_embeddings_uses_default_model() -> None:
    with patch.object(mod.settings, "OPENAI_API_KEY", "sk-test"):
        result = mod.create_embeddings()
        assert result.model == mod.DEFAULT_EMBEDDING_MODEL


def test_create_embeddings_respects_model_override() -> None:
    with patch.object(mod.settings, "OPENAI_API_KEY", "sk-test"):
        result = mod.create_embeddings(model="text-embedding-3-large")
        assert result.model == "text-embedding-3-large"


def test_default_embedding_model_constant() -> None:
    assert mod.DEFAULT_EMBEDDING_MODEL == "text-embedding-3-small"
