# gs42-cluster

42경산 교육생 요청(면담·회의실 등)과 교육운영팀 처리를 한곳에서 관리하는 웹 서비스. 기획은 README.md 참고.

## 구조

- `backend/` Django REST + PostgreSQL (DDD), `frontend/` React+TS+Vite PWA, `design/` 화면 시안, `docs/` 문서, `presentation/` 발표자료(개발 후 작성)
- 빌드·실행·테스트 명령은 docs/BUILD.md 를 따른다. 명령이 바뀌면 같은 PR에서 BUILD.md도 갱신한다.

## 백엔드 아키텍처 (DDD)

- Bounded Context = `accounts` `meetings` `rooms` `reviews` `notifications`. 각 앱은 `domain/ application/ infrastructure/ interfaces/` 4계층.
- 의존 방향: `interfaces → application → domain ← infrastructure`. `domain`은 Django/DRF를 import하지 않는다.
- 상태 전이·충돌 판단 등 비즈니스 규칙은 도메인 객체에 둔다(View/Serializer에 두지 않는다). Context 간 연동은 도메인 이벤트로 하고, `meetings`/`rooms`가 `notifications`를 직접 import하지 않는다.
- 도메인·유스케이스 테스트는 DB 없이 pytest, 통합 테스트만 pytest-django.

## 디자인

- `design/*.dc.html` 시안은 출발점이며 구현 중 바뀔 수 있다. 화면이 시안과 달라지면 같은 PR에서 시안/이슈를 갱신한다.
- API는 표시 문구가 아니라 도메인 코드(상태·유형)를 내려주고, 문구 매핑은 프론트에서 한다.

## 작업 방식

- 작업은 GitHub 이슈·마일스톤(Phase 0~5) 단위로 진행한다. 이슈 1개 = 브랜치 1개 = PR 1개 = squash 머지.
- 브랜치명 `feat/<이슈번호>-<slug>`(fix/docs/chore 동일), PR 본문에 `Closes #N`. main 직접 푸시 금지, CI 통과 후 머지(승인은 생략).
- 페이즈(마일스톤)가 끝나면 main에 태그(v0.x)를 찍는다. 페이즈 통합 브랜치는 만들지 않는다.
- 백엔드 PR은 `backend/**`, 프론트 PR은 `frontend/**`만 건드리는 것을 기본으로 한다. 화면 PR은 해당 API PR이 머지된 뒤 올린다.

## 환경변수·비밀값

- 비밀값(42 OAuth UID/SECRET, Slack/VAPID 키 등)은 `.env`에만 두고 커밋하지 않는다(`.env`는 gitignore).
- 새 환경변수는 반드시 `.env.example`에 키와 설명을 추가한다(값은 비우거나 예시 placeholder).

## 커밋 컨벤션

커밋 메시지는 CONTRIBUTING.md 의 Conventional Commits 규칙을 따른다.
