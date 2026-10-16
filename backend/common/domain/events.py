"""도메인 이벤트와 디스패처 인터페이스. Django/DRF를 import하지 않는다."""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol, TypeVar


@dataclass(frozen=True)
class DomainEvent:
    """모든 도메인 이벤트의 기반. 하위 Context가 상속해 필드를 추가한다."""

    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), kw_only=True)


E = TypeVar("E", bound=DomainEvent)
EventHandler = Callable[[E], None]


class EventDispatcher(Protocol):
    def subscribe(self, event_type: type[E], handler: EventHandler[E]) -> None: ...

    def publish(self, event: DomainEvent) -> None: ...
