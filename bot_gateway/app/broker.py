from app.core.settings import settings
from faststream.rabbit.fastapi import RabbitRouter

faststream_router = RabbitRouter(settings.RABBITMQ.RABBITMQ_URI)
