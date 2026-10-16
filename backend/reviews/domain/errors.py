from common.domain.errors import ConflictError, ForbiddenError, InvalidRequestError, NotFoundError


class CourseNotFound(NotFoundError):
    code = "course_not_found"


class NotParticipant(ForbiddenError):
    code = "not_participant"


class ReviewClosed(ConflictError):
    code = "review_closed"


class AlreadyReviewed(ConflictError):
    code = "already_reviewed"


class InvalidReview(InvalidRequestError):
    code = "invalid_review"
