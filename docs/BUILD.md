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

TBD (설치 · 실행 · 테스트 · 린트)

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
