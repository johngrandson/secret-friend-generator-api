"""Application settings loaded from environment / .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    ENV: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


def get_settings() -> Settings:
    """Return the global Settings instance (used by DI container)."""
    return settings
