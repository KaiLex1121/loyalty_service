from shared.schemas.schemas import BotManagementEvent, BroadcastTask
from app.broker import faststream_router


broadcast_publisher = faststream_router.publisher(
    "broadcast_tasks", schema=BroadcastTask
)

bot_management_events_publisher = faststream_router.publisher(
    "bot_management_events", schema=BotManagementEvent
)