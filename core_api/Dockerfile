FROM python:3.12-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Устанавливаем зависимости
COPY core_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения И общие схемы
COPY core_api/app /app
COPY shared /shared