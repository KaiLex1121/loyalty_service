from faststream.rabbit import RabbitBroker
from app.core.settings import settings

# Формируем URL для RabbitMQ из переменных окружения

broker = RabbitBroker(settings.RABBITMQ.RABBITMQ_URI)