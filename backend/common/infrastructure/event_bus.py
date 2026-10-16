"""프로세스 전역 이벤트 버스. 구독은 소비하는 Context(notifications 등)가 등록한다."""

from common.infrastructure.dispatcher import InProcessEventDispatcher

event_bus = InProcessEventDispatcher()
