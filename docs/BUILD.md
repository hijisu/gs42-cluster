# 빌드·실행 가이드

실행·테스트·빌드 방법의 기준 문서입니다. **명령이나 환경변수가 바뀌면 같은 PR에서 이 문서도 갱신합니다**(`.env.example`의 키는 이 문서에 모두 있어야 하며 CI가 검사합니다).

## 빠른 시작 (Docker)

```bash
cp .env.example .env                 # 처음 한 번
docker compose up --build            # DB·백엔드·프론트 (첫 실행은 몇 분)
```

1. http://localhost:5173 에 접속하면 로그인 화면이 나옵니다. 개발 환경에서는 **모의 로그인**(교육생 / 운영팀) 버튼("개발용 모의 로그인")으로 바로 들어갈 수 있습니다.
2. 화면에 보여 줄 예시 데이터가 필요하면(선택):
   ```bash
   docker compose exec backend python manage.py seed_meeting_demo   # 면담 슬롯·기본 담당자
   docker compose exec backend python manage.py seed_review_demo    # 교육과정·후기
   ```
3. 테스트: `docker compose exec backend pytest -q`, `docker compose exec frontend npm test`.
4. 실제 42 로그인은 [42 OAuth 앱 등록](#42-oauth-앱-등록)을 마친 뒤 가능합니다.

| 알고 싶은 것 | 위치 |
| --- | --- |
| 요구 버전, 환경변수 | [요구 사항](#요구-사항), [환경변수](#환경변수) |
| 컨테이너 없이 직접 실행 | [백엔드](#백엔드), [프론트엔드](#프론트엔드) |
| PR 전에 돌릴 검사 | [CI](#ci) |
| 팀 작업 규칙(브랜치·커밋·리뷰) | [팀 작업 방식](#팀-작업-방식) |
| 시연(회의실·면담 시나리오, 자동 점검) | [DEMO.md](DEMO.md) |

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
| `COMPOSE_PROJECT_NAME` | **개발용** compose 프로젝트 이름(기본 `gs42`). 한 PC에서 클론을 여러 개 돌릴 때만 변경. 운영 구성은 `-p <이름>-prod`로 따로 지정 | - |
| `DB_HOST_PORT` / `BACKEND_HOST_PORT` / `FRONTEND_HOST_PORT` | compose가 호스트에 여는 포트(기본 5432 / 8000 / 5173). 컨테이너 안 포트는 고정 | - |
| `FORTYTWO_UID` / `FORTYTWO_SECRET` / `FORTYTWO_REDIRECT_URI` | 42 OAuth 앱 정보 | O |
| `STAFF_INTRA_IDS` | 교육운영팀 intra login 목록(쉼표 구분) | O |
| `FRONTEND_ORIGIN` / `VITE_API_BASE_URL` | 프론트엔드 주소·API 경로. compose에서는 `FRONTEND_ORIGIN`이 `FRONTEND_HOST_PORT`로 자동 계산됨 | O |
| `PROD_HTTP_PORT` | 운영 구성(`docker-compose.prod.yml`)이 호스트 루프백(`127.0.0.1`)에 여는 HTTP 포트. 기본 80 | - |
| `GUNICORN_WORKERS` | 운영 구성 backend(gunicorn)의 워커 수. 기본 2 | - |
| `DJANGO_COOKIE_SECURE` | (선택) Secure 쿠키 여부. 기본은 `DJANGO_DEBUG=false`일 때 true. 로컬 http 검증에서만 false | - |
| `API_PROXY_TARGET` | (선택) 호스트에서 `npm run dev`할 때 `/api` 프록시 대상. 기본 `http://localhost:8000`, compose는 `http://backend:8000` 고정 | - |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` / `VAPID_SUBJECT` | 웹 푸시(VAPID) 키와 연락처. 비우면 푸시가 꺼지고 앱 안 알림만 동작. 생성: `manage.py generate_vapid_keys` ([웹 푸시](#웹-푸시-vapid) 참고) | - |
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
- **`.env`를 수정한 뒤에는 `docker compose up -d`로 적용합니다.** `docker compose restart`는 `.env`(`env_file`)를 다시 읽지 않아 컨테이너 안의 값이 그대로 남습니다. `up -d`는 환경변수가 바뀐 서비스만 새로 만들며 DB 볼륨은 유지됩니다.
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

# 비밀번호 등은 루트 .env 에서 자동으로 읽는다. .env 는 compose 용(POSTGRES_HOST=db)이라 호스트 실행에서만 덮어쓴다.
export POSTGRES_HOST=localhost       # DB_HOST_PORT 를 바꿨다면 POSTGRES_PORT 도 같은 값으로 지정
python manage.py migrate
python manage.py runserver 8000     # GET http://localhost:8000/api/health

pytest                              # 도메인 테스트는 DB 없이, 통합 테스트는 pytest-django(DB 필요)
ruff check . && ruff format --check .
```

`DJANGO_DEBUG=false`에서는 `DJANGO_SECRET_KEY`가 필수입니다.

**도서 데이터**: 42gslib(https://42gslib.pages.dev/) 도서 518종은 `backend/library/data/books.json`에 들어 있습니다. 마이그레이션 후 `python manage.py import_books`(compose는 `docker compose exec backend python manage.py import_books`)로 가져옵니다. 도서 코드 기준 upsert라 여러 번 실행해도 건수가 늘지 않고, 신고·희망 도서 기록은 그대로 둡니다. 다른 파일은 `--file 경로`로 지정합니다.

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

### 웹 푸시 (VAPID)

브라우저 푸시는 서버의 VAPID 키가 있어야 켜집니다. **키가 없으면 푸시는 꺼지고 앱 안 알림만 동작**하며 `GET /api/push/public-key`와 구독 등록은 503(`push_not_configured`)을 돌려줍니다.

```bash
python manage.py generate_vapid_keys            # docker: docker compose exec backend python manage.py generate_vapid_keys
# 출력된 VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY 두 줄을 .env 에 붙여 넣는다 (개인키는 비밀값: 커밋·채팅·이슈 금지)
docker compose up -d                            # .env 변경 적용 (restart 는 .env 를 다시 읽지 않는다)
```

- 서버는 `VAPID_PRIVATE_KEY`에서 공개키를 계산해 브라우저에 내려줍니다. `.env`의 `VAPID_PUBLIC_KEY`가 개인키와 짝이 아니면 경고를 남기고 계산한 값을 씁니다. 개인키 형식이 잘못돼도 서버는 뜨고 푸시만 꺼집니다(로그 확인).
- 알림은 면담 확정·시간 제안, 회의실 승인·반려·대체, 후기 요청 때 만들어지며, 구독한 기기마다 `{title, body, link, type}`이 암호화(aes128gcm)되어 전송됩니다. 구독이 없는 사용자는 앱 안 알림만 받고, 푸시 서비스가 만료(404/410)로 응답한 구독은 자동으로 삭제됩니다.
- 구독 API: `GET /api/push/public-key`, `POST /api/push/subscriptions`(브라우저의 `PushSubscription.toJSON()`), `DELETE /api/push/subscriptions`(body `{endpoint}`).
- 서버가 구독 endpoint로 직접 요청을 보내므로(SSRF 방지) **https이고 알려진 푸시 서비스 호스트만 허용**합니다: `fcm.googleapis.com`(Chrome·Edge·Samsung), `*.push.services.mozilla.com`(Firefox), `*.push.apple.com`(Safari/iOS), `*.notify.windows.com`. 공백·제어문자·비ASCII가 있거나 형식이 잘못된 주소를 포함해 그 밖의 주소는 400(`invalid_subscription`)입니다. 서버에서 이 호스트들로 나가는 HTTPS 연결이 필요합니다.
- 브라우저 요건: `localhost`는 보안 컨텍스트라 HTTPS 없이 확인할 수 있고, 그 외 주소는 HTTPS가 필요합니다. **iOS(16.4+)는 홈 화면에 설치한 PWA에서만** 푸시가 동작합니다.
- 확인 방법: 앱에서 알림(벨) → '푸시 알림 켜기' → 권한 허용 → 다른 계정으로 면담 확정 또는 회의실 승인 → 푸시 수신. 이 마지막 단계(실제 브라우저·푸시 서비스 수신)는 자동 테스트가 아니라 사람이 확인합니다.

## 프론트엔드

컨테이너 없이 호스트에서 실행하려면 Node.js 22가 필요합니다. 백엔드(`http://localhost:8000`)를 먼저 띄워 두면 `/api`가 그쪽으로 프록시됩니다(다른 주소는 `API_PROXY_TARGET`).

```bash
cd frontend
npm ci             # package-lock.json 기준으로 설치
npm run dev        # 개발 서버 (http://localhost:5173)
npm run typecheck  # 타입 검사
npm run lint       # ESLint
npm test           # vitest
npm run build      # tsc + vite build (PWA manifest·서비스워커 생성)
```

- 구조: `src/app`(라우터·메뉴 정의), `src/components`(공통 컴포넌트), `src/styles`(스타일·토큰), `src/features/<context>/`(기능별 화면).
- 라우트는 `src/app/routes.ts`의 메뉴 정의와 `design/*.dc.html` 파일 이름이 1:1이다.
- 서비스워커는 `src/sw.ts`(vite-plugin-pwa `injectManifest`): 프리캐시 + 웹 푸시 표시·클릭 이동. 푸시 구독 UI는 알림 모달(벨)의 '푸시 알림 켜기'. 개발 서버(`npm run dev`)에서도 서비스워커가 등록된다(`devOptions`, module 서비스워커라 Chrome 계열 기준이며 Firefox는 개발 서버에서 미지원 → `npm run build && npm run preview`로 확인). 서비스워커가 준비되지 않으면 버튼은 3초 뒤 활성화되고 '새로고침 후 다시 시도' 안내가 표시된다. 서비스워커는 `npm run build` 후 `npm run preview`(또는 localhost)에서 확인한다. iOS는 홈 화면에 설치한 PWA에서만 푸시가 동작한다.

## CI

`.github/workflows/ci.yml`이 PR과 `main` 푸시마다 두 job을 실행합니다. PR을 올리기 전에 같은 명령을 로컬에서 먼저 돌려 보세요.

| job | 검사 | 로컬 명령 |
| --- | --- | --- |
| `backend` | 린트·포맷, DDD 계층 의존 방향, 마이그레이션 누락, 테스트 | `cd backend && ruff check . && ruff format --check . && lint-imports && python manage.py makemigrations --check --dry-run && pytest -q` |
| `frontend` | 타입 검사, 린트, 테스트, 빌드 | `cd frontend && npm run typecheck && npm run lint && npm test && npm run build` |

- CI의 백엔드는 운영과 같은 `DJANGO_DEBUG=false`, 더미 시크릿, `postgres:16` 서비스로 실행합니다(`.env` 없음).
- `lint-imports`(import-linter, 설정은 `backend/.importlinter`)는 AGENTS.md의 규칙을 검사합니다: `domain`·`application`은 Django/DRF를 import하지 않고, `domain ← application ← interfaces` 바깥 계층을 거꾸로 import하지 않으며, `infrastructure`는 `interfaces`를 import하지 않고, `accounts`·`meetings`·`rooms`·`reviews`는 `notifications`를 import하지 않고(이벤트로만 연동), `meetings`·`rooms`·`reviews`는 서로를 import하지 않습니다. 새 Context나 앱을 추가하면 `.importlinter`의 `root_packages`와 계약에 추가합니다.
- 프론트의 ESLint는 TypeScript 7에 JS 컴파일러 API가 없어 `typescript-eslint` 대신 Babel 파서(`eslint.config.js`)를 씁니다. 타입 관련 검사는 `tsc`가 맡습니다.
- **main 보호 규칙**(ruleset `main protection`, 2026-10-17 적용): PR 필수(main 직접 푸시 금지), 병합은 squash만, force push·브랜치 삭제 금지, 필수 체크는 `backend`·`frontend`(위 CI job)입니다. 승인 수는 0이며 위험 PR의 `review:ok` 라벨 규칙은 규칙(ruleset)이 아니라 팀 규칙입니다. 규칙을 바꾸려면 사람이 repo Settings → Rules에서 합니다.

## 42 OAuth 앱 등록

실제 42 로그인을 쓰려면 intra에 OAuth 앱을 등록하고 `UID/SECRET`을 `.env`에 넣습니다. 모의 로그인만 쓸 때는 필요 없습니다. (이 절차는 문서 기준이며 실제 계정으로의 로그인 확인은 아직 사람 확인 대기 중입니다. intra 화면 문구는 바뀔 수 있습니다.)

1. 42 intra에 로그인해 **Settings → API → "Register a new app"**(https://profile.intra.42.fr/oauth/applications/new)으로 이동합니다.
2. 이름(예: `42gs-cluster dev`)을 적고, **Redirect URI**에 `.env`의 `FORTYTWO_REDIRECT_URI`와 **똑같은 값**을 등록합니다. 기본값은 `http://localhost:8000/api/auth/callback`이며 `BACKEND_HOST_PORT`를 바꿨다면 그 포트를 씁니다. Scope는 `public`이면 충분합니다.
3. 발급된 **UID**와 **SECRET**을 `.env`의 `FORTYTWO_UID`, `FORTYTWO_SECRET`에 넣습니다. **채팅·이슈·PR·커밋에 붙여 넣지 않습니다**(`.env`는 gitignore 대상).
4. 교육운영팀 계정은 `.env`의 `STAFF_INTRA_IDS`에 intra login을 쉼표로 적습니다(42 응답의 `staff?`는 보조). 바꾼 뒤 **`docker compose up -d`**로 적용합니다(`restart`는 `.env`를 다시 읽지 않아 값이 바뀌지 않습니다).
5. http://localhost:5173/login 에서 **"42 intra로 로그인"**을 누르고 승인하면 사이드바에 내 `intra_id`가 보입니다. 운영팀으로 등록한 계정이면 '교육운영팀 화면 보기' 토글이 나타납니다.

로그인에 실패하면 `/login?error=<코드>`로 돌아옵니다.

| 증상 | 원인 |
| --- | --- |
| `error=invalid_state` | 로그인 중 세션이 끊김(다른 브라우저로 콜백, 쿠키 차단, 오래 지연) → 처음부터 다시 |
| `error=auth_failed` | UID/SECRET 오류, redirect URI 불일치, 42 API 오류 → `docker compose logs backend`의 `42 OAuth 로그인 실패 stage=… status=… reason=…` 줄을 확인. `stage=token status=401`은 UID/SECRET·redirect URI 오류, `status=403`은 요청 거부, `reason=network_error/timeout`은 네트워크 문제, `stage=profile`은 토큰 이후 프로필 조회 실패. 코드·토큰·비밀값은 로그에 남지 않는다 |
| `/api/auth/login` 이 503 `oauth_not_configured` | `FORTYTWO_UID`가 비어 있음 |

운영(HTTPS·도메인) 배포용 redirect URI는 도메인이 정해진 뒤 별도로 등록합니다. 캠퍼스 제한 여부는 실계정 응답을 확인한 뒤 결정합니다.

## 팀 작업 방식

- 작업 단위·브랜치·PR·리뷰 규칙: [AGENTS.md](../AGENTS.md) (이슈 1개 = 브랜치 1개 = PR 1개, 브랜치명 `feat/<이슈번호>-<slug>`, PR 본문 `Closes #N`, main 직접 푸시 금지)
- 커밋 메시지: [CONTRIBUTING.md](../CONTRIBUTING.md) (Conventional Commits)
- 저장소 구조와 두 저장소 동기화: [docs/REPOSITORY.md](REPOSITORY.md)
- 시안과 구현의 차이 기록: [docs/DESIGN_DIFFS.md](DESIGN_DIFFS.md)
- 마이그레이션·CI·공통 파일(`docker-compose*.yml`, `.env.example`, 이 문서) 변경은 **위험 PR**이라 교차 리뷰어의 `review:ok` 라벨 후 머지합니다.

## 배포 (운영 구성 로컬 검증)

AWS 서버·도메인·외부 HTTPS는 아직 없습니다. 운영과 같은 구성(gunicorn, 정적 파일 서빙, 같은 origin의 `/api` 프록시, `DEBUG=false`)을 **`http://localhost`에서만** 컨테이너로 띄워 검증합니다.

```bash
cp .env.example .env     # 이미 있으면 생략
# .env 의 DJANGO_SECRET_KEY 를 실제 값으로 바꾼다 (예시 값 change-me 로는 기동하지 않는다)
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

docker compose -p gs42-prod -f docker-compose.prod.yml up -d --build
open http://localhost        # PROD_HTTP_PORT 를 바꿨다면 http://localhost:<포트>
docker compose -p gs42-prod -f docker-compose.prod.yml logs -f backend
docker compose -p gs42-prod -f docker-compose.prod.yml down          # 데이터 유지 / -v 는 DB 볼륨까지 삭제
```

**모든 운영 구성 명령에 `-p <이름>-prod`를 붙입니다.** `.env`의 `COMPOSE_PROJECT_NAME`(개발용 프로젝트 이름)이 compose 파일의 `name:`보다 우선하므로, `-p` 없이 실행하면 개발용 스택과 같은 프로젝트로 묶여 `db`·`backend` 서비스가 서로를 덮어씁니다. 한 PC에서 클론을 여러 개 쓰면 클론마다 `-p gs42-b-prod`처럼 다른 이름을 씁니다.

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
- 개발용(`docker-compose.yml`, 프로젝트 `gs42`)과 운영 구성(프로젝트 `gs42-prod`)은 컨테이너·네트워크·DB 볼륨이 서로 달라 동시에 띄울 수 있습니다. 운영 구성이 호스트에 여는 포트는 `PROD_HTTP_PORT`뿐이고, 어느 한쪽을 `down`해도 다른 쪽은 영향을 받지 않습니다.
- 이 구성은 HTTPS 없이 Secure 쿠키를 끄므로 **루프백(`127.0.0.1`)에만 포트를 엽니다**. 다른 PC에서는 접속할 수 없습니다.
- 외부 접속용 배포(AWS, 도메인, HTTPS 인증서)는 이 범위에 포함되지 않으며 필요해지면 별도 이슈로 진행합니다.
