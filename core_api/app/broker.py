from app.core.settings import settings
from faststream.rabbit.fastapi import RabbitRouter

from shared.schemas.schemas import BroadcastTask

faststream_router = RabbitRouter(settings.RABBITMQ.RABBITMQ_URI)
