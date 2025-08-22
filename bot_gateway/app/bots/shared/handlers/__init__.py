from aiogram import Dispatcher
from app.bots.shared.handlers import test


def setup_customer_bot_handlers(dp: Dispatcher):
    dp.include_router(test.router)