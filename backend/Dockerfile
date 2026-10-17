# syntax=docker/dockerfile:1
# 백엔드 이미지. dev: 개발용(소스 볼륨 마운트, runserver) / prod: 운영 구성(gunicorn, 소스 포함, 비루트).
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

COPY requirements.txt requirements-dev.txt ./

FROM base AS dev
RUN pip install -r requirements-dev.txt
# 소스는 compose에서 볼륨으로 마운트한다(코드 수정이 바로 반영됨).
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]

FROM base AS prod
RUN pip install -r requirements.txt \
    && useradd --system --uid 10001 --no-create-home app
COPY . .
USER app
EXPOSE 8000
# 시작할 때 migrate 후 gunicorn 으로 실행한다. 워커 수는 GUNICORN_WORKERS 로 조정한다.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2} --access-logfile -"]
