#!/usr/bin/env bash
# backend/web 이미지를 amd64 로 빌드해 hijaeui-server-1 의 containerd 에 가져온다(레지스트리 없이).
# 사용법: k8s/scripts/build.sh [태그]   (태그 기본값: git 짧은 SHA, 작업 트리가 더러우면 -dirty)
# 필요: docker(buildx), ssh hijae@hijaeui-server-1 접속(사용자가 microk8s 그룹, sudo 불필요). 전체 순서는 k8s/README.md.
set -euo pipefail
cd "$(dirname "$0")/../.."
HOST="${K8S_NODE:-hijae@hijaeui-server-1}"
TAG="${1:-$(git rev-parse --short HEAD)$(git diff --quiet && git diff --cached --quiet || echo -dirty)}"

echo "태그: $TAG"
docker buildx build --platform linux/amd64 --target prod -t "gs42-backend:$TAG" --load backend
docker buildx build --platform linux/amd64 -f k8s/web.Dockerfile -t "gs42-web:$TAG" --load .

for image in "gs42-backend:$TAG" "gs42-web:$TAG"; do
  echo "$HOST 로 $image 전송"
  # sudo 없이 microk8s 그룹 권한으로 containerd 소켓에 직접 가져온다.
  docker save "$image" | ssh "$HOST" 'ctr --address /var/snap/microk8s/common/run/containerd.sock -n k8s.io images import -'
done
echo "$TAG" > k8s/.last-tag
echo "완료. 배포: k8s/scripts/deploy.sh $TAG"
