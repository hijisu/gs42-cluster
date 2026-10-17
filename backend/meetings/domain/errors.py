from common.domain.errors import ConflictError, InvalidRequestError, NotFoundError


class InvalidTransition(ConflictError):
    code = "invalid_transition"


class SlotUnavailable(ConflictError):
    code = "slot_unavailable"


class InvalidSlot(InvalidRequestError):
    code = "invalid_slot"


class MeetingNotFound(NotFoundError):
    code = "meeting_not_found"


class MeetingTypeNotFound(NotFoundError):
    code = "meeting_type_not_found"


class StaffNotFound(NotFoundError):
    code = "staff_not_found"


class SlotHasMeeting(ConflictError):
    code = "slot_has_meeting"


class AvailabilityInPast(InvalidRequestError):
    code = "availability_past"


class AvailabilityBeyondWindow(InvalidRequestError):
    code = "availability_too_far"


class NotCancelable(InvalidTransition):
    """교육생이 취소할 수 없는 상태(확정된 면담 등). 운영팀 취소 경로는 따로 있다."""

    code = "not_cancelable"
