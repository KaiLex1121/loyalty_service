from faststream.rabbit.fastapi import RabbitRouter
from app.core.settings import settings
from shared.schemas.schemas import BroadcastTask


faststream_router = RabbitRouter(settings.RABBITMQ.RABBITMQ_URI)
