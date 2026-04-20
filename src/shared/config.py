"""Application settings via pydantic-settings.

Reads from environment variables and .env file. Provides typed,
validated configuration with sensible defaults. Equivalent to
Phoenix's config/runtime.exs pattern.
"""
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    PROJECT_NAME: str = "Secret Santa Generator"
    PROJECT_VERSION: str = "1.0.0"
    ENV: str = "local"
    LOG_LEVEL: str = "WARNING"

    # Database
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "tdd"

    # Sentry (optional)
    SENTRY_ENABLED: bool = False
    SENTRY_DSN: str = ""

    # Celery / RabbitMQ
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "rpc://"
    CELERY_TASK_ALWAYS_EAGER: bool = False

    # LLM / MCP
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0
    MCP_SERVERS_PATH: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
