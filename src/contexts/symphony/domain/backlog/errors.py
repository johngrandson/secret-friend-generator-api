"""Backlog adapter error hierarchy — raised by IBacklogAdapter implementations."""


class BacklogAdapterError(Exception):
    """Base error for backlog adapter implementations."""


class BacklogAuthError(BacklogAdapterError):
    """Raised when authentication with the backlog tracker fails."""


class BacklogRateLimitError(BacklogAdapterError):
    """Raised when the backlog tracker rate limit is exceeded."""

    def __init__(
        self, message: str, *, retry_after_seconds: float | None = None
    ) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class BacklogTransportError(BacklogAdapterError):
    """Raised when a network or transport failure occurs."""


class BacklogSchemaError(BacklogAdapterError):
    """Raised when the tracker response payload is malformed or unexpected."""
