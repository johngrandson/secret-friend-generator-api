"""Secret friend domain signals."""
from blinker import NamedSignal, signal

secret_friend_assigned: NamedSignal = signal("secret_friend.assigned")
