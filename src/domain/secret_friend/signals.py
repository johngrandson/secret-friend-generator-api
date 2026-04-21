"""Secret friend domain signals."""

from blinker import NamedSignal, signal

secret_friend_assigned: NamedSignal = signal("secret_friend.assigned")
secret_friend_deleted: NamedSignal = signal("secret_friend.deleted")
