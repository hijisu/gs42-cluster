# syntax=docker/dockerfile:1
# 백엔드 이미지. 개발용(dev) 스테이지만 있고, 운영용(prod, gunicorn) 스테이지는 #19에서 추가한다.
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
