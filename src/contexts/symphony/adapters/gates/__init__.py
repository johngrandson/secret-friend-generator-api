"""Concrete ``Gate`` implementations for the symphony harness.

Add new gates as siblings; each must extend
``src.shared.agentic.gate.Gate`` and declare a unique
``GateName``. Wired into :class:`GateRunner` via DI.
"""

from src.contexts.symphony.adapters.gates.ci import CIGate

__all__ = ["CIGate"]
