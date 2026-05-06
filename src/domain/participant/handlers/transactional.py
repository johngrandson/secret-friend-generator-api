"""Participant transactional handlers — currently empty.

The "reveal participant on assignment" flow used to live here as a signal
handler; it now runs as an explicit `participant_service.update(...)` call
inside `SecretFriendService.assign()` so the cross-domain coordination is
visible at the call site instead of hidden behind a signal-with-Session
payload.
"""


def register_transactional() -> None:
    """No-op: cross-domain coordination is handled inline in SecretFriendService."""
