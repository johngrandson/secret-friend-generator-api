"""Application settings loaded from environment / .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    ENV: str = "development"
    LINEAR_API_KEY: str | None = None
    LINEAR_PROJECT_SLUG: str | None = None
    SYMPHONY_WORKFLOW_PATH: str | None = None
    """Path to the WORKFLOW.md whose front matter configures the pipeline.

    Optional at boot: the symphony pipeline use cases (Start/Generate/Execute/
    Gates/OpenPR/Orchestrate/Dispatch) raise at first call when this is unset.
    Read-only endpoints (GET /runs, GET /specs, etc.) work without it.
    """

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


def get_settings() -> Settings:
    """Return the global Settings instance (used by DI container)."""
    return settings
