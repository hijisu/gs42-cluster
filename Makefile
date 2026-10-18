# 개발·운영 구성을 한 명령으로 띄우고 초기 데이터를 넣는다. 사용법: `make` (또는 docs/BUILD.md '빠른 시작').
# .env 전체를 include 하지 않는다(비밀값 때문에 Make 가 깨지지 않게). 필요한 값만 한 줄씩 읽는다.
env_value = $(shell sed -n 's/^$(1)=//p' .env 2>/dev/null | head -n 1)

PROJECT   := $(or $(call env_value,COMPOSE_PROJECT_NAME),gs42)
PORT      := $(or $(call env_value,FRONTEND_HOST_PORT),5173)
PROD_PORT := $(or $(call env_value,PROD_HTTP_PORT),80)
PROD      := docker compose -p $(PROJECT)-prod -f docker-compose.prod.yml

.PHONY: help dev up stop clean demoreset

help:
	@echo "make dev        개발 모드로 띄우고 seed_demo, import_books 실행 (http://localhost:$(PORT))"
	@echo "make up         운영 모드로 띄우고 import_books만 실행 (http://localhost:$(PROD_PORT), .env 의 DJANGO_SECRET_KEY 필요)"
	@echo "make stop       개발·운영 구성을 모두 정지 (데이터는 유지)"
	@echo "make clean      개발·운영 구성을 모두 정지하고 DB 데이터까지 삭제"
	@echo "make demoreset  시연 데이터를 처음 상태로 (seed_demo --reset, 개발 모드가 떠 있어야 함)"

dev:
	@test -f .env || { echo ".env 가 없습니다. 먼저: cp .env.example .env"; exit 1; }
	docker compose up -d --build
	@echo "백엔드가 준비될 때까지 기다립니다(마이그레이션 포함)..."
	@docker compose exec -T backend sh -c 'i=0; until python -c "import urllib.request as u; u.urlopen(\"http://127.0.0.1:$$BACKEND_PORT/api/health\", timeout=3)" 2>/dev/null; do i=$$((i+1)); [ $$i -ge 90 ] && { echo "백엔드가 준비되지 않았습니다: docker compose logs backend"; exit 1; }; sleep 2; done'
	docker compose exec -T backend python manage.py seed_demo
	docker compose exec -T backend python manage.py import_books
	@echo "개발 서버: http://localhost:$(PORT)"

up:
	@test -f .env || { echo ".env 가 없습니다. 먼저: cp .env.example .env (그리고 DJANGO_SECRET_KEY 를 실제 값으로)"; exit 1; }
	$(PROD) up -d --build --wait
	$(PROD) exec -T backend python manage.py import_books
	@echo "운영 구성: http://localhost:$(PROD_PORT)"

stop:
	docker compose down --remove-orphans
	$(PROD) down --remove-orphans

clean:
	@echo "개발·운영 구성의 컨테이너와 DB 데이터를 모두 삭제합니다."
	docker compose down -v --remove-orphans
	$(PROD) down -v --remove-orphans

demoreset:
	@docker compose ps --status running --services 2>/dev/null | grep -qx backend || { echo "개발 모드가 떠 있지 않습니다. 먼저: make dev"; exit 1; }
	docker compose exec -T backend python manage.py seed_demo --reset
