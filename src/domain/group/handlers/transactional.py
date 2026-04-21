"""Group transactional handlers — errors propagate, rolling back the transaction."""


def register_transactional() -> None:
    """Connect group transactional handlers to their signals."""
