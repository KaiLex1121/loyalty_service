from aiogram import Dispatcher
from app.bots.employee_bot.handlers.general import main_menu, onboarding, profile


def setup_employee_bot_handlers(dp: Dispatcher):
    dp.include_router(onboarding.router)
    dp.include_router(main_menu.router)
    dp.include_router(profile.router)
