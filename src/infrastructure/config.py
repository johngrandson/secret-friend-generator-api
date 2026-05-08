"""Application settings loaded from environment / .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app"
    ENV: str = "development"
    SYMPHONY_WORKFLOW_PATH: str | None = None
    """Path to the WORKFLOW.md whose front matter configures the pipeline.

    Optional at boot: the symphony pipeline use cases (Start/Generate/Execute/
    Gates/OpenPR/Orchestrate/Dispatch) raise at first call when this is unset.
    Read-only endpoints (GET /runs, GET /specs, etc.) work without it.

    The workflow YAML carries tracker credentials (``api_key``, ``project_slug``)
    via ``$VAR`` env-var references — ``LINEAR_API_KEY`` and ``LINEAR_PROJECT_SLUG``
    remain in the process env, but are no longer first-class Settings fields.
    """

    CELERY_BROKER_URL: str = "memory://"
    """Broker URL for the Celery worker. ``memory://`` works in-process for
    tests and local smoke (no external Redis/RabbitMQ). Production uses
    ``redis://...`` or ``amqp://...``."""

    CELERY_RESULT_BACKEND: str = "cache+memory://"
    """Result backend. ``cache+memory://`` for tests; production sets to
    ``redis://...``."""

    REDIS_URL: str | None = None
    """Redis URL for the run event bus (real-time agent event streaming).

    When None, the event bus is a no-op and streaming is disabled. In
    production set to the same URL as CELERY_BROKER_URL. In tests the
    default None disables the feature without needing a live server."""

    CELERY_TASK_ALWAYS_EAGER: bool = False
    """When True, tasks execute synchronously in the calling process.
    Pytest fixtures flip this on so the dispatch task runs inside the test
    transaction without spawning a worker."""

    WORKFLOWS_DIR: str = "workflows"
    """Directory scanned by the beat schedule discovery for WORKFLOW.md
    files. Each file produces one ``symphony.dispatch_tick`` schedule
    entry whose period derives from ``PollingConfig.interval_ms``."""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()


def get_settings() -> Settings:
    """Return the global Settings instance (used by DI container)."""
    return settings
