# syntax=docker/dockerfile:1
# 운영용 웹 이미지: 프론트를 빌드해 Caddy 로 서빙한다. 빌드 컨텍스트는 저장소 루트.
FROM node:22-slim AS build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM caddy:2-alpine
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/frontend/dist /srv
EXPOSE 80
