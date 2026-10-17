from common.domain.errors import ConflictError, InvalidRequestError, NotFoundError


class InvalidRange(InvalidRequestError):
    code = "invalid_range"


class PastTime(InvalidRequestError):
    code = "past_time"


class OutsideHours(InvalidRequestError):
    code = "outside_hours"


class InvalidTransition(ConflictError):
    code = "invalid_transition"


class NotCancelable(InvalidTransition):
    """교육생이 취소할 수 없는 상태(승인된 예약 등). 운영팀 취소 경로는 따로 있다."""

    code = "not_cancelable"


class RoomConflict(ConflictError):
    code = "room_conflict"


class RoomBlocked(ConflictError):
    code = "room_blocked"


class RoomNotFound(NotFoundError):
    code = "room_not_found"


class ReservationNotFound(NotFoundError):
    code = "reservation_not_found"


class ReasonRequired(InvalidRequestError):
    code = "reason_required"


class InvalidRules(InvalidRequestError):
    code = "invalid_rules"


class RoomCodeTaken(ConflictError):
    code = "room_code_taken"


class InvalidBlock(InvalidRequestError):
    code = "invalid_block"


class RoomBlockedPeriod(ConflictError):
    code = "room_block_conflict"


class BlockNotFound(NotFoundError):
    code = "block_not_found"
