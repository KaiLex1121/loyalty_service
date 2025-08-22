from app.bots.employee_bot.handlers.general import onboarding, main_menu, view_profile
from aiogram import Dispatcher

def setup_employee_bot_handlers(dp: Dispatcher):
    dp.include_router(onboarding.router)
    dp.include_router(main_menu.router)
    dp.include_router(view_profile.router)