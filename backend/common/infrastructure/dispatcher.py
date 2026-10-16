"""인프로세스 동기 이벤트 디스패처."""

from collections import defaultdict

from common.domain.events import DomainEvent, EventHandler


class InProcessEventDispatcher:
    """발행 즉시 같은 스레드에서 구독자를 등록 순서대로 호출한다."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        for event_type, handlers in list(self._handlers.items()):
            if isinstance(event, event_type):
                for handler in handlers:
                    handler(event)
