from aiogram import Bot
from app.broker import broker
from shared.schemas.schemas import BroadcastTask

@broker.subscriber("broadcast_tasks")
async def handle_broadcast_task(task: BroadcastTask):
    bot = Bot(token=task.bot_token)
    try:
        for user_id in task.user_ids:
            try:
                await bot.send_message(user_id, task.message_text, parse_mode="HTML")
            except Exception:
                # Логируем ошибку, но не останавливаем рассылку
                pass
    finally:
        await bot.session.close()