# 저장소 구조와 동기화

## 폴더 구조

| 경로 | 역할 |
| --- | --- |
| `backend/` | Django REST 백엔드, DDD 4계층 (#2에서 초기화) |
| `frontend/` | React·TypeScript·Vite PWA (#3에서 초기화) |
| `design/` | 구현의 출발점인 화면 시안 |
| `docs/` | [빌드·실행 가이드](BUILD.md)와 개발 문서 |
| `presentation/` | 개발 완료 후 작성할 발표자료, 현재는 `.gitkeep`만 유지 |
| `.github/` | PR 템플릿과 이후 CI 워크플로 |
| `hijisu_assets/` | 제출한 계획서의 이미지 |

빈 폴더는 `.gitkeep`으로 추적하므로 새로 클론해도 동일한 구조를 받습니다.

## 두 저장소 동기화

개발·이슈·PR·리뷰·squash 머지의 기준은 `hijisu/gs42-cluster`입니다.
`42gyeongsan-hackathon-2026/42.Zip-team10`에는 머지된 `main`만 동기화합니다.
기능 브랜치의 push는 개발 저장소 URL을 명시하여 제출 저장소에 올리지 않습니다.

```bash
git push https://github.com/hijisu/gs42-cluster.git feat/<번호>-<slug>
```

각 클론에서 fetch URL과 push URL을 확인합니다.

```bash
git remote get-url origin
git remote get-url --push --all origin
```

fetch URL은 개발 저장소, push URL은 아래 두 개여야 합니다.

```text
https://github.com/hijisu/gs42-cluster.git
https://github.com/42gyeongsan-hackathon-2026/42.Zip-team10.git
```

push URL이 아직 기본값 하나뿐인 새 클론에서는 다음과 같이 설정합니다.
이미 두 URL이 있다면 다시 추가하지 않습니다.

```bash
git remote set-url --add --push origin https://github.com/hijisu/gs42-cluster.git
git remote set-url --add --push origin https://github.com/42gyeongsan-hackathon-2026/42.Zip-team10.git
```

PR을 개발 저장소에서 머지한 뒤, 변경 사항이 없는 작업 트리에서 실행합니다.
아래 push는 이미 머지된 커밋을 양쪽에 동기화하는 용도입니다. main의 직접 커밋은 금지합니다.

```bash
git switch main
git pull --ff-only origin main
git push origin main
```

두 원격 push는 원자적이지 않습니다. 일부가 실패하면 각각의 main SHA를 확인하고
실패한 원격만 다시 동기화합니다. 분기된 이력은 force push로 덮어쓰지 않고 팀에 확인합니다.

```bash
git ls-remote https://github.com/hijisu/gs42-cluster.git refs/heads/main
git ls-remote https://github.com/42gyeongsan-hackathon-2026/42.Zip-team10.git refs/heads/main
```
