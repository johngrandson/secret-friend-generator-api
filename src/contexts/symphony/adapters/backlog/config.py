"""Linear adapter configuration schema."""

from pydantic import BaseModel, ConfigDict, Field


class TrackerConfig(BaseModel):
    """Linear tracker configuration. Validates env-supplied values at boot."""

    model_config = ConfigDict(extra="forbid", strict=True)

    api_key: str = Field(min_length=1)
    project_slug: str = Field(min_length=1)
    endpoint: str = "https://api.linear.app/graphql"
    active_states: tuple[str, ...] = ("Todo", "In Progress")
    terminal_states: tuple[str, ...] = (
        "Done",
        "Cancelled",
        "Canceled",
        "Duplicate",
        "Closed",
    )
