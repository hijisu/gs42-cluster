# syntax=docker/dockerfile:1
# k8s 배포용 웹 이미지. 빌드 컨텍스트는 저장소 루트(`docker build -f k8s/web.Dockerfile .`).
# deploy/web.Dockerfile 과 같지만 프론트를 개발 번들(import.meta.env.DEV=true)로 빌드한다.
# 이유: 로그인 화면의 "개발용 모의 로그인" 버튼이 개발 번들에서만 나온다(백엔드 DJANGO_DEBUG=true 와 짝).
# OAuth 만 쓸 때는 deploy/web.Dockerfile(운영 번들)로 바꾸고 백엔드 DJANGO_DEBUG=false 로 한다.
FROM node:22-slim AS build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
ENV NODE_ENV=development
RUN npx vite build --mode development \
    && grep -rl "개발용 모의 로그인" dist/assets > /dev/null

FROM caddy:2-alpine
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/frontend/dist /srv
EXPOSE 80
