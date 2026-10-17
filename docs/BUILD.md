# 빌드·실행 가이드

> 뼈대 문서입니다. 백엔드·프론트엔드가 구현되는 대로 각 섹션을 채우고, 명령이 바뀌면 같은 PR에서 이 문서도 갱신합니다.

## 요구 사항

| 도구 | 버전 | 비고 |
| --- | --- | --- |
| Python | 3.12+ (3.13에서 확인) | Django REST 백엔드. compose 이미지는 `python:3.13-slim` |
| Node.js | 22 (LTS) | React + Vite 프론트엔드. compose 이미지는 `node:22-slim` |
| PostgreSQL | 16 | docker compose로 실행. `btree_gist` 확장 필요(아래 백엔드 절) |
| Docker / Docker Compose | Compose v2 이상 | 로컬 통합 실행(`docker compose`) |

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
| `POSTGRES_*` | DB 이름·사용자·비밀번호·호스트·포트. compose에서는 `POSTGRES_HOST=db`로 자동 덮어씀 | O |
| `COMPOSE_PROJECT_NAME` | compose 프로젝트 이름(기본 `gs42`). 한 PC에서 클론을 여러 개 돌릴 때만 변경 | - |
| `DB_HOST_PORT` / `BACKEND_HOST_PORT` / `FRONTEND_HOST_PORT` | compose가 호스트에 여는 포트(기본 5432 / 8000 / 5173). 컨테이너 안 포트는 고정 | - |
| `FORTYTWO_UID` / `FORTYTWO_SECRET` / `FORTYTWO_REDIRECT_URI` | 42 OAuth 앱 정보 | O |
| `STAFF_INTRA_IDS` | 교육운영팀 intra login 목록(쉼표 구분) | O |
| `FRONTEND_ORIGIN` / `VITE_API_BASE_URL` | 프론트엔드 주소·API 경로. compose에서는 `FRONTEND_ORIGIN`이 `FRONTEND_HOST_PORT`로 자동 계산됨 | O |
| `PROD_HTTP_PORT` | 운영 구성(`docker-compose.prod.yml`)이 호스트 루프백(`127.0.0.1`)에 여는 HTTP 포트. 기본 80 | - |
| `GUNICORN_WORKERS` | 운영 구성 backend(gunicorn)의 워커 수. 기본 2 | - |
| `DJANGO_COOKIE_SECURE` | (선택) Secure 쿠키 여부. 기본은 `DJANGO_DEBUG=false`일 때 true. 로컬 http 검증에서만 false | - |
| `API_PROXY_TARGET` | (선택) 호스트에서 `npm run dev`할 때 `/api` 프록시 대상. 기본 `http://localhost:8000`, compose는 `http://backend:8000` 고정 | - |
| `VAPID_*` | Web Push 키 (Phase 2) | - |
| `SLACK_BOT_TOKEN` | Slack 알림 (Phase 3) | - |

## 로컬 실행

`docker compose up` 한 번으로 DB·백엔드·프론트를 함께 띄웁니다. 포트는 모두 이 PC의 루프백(`127.0.0.1`)에만 열립니다(예시 비밀번호의 DB와 모의 로그인이 같은 네트워크의 다른 PC에 노출되지 않게).

```bash
cp .env.example .env            # 처음 한 번 (비밀값은 .env에만 두고 커밋하지 않음)
docker compose up --build       # 첫 실행은 이미지 빌드와 npm ci 때문에 몇 분 걸립니다
```

| 서비스 | 주소 | 설명 |
| --- | --- | --- |
| frontend | http://localhost:5173 | Vite 개발 서버. `/api`는 backend로 프록시(같은 origin이라 세션 쿠키·CSRF가 그대로 동작) |
| backend | http://localhost:8000 | Django. 시작할 때 `migrate`를 자동 실행. 소스는 볼륨 마운트라 수정이 바로 반영됨 |
| db | localhost:5432 | PostgreSQL 16. 데이터는 `db-data` 볼륨에 보존 |

```bash
docker compose exec backend pytest -q      # 컨테이너 안에서 백엔드 테스트
docker compose exec frontend npm test      # 프론트 테스트
docker compose exec backend python manage.py seed_meeting_demo   # 개발용 시드 (아래 백엔드 절 참고)
docker compose down                         # 중지(데이터 유지) / down -v 는 DB·node_modules 볼륨까지 삭제
```

- 한 PC에서 클론/에이전트를 여러 개 돌릴 때는 `.env`의 `COMPOSE_PROJECT_NAME`과 `*_HOST_PORT`를 서로 다르게 지정합니다(예: `gs42-b`, 8100/5532/5273).
  - `FRONTEND_HOST_PORT`를 바꾸면 compose가 백엔드의 `FRONTEND_ORIGIN`(CSRF 신뢰 origin·CORS)을 `http://localhost:<FRONTEND_HOST_PORT>`로 자동 설정합니다. `.env`의 `FRONTEND_ORIGIN`은 호스트에서 직접 실행할 때만 쓰입니다.
  - `BACKEND_HOST_PORT`를 바꾸면 42 로그인용 `FORTYTWO_REDIRECT_URI`와 intra 앱에 등록한 redirect URI도 같은 포트로 맞춰야 합니다(모의 로그인만 쓰면 무관).
