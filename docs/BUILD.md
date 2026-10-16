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

## 42 OAuth 앱 등록

TBD (intra 앱 등록 절차, redirect URI)

## 배포

TBD (Phase 1 배포 이슈에서 작성)
