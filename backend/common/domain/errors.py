"""Context 공통 도메인 오류. interfaces 계층이 HTTP 상태로 매핑한다."""


class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)


class InvalidRequestError(DomainError):
    code = "invalid_request"


class ForbiddenError(DomainError):
    code = "forbidden"


class NotFoundError(DomainError):
    code = "not_found"


class ConflictError(DomainError):
    code = "conflict"
