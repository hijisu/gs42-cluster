"""VAPID 키 생성/변환. 개인키는 절대 출력·저장하지 않고 호출자가 .env 에 직접 넣는다."""

import base64

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def generate_keys() -> tuple[str, str]:
    """(public_key, private_key). 둘 다 base64url. public 은 브라우저 applicationServerKey 형식."""
    vapid = Vapid()
    vapid.generate_keys()
    private = _b64url(vapid.private_key.private_numbers().private_value.to_bytes(32, "big"))
    return public_key_of(private), private


def public_key_of(private_key: str) -> str:
    """개인키(base64url raw)에서 브라우저용 공개키(base64url, 비압축 점)를 계산한다."""
    vapid = Vapid.from_string(private_key)
    point = vapid.public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    return _b64url(point)
