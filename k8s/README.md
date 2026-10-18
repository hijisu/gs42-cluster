# 쿠버네티스 배포 (hijaeui-server-1 → https://42gs-cluster.hijae.dev)

MicroK8s 단일 노드(`hijaeui-server-1`)에 올리는 구성입니다. 이 폴더의 파일만 사용하며 다른 소스는 바꾸지 않습니다.

```
Cloudflare Tunnel (TLS 종단) → Traefik(nginx class) → web(Caddy, 프론트 정적 + /api 프록시) → backend(gunicorn) → db(PostgreSQL 16, PVC 5Gi)
```

네임스페이스는 `gs42-cluster`이고, 같은 클러스터의 다른 앱(`public` 등)은 건드리지 않습니다. DB는 `db-client=true` 라벨이 붙은 파드(backend, 관리 Job)에서만 접속할 수 있습니다(NetworkPolicy).

## 1. 사전 준비 (내 PC)

| 필요한 것 | 확인 |
| --- | --- |
| Docker (buildx) | `docker buildx version` — arm64 Mac에서도 `linux/amd64`로 교차 빌드합니다 |
| kubectl 컨텍스트 `z2mini` (= hijaeui-server-1) | `kubectl --context z2mini get nodes` |
| SSH 접속 `hijae@hijaeui-server-1` | `ssh hijae@hijaeui-server-1 microk8s status` (이미지 전송용. 사용자가 `microk8s` 그룹이면 sudo 없이 containerd 소켓에 가져옵니다) |
| python3 + `cryptography` | 비밀값·VAPID 키 생성 스크립트용 |

컨텍스트 이름이 다르면 `K8S_CONTEXT=이름`, SSH 호스트가 다르면 `K8S_NODE=사용자@호스트`를 환경변수로 지정합니다.

## 2. 설정할 값

| 위치 | 값 | 설명 |
| --- | --- | --- |
| `configmap.yaml` | `DJANGO_ALLOWED_HOSTS`, `FRONTEND_ORIGIN`, `FORTYTWO_REDIRECT_URI` | 도메인(`42gs-cluster.hijae.dev`). 도메인을 바꾸면 `ingress.yaml`의 host와 `backend.yaml`의 probe Host 헤더도 같이 바꿉니다 |
| `configmap.yaml` | `DJANGO_DEBUG` | 기본 `true` = **모의 로그인 켜짐**. 아래 "모의 로그인" 참고 |
| `secret.yaml` (자동 생성) | `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` | 처음 한 번 무작위로 만들어 `k8s/.env.k8s`에 저장하고 재사용합니다. **DB 비밀번호를 바꾸면 기존 DB에 접속할 수 없으니 `.env.k8s`를 지우지 마세요** |
| `secret.yaml` (자동 생성) | `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`, `VAPID_SUBJECT` | 웹 푸시(알림)용. 루트 `.env`에 개인키가 있으면 그 값, 없으면 새로 만들어 `.env.k8s`에 저장·재사용합니다. 키를 바꾸면 기존 푸시 구독이 모두 무효가 됩니다 |
| 저장소 루트 `.env` → `secret.yaml` | `FORTYTWO_UID`, `FORTYTWO_SECRET`, `STAFF_INTRA_IDS` | 값이 있을 때만 가져옵니다(실제 42 로그인용, 없어도 동작) |

`secret.yaml`, `.env.k8s`는 `.gitignore`에 있어 커밋되지 않습니다. 비밀값을 채팅·이슈·PR에 붙여 넣지 않습니다.

## 3. 배포 순서

```bash
k8s/scripts/make-secret.sh        # secret.yaml 생성 (처음 한 번, .env 값이 바뀌면 다시)
k8s/scripts/build.sh              # amd64 이미지 빌드 → 서버 containerd로 전송 (태그 = git 짧은 SHA)
k8s/scripts/deploy.sh diff        # (선택) 적용 전 차이 확인, 클러스터는 바뀌지 않음
k8s/scripts/deploy.sh             # 적용 + 롤아웃 대기 + 아래 두 Job 자동 실행
k8s/scripts/deploy.sh job import-books   # 도서 518종 (반복 실행 안전)
k8s/scripts/deploy.sh job seed-demo      # 시연 데이터(디버깅·시연용; DJANGO_DEBUG=true에서만). 면담 기본 담당자, 회의실 예약 예시, 교육과정·후기 포함
```