- 프론트 컨테이너는 `node_modules`를 컨테이너 전용 볼륨에 두므로 호스트의 `node_modules`와 섞이지 않습니다. 의존성을 바꾼 뒤에는 `docker compose restart frontend`(시작 시 `npm ci`)를 실행합니다.
- 컨테이너 없이 호스트에서 직접 실행하는 방법은 아래 "백엔드"·"프론트엔드" 절을 참고합니다.

## 백엔드

Python 3.12+ (3.13에서 확인), Django 5.2 LTS, PostgreSQL 16. 루트의 `.env`를 읽으며(이미 설정된 환경변수 우선), 로컬 실행 시 `POSTGRES_HOST=localhost`로 덮어씁니다.

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# 로컬 DB: compose의 db 서비스만 띄운다 (.env의 POSTGRES_* 값 사용)
docker compose up -d db

export POSTGRES_HOST=localhost POSTGRES_PASSWORD=<.env의 비밀번호>   # DB_HOST_PORT를 바꿨다면 POSTGRES_PORT도 같은 값으로
python manage.py migrate
python manage.py runserver 8000     # GET http://localhost:8000/api/health

pytest                              # 도메인 테스트는 DB 없이, 통합 테스트는 pytest-django(DB 필요)
ruff check . && ruff format --check .
```

`DJANGO_DEBUG=false`에서는 `DJANGO_SECRET_KEY`가 필수입니다.

**PostgreSQL 확장 `btree_gist`**: 회의실 예약의 겹침 방지(승인된 예약끼리 같은 장소·시간 중복 금지)를 DB 배타 제약으로도 보장하기 위해 `rooms` 마이그레이션(0003)이 `CREATE EXTENSION btree_gist`를 실행합니다. 신뢰 확장(trusted)이라 DB 소유자 권한이면 충분하며, docker `postgres` 이미지의 기본 사용자(`POSTGRES_USER`)는 바로 가능합니다. 운영 DB에서 권한이 없으면 관리자가 한 번 `CREATE EXTENSION btree_gist;`를 실행해 두세요.

### 인증 (개발용 모의 로그인)

`DJANGO_DEBUG=true`일 때만 `POST /api/auth/mock-login`이 열립니다(운영에서는 404). 시드 계정은 첫 호출 때 생성됩니다.

```bash
curl -c cookies.txt -X POST -H 'Content-Type: application/json' \
  -d '{"role":"staff"}' http://localhost:8000/api/auth/mock-login   # role: student | staff
