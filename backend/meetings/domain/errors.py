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
