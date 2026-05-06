"""Unit tests verifying Container.wiring_config covers the HTTP adapter packages.

The @inject decorators in each context's deps.py modules only resolve at call
time if the DI framework has been told to wire those packages. A misconfigured
wiring_config would silently pass at import time but fail at the first request.
These tests catch that class of misconfiguration early.
"""

from dependency_injector.containers import WiringConfiguration

from src.infrastructure.containers import Container


def test_wiring_config_present() -> None:
    """Container.wiring_config must be defined (not None)."""
    assert Container.wiring_config is not None


def test_wiring_config_is_wiring_configuration_instance() -> None:
    """wiring_config must be a dependency_injector WiringConfiguration object."""
    assert isinstance(Container.wiring_config, WiringConfiguration)


def test_wiring_config_includes_identity_http_package() -> None:
    """Identity HTTP adapters package must be listed so @inject resolves there."""
    cfg = Container.wiring_config
    packages: list[str] = list(getattr(cfg, "packages", None) or [])
    modules: list[str] = list(getattr(cfg, "modules", None) or [])
    all_targets = packages + modules
    assert any("identity" in t for t in all_targets), (
        f"Expected 'identity' in wiring packages/modules, got: {all_targets}"
    )


def test_wiring_config_includes_symphony_http_package() -> None:
    """Symphony HTTP adapters package must be listed so @inject resolves there."""
    cfg = Container.wiring_config
    packages: list[str] = list(getattr(cfg, "packages", None) or [])
    modules: list[str] = list(getattr(cfg, "modules", None) or [])
    all_targets = packages + modules
    assert any("symphony" in t for t in all_targets), (
        f"Expected 'symphony' in wiring packages/modules, got: {all_targets}"
    )


def test_wiring_config_targets_http_adapters() -> None:
    """Both HTTP adapter packages must be explicitly present in wiring config."""
    cfg = Container.wiring_config
    packages: list[str] = list(getattr(cfg, "packages", None) or [])
    modules: list[str] = list(getattr(cfg, "modules", None) or [])
    all_targets = packages + modules

    expected = [
        "src.contexts.identity.adapters.http",
        "src.contexts.symphony.adapters.http",
    ]
    for expected_target in expected:
        assert expected_target in all_targets, (
            f"Expected '{expected_target}' in wiring config, got: {all_targets}"
        )
