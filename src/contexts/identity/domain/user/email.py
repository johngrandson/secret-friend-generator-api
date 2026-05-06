"""Email value object — pure Python, zero framework dependencies."""

import re
from dataclasses import dataclass


_EMAIL_RE = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


@dataclass(frozen=True)
class Email:
    """Immutable value object that validates an e-mail address on construction."""

    value: str

    def __post_init__(self) -> None:
        if not _EMAIL_RE.match(self.value):
            raise ValueError(f"Invalid email address: {self.value!r}")

    def __str__(self) -> str:
        return self.value
