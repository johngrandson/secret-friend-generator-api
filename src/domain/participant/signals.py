"""Participant domain signals."""
from blinker import NamedSignal, signal

participant_created: NamedSignal = signal("participant.created")
participant_updated: NamedSignal = signal("participant.updated")
