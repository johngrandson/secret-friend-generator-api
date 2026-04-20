"""Secret friend transactional handlers — errors propagate, rolling back the transaction."""


def register_transactional() -> None:
    """Connect secret friend transactional handlers to their signals."""
