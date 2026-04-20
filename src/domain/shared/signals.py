"""Domain signals — Phoenix-style lifecycle hooks via blinker.

Define named signals for domain events. Services emit them after
state changes; handlers react without coupling to the service.

Usage in services:
    from src.domain.shared.signals import group_created
    group_created.send(None, group=result)

Usage in handlers:
    @group_created.connect
    def on_group_created(sender, **kwargs):
        log.info("Group created: %s", kwargs["group"].name)
"""
from blinker import signal

# Group lifecycle
group_created = signal("group.created")

# Participant lifecycle
participant_created = signal("participant.created")
participant_updated = signal("participant.updated")

# Secret friend lifecycle
secret_friend_assigned = signal("secret_friend.assigned")
