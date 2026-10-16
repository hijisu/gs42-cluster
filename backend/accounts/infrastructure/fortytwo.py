"""42 intra OAuth 클라이언트 (표준 라이브러리만 사용)."""

import json
import urllib.error
import urllib.parse
import urllib.request

from accounts.application.ports import FortyTwoProfile
from accounts.domain.errors import AuthenticationFailed

AUTHORIZE_URL = "https://api.intra.42.fr/oauth/authorize"
TOKEN_URL = "https://api.intra.42.fr/oauth/token"
ME_URL = "https://api.intra.42.fr/v2/me"


class FortyTwoOAuthClient:
    def __init__(self, uid: str, secret: str, redirect_uri: str, timeout: float = 10.0) -> None:
        self._uid = uid
        self._secret = secret
        self._redirect_uri = redirect_uri
        self._timeout = timeout

    def authorize_url(self, state: str) -> str:
        query = urllib.parse.urlencode(
            {
                "client_id": self._uid,
                "redirect_uri": self._redirect_uri,
                "response_type": "code",
                "scope": "public",
                "state": state,
            }
        )
        return f"{AUTHORIZE_URL}?{query}"

    def fetch_profile(self, code: str) -> FortyTwoProfile:
        try:
            token = self._post_token(code)
            me = self._get_json(ME_URL, token)
        except (urllib.error.URLError, ValueError, KeyError, TimeoutError) as exc:
            raise AuthenticationFailed("42 인증에 실패했습니다") from exc
        login = me.get("login")
        if not login:
            raise AuthenticationFailed("42 프로필에 login이 없습니다")
        name = me.get("usual_full_name") or me.get("displayname") or login
        return FortyTwoProfile(intra_id=login, name=name, is_staff=bool(me.get("staff?")))

    def _post_token(self, code: str) -> str:
        data = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "client_id": self._uid,
                "client_secret": self._secret,
                "code": code,
                "redirect_uri": self._redirect_uri,
            }
        ).encode()
        request = urllib.request.Request(TOKEN_URL, data=data, method="POST")
        with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310
            return json.load(response)["access_token"]

    def _get_json(self, url: str, token: str) -> dict:
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310
            return json.load(response)
