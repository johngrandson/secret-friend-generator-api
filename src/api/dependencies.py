from src.infrastructure.persistence import get_db

# Re-export get_db for convenience — routes import from here
__all__ = ["get_db"]
