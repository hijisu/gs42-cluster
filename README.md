# 42gs-cluster

42경산 교육생의 요청(면담·회의실 예약 등)과 교육운영팀의 처리를 한곳에서 관리하고, 흩어진 캠퍼스 정보(오아시스 도서, 교육과정 후기)를 연결하는 웹 서비스입니다.
팀 hijisu (대표 송희재 · 팀원 신지수). 기획 배경과 로드맵은 [개발 계획서](docs/PROPOSAL.md)를 참고하세요.

## 1. 서비스 소개

교육생은 신청하고, 교육운영팀은 처리하며, 두 화면이 같은 상태를 공유합니다.

| 기능 | 교육생 | 교육운영팀 |
| --- | --- | --- |
| 면담 | 유형·희망 시간·사유로 신청, 취소, 확정 일정 확인 | 가능 시간·기본 담당자 설정, 담당자 배정, 확정 또는 다른 시간 제안 |
| 회의실 | 현황 확인, 예약 요청, 승인 후 이용수칙 확인 | 승인·반려·대체 장소 제안, 시간 충돌 경고, 장소·이용수칙·사용 불가 시간 관리 |
| 오아시스 도서 | 검색, 분실·훼손 신고, 희망 도서 신청 | 도서 관리, 신고·희망 도서 처리 |
| 교육과정 후기 | 후기 작성(익명 선택)·열람 | 교육과정·참여자 등록, 후기 요청 |
| 알림 | 앱 안 알림(벨), 웹 푸시(선택) | 동일 |

구현 기술: Django 5.2 (REST) · PostgreSQL 16 · React + TypeScript + Vite (PWA) · Caddy(리버스 프록시) · Docker Compose.

## 2. 실행 환경 · 필요한 도구

| 도구 | 버전 | 필수 |
| --- | --- | --- |
| Docker Engine (macOS는 Docker Desktop) | 24 이상 (29에서 확인) | 필수 |
| Docker Compose | v2 이상 (`docker compose` 명령, v5에서 확인) | 필수 |
| git | 아무 버전 | 필수 |
| make | GNU Make 3.81 이상 (macOS 기본 포함) | 선택. 없으면 아래 "make 없이" 명령을 사용 |

Python·Node.js·PostgreSQL을 호스트에 설치할 필요가 없습니다. 모두 컨테이너 안에서 실행됩니다(Python 3.13, Node 22, PostgreSQL 16).
지원 OS는 macOS와 Linux입니다. 기본으로 TCP **5173** 포트를 사용하므로 비어 있어야 합니다(바꾸는 방법은 아래 "문제 해결").

## 3. 설치 · 실행

```bash
git clone https://github.com/42gyeongsan-hackathon-2026/42.Zip-team10.git
cd 42.Zip-team10
cp .env.example .env     # 기본값 그대로 실행됩니다 (4. 환경 변수)
make dev                 # 빌드 → 기동 → 시연 데이터와 도서 518종 입력. 첫 실행은 이미지 빌드로 몇 분 걸립니다
```

`make dev`가 끝나면 `개발 서버: http://localhost:5173`이 출력됩니다. 같은 명령을 다시 실행해도 안전합니다(데이터를 지우지 않음).

**make 없이** 같은 결과를 내려면:

```bash
docker compose up -d --build
docker compose exec backend python manage.py seed_demo      # 시연 데이터 (백엔드가 뜰 때까지 10~30초 걸리면 재시도)
docker compose exec backend python manage.py import_books   # 도서 518종
```

