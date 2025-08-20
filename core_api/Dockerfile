FROM python:3.12-slim

# Создаем корневую директорию для нашего приложения
WORKDIR /app_root

# Устанавливаем переменную окружения PYTHONPATH.
# Это скажет Python: "Когда ищешь модули, загляни еще и в /app_root"
ENV PYTHONPATH=/app_root

# Копируем requirements.txt в корень, чтобы не инвалидировать кэш
COPY core_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения в корень /app_root
COPY core_api /app_root
# Копируем общие схемы
COPY shared /app_root/shared
