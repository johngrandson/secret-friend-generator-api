"""Sanity tests for the Settings module and get_settings factory."""

from src.infrastructure.config import Settings, get_settings, settings


def test_get_settings_returns_module_singleton() -> None:
    assert get_settings() is settings


def test_get_settings_returns_settings_instance() -> None:
    result = get_settings()
    assert isinstance(result, Settings)
