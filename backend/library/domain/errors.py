from common.domain.errors import ConflictError, InvalidRequestError, NotFoundError


class BookNotFound(NotFoundError):
    code = "book_not_found"


class ReportNotFound(NotFoundError):
    code = "report_not_found"


class WishNotFound(NotFoundError):
    code = "wish_not_found"


class InvalidBook(InvalidRequestError):
    code = "invalid_book"


class InvalidReport(InvalidRequestError):
    code = "invalid_report"


class InvalidWish(InvalidRequestError):
    code = "invalid_wish"


class DuplicateBook(ConflictError):
    code = "duplicate_book"


class InvalidTransition(ConflictError):
    code = "invalid_transition"
