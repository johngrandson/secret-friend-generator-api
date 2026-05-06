"""Public entry point for the DI container — re-exports the root Container."""

from src.infrastructure.containers.root import Container

__all__ = ["Container"]
