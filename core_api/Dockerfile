FROM python:3.12-slim

WORKDIR /app_root
ENV PYTHONPATH=/app_root

# 1. Устанавливаем зависимости сервиса
COPY core_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Копируем и устанавливаем shared
COPY shared /shared
RUN pip install -e /shared

# 3. Копируем код сервиса
COPY core_api/app /app_root/app

# 4. Запускаем uvicorn по умолчанию
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
