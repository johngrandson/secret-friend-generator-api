"""Group domain signals."""
from blinker import NamedSignal, signal

group_created: NamedSignal = signal("group.created")
group_updated: NamedSignal = signal("group.updated")
group_deleted: NamedSignal = signal("group.deleted")
