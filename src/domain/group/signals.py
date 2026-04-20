"""Group domain signals."""
from blinker import NamedSignal, signal

group_created: NamedSignal = signal("group.created")
