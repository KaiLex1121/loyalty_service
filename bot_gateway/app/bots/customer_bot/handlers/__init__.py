from aiogram import Dispatcher
from app.bots.customer_bot.handlers.general import main_menu, onboarding, view_profile

def setup_customer_bot_handlers(dp: Dispatcher):
    dp.include_router(main_menu.router)
    dp.include_router(onboarding.router)
    dp.include_router(view_profile.router)