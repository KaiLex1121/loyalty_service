from aiogram import Bot
from app.broker import faststream_router
from shared.schemas.schemas import BotManagementEvent

@faststream_router.subscriber("bot_management_events")
async def handle_bot_management(event: BotManagementEvent):
    print(f"Received bot management event: {event.event_type} for token ...{event.token[-4:]}")
    bot = Bot(token=event.token)
    try:
        if event.event_type in ["bot_created", "bot_activated"]:
            if event.webhook_url:
                await bot.set_webhook(event.webhook_url, drop_pending_updates=True)
                print(f"Webhook SET for token ...{event.token[-4:]}")

        elif event.event_type in ["bot_deactivated", "bot_deleted"]:
            await bot.delete_webhook()
            print(f"Webhook DELETED for token ...{event.token[-4:]}")
    finally:
        await bot.session.close()