curl -b cookies.txt http://localhost:8000/api/auth/me
```

### 개발용 면담 슬롯 시드

면담 유형 6종은 마이그레이션으로 들어갑니다. 슬롯과 기본 담당자는 개발용 명령으로 채웁니다(`DJANGO_DEBUG=true`에서만, 반복 실행해도 안전).

```bash
python manage.py seed_meeting_demo --days 7   # 모의 운영팀(staff)을 기본 담당자로, 평일 10·11·13·14·15·16시 슬롯 생성
```

### 개발용 교육과정·후기 시드

```bash
python manage.py seed_review_demo   # 교육과정 3개, 참여자(student·intra_a·intra_b), 후기 예시 (DEBUG 전용, 반복 실행 안전)
```

실제 로그인은 42 intra OAuth 앱 등록 후 `FORTYTWO_UID/SECRET`을 `.env`에 넣어 확인합니다(아래 "42 OAuth 앱 등록"). 역할은 `STAFF_INTRA_IDS`가 우선이며 42 응답의 `staff?`는 보조입니다.

## 프론트엔드

```bash
cd frontend
npm install
npm run dev        # 개발 서버 (http://localhost:5173)
npm run typecheck  # 타입 검사
npm test           # vitest
npm run build      # tsc + vite build (PWA manifest·서비스워커 생성)
```

- 구조: `src/app`(라우터·메뉴 정의), `src/components`(공통 컴포넌트), `src/styles`(스타일·토큰), `src/features/<context>/`(기능별 화면).
- 라우트는 `src/app/routes.ts`의 메뉴 정의와 `design/*.dc.html` 파일 이름이 1:1이다.
- 서비스워커는 `src/sw.ts`(vite-plugin-pwa `injectManifest`): 프리캐시 + 웹 푸시 표시·클릭 이동. 푸시 구독 UI는 알림 모달(벨)의 '푸시 알림 켜기'. 서비스워커는 `npm run build` 후 `npm run preview`(또는 localhost)에서 확인한다. iOS는 홈 화면에 설치한 PWA에서만 푸시가 동작한다.

## CI

`.github/workflows/ci.yml`이 PR과 `main` 푸시마다 두 job을 실행합니다. PR을 올리기 전에 같은 명령을 로컬에서 먼저 돌려 보세요.

| job | 검사 | 로컬 명령 |
| --- | --- | --- |
| `backend` | 린트·포맷, DDD 계층 의존 방향, 마이그레이션 누락, 테스트 | `cd backend && ruff check . && ruff format --check . && lint-imports && python manage.py makemigrations --check --dry-run && pytest -q` |
| `frontend` | 타입 검사, 린트, 테스트, 빌드 | `cd frontend && npm run typecheck && npm run lint && npm test && npm run build` |

- CI의 백엔드는 운영과 같은 `DJANGO_DEBUG=false`, 더미 시크릿, `postgres:16` 서비스로 실행합니다(`.env` 없음).
- `lint-imports`(import-linter, 설정은 `backend/.importlinter`)는 AGENTS.md의 규칙을 검사합니다: `domain`·`application`은 Django/DRF를 import하지 않고, `domain ← application ← interfaces` 바깥 계층을 거꾸로 import하지 않으며, `infrastructure`는 `interfaces`를 import하지 않고, `accounts`·`meetings`·`rooms`·`reviews`는 `notifications`를 import하지 않고(이벤트로만 연동), `meetings`·`rooms`·`reviews`는 서로를 import하지 않습니다. 새 Context나 앱을 추가하면 `.importlinter`의 `root_packages`와 계약에 추가합니다.
- 프론트의 ESLint는 TypeScript 7에 JS 컴파일러 API가 없어 `typescript-eslint` 대신 Babel 파서(`eslint.config.js`)를 씁니다. 타입 관련 검사는 `tsc`가 맡습니다.
- main 보호 규칙의 필수 체크 이름은 `backend`, `frontend`입니다(적용은 사람 확인 후).

## 42 OAuth 앱 등록

TBD (intra 앱 등록 절차, redirect URI)

## 배포 (운영 구성 로컬 검증)

AWS 서버·도메인·외부 HTTPS는 아직 없습니다. 운영과 같은 구성(gunicorn, 정적 파일 서빙, 같은 origin의 `/api` 프록시, `DEBUG=false`)을 **`http://localhost`에서만** 컨테이너로 띄워 검증합니다.

```bash
cp .env.example .env     # 이미 있으면 생략
# .env 의 DJANGO_SECRET_KEY 를 실제 값으로 바꾼다 (예시 값 change-me 로는 기동하지 않는다)
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

docker compose -f docker-compose.prod.yml up -d --build
open http://localhost        # PROD_HTTP_PORT 를 바꿨다면 http://localhost:<포트>
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml down          # 데이터 유지 / -v 는 DB 볼륨까지 삭제
```

| 서비스 | 역할 | 외부 노출 |
| --- | --- | --- |
| `web` | Caddy. 프론트 빌드 산출물을 서빙(SPA 폴백, 해시 자산은 장기 캐시, `index.html`·`sw.js`는 no-cache)하고 `/api/*`를 backend로 프록시 | `127.0.0.1:<PROD_HTTP_PORT>`(기본 80), 루프백 전용 |
| `backend` | gunicorn(비루트 사용자). 시작할 때 `migrate`를 실행. 워커 수는 `GUNICORN_WORKERS`(기본 2) | 없음 |
| `db` | PostgreSQL 16, `prod-db-data` 볼륨(개발용 `db-data`와 별개) | 없음 |

- 프론트와 `/api`가 같은 origin이라 세션 쿠키·CSRF가 그대로 동작합니다. CSRF는 요청 Host와 같은 Origin을 허용하므로 포트를 바꿔도(`PROD_HTTP_PORT`) 추가 설정이 필요 없습니다.
- 운영 모드(`DJANGO_DEBUG=false`)에서는 **모의 로그인이 꺼지고**(`POST /api/auth/mock-login`이 404) 예시 시크릿 키(`change-me`)로는 기동하지 않습니다. 로그인은 42 OAuth(`FORTYTWO_UID/SECRET`을 `.env`에 넣은 경우)로만 가능하며, 없으면 모의 로그인이 막혀 있는지까지만 확인할 수 있습니다.
- `docker-compose.prod.yml`은 로컬 http 검증을 위해 backend에 `DJANGO_COOKIE_SECURE=false`를 지정합니다. HTTPS로 실제 배포할 때는 이 줄을 지워 Secure 쿠키(기본값)를 사용해야 합니다.
- Django는 정적 파일을 서빙하지 않습니다(JSON API만 제공). 정적 파일은 모두 `web`이 서빙합니다.
- `.env`(비밀값)는 이미지에 포함되지 않고 compose의 `env_file`로만 주입됩니다. 이미지 빌드 제외 목록은 루트 `.dockerignore`와 `backend/.dockerignore`.
- 개발용(`docker-compose.yml`)과 운영 구성은 동시에 띄울 수 있습니다(프로젝트 이름이 `gs42`, `gs42-prod`로 다르고 운영 구성은 `PROD_HTTP_PORT`만 호스트에 엽니다).
- 이 구성은 HTTPS 없이 Secure 쿠키를 끄므로 **루프백(`127.0.0.1`)에만 포트를 엽니다**. 다른 PC에서는 접속할 수 없습니다.
- 외부 접속용 배포(AWS, 도메인, HTTPS 인증서)는 이 범위에 포함되지 않으며 필요해지면 별도 이슈로 진행합니다.
