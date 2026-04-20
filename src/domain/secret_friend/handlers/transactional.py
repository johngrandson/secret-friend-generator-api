"""Secret friend transactional handlers.

Errors propagate, rolling back the transaction.
"""


def register_transactional() -> None:
    """Connect secret friend transactional handlers to their signals."""
