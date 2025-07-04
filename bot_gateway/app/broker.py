from faststream.rabbit import RabbitBroker
from app.core.settings import settings

broker = RabbitBroker(settings.RABBITMQ.RABBITMQ_URI)