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
REQUEST_HEADERS = {"User-Agent": "gs42-cluster/1.0", "Accept": "application/json"}


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
        token = self._call("token", self._post_token, code)
        me = self._call("profile", self._get_json, ME_URL, token)
        login = me.get("login")
        if not login:
            raise AuthenticationFailed(
                "42 프로필에 login이 없습니다", stage="profile", reason="missing_login"
            )
        name = me.get("usual_full_name") or me.get("displayname") or login
        image = me.get("image") or {}
        image_url = image.get("link") or (image.get("versions") or {}).get("medium") or ""
        if not isinstance(image_url, str) or not image_url.startswith("https://"):
            image_url = ""
        return FortyTwoProfile(
            intra_id=login, name=name, is_staff=bool(me.get("staff?")), image_url=image_url
        )

    @staticmethod
    def _call(stage: str, func, *args):
        """단계별 실패를 stage/status/reason으로 구분해 AuthenticationFailed로 바꾼다."""
        try:
            return func(*args)
        except urllib.error.HTTPError as exc:
            raise AuthenticationFailed(
                "42 인증에 실패했습니다", stage=stage, status=exc.code, reason="http_error"
            ) from exc
        except (TimeoutError, urllib.error.URLError) as exc:
            reason = "timeout" if isinstance(exc, TimeoutError) else "network_error"
            raise AuthenticationFailed(
                "42 인증에 실패했습니다", stage=stage, reason=reason
            ) from exc
        except (ValueError, KeyError) as exc:
            raise AuthenticationFailed(
                "42 인증에 실패했습니다", stage=stage, reason="invalid_response"
            ) from exc

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
        request = urllib.request.Request(
            TOKEN_URL, data=data, method="POST", headers=REQUEST_HEADERS
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310
            return json.load(response)["access_token"]

    def _get_json(self, url: str, token: str) -> dict:
        request = urllib.request.Request(
            url, headers={**REQUEST_HEADERS, "Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310
            return json.load(response)
