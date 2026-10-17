class AuthenticationFailed(Exception):
    """42 OAuth 인증 실패(코드 교환·프로필 조회 오류 등).

    stage/status/reason은 운영 로그용 진단 정보다. 코드·토큰·응답 본문은 담지 않는다.
    """

    def __init__(
        self, message: str = "", *, stage: str = "", status: int | None = None, reason: str = ""
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.status = status
        self.reason = reason
