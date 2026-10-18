#!/usr/bin/env bash
# k8s/secret.yaml 을 만든다(커밋 금지, .gitignore 됨). 사용법과 전체 순서는 k8s/README.md.
#  - DJANGO_SECRET_KEY, POSTGRES_PASSWORD: 처음 한 번 무작위로 만들어 k8s/.env.k8s 에 저장하고 이후 재사용한다.
#    (DB 비밀번호가 바뀌면 기존 DB 볼륨에 접속하지 못하므로 한 번 만든 값을 유지해야 한다.)
#  - VAPID_PRIVATE_KEY/PUBLIC_KEY(웹 푸시 알림): 루트 .env 에 있으면 그 값, 없으면 새로 만들어 .env.k8s 에 저장하고 재사용한다
#    (키를 바꾸면 기존 구독이 모두 무효가 되므로 한 번 만든 값을 유지한다). 필요: python3 + cryptography.
#  - FORTYTWO_UID/SECRET, STAFF_INTRA_IDS: 저장소 루트 .env 에 값이 있으면 가져온다(없으면 비움).
set -euo pipefail
cd "$(dirname "$0")/.."
STATE=.env.k8s
ROOT_ENV=../.env

[ -f "$STATE" ] || {
  umask 077
  {
    echo "DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
    echo "POSTGRES_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')"
  } > "$STATE"
  echo "새 비밀값을 $STATE 에 만들었습니다(커밋 금지)."
}

if ! grep -q '^VAPID_PRIVATE_KEY=.\+' "$ROOT_ENV" 2>/dev/null && ! grep -q '^VAPID_PRIVATE_KEY=' "$STATE"; then
  python3 - >> "$STATE" <<'PY'
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

b64 = lambda raw: base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
key = ec.generate_private_key(ec.SECP256R1())
public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
print("VAPID_PRIVATE_KEY=" + b64(key.private_numbers().private_value.to_bytes(32, "big")))
print("VAPID_PUBLIC_KEY=" + b64(public))
PY
  echo "웹 푸시용 VAPID 키를 $STATE 에 만들었습니다(커밋 금지)."
fi

python3 - "$STATE" "$ROOT_ENV" <<'PY'
import json, sys

def load(path):
    out = {}
    try:
        for line in open(path, encoding="utf-8"):
            line = line.rstrip("\n")
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                out[key.strip()] = value.strip().strip("'\"")
    except FileNotFoundError:
        pass
    return out

state, root = load(sys.argv[1]), load(sys.argv[2])
data = {k: state[k] for k in ("DJANGO_SECRET_KEY", "POSTGRES_PASSWORD")}
for key in ("FORTYTWO_UID", "FORTYTWO_SECRET", "STAFF_INTRA_IDS"):
    data[key] = root.get(key, "")
# 웹 푸시: 루트 .env 의 개인키가 있으면 그것을, 없으면 .env.k8s 의 것을 쓴다.
vapid = root if root.get("VAPID_PRIVATE_KEY") else state
data["VAPID_PRIVATE_KEY"] = vapid.get("VAPID_PRIVATE_KEY", "")
data["VAPID_PUBLIC_KEY"] = vapid.get("VAPID_PUBLIC_KEY", "")
data["VAPID_SUBJECT"] = root.get("VAPID_SUBJECT") or "mailto:admin@hijae.dev"
# JSON 은 YAML 의 부분집합이라 특수문자를 안전하게 이스케이프한다.
doc = {
    "apiVersion": "v1", "kind": "Secret",
    "metadata": {"name": "gs42-secret", "namespace": "gs42-cluster"},
    "type": "Opaque", "stringData": data,
}
open("secret.yaml", "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
PY
chmod 600 secret.yaml
echo "k8s/secret.yaml 을 만들었습니다(커밋 금지)."