`deploy.sh`는 끝에 두 Job을 자동 실행합니다(둘 다 반복 실행해도 안전, 시연 데이터는 모의 계정 데이터만 만듭니다). DB 마이그레이션은 backend가 시작할 때 자동으로 실행됩니다. 코드를 고친 뒤에는 `build.sh` → `deploy.sh`만 다시 실행합니다.

## 4. 사람이 해야 하는 설정

1. **Cloudflare Tunnel 호스트 매핑**: Zero Trust → Networks → Tunnels(`cloudflared`가 쓰는 터널) → Public Hostname에 `42gs-cluster.hijae.dev`를 추가하고 서비스를 기존 `gs42stat.hijae.dev`와 같은 Traefik 대상으로 지정합니다. DNS 레코드는 터널이 자동으로 만듭니다.
2. (권장) **Cloudflare Access**: 모의 로그인을 켠 동안에는 허용 이메일·IP로 접근을 제한합니다.
3. (실제 42 로그인을 쓸 때) 42 intra 앱에 Redirect URI `https://42gs-cluster.hijae.dev/api/auth/callback`을 추가하고 루트 `.env`에 `FORTYTWO_UID/SECRET`, `STAFF_INTRA_IDS`를 넣은 뒤 `make-secret.sh` → `deploy.sh`.

## 5. 확인

```bash
kubectl --context z2mini -n gs42-cluster get pods          # db-0, backend, web 모두 Running/Ready
curl https://42gs-cluster.hijae.dev/api/health            # {"status":"ok"}
```

브라우저에서 접속해 "개발용 모의 로그인"의 교육생/운영팀으로 들어가 회의실 예약 → 승인 흐름을 한 번 확인합니다.

## 6. 모의 로그인 (기본 켜짐)

`DJANGO_DEBUG=true`이면 비밀번호 없는 모의 로그인이 열립니다. **인터넷에 공개된 주소에서는 누구나 운영팀 계정으로 들어올 수 있고, Django 디버그 오류 페이지가 노출될 수 있습니다.** Cloudflare Access 등으로 접근을 제한하세요. 로그인 버튼은 개발 번들에서만 보이기 때문에 이 폴더의 `web.Dockerfile`은 프론트를 개발 모드로 빌드합니다(번들에 버튼 문구가 없으면 빌드가 실패합니다).

OAuth만 쓰려면: `configmap.yaml`의 `DJANGO_DEBUG`를 `"false"`로, `build.sh`의 웹 이미지 빌드를 `deploy/web.Dockerfile`로 바꾸고 다시 빌드·배포합니다(모의 로그인과 시연 데이터 Job은 꺼집니다).

## 7. 운영

| 일 | 명령 |
| --- | --- |
| 로그 | `kubectl --context z2mini -n gs42-cluster logs deploy/backend -f` |
| 롤백 | `kubectl --context z2mini -n gs42-cluster rollout undo deploy/backend` (web도 동일) |
| 재시작 | `kubectl --context z2mini -n gs42-cluster rollout restart deploy/backend` |
| 전체 삭제 | `kubectl --context z2mini delete ns gs42-cluster` — **PVC(DB 데이터)까지 삭제됩니다** |

## 문제 해결

| 증상 | 원인·해결 |
| --- | --- |
| `ImagePullBackOff` / `ErrImageNeverPull` | 이미지가 서버에 없음. `build.sh`를 다시 실행(태그가 `deploy.sh`와 같은지 확인) |
| backend가 Ready가 안 됨 | `kubectl -n gs42-cluster logs deploy/backend`. DB 비밀번호 불일치면 `.env.k8s`와 기존 PVC가 맞는지 확인 |
| 로그인/POST 403 | `FRONTEND_ORIGIN`이 접속 주소(https)와 같은지 확인 |
| 접속 시 Cloudflare 오류(502/1033) | 터널 호스트 매핑(4-1) 확인, `kubectl -n public logs deploy/cloudflared` |
