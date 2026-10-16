"""도메인 이벤트 → 알림 변환. 다른 Context의 이벤트를 import하는 쪽은 notifications뿐이다."""

import logging

from common.domain.events import DomainEvent, EventDispatcher
from meetings.domain.events import MeetingConfirmed, MeetingProposed
from notifications.application.ports import UserDirectory
from notifications.application.service import NotificationService
from notifications.domain.formatting import fmt_date, fmt_moment, fmt_range
from notifications.domain.notification import NotificationType
from reviews.domain.events import ReviewRequested
from rooms.domain.events import ReservationApproved, ReservationReassigned, ReservationRejected

logger = logging.getLogger(__name__)

MEETING_LINK = "/meeting"
ROOM_LINK = "/room"
REVIEW_LINK = "/reviews"


class NotificationHandlers:
    def __init__(self, service: NotificationService, users: UserDirectory) -> None:
        self._service = service
        self._users = users

    def on_meeting_confirmed(self, e: MeetingConfirmed) -> None:
        body = fmt_moment(e.slot_at) + (f" · {e.location}" if e.location else "")
        self._service.notify(
            e.student_id,
            NotificationType.MEETING_CONFIRMED,
            "면담이 확정되었어요",
            body,
            MEETING_LINK,
            {
                "meeting_id": e.meeting_id,
                "slot_at": e.slot_at.isoformat(),
                "location": e.location,
            },
        )

    def on_meeting_proposed(self, e: MeetingProposed) -> None:
        self._service.notify(
            e.student_id,
            NotificationType.MEETING_PROPOSED,
            "다른 면담 시간이 제안되었어요",
            f"제안 시간 {fmt_moment(e.proposed_at)}",
            MEETING_LINK,
            {"meeting_id": e.meeting_id, "proposed_at": e.proposed_at.isoformat()},
        )

    def on_reservation_approved(self, e: ReservationApproved) -> None:
        when = fmt_range(e.start_at, e.end_at)
        self._service.notify(
            e.user_id,
            NotificationType.RESERVATION_APPROVED,
            "회의실 예약이 확정되었어요",
            f"{e.room_name} · {when}" if e.room_name else when,
            ROOM_LINK,
            {
                "reservation_id": e.reservation_id,
                "room_id": e.room_id,
                "start_at": e.start_at.isoformat(),
                "end_at": e.end_at.isoformat(),
            },
        )

    def on_reservation_rejected(self, e: ReservationRejected) -> None:
        self._service.notify(
            e.user_id,
            NotificationType.RESERVATION_REJECTED,
            "회의실 예약이 반려되었어요",
            f"{e.room_name} · {e.reason}" if e.room_name else e.reason,
            ROOM_LINK,
            {"reservation_id": e.reservation_id, "room_id": e.room_id, "reason": e.reason},
        )

    def on_reservation_reassigned(self, e: ReservationReassigned) -> None:
        when = fmt_range(e.start_at, e.end_at)
        self._service.notify(
            e.user_id,
            NotificationType.RESERVATION_REASSIGNED,
            "다른 회의실로 변경되어 확정되었어요",
            f"{e.from_room_name} → {e.to_room_name} · {when}",
            ROOM_LINK,
            {
                "reservation_id": e.reservation_id,
                "from_room_id": e.from_room_id,
                "to_room_id": e.to_room_id,
                "start_at": e.start_at.isoformat(),
                "end_at": e.end_at.isoformat(),
            },
        )

    def on_review_requested(self, e: ReviewRequested) -> None:
        """가입한 참여자에게만 보낸다. 아직 가입하지 않은 intra ID는 건너뛴다."""
        user_ids = self._users.ids_by_intra_ids(list(e.intra_ids))
        deadline = f" (마감 {fmt_date(e.review_deadline)})" if e.review_deadline else ""
        body = (e.message or "다음 교육생을 위해 후기를 남겨 주세요.") + deadline
        for intra_id in e.intra_ids:
            user_id = user_ids.get(intra_id)
            if user_id is None:
                continue
            self._service.notify(
                user_id,
                NotificationType.REVIEW_REQUESTED,
                f"{e.course_name} 후기를 남겨 주세요",
                body,
                REVIEW_LINK,
                {
                    "course_id": e.course_id,
                    "review_deadline": e.review_deadline.isoformat() if e.review_deadline else None,
                },
            )


def _isolated(handler):
    """알림 처리 실패가 이벤트를 발행한 요청(면담 확정 등)을 깨뜨리지 않게 한다."""

    def wrapper(event: DomainEvent) -> None:
        try:
            handler(event)
        except Exception:
            logger.exception("알림 이벤트 처리 실패: %s", type(event).__name__)

    return wrapper


def register_handlers(bus: EventDispatcher, handlers: NotificationHandlers) -> None:
    for event_type, handler in (
        (MeetingConfirmed, handlers.on_meeting_confirmed),
        (MeetingProposed, handlers.on_meeting_proposed),
        (ReservationApproved, handlers.on_reservation_approved),
        (ReservationRejected, handlers.on_reservation_rejected),
        (ReservationReassigned, handlers.on_reservation_reassigned),
        (ReviewRequested, handlers.on_review_requested),
    ):
        bus.subscribe(event_type, _isolated(handler))
