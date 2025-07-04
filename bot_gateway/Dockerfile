FROM python:3.12-slim

# Создаем корневую директорию для нашего приложения
WORKDIR /app_root

# Устанавливаем переменную окружения PYTHONPATH.
# Это скажет Python: "Когда ищешь модули, загляни еще и в /app_root"
ENV PYTHONPATH=/app_root

# Копируем requirements.txt в корень, чтобы не инвалидировать кэш
COPY bot_gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения в папку app внутри /app_root
COPY bot_gateway/app /app_root/app
# Копируем общие схемы
COPY shared /app_root/shared