| 하고 싶은 일 | 명령 |
| --- | --- |
| 중지(데이터 유지) | `docker compose down` |
| 데이터까지 완전 삭제 | `docker compose down -v` |
| 시연 데이터를 처음 상태로 | `make demoreset` |
| 로그 보기 | `docker compose logs -f backend` |
| 운영 구성(gunicorn, `DEBUG=false`)으로 실행 | `make run` — `.env`의 `DJANGO_SECRET_KEY`를 실제 값으로 바꿔야 하고 모의 로그인이 꺼집니다. 자세한 내용은 [docs/BUILD.md](docs/BUILD.md#배포-운영-구성-로컬-검증) |

## 4. 환경 변수

`cp .env.example .env`로 만든 `.env`를 사용합니다. **심사·확인 목적이라면 값을 하나도 바꾸지 않아도 됩니다**(모의 로그인으로 모든 기능을 확인할 수 있습니다). `.env`는 비밀값이 들어갈 수 있어 커밋하지 않습니다(gitignore).

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `FRONTEND_HOST_PORT` | `5173` | 접속 포트. 충돌하면 다른 값으로 변경 |
| `FRONTEND_BIND` | `0.0.0.0` | 포트를 여는 주소. 같은 네트워크의 다른 기기에서 접속하려면 그대로, 이 PC에서만 쓰려면 `127.0.0.1` |
| `DJANGO_DEBUG` | `true` | `true`일 때만 모의 로그인 허용 |
| `DJANGO_SECRET_KEY` | `change-me` | 개발 모드는 예시 값으로 동작. 운영 구성(`make run`)은 실제 값 필수 |
| `POSTGRES_*` | `.env.example` 참조 | DB 이름·사용자·비밀번호. compose가 내부 네트워크로 연결(호스트에는 열리지 않음) |
| `FORTYTWO_UID` / `FORTYTWO_SECRET` / `STAFF_INTRA_IDS` | 비어 있음 | **선택.** 실제 42 intra 로그인에만 필요. 등록 방법은 [BUILD.md](docs/BUILD.md#42-oauth-앱-등록) |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` | 비어 있음 | **선택.** 웹 푸시. 비우면 앱 안 알림만 동작 |
| `SLACK_BOT_TOKEN` | 비어 있음 | 사용하지 않음(Slack 연동은 구현 범위 밖) |

전체 변수와 설명은 [.env.example](.env.example)과 [docs/BUILD.md](docs/BUILD.md#환경변수)에 있습니다. `.env`를 고친 뒤에는 `docker compose up -d`로 적용합니다(`restart`는 `.env`를 다시 읽지 않습니다).

## 5. 접속 · 확인 방법

**주소:** http://localhost:5173 (같은 네트워크의 다른 기기에서는 `http://<이 PC의 IP>:5173`)

**테스트 계정:** 로그인 화면의 **"개발용 모의 로그인"** 영역에서 `교육생` 또는 `운영팀` 버튼을 누르면 비밀번호 없이 들어갑니다. 개발 모드(프론트 개발 서버)에서만 나타납니다. 교육생과 운영팀 화면을 동시에 보려면 브라우저 창을 둘 쓰세요(일반 창 + 시크릿 창).

| 모의 계정 | 역할 | 볼 수 있는 것 |
| --- | --- | --- |
| 교육생 (`student`) | 교육생 | 면담 신청, 회의실 예약, 도서, 후기 |
| 운영팀 (`staff`) | 교육운영팀 | 면담·회의실·도서·교육과정 관리 화면 |

**미리 들어 있는 데이터(`make dev`):** 도서 518종, 면담 유형 6종과 평일 10~12시·13~17시 기본 가능 시간, 회의실 예약 예시(승인 1건·충돌하는 대기 1건 포함), 교육과정 3개와 후기 예시.

**3분 확인 시나리오**

1. 교육생으로 로그인 → **회의실 예약**에서 날짜·장소·시간·목적·인원을 입력하고 요청 → "승인 대기"로 나타남
2. 다른 창에서 운영팀으로 로그인 → **회의실 관리**에서 그 요청을 **승인** (겹치는 요청은 승인할 수 없음)
3. 교육생 창에서 알림(벨)과 **승인됨** 상태, 이용수칙 확인
4. 같은 방식으로 **면담 신청** → 운영팀이 담당자 배정·일정 확정 → 교육생이 확정 일정 확인

화면별 상세 시나리오는 [docs/DEMO.md](docs/DEMO.md)에 있습니다.

**동작 확인 명령**

```bash
curl http://localhost:5173/api/health                  # {"status":"ok"} 이면 정상
docker compose exec backend pytest -q                  # 백엔드 테스트
docker compose exec frontend npm test                  # 프론트엔드 테스트
```

실제 42 로그인은 선택 사항입니다. intra에 OAuth 앱을 등록한 뒤 `.env`에 입력하는 방법은 [docs/BUILD.md](docs/BUILD.md#42-oauth-앱-등록)에 있습니다.

## 6. 문제 해결

| 증상 | 해결 |
| --- | --- |
| `port is already allocated` / 5173 사용 중 | `.env`의 `FRONTEND_HOST_PORT`를 다른 값(예: 5273)으로 바꾸고 `docker compose up -d`, 접속 주소의 포트도 바꿔서 접속 |
| 모의 로그인 버튼이 안 보이거나 실패 | `.env`의 `DJANGO_DEBUG=true` 확인 후 `docker compose up -d` |
| `Cannot connect to the Docker daemon` / Linux에서 권한 오류 | Docker 데몬 실행 확인, Linux는 사용자를 `docker` 그룹에 추가하거나 `sudo` 사용 |
| `make dev`가 "백엔드가 준비되지 않았습니다" | `docker compose logs backend`로 오류 확인. 대개 첫 빌드 중 네트워크 문제이므로 `make dev` 재실행 |
| 처음부터 다시 | `docker compose down -v && make dev` |

## 문서

- [docs/BUILD.md](docs/BUILD.md) 빌드·실행·테스트 상세 · [docs/DEMO.md](docs/DEMO.md) 시연 가이드 · [docs/PROPOSAL.md](docs/PROPOSAL.md) 개발 계획서
- 팀 작업 규칙: [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md)
