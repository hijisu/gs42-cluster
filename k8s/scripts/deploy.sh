#!/usr/bin/env bash
# 사용법 (전체 순서는 k8s/README.md):
#   k8s/scripts/deploy.sh [태그]           매니페스트 적용 + 롤아웃 대기 (태그 기본값: build.sh 가 마지막으로 만든 태그)
#   k8s/scripts/deploy.sh job import-books  도서 518종 가져오기 Job
#   k8s/scripts/deploy.sh job seed-demo     시연 데이터 Job (DJANGO_DEBUG=true 에서만 동작)
#   k8s/scripts/deploy.sh diff [태그]       적용 전 차이 확인(클러스터 변경 없음)
# 컨텍스트는 K8S_CONTEXT(기본 z2mini = hijaeui-server-1).
set -euo pipefail
cd "$(dirname "$0")/.."
CTX="${K8S_CONTEXT:-z2mini}"
NS=gs42-cluster
K="kubectl --context $CTX"

tag_of() { echo "${1:-$(cat .last-tag 2>/dev/null || true)}"; }
render() { # 이미지 태그를 치환한 매니페스트
  local tag; tag="$(tag_of "${1:-}")"
  [ -n "$tag" ] || { echo "태그가 없습니다. 먼저 build.sh 를 실행하거나 태그를 지정하세요." >&2; exit 1; }
  kubectl kustomize . | sed "s#gs42-backend:local#gs42-backend:$tag#g; s#gs42-web:local#gs42-web:$tag#g"
}

case "${1:-}" in
  job)
    name="${2:?job 이름: import-books | seed-demo}"
    tag="$(tag_of)"; [ -n "$tag" ] || { echo "태그가 없습니다." >&2; exit 1; }
    sed "s#gs42-backend:local#gs42-backend:$tag#g" "jobs/$name.yaml" | $K create -f -
    $K -n $NS wait --for=condition=complete job -l app=backend-job --timeout=300s || true
    $K -n $NS logs -l app=backend-job --tail=20
    ;;
  diff)
    render "${2:-}" | $K diff -f - || true
    ;;
  *)
    [ -f secret.yaml ] || { echo "secret.yaml 이 없습니다. 먼저 k8s/scripts/make-secret.sh" >&2; exit 1; }
    render "${1:-}" | $K apply -f -
    $K -n $NS rollout status statefulset/db --timeout=300s
    $K -n $NS rollout status deploy/backend --timeout=300s
    $K -n $NS rollout status deploy/web --timeout=120s
    $K -n $NS get pods
    ;;
esac
