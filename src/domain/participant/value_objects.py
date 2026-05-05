"""Participant value objects — pure domain types, no framework deps."""

from enum import Enum


class ParticipantStatus(str, Enum):
    PENDING = "PENDING"
    REVEALED = "REVEALED"
