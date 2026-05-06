"""Unit tests for AggregateRoot base class."""

from dataclasses import dataclass

from src.shared.aggregate_root import AggregateRoot
from src.shared.events import DomainEvent


@dataclass(frozen=True)
class SomeEvent(DomainEvent):
    label: str


@dataclass
class SomeAggregate(AggregateRoot):
    name: str

    def do_thing(self) -> None:
        self.collect_event(SomeEvent(label="thing_done"))


def test_collect_event_appends():
    agg = SomeAggregate(name="test")
    event = SomeEvent(label="x")
    agg.collect_event(event)
    assert len(agg.pull_events()) == 1


def test_pull_events_clears_list():
    agg = SomeAggregate(name="test")
    agg.collect_event(SomeEvent(label="a"))
    agg.pull_events()
    assert agg.pull_events() == []


def test_pull_events_returns_in_order():
    agg = SomeAggregate(name="test")
    agg.collect_event(SomeEvent(label="first"))
    agg.collect_event(SomeEvent(label="second"))
    events = agg.pull_events()
    assert [e.label for e in events] == ["first", "second"]


def test_no_events_initially():
    agg = SomeAggregate(name="test")
    assert agg.pull_events() == []
