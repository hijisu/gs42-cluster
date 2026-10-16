# 빌드·실행 가이드

> 뼈대 문서입니다. 백엔드·프론트엔드가 구현되는 대로 각 섹션을 채우고, 명령이 바뀌면 같은 PR에서 이 문서도 갱신합니다.

## 요구 사항

| 도구 | 버전 | 비고 |
| --- | --- | --- |
| Python | TBD | Django REST 백엔드 |
| Node.js | TBD | React + Vite 프론트엔드 |
| PostgreSQL | TBD | docker compose로 실행 |
| Docker / Docker Compose | TBD | 로컬 통합 실행 |

## 환경변수

`.env.example`을 `.env`로 복사한 뒤 값을 채웁니다. 비밀값은 커밋하지 않습니다.

```bash
cp .env.example .env
```

| 변수 | 설명 | 필수 |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Django 시크릿 키 | O |
| `DJANGO_DEBUG` | 디버그 모드. `true`일 때만 모의 로그인 허용 | O |
| `DJANGO_ALLOWED_HOSTS` | 허용 호스트(쉼표 구분) | O |
| `TIME_ZONE` | 표시 시간대 (`Asia/Seoul`) | O |
| `POSTGRES_*` | DB 이름·사용자·비밀번호·호스트·포트 | O |
| `FORTYTWO_UID` / `FORTYTWO_SECRET` / `FORTYTWO_REDIRECT_URI` | 42 OAuth 앱 정보 | O |
| `STAFF_INTRA_IDS` | 교육운영팀 intra login 목록(쉼표 구분) | O |
| `FRONTEND_ORIGIN` / `VITE_API_BASE_URL` | 프론트엔드 주소·API 경로 | O |
| `VAPID_*` | Web Push 키 (Phase 2) | - |
| `SLACK_BOT_TOKEN` | Slack 알림 (Phase 3) | - |

## 로컬 실행

TBD (docker compose 구성 후 작성)

## 백엔드

Python 3.12+ (3.13에서 확인), Django 5.2 LTS, PostgreSQL 16. 루트의 `.env`를 읽으며(이미 설정된 환경변수 우선), 로컬 실행 시 `POSTGRES_HOST=localhost`로 덮어씁니다.

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# 로컬 DB (docker compose 구성 전 임시)
docker run -d --name gs42-db -e POSTGRES_DB=gs42 -e POSTGRES_USER=gs42 \
  -e POSTGRES_PASSWORD=<비밀번호> -p 5432:5432 postgres:16

export POSTGRES_HOST=localhost POSTGRES_PASSWORD=<비밀번호>
python manage.py migrate
python manage.py runserver 8000     # GET http://localhost:8000/api/health

pytest                              # 도메인 테스트는 DB 없이, 통합 테스트는 pytest-django(DB 필요)
ruff check . && ruff format --check .
```

`DJANGO_DEBUG=false`에서는 `DJANGO_SECRET_KEY`가 필수입니다.

## 프론트엔드

TBD (설치 · 실행 · 테스트 · 빌드)

## 42 OAuth 앱 등록

TBD (intra 앱 등록 절차, redirect URI)

## 배포

TBD (Phase 1 배포 이슈에서 작성)
