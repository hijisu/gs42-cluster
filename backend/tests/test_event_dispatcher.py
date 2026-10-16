from dataclasses import dataclass

from common.domain.events import DomainEvent
from common.infrastructure.dispatcher import InProcessEventDispatcher


@dataclass(frozen=True)
class Ping(DomainEvent):
    value: int = 0


def test_publish_calls_subscribers_in_order():
    dispatcher = InProcessEventDispatcher()
    calls = []
    dispatcher.subscribe(Ping, lambda e: calls.append(("a", e.value)))
    dispatcher.subscribe(Ping, lambda e: calls.append(("b", e.value)))
    dispatcher.publish(Ping(value=7))
    assert calls == [("a", 7), ("b", 7)]


def test_publish_without_subscribers_is_noop():
    InProcessEventDispatcher().publish(Ping())


def test_subscriber_of_other_event_not_called():
    @dataclass(frozen=True)
    class Other(DomainEvent):
        pass

    dispatcher = InProcessEventDispatcher()
    calls = []
    dispatcher.subscribe(Other, calls.append)
    dispatcher.publish(Ping())
    assert calls == []
