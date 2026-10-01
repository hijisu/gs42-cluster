# 커밋 컨벤션

[Conventional Commits](https://www.conventionalcommits.org/ko/v1.0.0/)를 따릅니다.

## 형식

```
<type>(<scope>): <subject>

<body>

<footer>
```

- `scope`, `body`, `footer`는 선택 사항입니다.
- 제목(subject)은 50자 이내, 마침표 없이 명령형/간결체로 작성합니다.
- 제목과 본문 사이에 빈 줄을 둡니다.
- 본문에는 **무엇을**보다 **왜** 바꿨는지를 적습니다.

## Type

| type | 용도 |
|------|------|
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `style` | 코드 의미 변화 없는 포맷팅 (공백, 세미콜론 등) |
| `refactor` | 기능 변화 없는 코드 구조 개선 |
| `perf` | 성능 개선 |
| `test` | 테스트 추가/수정 |
| `build` | 빌드 시스템, 의존성 변경 |
| `ci` | CI 설정 변경 |
| `chore` | 그 외 잡무 (설정, 기타 유지보수) |
| `revert` | 이전 커밋 되돌리기 |

## Footer

- 이슈 연결: `Closes #12`, `Refs #34`
- 호환성을 깨는 변경: type 뒤에 `!`를 붙이고 `BREAKING CHANGE: 설명`을 footer에 작성합니다.

## 예시

```
feat(auth): 42 OAuth 로그인 추가
```

```
fix(api): 클러스터 좌석 조회 시 null 응답 처리

좌석 정보가 없는 호스트에서 500이 발생하던 문제를 수정한다.

Closes #12
```

```
refactor!: 설정 파일 구조 변경

BREAKING CHANGE: config.yml의 `hosts` 키가 `clusters`로 변경됨
```
