"""Application settings via pydantic-settings.

Reads from environment variables and .env file. Provides typed,
validated configuration with sensible defaults. Equivalent to
Phoenix's config/runtime.exs pattern.
"""

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Queue type choices supported by RabbitMQ.
# - classic: simple, no replication (default, works with single-node RabbitMQ)
# - quorum:  HA, requires a 3-node RabbitMQ cluster
RABBITMQ_QUEUE_TYPES = ("classic", "quorum")


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
    # When True, tasks run synchronously in the same process (useful for tests).
    CELERY_TASK_ALWAYS_EAGER: bool = False

    # RabbitMQ queue type: "classic" (default) or "quorum" (HA, 3-node cluster).
    # Applies to all queues declared by the app factory.
    CELERY_QUEUE_TYPE: str = "classic"

    # Comma-separated list of extra queue names the app should declare.
    # The "default" queue is always declared; list additional ones here.
    # Example: "notifications,heavy"
    CELERY_EXTRA_QUEUES: str = ""

    # JSON mapping of task name → queue name for task routing.
    # Parsed at startup; tasks not listed here go to the default query.
    # Example: '{"notifications.*": "notifications", "heavy.*": "heavy"}'
    # Env var must be a valid JSON object string.
    CELERY_TASK_ROUTES: str = "{}"

    # Recommended worker pool (documented here, passed as --pool CLI flag).
    # Values: prefork | threads | gevent | solo
    # This setting is informational only — the factory does not enforce it.
    # Use: celery worker --pool=$CELERY_WORKER_POOL
    CELERY_WORKER_POOL: str = "prefork"

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
