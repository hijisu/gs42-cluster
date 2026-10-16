from common.domain.errors import ConflictError, InvalidRequestError, NotFoundError


class InvalidRange(InvalidRequestError):
    code = "invalid_range"


class PastTime(InvalidRequestError):
    code = "past_time"


class OutsideHours(InvalidRequestError):
    code = "outside_hours"


class InvalidTransition(ConflictError):
    code = "invalid_transition"


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
