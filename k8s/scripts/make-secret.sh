#!/usr/bin/env bash
# k8s/secret.yaml 을 만든다(커밋 금지, .gitignore 됨). 사용법과 전체 순서는 k8s/README.md.
#  - DJANGO_SECRET_KEY, POSTGRES_PASSWORD: 처음 한 번 무작위로 만들어 k8s/.env.k8s 에 저장하고 이후 재사용한다.
#    (DB 비밀번호가 바뀌면 기존 DB 볼륨에 접속하지 못하므로 한 번 만든 값을 유지해야 한다.)
#  - FORTYTWO_UID/SECRET, STAFF_INTRA_IDS, VAPID_*: 저장소 루트 .env 에 값이 있으면 가져온다(없으면 비움).
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
for key in ("FORTYTWO_UID", "FORTYTWO_SECRET", "STAFF_INTRA_IDS", "VAPID_PRIVATE_KEY", "VAPID_PUBLIC_KEY", "VAPID_SUBJECT"):
    data[key] = root.get(key, "")
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
